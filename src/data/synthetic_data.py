"""Synthetic Olist-like data and simulated marketing spend.

This module exists to support local development when the real Olist CSVs are
not available. The data is intentionally simple and deterministic so the
portfolio project remains reproducible and easy to explain in interviews.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def generate_synthetic_orders(
    data_dir: Path,
    seed: int = 42,
    n_customers: int = 450,
    n_orders: int = 1200,
) -> dict[str, pd.DataFrame]:
    """Create a small Olist-like dataset plus a simulated marketing plan."""
    rng = np.random.default_rng(seed)
    raw_dir = data_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    customer_ids = [f"CUST-{idx:04d}" for idx in range(1, n_customers + 1)]
    signup_dates = pd.to_datetime(
        np.random.default_rng(seed + 1).choice(
            pd.date_range("2022-01-01", "2023-12-31", periods=365), size=n_customers, replace=True
        )
    )
    customers = pd.DataFrame(
        {
            "customer_id": customer_ids,
            "customer_unique_id": customer_ids,
            "signup_date": signup_dates,
        }
    )

    order_rows: list[dict[str, object]] = []
    order_ids = [f"ORD-{idx:05d}" for idx in range(1, n_orders + 1)]

    for idx in range(n_orders):
        customer_id = customer_ids[rng.integers(0, len(customer_ids))]
        customer_signup = customers.loc[customers["customer_id"] == customer_id, "signup_date"].iloc[0]
        purchase_dt = customer_signup + pd.to_timedelta(
            int(rng.integers(5, 730)), unit="D"
        ) + pd.to_timedelta(int(rng.integers(0, 23)), unit="h")
        purchase_dt = purchase_dt + pd.to_timedelta(int(rng.integers(0, 59)), unit="min")
        order_value = float(max(25.0, rng.lognormal(mean=3.6, sigma=0.55) * 10))
        order_rows.append(
            {
                "order_id": order_ids[idx],
                "customer_id": customer_id,
                "customer_unique_id": customer_id,
                "order_purchase_timestamp": purchase_dt,
                "order_status": "delivered",
                "order_value": round(order_value, 2),
            }
        )

    orders = pd.DataFrame(order_rows)
    orders["order_month"] = orders["order_purchase_timestamp"].dt.to_period("M").astype(str)

    # Simulated spend by month and channel. Important: this is not real marketing
    # data and should be clearly treated as a planning assumption.
    month_index = pd.period_range("2023-01", periods=12, freq="M")
    channels = ["search", "social", "email", "affiliate", "brand"]
    spend_rows = []
    base_spend = {
        "search": 18000,
        "social": 15000,
        "email": 8000,
        "affiliate": 9000,
        "brand": 12000,
    }
    for month in month_index:
        for channel in channels:
            seasonal_multiplier = 1.0 + (month.month / 12) * 0.25
            spend = base_spend[channel] * seasonal_multiplier + rng.integers(500, 2500)
            spend_rows.append(
                {
                    "month": str(month),
                    "channel": channel,
                    "spend": round(spend, 2),
                    "clicks": int(spend / 4),
                    "impressions": int(spend * 8),
                    "attributed_orders": int(spend / 120),
                }
            )

    marketing_spend = pd.DataFrame(spend_rows)

    # Align with an Olist-like raw layout so the app can work with both synthetic and
    # real files without branching too much in the pipeline.
    olist_customers = customers[["customer_id", "customer_unique_id", "signup_date"]].copy()
    olist_orders = orders[
        [
            "order_id",
            "customer_id",
            "customer_unique_id",
            "order_status",
            "order_purchase_timestamp",
            "order_value",
        ]
    ].copy()
    olist_order_items = pd.DataFrame(
        {
            "order_id": olist_orders["order_id"],
            "product_id": [f"PRD-{idx:05d}" for idx in range(1, len(olist_orders) + 1)],
            "seller_id": [f"SELL-{idx:05d}" for idx in range(1, len(olist_orders) + 1)],
            "shipping_limit_date": olist_orders["order_purchase_timestamp"] + pd.to_timedelta(7, unit="D"),
            "price": olist_orders["order_value"],
            "freight_value": (olist_orders["order_value"] * 0.16).round(2),
        }
    )

    # Save to disk for local testing and app usage.
    customers_path = raw_dir / "customers.csv"
    orders_path = raw_dir / "orders.csv"
    order_items_path = raw_dir / "order_items.csv"
    spend_path = raw_dir / "marketing_spend_by_channel.csv"

    olist_customers.to_csv(customers_path, index=False)
    olist_orders.to_csv(orders_path, index=False)
    olist_order_items.to_csv(order_items_path, index=False)
    marketing_spend.to_csv(spend_path, index=False)

    return {
        "customers": olist_customers,
        "orders": olist_orders,
        "order_items": olist_order_items,
        "marketing_spend": marketing_spend,
    }
