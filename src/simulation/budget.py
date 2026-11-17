"""Simple budget reallocation simulator.

This module is deliberately transparent and uses a few explicit assumptions to
translate a channel move into an estimated impact on revenue and LTV. It is a
planning tool, not a causal measurement model.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

CHANNEL_EFFICIENCY = {
    "search": 1.10,
    "social": 1.00,
    "email": 1.35,
    "affiliate": 0.90,
    "brand": 1.20,
}

SEGMENT_CHANNEL_PRESET = {
    "Loyal High-Value": {"email": 1.30, "brand": 1.20, "search": 0.95, "social": 0.90, "affiliate": 0.80},
    "At Risk": {"email": 1.35, "social": 1.05, "search": 0.90, "affiliate": 0.70, "brand": 0.80},
    "Occasional": {"search": 1.15, "social": 1.10, "email": 0.95, "affiliate": 1.00, "brand": 0.70},
    "New / Growing": {"social": 1.25, "search": 1.10, "email": 0.95, "affiliate": 1.00, "brand": 0.75},
    "Core / Growth": {"search": 1.15, "email": 1.10, "social": 1.00, "affiliate": 0.95, "brand": 1.05},
}


def estimate_budget_reallocation(
    segment_name: str,
    segment_summary: pd.DataFrame,
    marketing_spend: pd.DataFrame,
    source_channel: str,
    target_channel: str,
    reallocation_pct: float,
) -> dict[str, Any]:
    """Estimate how moving budget between channels affects this segment's revenue and LTV.

    Assumptions:
    - We only use the observed spend by channel as a planning base.
    - A channel move changes expected contribution in proportion to channel efficiency times segment affinity.
    - The estimated revenue effect is a directional planning heuristic, not a causal claim.
    """
    if source_channel == target_channel:
        raise ValueError("Source and target channels must be different.")

    if not 0 < reallocation_pct <= 100:
        raise ValueError("reallocation_pct must be between 0 and 100.")

    segment_row = segment_summary[segment_summary["segment_name"] == segment_name]
    if segment_row.empty:
        raise ValueError(f"Segment '{segment_name}' not found in segment_summary.")
    segment_row = segment_row.iloc[0]

    spend_by_channel = (
        marketing_spend.groupby("channel", as_index=False)["spend"].sum().rename(columns={"spend": "total_spend"})
    )
    source_budget = float(spend_by_channel.loc[spend_by_channel["channel"] == source_channel, "total_spend"].sum())
    target_budget = float(spend_by_channel.loc[spend_by_channel["channel"] == target_channel, "total_spend"].sum())

    source_shift = source_budget * (reallocation_pct / 100.0)
    # A reallocation transfers the same amount out of one channel and into the
    # other; it must not increase the total budget.
    target_shift = source_shift

    source_efficiency = CHANNEL_EFFICIENCY.get(source_channel, 1.0)
    target_efficiency = CHANNEL_EFFICIENCY.get(target_channel, 1.0)
    segment_affinity = SEGMENT_CHANNEL_PRESET.get(segment_name, {}).get(target_channel, 1.0)
    source_affinity = SEGMENT_CHANNEL_PRESET.get(segment_name, {}).get(source_channel, 1.0)

    segment_revenue = float(segment_row.get("total_revenue", 0.0) or 0.0)
    segment_ltv = float(segment_row.get("total_ltv", segment_row.get("avg_ltv", 0.0) or 0.0))
    if segment_ltv == 0:
        segment_ltv = float(segment_row.get("avg_ltv", 0.0) or 0.0) * float(segment_row.get("customers", 1) or 1)

    revenue_multiplier = (target_efficiency * segment_affinity) - (source_efficiency * source_affinity)
    estimated_revenue_delta = segment_revenue * (reallocation_pct / 100.0) * max(revenue_multiplier, -0.5) * 0.35
    estimated_ltv_delta = segment_ltv * (reallocation_pct / 100.0) * max((target_efficiency - source_efficiency), 0.0) * 0.25

    result = {
        "segment_name": segment_name,
        "source_channel": source_channel,
        "target_channel": target_channel,
        "reallocation_pct": reallocation_pct,
        "source_budget_before": round(source_budget, 2),
        "source_budget_after": round(source_budget - source_shift, 2),
        "target_budget_before": round(target_budget, 2),
        "target_budget_after": round(target_budget + target_shift, 2),
        "estimated_revenue_delta": round(estimated_revenue_delta, 2),
        "estimated_ltv_delta": round(estimated_ltv_delta, 2),
        "estimated_total_revenue_after": round(segment_revenue + estimated_revenue_delta, 2),
        "estimated_total_ltv_after": round(segment_ltv + estimated_ltv_delta, 2),
        "assumptions": {
            "channel_efficiencies": CHANNEL_EFFICIENCY,
            "segment_affinity": SEGMENT_CHANNEL_PRESET.get(segment_name, {}),
            "note": "This is a directional scenario: it assumes efficiency differs by channel and that the segment responds differently by media type."
        },
    }
    return result
