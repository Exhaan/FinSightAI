"""
Comprehensive Test Suite for FinSight AI (Phases 1–6).
Run with:  py -3.12 -m pytest tests/ -v
"""
import sys
import os
import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from document_processing.section_identifier import classify_page_section, classify_document_sections
from extraction.financial_extractor import detect_unit_scale, _extract_from_line, _parse_number, extract_financial_metrics
from analytics.financial_metrics import (
    revenue_growth, revenue_cagr, gross_margin, operating_margin, net_margin,
    roe, roic, debt_to_equity, current_ratio, pe_ratio, calculate_dcf_intrinsic_value,
    dcf_upside, compute_all_ratios
)
from analytics.feature_vector import (
    FEATURE_NAMES, build_raw_feature_vector, build_feature_dataframe, normalize_feature_vectors
)
from analytics.scoring import compute_category_scores, score_company
from recommendation.similarity import build_user_target_vector, compute_cosine_similarities
from recommendation.clustering import cluster_companies
from recommendation.filters import passes_hard_filters
from recommendation.explain import build_explanation
from recommendation.hybrid_engine import HybridRecommendationEngine
from document_processing.text_extractor import extract_text_per_page
from document_processing.table_extractor import extract_tables_per_page, tables_to_flat_text


# ---------------------------------------------------- 1. Document Intelligence & Section Recognition
def test_section_identifier():
    inc_text = "CONSOLIDATED STATEMENTS OF OPERATIONS\nTotal Revenue: 50,000"
    res = classify_page_section(inc_text, page_number=3)
    assert res["primary_section"] == "Income Statement"
    assert res["is_financial_statement"] is True

    bs_text = "CONSOLIDATED BALANCE SHEETS\nTotal Assets: 100,000"
    res_bs = classify_page_section(bs_text, page_number=4)
    assert res_bs["primary_section"] == "Balance Sheet"

    cf_text = "CONSOLIDATED STATEMENTS OF CASH FLOWS\nOperating Cash Flow: 20,000"
    res_cf = classify_page_section(cf_text, page_number=5)
    assert res_cf["primary_section"] == "Cash Flow Statement"

    mda_text = "MANAGEMENT'S DISCUSSION AND ANALYSIS (MD&A)\nOverview of operations"
    res_mda = classify_page_section(mda_text, page_number=2)
    assert res_mda["primary_section"] == "MD&A"


def test_unit_scale_detection():
    mult, name = detect_unit_scale("Amounts in millions of dollars")
    assert mult == 1_000_000
    assert name == "millions"

    mult_k, name_k = detect_unit_scale("(in thousands)")
    assert mult_k == 1_000
    assert name_k == "thousands"

    mult_raw, name_raw = detect_unit_scale("Standard report")
    assert mult_raw == 1.0
    assert name_raw == "raw"


# ---------------------------------------------------- 2. Financial Analytics Ratios
def test_cagr_calculation():
    # 100 to 144 in 2 years = 20% CAGR
    assert round(revenue_cagr(100, 144, 2), 2) == 0.20


def test_margins():
    assert round(gross_margin(60, 100), 2) == 0.60
    assert round(operating_margin(25, 100), 2) == 0.25
    assert round(net_margin(18, 100), 2) == 0.18


def test_roic():
    # Operating Income=20, Debt=30, Equity=70, Cash=0, Tax=0.21 -> NOPAT=15.8 / 100 = 0.158
    assert round(roic(20, 30, 70, cash=0, tax_rate=0.21), 3) == 0.158


def test_current_ratio():
    assert round(current_ratio(200, 100), 2) == 2.0


def test_pe_ratio():
    assert round(pe_ratio(1000, 50), 1) == 20.0


def test_dcf_model():
    fcf = 100.0
    intrinsic = calculate_dcf_intrinsic_value(fcf, growth_rate=0.08, discount_rate=0.09)
    assert intrinsic is not None and intrinsic > fcf * 5
    upside = dcf_upside(intrinsic, market_cap=intrinsic * 0.8)
    assert round(upside, 2) == 0.25


# ---------------------------------------------------- 3. Feature Vectors & Normalization
def test_15_dim_feature_vector():
    sample_ratios = {
        "revenue_growth": 0.12, "revenue_cagr": 0.10, "roe": 0.22, "roic": 0.16,
        "operating_margin": 0.20, "net_margin": 0.15, "fcf_growth": 0.10,
        "debt_to_equity": 0.50, "current_ratio": 1.8, "pe_ratio": 24.0,
        "ev_ebitda": 15.0, "beta": 1.1, "volatility": 0.22, "esg_score": 80.0,
        "dcf_upside": 0.15,
    }
    vec = build_raw_feature_vector(sample_ratios)
    assert len(vec) == 15
    assert len(FEATURE_NAMES) == 15

    df = build_feature_dataframe({"AAPL": sample_ratios, "MSFT": sample_ratios})
    assert df.shape == (2, 15)

    norm_mat, scaler = normalize_feature_vectors(df)
    assert norm_mat.shape == (2, 15)


# ---------------------------------------------------- 4. Scoring & Category Scores
def test_category_scores():
    ratios = {
        "revenue_growth": 0.25, "revenue_cagr": 0.20, "fcf_growth": 0.15,
        "gross_margin": 0.50, "operating_margin": 0.30, "net_margin": 0.22,
        "roe": 0.28, "roic": 0.20, "debt_to_equity": 0.30, "debt_to_assets": 0.20,
        "current_ratio": 2.0, "free_cash_flow": 15000.0, "pe_ratio": 28.0,
        "ev_ebitda": 18.0, "dcf_upside": 0.20, "beta": 1.1, "volatility": 0.22,
        "esg_score": 82.0,
    }
    cat_scores = compute_category_scores(ratios)
    assert 0 <= cat_scores["growth_score"] <= 100
    assert 0 <= cat_scores["profitability_score"] <= 100
    assert 0 <= cat_scores["financial_health_score"] <= 100
    assert 0 <= cat_scores["valuation_score"] <= 100
    assert 0 <= cat_scores["risk_score"] <= 100
    assert 0 <= cat_scores["esg_score"] <= 100

    score_res = score_company(ratios, user_similarity=0.85)
    assert 0 <= score_res["score"] <= 100


# ---------------------------------------------------- 5. Cosine Similarity & Clustering
def test_cosine_similarity():
    user_vec = build_user_target_vector({"investment_style": "Growth", "risk_tolerance": "High"})
    assert len(user_vec) == 15

    company_vecs = np.array([user_vec, user_vec * 0.5])
    sims = compute_cosine_similarities(company_vecs, user_vec)
    assert len(sims) == 2
    assert round(sims[0], 2) == 1.0  # Identical vector gives max match


def test_kmeans_clustering():
    vecs = np.random.rand(5, 15)
    names = ["AAPL", "NVDA", "PFE", "TSLA", "NEE"]
    res = cluster_companies(vecs, names, n_clusters=3)
    assert len(res["cluster_ids"]) == 5
    assert len(res["archetypes"]) == 5
    assert len(res["pca_2d"]) == 5


# ---------------------------------------------------- 6. Hybrid Recommendation Engine & Grounded Explanations
def test_hybrid_recommendation_engine():
    universe = {
        "TechCo": {
            "ratios": {
                "revenue_growth": 0.35, "revenue_cagr": 0.30, "roe": 0.30, "roic": 0.25,
                "gross_margin": 0.60, "operating_margin": 0.35, "net_margin": 0.28,
                "debt_to_equity": 0.3, "current_ratio": 2.2, "free_cash_flow": 20000.0,
                "pe_ratio": 32.0, "ev_ebitda": 20.0, "dcf_upside": 0.18,
                "beta": 1.2, "volatility": 0.30, "esg_score": 78.0,
            },
            "metadata": {"ticker": "TCO", "sector": "Technology", "market_cap": 1500000.0},
            "citations": [],
        },
        "SafeUtility": {
            "ratios": {
                "revenue_growth": 0.04, "revenue_cagr": 0.04, "roe": 0.11, "roic": 0.08,
                "gross_margin": 0.35, "operating_margin": 0.18, "net_margin": 0.12,
                "debt_to_equity": 1.4, "current_ratio": 1.2, "free_cash_flow": 2500.0,
                "pe_ratio": 16.0, "ev_ebitda": 10.0, "dcf_upside": 0.08,
                "beta": 0.55, "volatility": 0.15, "esg_score": 90.0,
            },
            "metadata": {"ticker": "SUT", "sector": "Utilities", "market_cap": 80000.0},
            "citations": [],
        },
    }

    engine = HybridRecommendationEngine()
    rec_res = engine.recommend(
        universe,
        user_preferences={"investment_style": "Growth", "risk_tolerance": "Medium", "maximum_debt_equity": 2.0},
        n_clusters=2
    )

    ranked = rec_res["ranked_recommendations"]
    assert len(ranked) == 2
    assert ranked[0]["rank"] == 1
    assert ranked[0]["investment_match_score"] >= ranked[1]["investment_match_score"]
    assert "explanation" in ranked[0]
    assert len(ranked[0]["explanation"]["strengths"]) > 0


# ---------------------------------------------------- 7. End-to-End PDF Extraction on Real Generated PDF
def test_pdf_extraction_traceability():
    pdf_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "raw_documents", "AAPL_Annual_Report_2024.pdf"
    )
    if not os.path.exists(pdf_path):
        from data.generate_sample_reports import generate_all_sample_reports
        generate_all_sample_reports()

    pages = extract_text_per_page(pdf_path)
    assert len(pages) == 5

    classified = classify_document_sections(pages)
    sections = [p["primary_section"] for p in classified]
    assert "Income Statement" in sections
    assert "Balance Sheet" in sections
    assert "Cash Flow Statement" in sections

    tables_raw = extract_tables_per_page(pdf_path)
    tables_by_page = {t["page_number"]: tables_to_flat_text(t["tables"]) for t in tables_raw}
    extracted = extract_financial_metrics(pages, tables_by_page, "AAPL_Annual_Report_2024.pdf")

    # Traceability checks
    assert len(extracted) > 0
    for item in extracted:
        assert item.source_page in [1, 2, 3, 4, 5]
        assert item.confidence > 0
        assert len(item.raw_context) > 0
