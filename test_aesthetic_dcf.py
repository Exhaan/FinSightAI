import pytest
from valuation.aesthetic_dcf import AestheticDCFFacts, AestheticDCFAssumptions, AestheticDCFEngine, with_long_run_margin


def test_aesthetic_dcf_basic_calculation():
    facts = AestheticDCFFacts(
        price=1023.40,
        shares=405.04,
        rev0=153670.0,
        m0=0.23,
        net_cash=6000.0,
        debt=8200.0,
        rf=0.071,
        t_shield=0.25,
        reinvest_type="pct"
    )
    assump = AestheticDCFAssumptions(
        beta=0.85,
        erp=0.055,
        kd=0.075,
        tax=0.25,
        inv=0.035,
        tg=0.045,
        roic=0.25,
        lr=0.23
    )
    engine = AestheticDCFEngine()
    res = engine.calculate_dcf(facts, assump)

    assert res["valid"] is True
    assert res["value_per_share"] > 500.0
    assert res["enterprise_value"] > 200000.0
    assert 0.05 < res["wacc"] < 0.20
    assert len(res["rows"]) == 10


def test_aesthetic_dcf_implied_margin():
    facts = AestheticDCFFacts(
        price=1023.40,
        shares=405.04,
        rev0=153670.0,
        m0=0.23,
        net_cash=6000.0,
        debt=8200.0,
        rf=0.071,
        t_shield=0.25,
        reinvest_type="pct"
    )
    assump = AestheticDCFAssumptions(
        beta=0.85,
        erp=0.055,
        kd=0.075,
        tax=0.25,
        inv=0.035,
        tg=0.045,
        roic=0.25,
        lr=0.23
    )
    engine = AestheticDCFEngine()
    implied_m = engine.calculate_implied_margin(facts, assump)

    assert 0.05 < implied_m < 0.60
    # Valuing at implied margin should match stock price closely
    test_assump = with_long_run_margin(assump, implied_m)
    val_at_imp = engine.calculate_dcf(facts, test_assump)["value_per_share"]
    assert abs(val_at_imp - facts.price) < 5.0


def test_aesthetic_dcf_sensitivity_grid():
    facts = AestheticDCFFacts(
        price=1023.40,
        shares=405.04,
        rev0=153670.0,
        m0=0.23,
        net_cash=6000.0,
        debt=8200.0,
        rf=0.071,
        t_shield=0.25,
        reinvest_type="pct"
    )
    assump = AestheticDCFAssumptions(
        beta=0.85,
        erp=0.055,
        kd=0.075,
        tax=0.25,
        inv=0.035,
        tg=0.045,
        roic=0.25,
        lr=0.23
    )
    engine = AestheticDCFEngine()
    sens = engine.generate_sensitivity_grid(facts, assump)

    assert len(sens["wacc_headers"]) == 5
    assert len(sens["margin_headers"]) == 5
    assert len(sens["matrix"]) == 5
    assert len(sens["matrix"][0]) == 5
    assert sens["center_cell"] == (2, 2)
    assert sens["nearest_market_price_cell"] is not None
