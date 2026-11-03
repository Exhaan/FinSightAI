"""
Phase 1 smoke tests. Run with:  pytest tests/test_phase1.py -v

These test the parsing/calculation logic directly (no PDF needed) so you can
verify correctness before wiring in a real annual report.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extraction.financial_extractor import _extract_from_line, _parse_number
from extraction.validation import (
    validate_balance_sheet, validate_free_cash_flow, run_all_validations
)
from analytics.financial_metrics import (
    revenue_growth, roe, debt_to_equity, free_cash_flow, compute_ratios_for_company_year
)
from analytics.scoring import score_company
from recommendation.filters import passes_hard_filters


def test_parse_number_handles_commas_and_brackets():
    assert _parse_number("45,000") == 45000.0
    assert _parse_number("(1,234.5)") == -1234.5
    assert _parse_number("$3,200") == 3200.0


def test_extract_from_line_finds_revenue():
    line = "Total Revenue | 45,000 | 41,200"
    results = _extract_from_line(line, page_number=10, document="test.pdf",
                                  method="table", default_year=2024)
    assert any(r.metric == "Revenue" for r in results)
    rev = [r for r in results if r.metric == "Revenue"][0]
    assert rev.value == 45000.0
    assert rev.source_page == 10
    assert rev.extraction_method == "table"


def test_revenue_growth():
    assert revenue_growth(110, 100) == 0.10


def test_roe():
    assert roe(20, 100) == 0.20


def test_debt_to_equity():
    assert debt_to_equity(50, 100) == 0.5


def test_free_cash_flow():
    assert free_cash_flow(120, 20) == 100


def test_balance_sheet_validation_flags_mismatch():
    warning = validate_balance_sheet(assets=1000, liabilities=400, equity=400)
    assert warning is not None  # 400+400=800 != 1000, >10% off


def test_balance_sheet_validation_passes_when_consistent():
    warning = validate_balance_sheet(assets=1000, liabilities=600, equity=400)
    assert warning is None


def test_fcf_validation():
    assert validate_free_cash_flow(fcf=100, ocf=120, capex=20) is None
    assert validate_free_cash_flow(fcf=50, ocf=120, capex=20) is not None


def test_run_all_validations_returns_list():
    warnings = run_all_validations({
        "assets": 1000, "liabilities": 600, "equity": 400,
        "revenue": 500, "gross_profit": 200, "cost_of_revenue": 300,
        "free_cash_flow": 100, "operating_cash_flow": 120, "capex": 20,
    })
    assert isinstance(warnings, list)


def test_compute_ratios_for_company_year():
    current = {"revenue": 110, "net_income": 20, "equity": 100, "debt": 50,
               "operating_cash_flow": 120, "capex": 20}
    previous = {"revenue": 100}
    ratios = compute_ratios_for_company_year(current, previous)
    assert round(ratios["revenue_growth"], 2) == 0.10
    assert ratios["roe"] == 0.20
    assert ratios["debt_to_equity"] == 0.5
    assert ratios["free_cash_flow"] == 100


def test_score_company_returns_0_to_100():
    ratios = {"revenue_growth": 0.15, "roe": 0.20, "debt_to_equity": 0.4,
              "free_cash_flow": 100}
    result = score_company(ratios)
    assert 0 <= result["score"] <= 100


def test_hard_filters_reject_high_debt():
    ratios = {"debt_to_equity": 3.0, "roe": 0.20, "revenue_growth": 0.10}
    ok, reasons = passes_hard_filters(ratios, {"maximum_debt_equity": 1.0})
    assert ok is False
    assert len(reasons) == 1


def test_hard_filters_pass_when_within_limits():
    ratios = {"debt_to_equity": 0.5, "roe": 0.20, "revenue_growth": 0.10}
    ok, reasons = passes_hard_filters(ratios, {"maximum_debt_equity": 1.0, "minimum_roe": 0.10})
    assert ok is True
    assert reasons == []
