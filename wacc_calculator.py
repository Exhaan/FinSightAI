"""
Valuation Package — Weighted Average Cost of Capital (WACC) via CAPM (spec §7).

Calculates:
1. Cost of Equity (Ke) via CAPM: Ke = Rf + Beta * ERP
2. After-tax Cost of Debt (Kd): Kd = Pre_tax_cost_of_debt * (1 - Tax_Rate)
3. Capital Structure Weights: Weight_Equity = Market_Cap / (Market_Cap + Debt)
4. WACC = Weight_Equity * Ke + Weight_Debt * Kd

Market Inputs:
- Risk-Free Rate (Rf): Default 7.10% (10-year Indian Government Bond yield) or FRED/user adapter.
- Equity Risk Premium (ERP): Default 5.50% (Emerging Market / India consensus equity risk premium).
"""
from typing import Dict, Any, Optional


def compute_cost_of_equity(
    beta: float,
    risk_free_rate: float = 0.071,
    equity_risk_premium: float = 0.055,
) -> float:
    """
    Cost of Equity Ke = Rf + Beta * ERP
    """
    return risk_free_rate + (beta * equity_risk_premium)


def compute_after_tax_cost_of_debt(
    interest_expense: Optional[float],
    total_debt: Optional[float],
    tax_rate: float = 0.25,
    default_pre_tax_kd: float = 0.085,
) -> float:
    """
    After-tax Kd = (Interest Expense / Total Debt) * (1 - Tax_Rate)
    """
    if interest_expense is not None and total_debt is not None and total_debt > 0 and interest_expense > 0:
        pre_tax_kd = interest_expense / total_debt
    else:
        pre_tax_kd = default_pre_tax_kd

    return pre_tax_kd * (1.0 - tax_rate)


def calculate_wacc(
    market_cap: float,
    total_debt: float,
    beta: float = 1.0,
    risk_free_rate: float = 0.071,
    equity_risk_premium: float = 0.055,
    interest_expense: Optional[float] = None,
    tax_rate: float = 0.25,
    preferred_stock: float = 0.0,
) -> Dict[str, Any]:
    """
    Calculates WACC and returns detailed component breakdown.
    """
    # Guardrail
    safe_market_cap = max(market_cap, 1.0)
    safe_debt = max(total_debt, 0.0)
    total_capital = safe_market_cap + safe_debt + preferred_stock

    weight_equity = safe_market_cap / total_capital
    weight_debt = safe_debt / total_capital

    ke = compute_cost_of_equity(beta, risk_free_rate, equity_risk_premium)
    kd_after_tax = compute_after_tax_cost_of_debt(interest_expense, safe_debt, tax_rate)

    wacc = (weight_equity * ke) + (weight_debt * kd_after_tax)

    return {
        "wacc": round(wacc, 4),
        "cost_of_equity": round(ke, 4),
        "cost_of_debt_after_tax": round(kd_after_tax, 4),
        "weight_equity": round(weight_equity, 4),
        "weight_debt": round(weight_debt, 4),
        "assumptions": {
            "risk_free_rate": risk_free_rate,
            "equity_risk_premium": equity_risk_premium,
            "beta": beta,
            "tax_rate": tax_rate,
            "total_capital": total_capital,
        }
    }
