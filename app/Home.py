"""Streamlit dashboard for the GTM Intelligence Lab."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data.pipeline import build_customer_base, ensure_raw_data
from src.llm.briefs import generate_gtm_brief
from src.models.ltv import aggregate_ltv_by_segment
from src.models.rfm_segmentation import segment_customers
from src.simulation.budget import estimate_budget_reallocation


ROOT = Path(__file__).resolve().parents[1]
CHANNEL_LABELS = {
    "search": "Paid search",
    "social": "Paid social",
    "email": "Email",
    "affiliate": "Affiliate",
    "brand": "Brand",
}


st.set_page_config(
    page_title="GTM Intelligence Lab",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root {
        --ink: #172a3a;
        --muted: #627587;
        --teal: #157a72;
        --teal-dark: #0e5c57;
        --canvas: #f5f8f8;
        --line: #e3ebeb;
    }

    .stApp { background: var(--canvas); color: var(--ink); }
    .block-container { max-width: 1280px; padding-top: 2rem; padding-bottom: 3rem; }
    html, body, [class*="css"] { font-family: 'Segoe UI', Arial, sans-serif; }
    h1, h2, h3 { font-family: 'Segoe UI', Arial, sans-serif; color: var(--ink); letter-spacing: -0.035em; }
    h1 { font-size: 2.65rem; font-weight: 800; }
    h2 { font-size: 1.65rem; font-weight: 700; }
    h3 { font-size: 1.15rem; font-weight: 700; }
    [data-testid="stMetric"] {
        background: #ffffff; padding: 1.15rem 1.3rem; border: 1px solid var(--line);
        border-radius: 14px; box-shadow: 0 3px 14px rgba(23, 42, 58, 0.035);
    }
    [data-testid="stMetricLabel"] { color: var(--muted); font-weight: 600; }
    [data-testid="stMetricValue"] { color: var(--ink); font-family: 'Segoe UI', Arial, sans-serif; }
    [data-testid="stTabs"] button { font-weight: 600; }
    [data-testid="stTabs"] button[aria-selected="true"] { color: var(--teal-dark); }
    .hero {
        background: linear-gradient(115deg, #123f46 0%, #157a72 65%, #41a38e 100%);
        border-radius: 20px; padding: 2rem 2.25rem; margin-bottom: 1.5rem;
        color: #ffffff; box-shadow: 0 12px 30px rgba(14, 92, 87, 0.14);
    }
    .hero h1 { color: #ffffff; margin: 0.2rem 0 0.45rem 0; }
    .hero p { color: #e0f0ec; margin: 0; font-size: 1.05rem; }
    .eyebrow {
        color: #a9ddd1; font-size: 0.75rem; font-weight: 700;
        letter-spacing: 0.14em; text-transform: uppercase;
    }
    .section-note { color: var(--muted); margin-top: -0.5rem; }
    .stButton > button[kind="primary"] {
        background: var(--teal); border-color: var(--teal); border-radius: 9px;
        font-weight: 700; padding: 0.55rem 1rem;
    }
    .stButton > button[kind="primary"]:hover { background: var(--teal-dark); border-color: var(--teal-dark); }
    .callout {
        border-left: 4px solid var(--teal); background: #eaf4f1;
        border-radius: 0 10px 10px 0; padding: 0.9rem 1rem; color: var(--ink);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Preparing customer and segment analysis...")
def load_analysis(
    root_path: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    root = Path(root_path)
    customers, orders, marketing_spend = ensure_raw_data(root)
    customer_base = build_customer_base(
        customers,
        orders,
        output_dir=root / "data" / "processed",
    )
    segment_table, segment_summary, k_analysis, _, _ = segment_customers(customer_base)
    segment_ltv = aggregate_ltv_by_segment(customer_base, segment_table)
    segment_overview = segment_summary.merge(segment_ltv, on="segment_name", how="left")
    return customer_base, orders, marketing_spend, segment_table, segment_overview, k_analysis


def format_brl(value: float) -> str:
    """Format a number using Brazilian Real separators."""
    formatted = f"{value:,.2f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def render_brief(brief: dict[str, Any]) -> None:
    if brief.get("source") == "fallback":
        st.info(brief.get("note", "Using the local brief template."))
    else:
        st.success("Brief generated with Anthropic.")

    st.markdown(f"**Persona**  \n{brief.get('persona', 'Not provided')}")
    st.markdown(f"**Main pain**  \n{brief.get('pain_main', 'Not provided')}")
    st.markdown(f"**Value proposition**  \n{brief.get('value_proposition', 'Not provided')}")
    st.markdown(f"**Recommended channel**  \n{CHANNEL_LABELS.get(brief.get('recommended_channel', ''), brief.get('recommended_channel', 'Not provided'))}")

    messages = brief.get("message_variants", [])
    if messages:
        st.markdown("#### Message directions")
        for index, message in enumerate(messages[:3], start=1):
            st.markdown(f"{index}. {message}")

    objections = brief.get("objections", [])
    if objections:
        st.markdown("#### Likely objections")
        for objection in objections:
            st.markdown(f"- {objection}")

    tests = brief.get("ab_tests", [])
    if tests:
        st.markdown("#### A/B test hypotheses")
        for index, test in enumerate(tests[:2], start=1):
            st.markdown(f"**{index}. {test.get('hypothesis', 'Hypothesis not provided')}**")
            st.caption(f"A: {test.get('variant_a', 'Not provided')}  |  B: {test.get('variant_b', 'Not provided')}")


customer_base, orders, marketing_spend, segment_table, segment_overview, k_analysis = load_analysis(str(ROOT))
synthetic_demo = (
    "customer_id" in customer_base.columns
    and customer_base["customer_id"].astype(str).str.startswith("CUST-").all()
)
data_label = "Synthetic demo data" if synthetic_demo else "Customer transaction data"

st.markdown(
    f"""
    <div class="hero">
        <div class="eyebrow">Marketing analytics · Data science · Product marketing</div>
        <h1>GTM Intelligence Lab</h1>
        <p>Turn customer behavior into segment value, sharper messaging, and testable go-to-market decisions.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption(f"Data mode: {data_label} · Channel spend is simulated for planning only.")

total_revenue = float(customer_base["total_revenue"].sum())
total_ltv = float(segment_overview["total_ltv"].sum())
repeat_rate = float(customer_base["repeat_purchase_flag"].mean())

metric_cols = st.columns(4)
metric_cols[0].metric("Customers", f"{len(customer_base):,}")
metric_cols[1].metric("Historical revenue", format_brl(total_revenue))
metric_cols[2].metric("Estimated segment LTV", format_brl(total_ltv))
metric_cols[3].metric("Repeat purchase rate", f"{repeat_rate:.1%}")

overview_tab, playbook_tab, budget_tab, methodology_tab = st.tabs(
    ["Segment overview", "GTM playbook", "Budget scenarios", "Method & assumptions"]
)

with overview_tab:
    st.subheader("Segment value and behavior")
    st.markdown(
        '<p class="section-note">Use the profile to decide where to protect retention, build consideration, or test acquisition.</p>',
        unsafe_allow_html=True,
    )

    table = segment_overview[
        [
            "segment_name",
            "customers",
            "share_of_customers",
            "avg_recency",
            "avg_frequency",
            "avg_monetary",
            "total_revenue",
            "total_ltv",
            "avg_ltv",
        ]
    ].sort_values("total_ltv", ascending=False).copy()
    table = table.rename(
        columns={
            "segment_name": "Segment",
            "customers": "Customers",
            "share_of_customers": "Customer share",
            "avg_recency": "Avg. recency (days)",
            "avg_frequency": "Avg. orders",
            "avg_monetary": "Avg. order value",
            "total_revenue": "Historical revenue",
            "total_ltv": "Estimated total LTV",
            "avg_ltv": "Estimated LTV / customer",
        }
    )
    st.dataframe(
        table,
        width="stretch",
        hide_index=True,
        column_config={
            "Customer share": st.column_config.ProgressColumn(
                "Customer share", format="percent", min_value=0, max_value=1
            ),
            "Historical revenue": st.column_config.NumberColumn(format="R$ %.2f"),
            "Estimated total LTV": st.column_config.NumberColumn(format="R$ %.2f"),
            "Estimated LTV / customer": st.column_config.NumberColumn(format="R$ %.2f"),
            "Avg. order value": st.column_config.NumberColumn(format="R$ %.2f"),
            "Avg. recency (days)": st.column_config.NumberColumn(format="%.0f"),
            "Avg. orders": st.column_config.NumberColumn(format="%.2f"),
        },
    )

    left, right = st.columns(2)
    with left:
        st.markdown("#### Estimated LTV by segment")
        ltv_chart = px.bar(
            segment_overview.sort_values("total_ltv", ascending=False),
            x="segment_name",
            y="total_ltv",
            color="total_ltv",
            color_continuous_scale=["#b7d9d2", "#157a72"],
            labels={"segment_name": "Segment", "total_ltv": "Estimated total LTV"},
        )
        ltv_chart.update_layout(showlegend=False, coloraxis_showscale=False, yaxis_title="Estimated LTV (R$)")
        st.plotly_chart(ltv_chart, width="stretch")
    with right:
        st.markdown("#### Segment size and purchase frequency")
        profile_chart = px.scatter(
            segment_overview,
            x="avg_recency",
            y="avg_frequency",
            size="customers",
            color="segment_name",
            hover_name="segment_name",
            hover_data={"avg_monetary": ":.2f", "avg_ltv": ":.2f", "customers": True},
            labels={
                "avg_recency": "Avg. days since last order",
                "avg_frequency": "Avg. number of orders",
                "segment_name": "Segment",
            },
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        profile_chart.update_layout(legend_title_text="Segment")
        st.plotly_chart(profile_chart, width="stretch")

with playbook_tab:
    st.subheader("Build a segment-specific GTM brief")
    st.markdown(
        '<p class="section-note">A strategic draft for discussion and testing. Review messaging before launch.</p>',
        unsafe_allow_html=True,
    )
    selected_segment = st.selectbox(
        "Customer segment",
        segment_overview["segment_name"].tolist(),
        key="brief_segment",
    )
    selected_profile = segment_overview.loc[
        segment_overview["segment_name"] == selected_segment
    ].iloc[0].to_dict()

    if st.button("Generate GTM brief", type="primary", key="generate_brief"):
        with st.spinner("Preparing the segment brief..."):
            st.session_state["generated_brief"] = generate_gtm_brief(selected_segment, selected_profile)
            st.session_state["generated_brief_segment"] = selected_segment

    if "generated_brief" in st.session_state:
        if st.session_state.get("generated_brief_segment") != selected_segment:
            st.caption("The displayed brief belongs to the previously selected segment. Generate again to refresh it.")
        render_brief(st.session_state["generated_brief"])

with budget_tab:
    st.subheader("Explore a budget shift")
    st.markdown(
        '<p class="section-note">Move a share of the source channel budget into another channel and inspect the directional estimate.</p>',
        unsafe_allow_html=True,
    )
    channels = sorted(marketing_spend["channel"].dropna().unique().tolist())
    if len(channels) < 2:
        st.warning("At least two marketing channels are required to run this scenario.")
    else:
        segment_for_simulation = st.selectbox(
            "Segment to analyze",
            segment_overview["segment_name"].tolist(),
            key="budget_segment",
        )
        source_channel = st.selectbox(
            "Move budget from",
            channels,
            key="source_channel",
            format_func=lambda value: CHANNEL_LABELS.get(value, value.title()),
        )
        targets = [channel for channel in channels if channel != source_channel]
        target_channel = st.selectbox(
            "Move budget to",
            targets,
            key="target_channel",
            format_func=lambda value: CHANNEL_LABELS.get(value, value.title()),
        )
        reallocation_pct = st.slider(
            "Share of source-channel budget to move",
            min_value=5,
            max_value=40,
            value=15,
            step=5,
            format="%d%%",
        )

        if st.button("Estimate scenario", type="primary", key="estimate_budget"):
            st.session_state["budget_scenario"] = estimate_budget_reallocation(
                segment_name=segment_for_simulation,
                segment_summary=segment_overview,
                marketing_spend=marketing_spend,
                source_channel=source_channel,
                target_channel=target_channel,
                reallocation_pct=reallocation_pct,
            )

        if "budget_scenario" in st.session_state:
            scenario = st.session_state["budget_scenario"]
            budget_cols = st.columns(2)
            budget_cols[0].metric(
                "Estimated revenue change",
                format_brl(scenario["estimated_revenue_delta"]),
            )
            budget_cols[1].metric(
                "Estimated LTV change",
                format_brl(scenario["estimated_ltv_delta"]),
            )
            moved_amount = scenario["source_budget_before"] - scenario["source_budget_after"]
            st.markdown(
                f"""
                <div class="callout">
                    <strong>Budget transfer:</strong> {format_brl(moved_amount)} moves from
                    {CHANNEL_LABELS.get(scenario['source_channel'], scenario['source_channel'])}
                    to {CHANNEL_LABELS.get(scenario['target_channel'], scenario['target_channel'])}.
                    Total marketing budget stays constant.
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption(scenario["assumptions"]["note"])
            st.caption(
                "Revenue and LTV changes are directional scenario estimates based on fixed channel-efficiency and segment-affinity assumptions. They are not causal forecasts."
            )

with methodology_tab:
    st.subheader("How to interpret this dashboard")
    st.markdown(
        """
        - **RFM segmentation:** K-means groups customers using recency, purchase frequency, and average order value.
        - **K selection:** elbow inertia and silhouette are compared; silhouette selects the displayed K, with elbow retained as a diagnostic.
        - **Estimated LTV:** a transparent, frequency-based estimate using a 35% gross-margin assumption. It is not a calibrated survival model.
        - **Marketing spend:** channel/month investments are synthetic planning data because Olist does not include media spend.
        - **Budget scenario:** moves the same currency amount between two channels; the modeled effect relies on fixed heuristic assumptions, not causal evidence.
        """
    )
    k_cols = st.columns(2)
    k_cols[0].metric("Selected K", str(k_analysis["selected_k"]))
    k_cols[1].metric("Best silhouette K", str(k_analysis["best_silhouette_k"]))
    diagnostics = pd.DataFrame(
        {
            "K": k_analysis["k_values"],
            "Inertia": [k_analysis["inertia_by_k"][k] for k in k_analysis["k_values"]],
            "Silhouette": [k_analysis["silhouette_by_k"][k] for k in k_analysis["k_values"]],
        }
    )
    st.dataframe(diagnostics, width="stretch", hide_index=True)

st.divider()
st.caption(
    "Portfolio prototype · Estimates are directional and depend on the displayed assumptions. "
    "Validate with real customer, margin, and channel data before operational decisions."
)
