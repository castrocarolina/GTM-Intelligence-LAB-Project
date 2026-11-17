from __future__ import annotations

import pandas as pd

from src.models.ltv import aggregate_ltv_by_segment, estimate_customer_ltv
from src.models.rfm_segmentation import analyze_k_selection, prepare_rfm_features, segment_customers


def test_prepare_rfm_features_generates_expected_columns() -> None:
    customer_base = pd.DataFrame(
        {
            "customer_id": ["A", "B", "C"],
            "order_count": [2, 1, 4],
            "total_revenue": [600.0, 150.0, 1400.0],
            "avg_order_value": [300.0, 150.0, 350.0],
            "recency_days": [20.0, 85.0, 15.0],
            "customer_tenure_days": [180.0, 90.0, 365.0],
        }
    )

    rfm = prepare_rfm_features(customer_base)

    assert {"customer_id", "recency_days", "frequency", "monetary"}.issubset(rfm.columns)
    assert rfm["frequency"].tolist() == [2.0, 1.0, 4.0]


def test_k_selection_returns_valid_analysis() -> None:
    customer_base = pd.DataFrame(
        {
            "customer_id": [f"C{i}" for i in range(1, 11)],
            "order_count": [5, 5, 4, 4, 3, 3, 1, 1, 1, 1],
            "total_revenue": [500, 520, 440, 430, 250, 270, 80, 90, 95, 85],
            "avg_order_value": [100, 104, 110, 107, 83, 90, 80, 90, 95, 85],
            "recency_days": [10, 8, 14, 15, 32, 45, 80, 90, 100, 105],
            "customer_tenure_days": [300, 310, 280, 260, 180, 200, 120, 130, 90, 100],
        }
    )

    rfm = prepare_rfm_features(customer_base)
    analysis = analyze_k_selection(rfm, k_values=range(2, 5))

    assert analysis["selected_k"] in {2, 3, 4}
    assert analysis["elbow_k"] in {2, 3, 4}


def test_segment_customers_returns_cluster_summary() -> None:
    customer_base = pd.DataFrame(
        {
            "customer_id": [f"C{i}" for i in range(1, 21)],
            "order_count": [5, 4, 3, 3, 2, 2, 1, 1, 1, 1] * 2,
            "total_revenue": [1000, 700, 500, 450, 350, 300, 90, 110, 130, 100] * 2,
            "avg_order_value": [200, 175, 167, 150, 175, 150, 90, 110, 130, 100] * 2,
            "recency_days": [10, 15, 18, 20, 25, 35, 60, 70, 80, 90] * 2,
            "customer_tenure_days": [400, 300, 260, 330, 190, 180, 100, 120, 110, 105] * 2,
        }
    )

    segment_table, summary, _, _, _ = segment_customers(customer_base)

    assert not segment_table.empty
    assert not summary.empty
    assert {"segment_name", "customers", "avg_recency"}.issubset(summary.columns)


def test_estimate_customer_ltv_returns_nonnegative_values() -> None:
    customer_base = pd.DataFrame(
        {
            "customer_id": ["A", "B", "C"],
            "order_count": [2, 1, 4],
            "avg_order_value": [200.0, 100.0, 250.0],
            "recency_days": [30.0, 120.0, 15.0],
            "customer_tenure_days": [300.0, 90.0, 450.0],
            "total_revenue": [400.0, 100.0, 1000.0],
        }
    )

    ltv = estimate_customer_ltv(customer_base)

    assert ltv["ltv"].ge(0).all()
    assert ltv["customer_id"].nunique() == 3


def test_aggregate_ltv_by_segment_works() -> None:
    customer_base = pd.DataFrame(
        {
            "customer_id": ["A", "B", "C"],
            "order_count": [3, 2, 1],
            "avg_order_value": [250.0, 200.0, 100.0],
            "recency_days": [20.0, 30.0, 60.0],
            "customer_tenure_days": [300.0, 180.0, 60.0],
            "total_revenue": [750.0, 400.0, 100.0],
        }
    )
    segment_table = pd.DataFrame(
        {
            "customer_id": ["A", "B", "C"],
            "segment_name": ["Loyal High-Value", "Core / Growth", "Occasional"],
        }
    )

    by_segment = aggregate_ltv_by_segment(customer_base, segment_table)

    assert {"segment_name", "segment_size", "total_ltv"}.issubset(by_segment.columns)
    assert by_segment["total_ltv"].sum() > 0
