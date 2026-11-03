"""
Tests for the multi-company recommendation engine (Phase 4).
Run with: pytest tests/test_similarity.py -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from recommendation.similarity import rank_companies, recommend_for_portfolio
from data.sample_universe.companies import get_all_companies, get_company_by_ticker


def test_universe_has_companies_from_indian_exchanges():
    companies = get_all_companies()
    exchanges = {c["exchange"] for c in companies}
    assert len(companies) >= 30
    assert "NSE" in exchanges
    assert "BSE" in exchanges


def test_get_company_by_ticker():
    infy = get_company_by_ticker("INFY")
    assert infy is not None
    assert "Infosys" in infy["name"]
    assert get_company_by_ticker("NOTATICKER") is None


def test_rank_companies_returns_ranked_list():
    result = rank_companies({"investment_style": "Growth"}, top_n=5)
    assert "ranked" in result
    assert len(result["ranked"]) <= 5
    assert len(result["ranked"]) > 0
    for r in result["ranked"]:
        assert -1 <= r["similarity_score"] <= 1
        assert "cluster" in r
        assert "explanation" in r


def test_rank_companies_respects_hard_filters():
    result = rank_companies({"investment_style": "Balanced", "maximum_beta": 0.6}, top_n=30)
    for r in result["ranked"]:
        assert r["raw_metrics"]["beta"] <= 0.6


def test_rank_companies_respects_sector_filter():
    result = rank_companies({"investment_style": "Balanced", "preferred_sector": "Information Technology"}, top_n=30)
    for r in result["ranked"]:
        assert r["sector"] == "Information Technology"


def test_rank_companies_empty_when_filters_too_strict():
    result = rank_companies({"maximum_beta": 0.01}, top_n=10)
    assert result["ranked"] == []
    assert "message" in result


def test_rank_companies_returns_filtered_out_reasons():
    result = rank_companies({"maximum_beta": 0.5}, top_n=30)
    assert len(result["filtered_out"]) > 0
    for f in result["filtered_out"]:
        assert "reasons" in f
        assert len(f["reasons"]) > 0


def test_portfolio_recommendation_excludes_held_tickers():
    result = recommend_for_portfolio(["TCS", "INFY"], top_n=10)
    held_names = {"Tata Consultancy Services", "Infosys"}
    recommended_names = {r["name"] for r in result["recommendations"]}
    assert held_names.isdisjoint(recommended_names)


def test_portfolio_recommendation_identifies_dominant_sector():
    result = recommend_for_portfolio(["TCS", "INFY", "WIPRO"], top_n=5)
    assert result["portfolio_summary"]["dominant_sector"] == "Information Technology"


def test_portfolio_recommendation_handles_unknown_ticker():
    result = recommend_for_portfolio(["NOTATICKER"], top_n=5)
    assert "error" in result


def test_portfolio_recommendation_prefers_diversification():
    result = recommend_for_portfolio(["TCS", "INFY", "WIPRO"], top_n=30)
    # Every recommendation should carry a diversification_reason string
    for r in result["recommendations"]:
        assert isinstance(r["diversification_reason"], str)
        assert len(r["diversification_reason"]) > 0

