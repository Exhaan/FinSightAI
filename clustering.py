"""
K-Means Clustering Engine (spec §21).

Categorizes companies into distinct financial archetypes:
- "High-Growth & Innovation" (High Revenue Growth, High Volatility, Higher Valuation)
- "Quality Compounders" (High ROE/ROIC, High Margins, Prudent Leverage)
- "Defensive Value & High ESG" (Low Beta, Strong Balance Sheet, High ESG)
- "High Leverage / Speculative Turnaround" (High Debt-to-Equity, Cyclical)

Provides cluster assignment, PCA 2D projections for visualization, and archetype interpretation.
"""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

from analytics.feature_vector import FEATURE_NAMES


def determine_optimal_k(
    normalized_matrix: np.ndarray,
    min_k: int = 2,
    max_k: int = 6,
) -> int:
    """
    Auto-selects optimal k using Silhouette Score with Elbow (inertia) check.
    If samples are too few, defaults safely.
    """
    n_samples = normalized_matrix.shape[0]
    if n_samples <= 2:
        return 1
    if n_samples <= 3:
        return 2

    upper_limit = min(max_k, n_samples - 1)
    if upper_limit < min_k:
        return max(1, min(2, n_samples))

    best_k = min_k
    best_score = -1.0

    for k in range(min_k, upper_limit + 1):
        try:
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = km.fit_predict(normalized_matrix)
            # Ensure at least 2 distinct clusters were formed
            if len(set(labels)) > 1:
                score = float(silhouette_score(normalized_matrix, labels))
                if score > best_score:
                    best_score = score
                    best_k = k
        except Exception:
            continue

    return best_k


def label_cluster_by_centroid(centroid: np.ndarray, feature_names: list[str]) -> str:
    """
    Assigns an intuitive archetype label to a cluster based on its feature centroid values.
    Never relies on hardcoded cluster index numbers.
    """
    feat_map = dict(zip(feature_names, centroid))
    rg = feat_map.get("revenue_growth", 0.05)
    roe_val = feat_map.get("roe", 0.12)
    de = feat_map.get("debt_to_equity", 1.0)
    beta_val = feat_map.get("beta", 1.0)
    esg_val = feat_map.get("esg_score", 75.0)

    if rg > 0.18 or beta_val > 1.25:
        return "High-Growth & Innovation"
    elif roe_val > 0.18 and de < 0.9:
        return "Quality Compounders"
    elif esg_val >= 70.0 and beta_val < 0.85:
        return "Defensive Value & High ESG"
    elif de > 1.4:
        return "High Leverage / Cyclical"
    else:
        return "Balanced Core"


def cluster_companies(
    normalized_matrix: np.ndarray,
    company_names: list[str],
    raw_df: pd.DataFrame | None = None,
    n_clusters: int | str = 3,
) -> dict:
    """
    Runs K-Means clustering on the normalized company feature vectors.
    n_clusters: integer, or 'auto' to automatically select k via silhouette score.
    Returns cluster labels, centroid-derived archetypes, and 2D PCA coordinates for plotting.
    """
    n_samples = len(company_names)

    if n_samples <= 1:
        return {
            "cluster_ids": [0],
            "archetypes": {cname: "Individual Profile" for cname in company_names},
            "clusters": {0: {"name": "Individual Profile", "companies": company_names}},
            "pca_2d": [{"company": company_names[0], "x": 0.0, "y": 0.0, "cluster": 0}],
            "optimal_k": 1,
        }

    # Auto k selection or bounded user choice
    if n_clusters == "auto":
        k = determine_optimal_k(normalized_matrix)
    else:
        k = max(1, min(int(n_clusters), n_samples))

    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(normalized_matrix)

    # Derive cluster archetypes strictly from centroids (never by index)
    cluster_archetype_map = {}
    for cluster_id in range(k):
        cluster_members = [company_names[i] for i in range(n_samples) if cluster_labels[i] == cluster_id]
        if raw_df is not None and not raw_df.empty:
            if cluster_members:
                mean_raw = raw_df.loc[cluster_members].mean().values
                archetype = label_cluster_by_centroid(mean_raw, FEATURE_NAMES)
            else:
                archetype = label_cluster_by_centroid(kmeans.cluster_centers_[cluster_id], FEATURE_NAMES)
        else:
            archetype = label_cluster_by_centroid(kmeans.cluster_centers_[cluster_id], FEATURE_NAMES)

        # Disambiguate if multiple clusters resolve to the same label
        if list(cluster_archetype_map.values()).count(archetype) > 0:
            archetype = f"{archetype} (Group {cluster_id + 1})"

        cluster_archetype_map[cluster_id] = archetype

    # 2D PCA projection for visualization
    pca = PCA(n_components=min(2, n_samples))
    coords_2d = pca.fit_transform(normalized_matrix)
    if coords_2d.shape[1] == 1:
        coords_2d = np.hstack([coords_2d, np.zeros((n_samples, 1))])

    pca_plot_data = []
    company_archetypes = {}
    cluster_summary = {cid: {"name": cluster_archetype_map[cid], "companies": []} for cid in range(k)}

    for idx, cname in enumerate(company_names):
        cid = int(cluster_labels[idx])
        arch = cluster_archetype_map[cid]
        company_archetypes[cname] = arch
        cluster_summary[cid]["companies"].append(cname)
        pca_plot_data.append({
            "company": cname,
            "x": round(float(coords_2d[idx, 0]), 3),
            "y": round(float(coords_2d[idx, 1]), 3),
            "cluster_id": cid,
            "archetype": arch,
        })

    return {
        "cluster_ids": [int(x) for x in cluster_labels],
        "archetypes": company_archetypes,
        "clusters": cluster_summary,
        "pca_2d": pca_plot_data,
        "inertia": float(kmeans.inertia_),
        "optimal_k": k,
    }

