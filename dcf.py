"""
valuation.dcf — Discounted Cash Flow Valuation Compatibility Module.
Ports and wraps the 10-year aesthetic DCF calculation logic inspired by zi-cong-tan/DCF-Calculator-Aesthetic.
See THIRD_PARTY_NOTICES.md for MIT license attribution.
"""
import os
import json
from typing import Dict, Any, List, Optional
from valuation.aesthetic_dcf import (
    AestheticDCFFacts,
    AestheticDCFAssumptions,
    AestheticDCFEngine,
    with_long_run_margin
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLES_PATH = os.path.join(BASE_DIR, "data", "dcf_reference_examples.json")


def load_dcf_examples() -> List[Dict[str, Any]]:
    """Loads reference DCF examples (MU, AAPL, AMZN, TSLA)."""
    if os.path.exists(EXAMPLES_PATH):
        try:
            with open(EXAMPLES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("examples", [])
        except Exception:
            pass
    return []


def compute_dcf(
    price: float,
    shares: float,
    rev0: float,
    m0: float,
    net_cash: float,
    debt: float,
    rf: float = 0.071,
    t_shield: float = 0.25,
    beta: float = 1.0,
    erp: float = 0.055,
    crp: float = 0.0,
    kd: float = 0.075,
    tax: float = 0.25,
    inv: float = 0.035,
    tg: float = 0.045,
    roic: float = 0.20,
    lr: float = 0.20,
    reinvest_type: str = "pct",
    growth_rates: Optional[List[float]] = None,
    margins: Optional[List[float]] = None,
    bear_case: bool = False,
    bear_lr: Optional[float] = None
) -> Dict[str, Any]:
    """
    Computes 10-year DCF intrinsic value, cash flow forecast, and valuation metrics.
    """
    facts = AestheticDCFFacts(
        price=price,
        shares=shares,
        rev0=rev0,
        m0=m0,
        net_cash=net_cash,
        debt=debt,
        rf=rf,
        t_shield=t_shield,
        reinvest_type=reinvest_type
    )

    g = growth_rates or [0.08, 0.08, 0.07, 0.07, 0.06, 0.06, 0.05, 0.05, 0.045, 0.045]
    m = margins or [lr] * 10
    active_lr = bear_lr if (bear_case and bear_lr is not None) else lr

    assumptions = AestheticDCFAssumptions(
        beta=beta,
        erp=erp,
        crp=crp,
        kd=kd,
        tax=tax,
        tax_t=tax,
        inv=inv,
        tg=tg,
        roic=roic,
        lr=active_lr,
        g=g,
        m=m,
        bear_lr=bear_lr
    )

    if bear_case:
        assumptions = with_long_run_margin(assumptions, active_lr)

    engine = AestheticDCFEngine()
    res = engine.calculate_dcf(facts, assumptions)
    res["facts"] = facts
    res["assumptions"] = assumptions
    return res


def implied_long_run_margin(
    facts: AestheticDCFFacts,
    assumptions: AestheticDCFAssumptions
) -> float:
    """
    Reverse DCF bisection solving for long-run operating margin required to justify current price.
    """
    engine = AestheticDCFEngine()
    return engine.calculate_implied_margin(facts, assumptions)


def sensitivity_grid(
    facts: AestheticDCFFacts,
    assumptions: AestheticDCFAssumptions
) -> Dict[str, Any]:
    """
    Generates 5x5 sensitivity matrix (WACC x Margin).
    """
    engine = AestheticDCFEngine()
    return engine.generate_sensitivity_grid(facts, assumptions)
