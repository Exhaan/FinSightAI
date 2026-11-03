"""
Cosine Similarity & Content-Based Recommendation (spec §17 & §18).

Builds a user target feature vector from investment preferences:
- Investment Style (Growth, Value, Income, Balanced)
- Risk Tolerance (Low, Medium, High)
- ESG Importance
- Horizon & Sector

Computes Cosine Similarity between user target profile and normalized company feature vectors.
"""
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from analytics.feature_vector import FEATURE_NAMES, build_raw_feature_vector


# Archetype target vectors across the 15 features for different investment styles
# [rev_growth, rev_cagr, roe, roic, op_margin, net_margin, fcf_growth, d_e, curr_ratio, pe, ev_ebitda, beta, vol, esg, dcf_upside]
STYLE_PROFILES = {
    "Growth": {
        "revenue_growth": 0.25, "revenue_cagr": 0.20, "roe": 0.22, "roic": 0.18,
        "operating_margin": 0.25, "net_margin": 0.20, "fcf_growth": 0.20,
        "debt_to_equity": 0.8, "current_ratio": 1.8, "pe_ratio": 35.0, "ev_ebitda": 22.0,
        "beta": 1.30, "volatility": 0.35, "esg_score": 75.0, "dcf_upside": 0.15,
    },
    "Value": {
        "revenue_growth": 0.06, "revenue_cagr": 0.05, "roe": 0.15, "roic": 0.12,
        "operating_margin": 0.18, "net_margin": 0.12, "fcf_growth": 0.08,
        "debt_to_equity": 0.5, "current_ratio": 2.0, "pe_ratio": 14.0, "ev_ebitda": 9.0,
        "beta": 0.85, "volatility": 0.18, "esg_score": 80.0, "dcf_upside": 0.30,
    },
    "Income": {
        "revenue_growth": 0.04, "revenue_cagr": 0.04, "roe": 0.14, "roic": 0.10,
        "operating_margin": 0.20, "net_margin": 0.14, "fcf_growth": 0.06,
        "debt_to_equity": 1.2, "current_ratio": 1.5, "pe_ratio": 16.0, "ev_ebitda": 11.0,
        "beta": 0.70, "volatility": 0.16, "esg_score": 85.0, "dcf_upside": 0.10,
    },
    "Balanced": {
        "revenue_growth": 0.10, "revenue_cagr": 0.09, "roe": 0.18, "roic": 0.14,
        "operating_margin": 0.20, "net_margin": 0.15, "fcf_growth": 0.10,
        "debt_to_equity": 0.7, "current_ratio": 1.8, "pe_ratio": 22.0, "ev_ebitda": 14.0,
        "beta": 1.00, "volatility": 0.22, "esg_score": 80.0, "dcf_upside": 0.15,
    },
}


def build_user_target_vector(preferences: dict) -> np.ndarray:
    """
    Constructs a 15-dimensional user investment target vector based on style and risk preferences.
    """
    style = preferences.get("investment_style", "Growth")
    base_profile = STYLE_PROFILES.get(style, STYLE_PROFILES["Balanced"]).copy()

    risk_tolerance = preferences.get("risk_tolerance", "Medium")
    if risk_tolerance == "Low":
        base_profile["beta"] = min(base_profile["beta"], 0.75)
        base_profile["volatility"] = min(base_profile["volatility"], 0.18)
        base_profile["debt_to_equity"] = min(base_profile["debt_to_equity"], 0.6)
    elif risk_tolerance == "High":
        base_profile["beta"] = max(base_profile["beta"], 1.4)
        base_profile["volatility"] = max(base_profile["volatility"], 0.40)

    min_esg = preferences.get("minimum_esg_score")
    if min_esg is not None:
        base_profile["esg_score"] = max(base_profile["esg_score"], float(min_esg))

    vec = [base_profile[feat] for feat in FEATURE_NAMES]
    return np.array(vec, dtype=float)


def compute_cosine_similarities(
    company_vectors: np.ndarray,
    user_vector: np.ndarray,
    scaler=None,
) -> np.ndarray:
    """
    Computes cosine similarity between normalized company vectors and normalized user vector.
    Returns 1D array of similarity scores in [0, 1].
    """
    if scaler is not None and hasattr(scaler, "transform"):
        try:
            import pandas as pd
            df_user = pd.DataFrame(user_vector.reshape(1, -1), columns=FEATURE_NAMES)
            norm_user = scaler.transform(df_user)
        except Exception:
            norm_user = user_vector.reshape(1, -1)
    else:
        norm_user = user_vector.reshape(1, -1)

    # Ensure 2D
    if company_vectors.ndim == 1:
        company_vectors = company_vectors.reshape(1, -1)

    sims = cosine_similarity(company_vectors, norm_user).flatten()
    
    # Scale from [-1, 1] onto [0, 1] for intuitive percentage match
    scaled_sims = np.clip((sims + 1.0) / 2.0, 0.0, 1.0)
    return scaled_sims


def rank_companies(user_preferences: dict, top_n: int = 5) -> dict:
    """
    Ranks the sample/universe companies using user target vector similarity,
    respecting hard filters, and returning explanations and cluster information.
    """
    from data.sample_universe.companies import get_all_companies
    from recommendation.filters import passes_hard_filters
    from recommendation.clustering import cluster_companies, label_cluster_by_centroid
    from recommendation.explain import build_explanation

    all_companies = get_all_companies()
    if not all_companies:
        return {"ranked": [], "filtered_out": [], "message": "No companies available"}

    eligible = []
    filtered_out = []

    for c in all_companies:
        # Prepare data for hard filter check
        c_filter_data = {
            "debt_to_equity": c.get("debt_to_equity"),
            "roe": c.get("roe"),
            "revenue_growth": c.get("revenue_growth"),
            "beta": c.get("beta"),
            "esg_score": c.get("esg_score"),
            "market_cap": c.get("market_cap_busd", 0) * 1000,
            "sector": c.get("sector"),
        }
        passed, reasons = passes_hard_filters(c_filter_data, user_preferences)
        if passed:
            eligible.append(c)
        else:
            filtered_out.append({
                "name": c.get("name"),
                "ticker": c.get("ticker"),
                "reasons": reasons,
            })

    if not eligible:
        return {
            "ranked": [],
            "filtered_out": filtered_out,
            "message": "No companies matched your investment criteria.",
        }

    # Build user target vector
    user_vec = build_user_target_vector(user_preferences)

    # Build company feature vectors
    company_vecs = []
    company_names = [c["name"] for c in eligible]
    for c in eligible:
        # Map 15-dim features or fallback values
        fvec = build_raw_feature_vector({
            "revenue_growth": c.get("revenue_growth", 0.05),
            "revenue_cagr": c.get("revenue_growth", 0.05),
            "roe": c.get("roe", 0.15),
            "roic": c.get("roe", 0.15) * 0.8,
            "operating_margin": 0.20,
            "net_margin": 0.15,
            "fcf_growth": 0.08,
            "debt_to_equity": c.get("debt_to_equity", 0.5),
            "current_ratio": 1.5,
            "pe_ratio": 20.0,
            "ev_ebitda": 14.0,
            "beta": c.get("beta", 1.0),
            "volatility": 0.20,
            "esg_score": c.get("esg_score", 70.0),
            "dcf_upside": 0.10,
        })
        company_vecs.append(fvec)

    company_mat = np.array(company_vecs, dtype=float)

    # Compute cosine similarities directly
    norm_c = company_mat / (np.linalg.norm(company_mat, axis=1, keepdims=True) + 1e-9)
    norm_u = user_vec / (np.linalg.norm(user_vec) + 1e-9)
    raw_sims = np.dot(norm_c, norm_u)

    # Cluster eligible companies
    clustering_res = cluster_companies(
        normalized_matrix=norm_c,
        company_names=company_names,
        n_clusters=min(3, len(eligible)),
    )
    archetypes = clustering_res.get("archetypes", {})

    ranked_items = []
    for idx, c in enumerate(eligible):
        sim = float(raw_sims[idx])
        cname = c["name"]
        arch = archetypes.get(cname, "Quality Compounders")
        
        # Build explanation
        ratios_dict = {
            "revenue_growth": c.get("revenue_growth"),
            "roe": c.get("roe"),
            "debt_to_equity": c.get("debt_to_equity"),
            "free_cash_flow": c.get("free_cash_flow_musd"),
        }
        score_res = {
            "composite_score": round(max(0.0, sim) * 100, 1),
            "categories": {
                "Growth": round(c.get("revenue_growth", 0.05) * 100, 1),
                "Profitability": round(c.get("roe", 0.15) * 100, 1),
                "Health": round(max(0, 100 - c.get("debt_to_equity", 0.5) * 30), 1),
                "Risk": round(max(0, 100 - (c.get("beta", 1.0) - 1.0) * 50), 1),
                "ESG": c.get("esg_score", 70.0),
            }
        }
        explanation_obj = build_explanation(
            company_name=cname,
            ratios=ratios_dict,
            score_result=score_res,
            archetype=arch,
        )

        ranked_items.append({
            "name": cname,
            "ticker": c.get("ticker"),
            "exchange": c.get("exchange"),
            "sector": c.get("sector"),
            "similarity_score": round(sim, 4),
            "cluster": arch,
            "raw_metrics": {
                "beta": c.get("beta"),
                "roe": c.get("roe"),
                "revenue_growth": c.get("revenue_growth"),
                "debt_to_equity": c.get("debt_to_equity"),
                "market_cap_busd": c.get("market_cap_busd"),
                "esg_score": c.get("esg_score"),
            },
            "explanation": explanation_obj.get("summary_rationale", f"Recommended based on {user_preferences.get('investment_style', 'Balanced')} alignment."),
        })

    # Sort descending by similarity score
    ranked_items.sort(key=lambda x: x["similarity_score"], reverse=True)

    return {
        "ranked": ranked_items[:top_n],
        "filtered_out": filtered_out,
        "total_eligible": len(eligible),
    }


def recommend_for_portfolio(portfolio_tickers: list[str], top_n: int = 5) -> dict:
    """
    Analyzes an existing portfolio of tickers and recommends diversifying companies
    from under-represented sectors and complementary risk profiles.
    """
    from data.sample_universe.companies import get_all_companies, get_company_by_ticker

    all_companies = get_all_companies()
    held_companies = []
    unknown_tickers = []

    for ticker in portfolio_tickers:
        c = get_company_by_ticker(ticker)
        if c:
            held_companies.append(c)
        else:
            unknown_tickers.append(ticker)

    if unknown_tickers and not held_companies:
        return {"error": f"Unknown tickers: {', '.join(unknown_tickers)}"}

    held_tickers_set = {c["ticker"].upper() for c in held_companies}
    held_sectors = [c.get("sector") for c in held_companies if c.get("sector")]

    # Find dominant sector
    sector_counts = {}
    for s in held_sectors:
        sector_counts[s] = sector_counts.get(s, 0) + 1
    
    dominant_sector = max(sector_counts.items(), key=lambda x: x[1])[0] if sector_counts else "Unknown"

    # Filter out companies already held
    candidates = [c for c in all_companies if c["ticker"].upper() not in held_tickers_set]

    # Rank candidates by diversification potential:
    # Prioritize sectors other than dominant_sector and with solid ROE / low beta
    recommendations = []
    for c in candidates:
        c_sector = c.get("sector")
        is_diff_sector = c_sector != dominant_sector
        
        # Build diversification rationale
        if is_diff_sector:
            div_reason = f"Diversifies away from concentrated {dominant_sector} exposure into {c_sector}."
        else:
            div_reason = f"Adds balanced intra-sector quality via {c['name']}."

        recommendations.append({
            "name": c["name"],
            "ticker": c["ticker"],
            "sector": c_sector,
            "exchange": c.get("exchange"),
            "diversification_reason": div_reason,
            "raw_metrics": {
                "beta": c.get("beta"),
                "roe": c.get("roe"),
                "debt_to_equity": c.get("debt_to_equity"),
            },
            "is_cross_sector": is_diff_sector,
        })

    # Sort cross-sector first, then by lower beta
    recommendations.sort(key=lambda x: (not x["is_cross_sector"], x["raw_metrics"]["beta"] or 1.0))

    return {
        "portfolio_summary": {
            "num_holdings": len(held_companies),
            "dominant_sector": dominant_sector,
            "held_sectors": list(set(held_sectors)),
        },
        "recommendations": recommendations[:top_n],
    }

