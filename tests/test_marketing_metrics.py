from __future__ import annotations

import pandas as pd

from src.data.pipeline import build_customer_base, ensure_raw_data
from src.features.marketing_metrics import calculate_business_summary, calculate_payback, get_funnel_snapshot


def test_calculate_business_summary_basic_values() -> None:
    orders = pd.DataFrame(
        {
            "customer_id": ["C1", "C1", "C2", "C3"],
            "order_id": ["O1", "O2", "O3", "O4"],
            "order_purchase_timestamp": [
                "2024-01-02",
                "2024-02-05",
                "2024-01-09",
                "2024-03-12",
            ],
            "order_value": [150.0, 250.0, 90.0, 120.0],
        }
    )
    marketing_spend = pd.DataFrame({"spend": [500.0, 700.0]})

    summary = calculate_business_summary(orders, marketing_spend)

    assert summary["total_revenue"] == 610.0
    assert summary["order_count"] == 4
    assert summary["avg_order_value"] == 152.5
    assert summary["repeat_purchase_rate"] == 0.3333
    assert summary["cac"] > 0


def test_calculate_payback_uses_margin_logic() -> None:
    orders = pd.DataFrame(
        {
            "customer_id": ["A", "A", "B"],
            "order_id": ["O1", "O2", "O3"],
            "order_purchase_timestamp": ["2024-01-05", "2024-02-05", "2024-01-20"],
            "order_value": [200.0, 150.0, 100.0],
        }
    )
    marketing_spend = pd.DataFrame({"spend": [500.0, 400.0]})

    payback = calculate_payback(orders, marketing_spend, gross_margin_rate=0.35)

    assert payback > 0
    assert payback == round(payback, 2)


def test_customer_base_build_has_expected_columns() -> None:
    customers = pd.DataFrame(
        {
            "customer_id": ["A", "B"],
            "signup_date": ["2023-01-01", "2023-02-01"],
        }
    )
    orders = pd.DataFrame(
        {
            "customer_id": ["A", "A", "B"],
            "order_id": ["O1", "O2", "O3"],
            "order_purchase_timestamp": ["2023-02-10", "2023-05-13", "2023-03-10"],
            "order_value": [50.0, 75.0, 60.0],
        }
    )

    base = build_customer_base(customers, orders)

    assert {"customer_id", "signup_date", "total_revenue", "order_count", "repeat_purchase_flag"}.issubset(base.columns)
    assert base["customer_id"].nunique() == 2
    assert base.loc[base["customer_id"] == "A", "order_count"].iloc[0] == 2


def test_pipeline_generates_mock_data_when_missing() -> None:
    customers, orders, marketing_spend = ensure_raw_data(".")

    assert not customers.empty
    assert not orders.empty
    assert not marketing_spend.empty
    assert "spend" in marketing_spend.columns
    assert "order_value" in orders.columns


def test_funnel_snapshot_has_metric_names() -> None:
    orders = pd.DataFrame(
        {
            "customer_id": ["A", "B", "C"],
            "order_id": ["O1", "O2", "O3"],
            "order_purchase_timestamp": ["2024-01-05", "2024-02-02", "2024-02-24"],
            "order_value": [100.0, 200.0, 300.0],
        }
    )
    marketing_spend = pd.DataFrame({"spend": [1500.0, 500.0]})

    snapshot = get_funnel_snapshot(orders, marketing_spend)

    assert {"Revenue", "Avg. order value", "Repeat purchase rate", "CAC", "ROAS", "Payback (months)"}.issubset(snapshot["metric"].unique())
