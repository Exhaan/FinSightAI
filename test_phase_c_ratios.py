"""
Unit and Integration Tests for Phase C: Multi-Period Statements, Validations, and Full Ratio Library.
Run with: pytest tests/test_phase_c_ratios.py -v
"""
from extraction.statement_extractor import StatementExtractionEngine, deduplicate_citable_metrics
from extraction.accounting_validator import FinancialStatementValidator
from analytics.ratio_library import FinancialRatioLibrary
from analytics.ttm_engine import compute_ttm_metric, compute_ttm_financials

PDF_PATH = "data/raw_documents/INFOSYS_Financial_Statements_FY24.pdf"


def test_statement_extraction_on_real_filing():
    engine = StatementExtractionEngine()
    citable = engine.extract_from_pdf(PDF_PATH, default_year=2024)
    deduped = deduplicate_citable_metrics(citable)

    assert len(deduped) >= 15

    # Check for crucial Ind AS statement line items
    rev_2026 = next((x for x in deduped if x.metric == "Revenue" and x.year == 2026), None)
    assert rev_2026 is not None
    assert rev_2026.value == 178650.0
    assert rev_2026.source_page == 3
    assert len(rev_2026.bbox) == 4

    ni_2026 = next((x for x in deduped if x.metric == "Net Income" and x.year == 2026), None)
    assert ni_2026 is not None
    assert ni_2026.value == 29474.0

    assets_2026 = next((x for x in deduped if x.metric == "Total Assets" and x.year == 2026), None)
    assert assets_2026 is not None
    assert assets_2026.value == 155967.0


def test_accounting_identity_validation_and_quality_score():
    validator = FinancialStatementValidator()
    # Verified extracted figures for Infosys FY26
    metrics = {
        "Revenue": 178650.0,
        "Operating Expenses": 141688.0,
        "Net Income": 29474.0,
        "Total Assets": 155967.0,
        "Shareholders Equity": 92852.0,
        "Total Liabilities": 155967.0, # Reported as Total Equity & Liabilities
        "Operating Cash Flow": 42634.0,
        "Capital Expenditure": 4902.0,
        "Free Cash Flow": 37732.0,
    }
    eval_res = validator.validate_year(metrics, year=2026)
    assert eval_res["data_quality_score"] >= 80.0
    assert eval_res["is_valid"] is True


def test_ratio_library_dupont_3_step_and_5_step():
    ratios = FinancialRatioLibrary()
    # 3-step DuPont
    d3 = ratios.dupont_3_step(
        net_income=29474.0, revenue=178650.0, assets=155967.0, equity=92852.0
    )
    assert d3["net_margin"] is not None
    assert d3["asset_turnover"] is not None
    assert d3["financial_leverage"] is not None
    assert d3["roe"] == round(29474.0 / 92852.0, 4)

    # 5-step DuPont
    d5 = ratios.dupont_5_step(
        net_income=29474.0, pbt=39995.0, ebit=41284.0,
        revenue=178650.0, assets=155967.0, equity=92852.0
    )
    assert d5["tax_burden"] is not None
    assert d5["interest_burden"] is not None
    assert d5["operating_margin"] is not None
    assert d5["roe"] == round(29474.0 / 92852.0, 4)


def test_piotroski_f_score_and_altman_z_score():
    ratios = FinancialRatioLibrary()
    curr = {
        "Net Income": 29474.0,
        "Total Assets": 155967.0,
        "Operating Cash Flow": 42634.0,
        "Total Debt": 6016.0,
        "Current Assets": 103489.0,
        "Current Liabilities": 52322.0,
        "Revenue": 178650.0,
    }
    prior = {
        "Net Income": 26750.0,
        "Total Assets": 148903.0,
        "Operating Cash Flow": 41296.0,
        "Total Debt": 5772.0,
        "Current Assets": 97099.0,
        "Current Liabilities": 42850.0,
        "Revenue": 162990.0,
    }
    f_res = ratios.piotroski_f_score(curr, prior)
    assert f_res["piotroski_f_score"] >= 6
    assert f_res["financial_strength"] in ["Strong", "Moderate"]

    z_res = ratios.altman_z_score(
        current_assets=103489.0, current_liab=52322.0, total_assets=155967.0,
        retained_earnings=90828.0, ebit=41284.0, market_cap=600000.0,
        total_liab=62670.0, revenue=178650.0
    )
    assert z_res["z_score"] > 2.6
    assert z_res["zone"] == "Safe Zone"


def test_ttm_calculation():
    annual = 162990.0
    curr_q_ytd = 90000.0
    prior_q_ytd = 80000.0
    ttm_val = compute_ttm_metric(annual, curr_q_ytd, prior_q_ytd)
    assert ttm_val == 162990.0 + 90000.0 - 80000.0
