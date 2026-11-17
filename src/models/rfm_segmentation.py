"""RFM-based customer segmentation with K-means.

The logic is intentionally transparent: we compute a customer-level RFM table,
choose K with a simple elbow + silhouette comparison, and then label clusters
with business-friendly names based on their typical behavior.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


def prepare_rfm_features(customer_base: pd.DataFrame) -> pd.DataFrame:
    """Create a clean RFM table from the processed customer base."""
    rfm = customer_base.copy()
    rfm["recency_days"] = pd.to_numeric(rfm.get("recency_days", 0), errors="coerce").fillna(0)
    rfm["order_count"] = pd.to_numeric(rfm.get("order_count", 0), errors="coerce").fillna(0)
    rfm["total_revenue"] = pd.to_numeric(rfm.get("total_revenue", 0), errors="coerce").fillna(0)
    rfm["avg_order_value"] = pd.to_numeric(rfm.get("avg_order_value", 0), errors="coerce").fillna(0)

    rfm["frequency"] = rfm["order_count"].astype(float)
    rfm["monetary"] = np.where(
        rfm["order_count"] > 0,
        rfm["total_revenue"] / rfm["order_count"],
        0.0,
    )
    rfm["recency_days"] = rfm["recency_days"].clip(lower=0)
    return rfm[["customer_id", "recency_days", "frequency", "monetary", "total_revenue", "order_count", "avg_order_value"]].copy()


def _select_elbow_k(inertia_by_k: dict[int, float]) -> int:
    """Choose K by the largest inertia drop between consecutive Ks."""
    if len(inertia_by_k) < 2:
        return min(inertia_by_k, default=1)

    ks = sorted(inertia_by_k)
    inertia = [inertia_by_k[k] for k in ks]
    diffs = np.diff(inertia)
    elbow_index = int(np.argmax(np.abs(diffs))) + 1
    return ks[elbow_index]


def analyze_k_selection(rfm_df: pd.DataFrame, k_values: range = range(2, 8)) -> dict[str, Any]:
    """Evaluate cluster quality for multiple K values.

    This is a transparent way to support the final choice of K in interviews and
    documentation without adding unnecessary complexity to the app.
    """
    features = rfm_df[["recency_days", "frequency", "monetary"]].copy()
    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)

    inertia_by_k: dict[int, float] = {}
    silhouette_by_k: dict[int, float] = {}

    for k in k_values:
        model = KMeans(n_clusters=k, n_init=10, random_state=42)
        labels = model.fit_predict(scaled)
        inertia_by_k[k] = float(model.inertia_)
        if len(np.unique(labels)) > 1:
            silhouette_by_k[k] = float(silhouette_score(scaled, labels))
        else:
            silhouette_by_k[k] = float("nan")

    elbow_k = _select_elbow_k(inertia_by_k)
    best_sil_k = max(
        silhouette_by_k,
        key=lambda k: silhouette_by_k[k] if pd.notna(silhouette_by_k[k]) else float("-inf"),
    )

    selected_k = best_sil_k if pd.notna(silhouette_by_k.get(best_sil_k, np.nan)) else elbow_k
    return {
        "k_values": list(k_values),
        "inertia_by_k": inertia_by_k,
        "silhouette_by_k": silhouette_by_k,
        "elbow_k": elbow_k,
        "best_silhouette_k": best_sil_k,
        "selected_k": int(selected_k),
    }


def _name_clusters(cluster_summary: pd.DataFrame) -> dict[int, str]:
    """Assign business-friendly names to cluster IDs based on observed behavior."""
    recency_median = cluster_summary["avg_recency"].median()
    frequency_median = cluster_summary["avg_frequency"].median()
    monetary_median = cluster_summary["avg_monetary"].median()

    labels: dict[int, str] = {}
    for cluster_id, row in cluster_summary.iterrows():
        avg_recency = row["avg_recency"]
        avg_frequency = row["avg_frequency"]
        avg_monetary = row["avg_monetary"]

        if avg_frequency >= frequency_median and avg_monetary >= monetary_median and avg_recency <= recency_median:
            labels[cluster_id] = "Loyal High-Value"
        elif avg_recency >= recency_median and avg_frequency <= frequency_median:
            labels[cluster_id] = "At Risk"
        elif avg_frequency <= frequency_median and avg_monetary <= monetary_median:
            labels[cluster_id] = "Occasional"
        elif avg_frequency <= 1 and avg_recency <= recency_median:
            labels[cluster_id] = "New / Growing"
        else:
            labels[cluster_id] = "Core / Growth"

    return labels


def build_segment_summary(rfm_df: pd.DataFrame, cluster_labels: pd.Series) -> pd.DataFrame:
    """Summarize the cluster profile at segment level."""
    summary = (
        rfm_df.assign(segment_name=cluster_labels)
        .groupby("segment_name", as_index=False)
        .agg(
            customers=("customer_id", "count"),
            avg_recency=("recency_days", "mean"),
            avg_frequency=("frequency", "mean"),
            avg_monetary=("monetary", "mean"),
            total_revenue=("total_revenue", "sum"),
            avg_order_value=("avg_order_value", "mean"),
        )
        .sort_values("total_revenue", ascending=False)
        .reset_index(drop=True)
    )
    summary["share_of_customers"] = summary["customers"] / summary["customers"].sum()
    return summary


def segment_customers(
    customer_base: pd.DataFrame,
    k_values: range = range(2, 8),
    selected_k: int | None = None,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], KMeans, StandardScaler]:
    """Cluster customers with RFM features and return the enriched table plus summary."""
    rfm_df = prepare_rfm_features(customer_base)
    selection = analyze_k_selection(rfm_df, k_values=k_values)
    k = int(selected_k or selection["selected_k"])

    features = rfm_df[["recency_days", "frequency", "monetary"]].copy()
    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)

    model = KMeans(n_clusters=k, n_init=10, random_state=random_state)
    cluster_labels = model.fit_predict(scaled)
    rfm_df["cluster_id"] = cluster_labels

    cluster_summary = (
        rfm_df.groupby("cluster_id")
        .agg(
            avg_recency=("recency_days", "mean"),
            avg_frequency=("frequency", "mean"),
            avg_monetary=("monetary", "mean"),
        )
        .reset_index()
    )
    names = _name_clusters(cluster_summary.set_index("cluster_id"))
    rfm_df["segment_name"] = rfm_df["cluster_id"].map(names)
    summary = build_segment_summary(rfm_df, rfm_df["segment_name"])
    return rfm_df, summary, selection, model, scaler
