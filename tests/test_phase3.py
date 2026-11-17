from __future__ import annotations

import pandas as pd

from src.llm.briefs import generate_gtm_brief
from src.simulation.budget import estimate_budget_reallocation


def test_generate_gtm_brief_returns_structured_payload() -> None:
    segment_profile = {
        "segment_name": "Loyal High-Value",
        "customers": 120,
        "avg_recency": 30,
        "avg_frequency": 4.5,
        "avg_monetary": 280,
        "total_revenue": 55000,
        "total_ltv": 180000,
    }

    brief = generate_gtm_brief("Loyal High-Value", segment_profile)

    assert brief["source"] in {"fallback", "anthropic"}
    assert "persona" in brief
    assert len(brief["message_variants"]) == 3
    assert len(brief["ab_tests"]) == 2


def test_budget_reallocation_estimates_directional_change() -> None:
    segment_summary = pd.DataFrame(
        [
            {
                "segment_name": "Loyal High-Value",
                "customers": 120,
                "total_revenue": 50000,
                "total_ltv": 150000,
            }
        ]
    )
    marketing_spend = pd.DataFrame(
        {
            "channel": ["search", "email", "social", "brand"],
            "spend": [20000, 15000, 12000, 11000],
        }
    )

    simulation = estimate_budget_reallocation(
        segment_name="Loyal High-Value",
        segment_summary=segment_summary,
        marketing_spend=marketing_spend,
        source_channel="search",
        target_channel="email",
        reallocation_pct=20,
    )

    assert simulation["source_channel"] == "search"
    assert simulation["target_channel"] == "email"
    assert simulation["estimated_revenue_delta"] != 0
    amount_moved = simulation["source_budget_before"] * 0.20
    assert simulation["source_budget_before"] - simulation["source_budget_after"] == amount_moved
    assert simulation["target_budget_after"] - simulation["target_budget_before"] == amount_moved
    assert (
        simulation["source_budget_after"] + simulation["target_budget_after"]
        == simulation["source_budget_before"] + simulation["target_budget_before"]
    )
