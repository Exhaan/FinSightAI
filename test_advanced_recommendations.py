"""
Unit tests for Advanced Recommendation Engines:
1. Portfolio-Aware Diversification Engine (Correlation & Concentration Penalty)
2. Qualitative 10-K NLP & Sentiment Engine (MD&A & Risk Factors)
3. Macroeconomic Regime Adaptation
4. Enhanced End-to-End Hybrid Recommendation Engine
"""
import pytest
from recommendation.portfolio_diversification import PortfolioDiversificationEngine
from recommendation.qualitative_scorer import QualitativeDocumentScorer
from recommendation.macro_regime import adjust_weights_for_macro_regime, get_macro_regime_info
from recommendation.hybrid_engine import HybridRecommendationEngine


def test_portfolio_diversification_engine_standalone():
    engine = PortfolioDiversificationEngine()

    # User holds AAPL (Tech)
    holdings = [{"ticker": "AAPL", "sector": "Technology", "weight": 1.0}]

    # Case A: Candidate is NVDA (Tech, highly correlated with AAPL ~0.72)
    nvda_res = engine.evaluate_candidate("NVDA", "Technology", holdings)
    assert nvda_res["concentration_flag"] is True
    assert nvda_res["avg_correlation"] >= 0.65
    assert nvda_res["diversification_score"] < 60.0

    # Case B: Candidate is NEE (Utilities, low correlation with AAPL ~0.18)
    nee_res = engine.evaluate_candidate("NEE", "Utilities", holdings)
    assert nee_res["concentration_flag"] is False
    assert nee_res["avg_correlation"] <= 0.25
    assert nee_res["diversification_score"] >= 80.0
    assert "Low correlation" in nee_res["insights"] or "volatility" in nee_res["insights"]


def test_qualitative_10k_nlp_scorer():
    scorer = QualitativeDocumentScorer()

    sample_mda = (
        "ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS. "
        "The company achieved record revenue growth of 24% and significant margin expansion driven by "
        "innovative product adoption and operational momentum. Management expects strong tailwinds and profitability. "
        "However, we face potential supply chain component shortage, tariff headwinds, and ongoing regulatory investigation "
        "regarding patent dispute."
    )

    res = scorer.analyze_text(sample_mda, page_number=2)
    assert 20.0 <= res["management_sentiment"] <= 95.0
    assert 15.0 <= res["litigation_safety"] <= 95.0
    assert 20.0 <= res["supply_resilience"] <= 95.0
    assert 30.0 <= res["composite_qualitative_score"] <= 95.0
    assert len(res["key_excerpts"]) > 0
    assert len(res["risk_flags"]) > 0


def test_macro_regime_adaptation():
    base_weights = {
        "growth": 0.25,
        "profitability": 0.20,
        "financial_health": 0.20,
        "valuation": 0.15,
        "risk": 0.10,
        "esg": 0.10,
    }

    # Rising Rates / Inflation regime should boost financial health & profitability over speculative growth
    inflation_weights = adjust_weights_for_macro_regime(base_weights, "rising_rates_inflation")
    assert inflation_weights["financial_health"] > base_weights["financial_health"]
    assert inflation_weights["growth"] < base_weights["growth"]
    assert pytest.approx(sum(inflation_weights.values()), rel=1e-3) == 1.0

    # Expansion Bull regime should boost growth
    bull_weights = adjust_weights_for_macro_regime(base_weights, "expansion_bull")
    assert bull_weights["growth"] > base_weights["growth"]
    assert pytest.approx(sum(bull_weights.values()), rel=1e-3) == 1.0


def test_hybrid_engine_with_portfolio_and_regime():
    engine = HybridRecommendationEngine()

    dummy_universe = {
        "Apple Inc.": {
            "ratios": {
                "revenue_growth": 0.08, "revenue_cagr": 0.08, "roe": 0.28, "roic": 0.22,
                "operating_margin": 0.30, "net_margin": 0.24, "debt_to_equity": 0.8,
                "current_ratio": 1.4, "pe_ratio": 30.0, "ev_ebitda": 22.0, "beta": 1.1,
                "volatility": 0.22, "esg_score": 82.0, "dcf_upside": 0.10, "free_cash_flow": 100000.0
            },
            "metadata": {"ticker": "AAPL", "sector": "Technology", "market_cap": 3000000},
            "citations": [],
            "text": "Apple achieved record gross margin and services revenue growth driven by customer momentum."
        },
        "NextEra Energy": {
            "ratios": {
                "revenue_growth": 0.09, "revenue_cagr": 0.09, "roe": 0.12, "roic": 0.09,
                "operating_margin": 0.28, "net_margin": 0.22, "debt_to_equity": 1.4,
                "current_ratio": 1.1, "pe_ratio": 20.0, "ev_ebitda": 13.0, "beta": 0.65,
                "volatility": 0.18, "esg_score": 88.0, "dcf_upside": 0.18, "free_cash_flow": 8000.0
            },
            "metadata": {"ticker": "NEE", "sector": "Utilities", "market_cap": 150000},
            "citations": [],
            "text": "NextEra continues leadership in clean energy expansion with resilient regulated utility earnings."
        }
    }

    # Case 1: User already holds AAPL -> NEE should get a strong diversification boost
    user_prefs = {
        "investment_style": "Balanced",
        "risk_tolerance": "Medium",
        "current_holdings": ["AAPL"],
        "macro_regime": "rising_rates_inflation"
    }

    result = engine.recommend(dummy_universe, user_prefs, macro_regime="rising_rates_inflation")
    assert len(result["ranked_recommendations"]) == 2
    top = result["ranked_recommendations"][0]
    assert "diversification_score" in top
    assert "qualitative_score" in top
    assert "explanation" in top
    assert top["explanation"]["macro_regime"]["name"] == "Rising Rates & Inflationary Regime"
