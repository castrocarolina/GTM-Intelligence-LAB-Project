"""Simple and explainable customer value forecasting.

This project uses a transparent LTV estimator as the default. The logic is easy
for interviewers to follow and is robust for a synthetic or Olist-like dataset
without requiring a full survival-model pipeline from day one.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def estimate_customer_ltv(
    customer_base: pd.DataFrame,
    gross_margin_rate: float = 0.35,
    annualization_days: int = 365,
) -> pd.DataFrame:
    """Estimate customer LTV using a simple frequency-based model.

    Formula:
      expected_annual_orders = annualization_days / avg_customer_interval
      ltv = expected_annual_orders * avg_order_value * gross_margin_rate

    The model intentionally keeps the calculation visible and explainable while
    still producing an estimate of customer-level value for segment reporting.
    """
    df = customer_base.copy()
    df["order_count"] = pd.to_numeric(df.get("order_count", 0), errors="coerce").fillna(0)
    df["avg_order_value"] = pd.to_numeric(df.get("avg_order_value", 0), errors="coerce").fillna(0)
    df["recency_days"] = pd.to_numeric(df.get("recency_days", 0), errors="coerce").fillna(0)
    df["customer_tenure_days"] = pd.to_numeric(df.get("customer_tenure_days", 0), errors="coerce").fillna(0)
    df["total_revenue"] = pd.to_numeric(df.get("total_revenue", 0), errors="coerce").fillna(0)

    df["average_interval_days"] = np.where(
        df["order_count"] > 1,
        (df["customer_tenure_days"] / (df["order_count"] - 1)).clip(lower=30),
        np.where(df["order_count"] == 1, annualization_days, annualization_days),
    )
    df["expected_annual_orders"] = annualization_days / df["average_interval_days"].clip(lower=30)

    recency_factor = 1.0 - (df["recency_days"] / max(annualization_days * 2, 1))
    recency_factor = recency_factor.clip(lower=0.25, upper=1.0)

    df["ltv"] = (df["expected_annual_orders"] * df["avg_order_value"] * gross_margin_rate * recency_factor).round(2)
    df["ltv"] = df["ltv"].clip(lower=0)
    return df[["customer_id", "ltv", "order_count", "avg_order_value", "recency_days", "customer_tenure_days"]].copy()


def aggregate_ltv_by_segment(
    customer_base: pd.DataFrame,
    segment_table: pd.DataFrame,
    gross_margin_rate: float = 0.35,
) -> pd.DataFrame:
    """Aggregate LTV estimates by segment for business reporting."""
    ltv_table = estimate_customer_ltv(customer_base, gross_margin_rate=gross_margin_rate)
    segment_ltv = (
        segment_table[["customer_id", "segment_name"]]
        .merge(ltv_table[["customer_id", "ltv"]], on="customer_id", how="left")
        .groupby("segment_name", as_index=False)
        .agg(
            segment_size=("customer_id", "count"),
            total_ltv=("ltv", "sum"),
            avg_ltv=("ltv", "mean"),
        )
        .sort_values("total_ltv", ascending=False)
        .reset_index(drop=True)
    )
    return segment_ltv
