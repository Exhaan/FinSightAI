"""
Unit and Integration Tests for Phase E: Recommendation Systems & Collaborative Filtering.
Run with: pytest tests/test_recommender_phase_e.py -v
"""
import numpy as np
from recommendation.collaborative_filter import InstitutionalCollaborativeFilter
from recommendation.eval_metrics import (
    precision_at_k, recall_at_k, ndcg_at_k, catalog_coverage, intra_list_diversity
)
from recommendation.hybrid_engine import HybridRecommendationEngine


def test_institutional_collaborative_filtering_similar_items():
    cf = InstitutionalCollaborativeFilter()
    # Find similar co-held companies for Infosys (INFY)
    similar_to_infy = cf.get_similar_items("INFY", top_n=5)
    assert len(similar_to_infy) > 0
    tickers = [x["ticker"] for x in similar_to_infy]
    # TCS and large banking peers are frequently co-held by institutional personas
    assert any(t in tickers for t in ["TCS", "HDFCBANK", "ICICIBANK"])
    assert 0.0 <= similar_to_infy[0]["cf_similarity"] <= 1.0


def test_collaborative_filtering_cold_start():
    cf = InstitutionalCollaborativeFilter()
    # A ticker not present in the institutional holding matrix should return empty for cold start fallback
    similar_unknown = cf.get_similar_items("UNKNOWN_TICKER", top_n=5)
    assert similar_unknown == []


def test_recommender_evaluation_metrics():
    recommended = ["TCS", "INFY", "HDFCBANK", "RELIANCE", "ITC"]
    ground_truth = {"INFY", "TCS", "WIPRO"}

    # Precision@3 = 2/3 = 0.6667
    p3 = precision_at_k(recommended, ground_truth, k=3)
    assert round(p3, 2) == 0.67

    # Recall@5 = 2/3 = 0.6667
    r5 = recall_at_k(recommended, ground_truth, k=5)
    assert round(r5, 2) == 0.67

    # NDCG@5 > 0.0
    ndcg = ndcg_at_k(recommended, ground_truth, k=5)
    assert ndcg > 0.50

    # Catalog Coverage
    cov = catalog_coverage([["TCS", "INFY"], ["HDFCBANK", "ITC"]], catalog_size=10)
    assert cov == 0.40

    # Diversity
    vecs = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ])
    div = intra_list_diversity(vecs)
    assert div == 1.0  # Completely orthogonal items have diversity = 1.0


def test_hybrid_engine_blends_content_and_cf():
    engine = HybridRecommendationEngine()
    universe = {
        "Infosys": {
            "ratios": {"revenue_growth": 0.08, "roe": 0.31, "debt_to_equity": 0.05, "free_cash_flow": 2800},
            "metadata": {"ticker": "INFY.NS", "sector": "Information Technology"},
        },
        "TCS": {
            "ratios": {"revenue_growth": 0.07, "roe": 0.48, "debt_to_equity": 0.05, "free_cash_flow": 4500},
            "metadata": {"ticker": "TCS.NS", "sector": "Information Technology"},
        },
    }
    user_prefs = {
        "investment_style": "Growth",
        "current_holdings": ["INFY"],
    }
    res = engine.recommend(universe, user_prefs)
    assert len(res["ranked_recommendations"]) == 2
    top = res["ranked_recommendations"][0]
    assert "cf_score" in top
    assert "content_score" in top
    assert "cluster_archetype" in top
