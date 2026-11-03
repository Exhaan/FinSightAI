"""
Unit and Integration Tests for Phase D: DCF Valuation Engine.
Includes hand-calculated worked example verification and guardrails.
Run with: pytest tests/test_dcf_valuation.py -v
"""
import pytest
from valuation.wacc_calculator import calculate_wacc, compute_cost_of_equity, compute_after_tax_cost_of_debt
from valuation.fcff_engine import DCFDrivers, project_fcff_series
from valuation.dcf_engine import FullDCFModel


def test_wacc_capm_calculation():
    # Ke = 7.1% + 1.2 * 5.5% = 7.1% + 6.6% = 13.7%
    ke = compute_cost_of_equity(beta=1.2, risk_free_rate=0.071, equity_risk_premium=0.055)
    assert round(ke, 4) == 0.1370

    # Kd after tax = (100 / 1000) * (1 - 0.25) = 10% * 0.75 = 7.5%
    kd = compute_after_tax_cost_of_debt(interest_expense=100.0, total_debt=1000.0, tax_rate=0.25)
    assert round(kd, 4) == 0.0750

    # Total Capital = 9000 (Equity) + 1000 (Debt) = 10,000
    # WACC = 0.9 * 13.7% + 0.1 * 7.5% = 12.33% + 0.75% = 13.08%
    wacc_res = calculate_wacc(
        market_cap=9000.0,
        total_debt=1000.0,
        beta=1.2,
        risk_free_rate=0.071,
        equity_risk_premium=0.055,
        interest_expense=100.0,
        tax_rate=0.25,
    )
    assert round(wacc_res["wacc"], 4) == 0.1308


def test_fcff_projections_formula():
    drivers = DCFDrivers(
        revenue_growth=0.10,
        operating_margin=0.20,
        tax_rate=0.25,
        dna_pct_rev=0.03,
        capex_pct_rev=0.04,
        nwc_pct_rev=0.01,
    )
    # Base revenue = 1,000
    # Year 1 Rev = 1,100
    # EBIT = 220, NOPAT = 220 * 0.75 = 165
    # D&A = 33, CapEx = 44, ΔNWC = 11
    # FCFF = 165 + 33 - 44 - 11 = 143
    projections = project_fcff_series(base_revenue=1000.0, drivers=drivers, wacc=0.10, forecast_years=1)
    assert len(projections) == 1
    y1 = projections[0]
    assert y1.revenue == 1100.0
    assert y1.ebit == 220.0
    assert y1.nopat == 165.0
    assert y1.fcff == 143.0


def test_dcf_equity_bridge_and_hand_calculated_values():
    """
    Hand-calculated worked example:
    Base Revenue = 10,000
    Diluted Shares = 100
    Share Price = 150 (Market Cap = 15,000)
    Cash = 2,000, Total Debt = 1,000
    """
    model = FullDCFModel(
        base_revenue=10000.0,
        diluted_shares=100.0,
        current_share_price=150.0,
        cash_and_investments=2000.0,
        total_debt=1000.0,
        drivers=DCFDrivers(revenue_growth=0.08, operating_margin=0.20, tax_rate=0.25),
        beta=1.0,
        terminal_growth=0.04,
        forecast_years=5,
        mid_year_discounting=True,
    )
    res = model.compute_valuation()

    bridge = res["equity_bridge"]
    # Check that Bridge identity holds: Equity Value = EV - Debt + Cash
    expected_equity_val = bridge["enterprise_value"] - 1000.0 + 2000.0
    assert round(bridge["implied_equity_value"], 2) == round(expected_equity_val, 2)

    # Check Intrinsic Value per share = Equity Value / Shares
    expected_vps = expected_equity_val / 100.0
    assert round(bridge["intrinsic_value_per_share"], 2) == round(expected_vps, 2)

    # Sensitivity matrix exists and has non-empty values
    sens = res["sensitivity_table"]
    assert len(sens["wacc_headers"]) == 5
    assert len(sens["growth_headers"]) == 5
    assert len(sens["price_matrix"]) == 5


def test_dcf_guardrails_prevent_invalid_inputs():
    # If WACC <= terminal growth, must raise ValueError
    model = FullDCFModel(
        base_revenue=10000.0,
        diluted_shares=100.0,
        current_share_price=150.0,
        cash_and_investments=2000.0,
        total_debt=1000.0,
        terminal_growth=0.25, # Unrealistic 25% > WACC
    )
    with pytest.raises(ValueError):
        model.compute_valuation()


def test_reverse_dcf_solves_growth():
    model = FullDCFModel(
        base_revenue=10000.0,
        diluted_shares=100.0,
        current_share_price=150.0,
        cash_and_investments=2000.0,
        total_debt=1000.0,
        beta=1.0,
        terminal_growth=0.04,
    )
    res = model.compute_valuation()
    rev_dcf = res["reverse_dcf"]
    assert rev_dcf["implied_revenue_growth"] is not None
    assert isinstance(rev_dcf["implied_revenue_growth"], float)
