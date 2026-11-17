"""Anthropic-powered GTM brief generation with a safe fallback.

The app prefers the Anthropic API when an API key is configured. If the key is
missing or the call fails, the system falls back to a deterministic template so
that the product still works in local demo mode without exposing secrets.
"""

from __future__ import annotations

import json
import os
from typing import Any

from anthropic import APIError, Anthropic
from dotenv import load_dotenv


def _load_api_key() -> str | None:
    load_dotenv()
    return os.getenv("ANTHROPIC_API_KEY")


def _fallback_brief(segment_name: str, segment_profile: dict[str, Any]) -> dict[str, Any]:
    segment = segment_name or "segment"
    total_ltv = float(segment_profile.get("total_ltv", segment_profile.get("avg_ltv", 0.0) or 0.0))
    total_revenue = float(segment_profile.get("total_revenue", 0.0) or 0.0)
    customers = int(segment_profile.get("customers", 0) or 0)

    if "Loyal" in segment or "High-Value" in segment:
        persona = "Repeat buyers with high willingness to pay and strong retention potential."
        pain = "They want a more premium, low-friction experience and clear proof of value before expanding spend."
        value_prop = "A premium, reliable offer with faster delivery and tailored upsell journeys."
        channels = ["email", "brand", "retargeting"]
        message_variants = [
            "Premium support and continuity for customers who buy repeatedly.",
            "Fewer decisions, stronger trust, and better retention across recurring orders.",
            "A playbook for better recurring value without sacrificing convenience."
        ]
    elif "At Risk" in segment:
        persona = "Past buyers with declining engagement and lower recent purchase frequency."
        pain = "They are uncertain about continued value and are more sensitive to friction or price changes."
        value_prop = "A reactivation offer that reduces friction and shows tangible, quick wins."
        channels = ["email", "social", "search"]
        message_variants = [
            "Come back with a simpler, higher-value experience and a win-back offer.",
            "Re-engage with a tailored reminder tied to value they already know.",
            "We make it easier to get back to the products and outcomes they already trust."
        ]
    elif "Occasional" in segment:
        persona = "Low-frequency buyers who respond to strong offers and simple positioning."
        pain = "They are not fully convinced and need a clear reason to buy again beyond a generic discount."
        value_prop = "A straightforward value message that makes the product feel worth the first decision."
        channels = ["search", "social", "affiliate"]
        message_variants = [
            "A better product fit for the moments when they are ready to act.",
            "A fast, low-friction way to try a solution that fits their life or business.",
            "Prove the value quickly and make the next step feel obvious."
        ]
    else:
        persona = "Balanced buyers with moderate spending but room to grow through targeted reach."
        pain = "They need clearer differentiation and buying confidence before expanding."
        value_prop = "A clear and credible offer that balances trust, convenience, and measurable wins."
        channels = ["search", "social", "email"]
        message_variants = [
            "A practical offer that balances value, trust, and simplicity.",
            "A straightforward path to results with less friction and more clarity.",
            "Better customer fit, easier buying, and stronger confidence in the decision."
        ]

    if total_ltv > 0:
        value_statement = f"This segment contributes an estimated {total_ltv:,.0f} in cumulative LTV potential and {total_revenue:,.0f} in current revenue across {customers} customers."
    else:
        value_statement = "This segment has credible upside if we improve conversion efficiency and retention."

    return {
        "persona": persona,
        "pain_main": pain,
        "value_proposition": value_prop,
        "message_variants": message_variants,
        "recommended_channel": channels[0],
        "objections": [
            "Price sensitivity or unclear value perception",
            "Distrust due to inconsistent messaging or weak proof",
            "Low urgency without a compelling trigger"
        ],
        "ab_tests": [
            {
                "hypothesis": "A message focused on retention and ROI will outperform a generic acquisition headline.",
                "variant_a": "Value-first message with proof points and a stronger CTA.",
                "variant_b": "Offer-focused message tied to a lower-friction trial or win-back path."
            },
            {
                "hypothesis": "A channel-first plan using the recommended channel will improve conversion efficiency for this segment.",
                "variant_a": "Priority channel investment with tuned audience sequencing.",
                "variant_b": "Balanced mix with a lighter investment in the second-best channel."
            }
        ],
        "background_context": value_statement,
        "source": "fallback",
        "note": "Generated locally because no Anthropic API key was configured.",
    }


def _parse_brief_response(raw_content: str) -> dict[str, Any] | None:
    try:
        cleaned = raw_content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`\n ")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()
        payload = json.loads(cleaned)
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        return None
    return None


def generate_gtm_brief(
    segment_name: str,
    segment_profile: dict[str, Any],
    model_name: str | None = None,
) -> dict[str, Any]:
    """Generate or fallback a GTM brief for a segment.

    The model name can be overridden from code or via the environment variable
    ANTHROPIC_MODEL. We keep the main default explicit and clear for interviews.
    """
    fallback = _fallback_brief(segment_name, segment_profile)
    api_key = _load_api_key()
    if not api_key:
        return fallback

    selected_model = model_name or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

    client = Anthropic(api_key=api_key)
    prompt = (
        "You are a product marketing strategist. Return valid JSON only with keys: "
        "persona, pain_main, value_proposition, message_variants, recommended_channel, "
        "objections, ab_tests, background_context. "
        f"Segment: {segment_name}. "
        f"Profile: {json.dumps(segment_profile, ensure_ascii=False, default=str)}. "
        "Keep the response business-ready and explainable for an interview portfolio."
    )
    try:
        response = client.messages.create(
            model=selected_model,
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )
        if not getattr(response, "content", None):
            fallback["note"] = "Anthropic returned no content; the local fallback brief was used."
            return fallback
        raw_text = "".join(part.text for part in response.content if getattr(part, "type", "") == "text")
        parsed = _parse_brief_response(raw_text)
        if parsed:
            brief = {**fallback, **parsed}
            brief["source"] = "anthropic"
            brief["note"] = "Generated by the Anthropic API."
            return brief
        fallback["note"] = "Anthropic returned a response that was not valid JSON; the local fallback brief was used."
    except APIError as exc:
        fallback["note"] = (
            f"Anthropic request failed ({type(exc).__name__}); the local fallback brief was used."
        )

    return fallback
