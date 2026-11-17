"""Pipeline for cleaning raw customer/order files and building the customer base."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .synthetic_data import generate_synthetic_orders


def ensure_raw_data(project_root: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load real Olist data if present; otherwise generate a deterministic mock.

    The synthetic dataset is explicitly documented as simulated and is meant only
    to make local development and demos possible before real production data is
    added to the repository.
    """
    root = Path(project_root)
    raw_dir = root / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    required_paths = [
        raw_dir / "customers.csv",
        raw_dir / "orders.csv",
        raw_dir / "marketing_spend_by_channel.csv",
    ]

    if all(path.exists() for path in required_paths):
        customers = pd.read_csv(raw_dir / "customers.csv")
        orders = pd.read_csv(raw_dir / "orders.csv")
        marketing_spend = pd.read_csv(raw_dir / "marketing_spend_by_channel.csv")
        return customers, orders, marketing_spend

    synthetic = generate_synthetic_orders(root / "data")
    return synthetic["customers"], synthetic["orders"], synthetic["marketing_spend"]


def _coerce_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def build_customer_base(
    customers: pd.DataFrame,
    orders: pd.DataFrame,
    output_dir: str | Path | None = None,
) -> pd.DataFrame:
    """Create a customer-level table with lifetime metrics and repeated purchase flags."""
    customers = customers.copy()
    orders = orders.copy()

    if "customer_unique_id" not in customers.columns and "customer_id" in customers.columns:
        customers["customer_unique_id"] = customers["customer_id"]
    if "customer_unique_id" not in orders.columns and "customer_id" in orders.columns:
        orders["customer_unique_id"] = orders["customer_id"]

    customers["signup_date"] = _coerce_datetime(customers.get("signup_date", pd.Timestamp.now()))
    orders["order_purchase_timestamp"] = _coerce_datetime(orders.get("order_purchase_timestamp", pd.Timestamp.now()))
    orders["order_value"] = pd.to_numeric(orders.get("order_value", 0), errors="coerce").fillna(0.0)

    customer_metrics = (
        orders.groupby("customer_unique_id", as_index=False)
        .agg(
            first_order_date=("order_purchase_timestamp", "min"),
            last_order_date=("order_purchase_timestamp", "max"),
            order_count=("order_id", "count"),
            total_revenue=("order_value", "sum"),
            avg_order_value=("order_value", "mean"),
        )
        .rename(columns={"customer_unique_id": "customer_id"})
    )

    customer_metrics["recency_days"] = (
        (pd.Timestamp.now().tz_localize(None) - customer_metrics["last_order_date"]).dt.days
    )
    customer_metrics["repeat_purchase_flag"] = customer_metrics["order_count"] > 1
    customer_metrics["customer_tenure_days"] = (
        (customer_metrics["last_order_date"] - customer_metrics["first_order_date"]).dt.days
    )

    customer_base = customers[["customer_unique_id", "signup_date"]].rename(columns={"customer_unique_id": "customer_id"}).copy()
    customer_base = customer_base.merge(customer_metrics, on="customer_id", how="left")
    customer_base["total_revenue"] = customer_base["total_revenue"].fillna(0.0)
    customer_base["avg_order_value"] = customer_base["avg_order_value"].fillna(0.0)
    customer_base["order_count"] = customer_base["order_count"].fillna(0)
    customer_base["recency_days"] = customer_base["recency_days"].fillna(9999)
    customer_base["repeat_purchase_flag"] = customer_base["repeat_purchase_flag"].fillna(False)
    customer_base["customer_tenure_days"] = customer_base["customer_tenure_days"].fillna(0)

    if output_dir is not None:
        output_path = Path(output_dir) / "customers_processed.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        customer_base.to_csv(output_path, index=False)

    return customer_base
