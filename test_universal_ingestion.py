"""
Unit & Integration Tests for Universal Filing Ingestion, Company Entity Detection,
and Non-Silent Grounding (specifying US GAAP, Ind AS, and British English formats).
"""
import os
import pytest
from extraction.company_detector import (
    detect_company_from_document,
    _extract_bse_nse_filename_ticker,
    KNOWN_PROFILES,
    STOP_TOKENS,
)
from api.main import _get_reconciled_filing_facts


def test_bse_nse_filename_ticker_extraction():
    # Automated download patterns from BSE/NSE
    assert _extract_bse_nse_filename_ticker("AR_29731_UNITDSPR_2025_2026_A_10956084.pdf") == "UNITDSPR"
    assert _extract_bse_nse_filename_ticker("AR_500209_INFY_2024.pdf") == "INFY"
    assert _extract_bse_nse_filename_ticker("AR_532478_UBL_2024.pdf") == "UBL"
    # Stop tokens should never be extracted
    assert _extract_bse_nse_filename_ticker("AR_2024.pdf") is None
    assert _extract_bse_nse_filename_ticker("Annual_Report_2024.pdf") is None


def test_stop_tokens_are_not_tickers():
    for token in ["AR", "ANNUAL", "REPORT", "10-K", "10-Q", "CONSOLIDATED"]:
        assert token in STOP_TOKENS


def test_united_spirits_detection():
    filing_name = "AR_29731_UNITDSPR_2025_2026_A_10956084_10072026221040.pdf"
    path = os.path.join("data", "raw_documents", filing_name)
    if os.path.exists(path):
        profile = detect_company_from_document(path, filing_name)
        assert profile["ticker"] in ["MCDOWELL-N", "UNITDSPR"]
        assert "United Spirits" in profile["name"]
        assert profile["is_indian"] is True
        assert profile["currency"] == "₹"
        assert profile["unit_label"] == "₹ Crores"


def test_reconciled_filing_facts_no_silent_fallback():
    # If document has actual extracted metrics, use them directly
    custom_metrics = {
        "Revenue": 27816.0,
        "Operating Expenses": 25000.0,
        "Net Income": 1847.0,
        "Total Assets": 14000.0,
        "Shareholders Equity": 8000.0,
    }
    profile = {
        "name": "United Spirits Limited",
        "ticker": "MCDOWELL-N",
        "is_indian": True,
        "tax_rate": 0.25,
    }
    facts = _get_reconciled_filing_facts(custom_metrics, profile, "MCDOWELL-N")

    # Values must match the document, NOT Infosys (178650) or NVIDIA (60922)
    assert facts["rev"] == 27816.0
    assert facts["ebit"] == 2816.0  # 27816 - 25000
    assert facts["ni"] == 1847.0
    assert facts["assets"] == 14000.0
    assert facts["equity"] == 8000.0
    assert facts["liab"] == 6000.0  # Assets - Equity = 14000 - 8000


def test_global_company_detection():
    for name in ["NVDA_Annual_Report_2024.pdf", "AAPL_Annual_Report_2024.pdf"]:
        path = os.path.join("data", "raw_documents", name)
        if os.path.exists(path):
            profile = detect_company_from_document(path, name)
            assert profile["is_indian"] is False
            assert profile["currency"] == "$"
            assert profile["unit_label"] == "$ Millions"
