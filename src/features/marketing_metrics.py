"""Business and marketing KPIs for the GTM Intelligence Lab."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _as_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def calculate_business_summary(
    orders: pd.DataFrame,
    marketing_spend: pd.DataFrame | None = None,
    customers: pd.DataFrame | None = None,
    gross_margin_rate: float = 0.35,
) -> dict[str, Any]:
    """Return a compact KPI summary for the business and acquisition funnel.

    The market spend dataframe is treated as a planning assumption and should be
    interpreted as simulated, not observed, spend by channel and month.
    """
    orders = orders.copy()
    orders["order_value"] = pd.to_numeric(orders.get("order_value", 0), errors="coerce").fillna(0.0)
    orders["order_purchase_timestamp"] = _as_datetime(orders.get("order_purchase_timestamp", pd.Timestamp.now()))

    total_revenue = float(orders["order_value"].sum())
    order_count = int(len(orders))
    avg_order_value = float(total_revenue / order_count) if order_count else 0.0

    if customers is not None:
        customer_count = int(customers["customer_id"].nunique()) if "customer_id" in customers.columns else 0
    else:
        customer_count = int(orders["customer_id"].nunique()) if "customer_id" in orders.columns else 0

    repeat_purchase_rate = 0.0
    if "customer_id" in orders.columns:
        customer_orders = orders.groupby("customer_id").size()
        repeat_purchase_rate = float((customer_orders > 1).mean()) if not customer_orders.empty else 0.0

    spend_total = 0.0
    if marketing_spend is not None and "spend" in marketing_spend.columns:
        spend_total = float(pd.to_numeric(marketing_spend["spend"], errors="coerce").fillna(0.0).sum())

    cac = float(spend_total / customer_count) if customer_count else 0.0
    roas = float(total_revenue / spend_total) if spend_total else 0.0

    period_revenue = orders.groupby(orders["order_purchase_timestamp"].dt.to_period("M").astype(str))["order_value"].sum()
    monthly_margin = period_revenue * gross_margin_rate
    avg_monthly_margin = float(monthly_margin.mean()) if not monthly_margin.empty else 0.0
    payback_months = float(spend_total / avg_monthly_margin) if avg_monthly_margin else 0.0

    return {
        "total_revenue": round(total_revenue, 2),
        "order_count": order_count,
        "avg_order_value": round(avg_order_value, 2),
        "repeat_purchase_rate": round(repeat_purchase_rate, 4),
        "customer_count": customer_count,
        "cac": round(cac, 2),
        "roas": round(roas, 4),
        "payback_months": round(payback_months, 2),
        "monthly_revenue": period_revenue.round(2).to_dict(),
        "gross_margin_rate": gross_margin_rate,
    }


def calculate_payback(
    orders: pd.DataFrame,
    marketing_spend: pd.DataFrame,
    gross_margin_rate: float = 0.35,
) -> float:
    """Estimate simple payback months from simulated acquisition spend.

    Payback = total spend / average monthly gross margin contribution.
    This is deliberately simple and should be used for planning, not financial
    accounting.
    """
    summary = calculate_business_summary(
        orders=orders,
        marketing_spend=marketing_spend,
        gross_margin_rate=gross_margin_rate,
    )
    return float(summary["payback_months"])


def get_funnel_snapshot(
    orders: pd.DataFrame,
    marketing_spend: pd.DataFrame,
    customers: pd.DataFrame | None = None,
    gross_margin_rate: float = 0.35,
) -> pd.DataFrame:
    """Return a KPI table that is easy to display in Streamlit."""
    summary = calculate_business_summary(
        orders=orders,
        marketing_spend=marketing_spend,
        customers=customers,
        gross_margin_rate=gross_margin_rate,
    )

    metrics = [
        ("Revenue", summary["total_revenue"]),
        ("Avg. order value", summary["avg_order_value"]),
        ("Repeat purchase rate", summary["repeat_purchase_rate"]),
        ("CAC", summary["cac"]),
        ("ROAS", summary["roas"]),
        ("Payback (months)", summary["payback_months"]),
    ]
    return pd.DataFrame(metrics, columns=["metric", "value"])
