"""
Aesthetic DCF Engine — Pure 10-Year Valuation, Implied Long-Run Margin & 2D Sensitivity Grid.
Inspired by Zi Cong Tan's Aesthetic DCF Calculator (https://github.com/zi-cong-tan/DCF-Calculator-Aesthetic).

Key Features:
- Answer First: Instant Intrinsic Value Per Share, Upside/Downside vs Market Price.
- Separation of Concerns: Locked accounting facts vs. editable judgment assumptions.
- Reverse DCF: "Long-run margin the price needs" via binary search bisection.
- 10-Year Forecast with Mid-Year Discounting and Reinvestment Dynamics (sales-to-capital or % of revenue).
- Terminal Value with ROIC-driven Reinvestment: Reinvestment = g / ROIC.
- 5x5 Sensitivity Matrix: (WACC x Long-Run Operating Margin), highlighting base cell & cell nearest market price.
- Bear Case scenario toggle & quick reset.
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple
import math


@dataclass
class AestheticDCFFacts:
    """Locked reported accounting facts and market data."""
    price: float                   # Current market share price (₹ or $)
    shares: float                  # Diluted shares outstanding (in millions / crores)
    rev0: float                    # Last full-year revenue
    m0: float                      # Last full-year operating margin (EBIT / Revenue)
    net_cash: float                # Net cash (positive) or Net debt (negative)
    debt: float                    # Total debt (for weighting debt in cost of capital)
    rf: float = 0.071              # Risk-free rate (e.g. 7.1% for India 10-yr G-Sec, 5.19% US)
    t_shield: float = 0.25         # Tax shield / corporate tax rate on interest
    reinvest_type: str = "pct"     # "pct" (net investment % of revenue) or "stc" (sales-to-capital ratio)
    date_str: str = "2026-10-18"
    currency_symbol: str = "₹"
    unit_label: str = "₹ Crores"


@dataclass
class AestheticDCFAssumptions:
    """Editable forward-looking judgment calls."""
    beta: float = 1.05
    erp: float = 0.055             # Equity risk premium (5.5%)
    crp: float = 0.0               # Country risk premium
    kd: float = 0.075              # Cost of debt before tax
    tax: float = 0.25              # Forecast effective tax rate
    tax_t: float = 0.25            # Terminal tax rate
    inv: float = 0.035             # Net investment % of rev (if pct) or sales-to-capital (if stc)
    tg: float = 0.045              # Terminal growth rate (4.5% for India, 2.5% for mature US)
    roic: float = 0.18             # Terminal Return on Invested Capital
    lr: float = 0.22               # Long-run operating margin
    g: List[float] = field(default_factory=lambda: [0.08, 0.08, 0.07, 0.07, 0.06, 0.06, 0.05, 0.05, 0.045, 0.045])
    m: List[float] = field(default_factory=lambda: [0.22] * 10)
    bear_lr: Optional[float] = None


def with_long_run_margin(assumptions: AestheticDCFAssumptions, lr: float) -> AestheticDCFAssumptions:
    """
    Moving the long-run margin moves the terminal margin and every forecast margin
    from year 5 onward (years 2030-2035) by the same delta, matching the model's grid logic.
    """
    delta = lr - assumptions.lr
    new_m = list(assumptions.m)
    for i in range(4, 10):
        if i < len(new_m):
            new_m[i] = max(0.01, min(0.90, new_m[i] + delta))
    
    return AestheticDCFAssumptions(
        beta=assumptions.beta,
        erp=assumptions.erp,
        crp=assumptions.crp,
        kd=assumptions.kd,
        tax=assumptions.tax,
        tax_t=assumptions.tax_t,
        inv=assumptions.inv,
        tg=assumptions.tg,
        roic=assumptions.roic,
        lr=lr,
        g=list(assumptions.g),
        m=new_m,
        bear_lr=assumptions.bear_lr
    )


class AestheticDCFEngine:
    """Computes full valuation, cash flow waterfall, reverse DCF implied margin, and 5x5 sensitivity."""

    @staticmethod
    def calculate_dcf(facts: AestheticDCFFacts, assumptions: AestheticDCFAssumptions) -> Dict[str, Any]:
        """
        Executes the 10-year discounted cash flow valuation cell-for-cell.
        """
        ke = facts.rf + assumptions.beta * assumptions.erp + assumptions.crp
        total_market_equity = facts.price * facts.shares
        total_capital = facts.debt + total_market_equity
        wd = (facts.debt / total_capital) if total_capital > 0 else 0.0
        wacc = ke * (1.0 - wd) + assumptions.kd * (1.0 - facts.t_shield) * wd

        stub = 1.0  # Normalized full forward annual period for clean multi-year forecasts
        rev = facts.rev0
        prev = facts.rev0
        rows = []
        pv_sum = 0.0

        for i in range(10):
            growth = assumptions.g[i] if i < len(assumptions.g) else assumptions.tg
            margin = assumptions.m[i] if i < len(assumptions.m) else assumptions.lr
            
            rev = prev * (1.0 + growth)
            ebit = rev * margin
            nopat = ebit * (1.0 - assumptions.tax)

            if facts.reinvest_type == "pct":
                inv = rev * assumptions.inv
            else:
                inv = max(0.0, rev - prev) / assumptions.inv if assumptions.inv > 0 else 0.0

            fcf = nopat - inv
            # Mid-year discounting: (t - 0.5)
            t = (i + 0.5)
            disc_factor = 1.0 / ((1.0 + wacc) ** t)
            p = fcf * disc_factor

            rows.append({
                "year": 2026 + i,
                "growth": growth,
                "revenue": rev,
                "margin": margin,
                "ebit": ebit,
                "nopat": nopat,
                "inv": inv,
                "fcf": fcf,
                "pv": p,
            })
            pv_sum += p
            prev = rev

        # Terminal Value
        rev_t = rev * (1.0 + assumptions.tg)
        nopat_t = rev_t * assumptions.lr * (1.0 - assumptions.tax_t)
        # Reinvestment in terminal value = growth / ROIC
        reinvest_rate_t = (assumptions.tg / assumptions.roic) if assumptions.roic > 0 else 0.0
        fcf_t = nopat_t * (1.0 - reinvest_rate_t)

        is_valid = (wacc > assumptions.tg) and (assumptions.roic > 0) and (facts.reinvest_type == "pct" or assumptions.inv > 0)
        
        if is_valid and (wacc - assumptions.tg) > 0:
            tv = fcf_t / (wacc - assumptions.tg)
            pv_tv = tv / ((1.0 + wacc) ** 9.5)
        else:
            tv = 0.0
            pv_tv = 0.0

        ev = pv_sum + pv_tv
        eq = ev + facts.net_cash
        value_per_share = (eq / facts.shares) if facts.shares > 0 else 0.0
        tv_share = (pv_tv / ev) if ev > 0 else 0.0

        return {
            "ke": ke,
            "wd": wd,
            "wacc": wacc,
            "rows": rows,
            "pv_fcf": pv_sum,
            "pv_tv": pv_tv,
            "tv": tv,
            "enterprise_value": ev,
            "tv_share": tv_share,
            "equity_value": eq,
            "value_per_share": value_per_share,
            "valid": is_valid and math.isfinite(value_per_share),
        }

    @classmethod
    def calculate_implied_margin(cls, facts: AestheticDCFFacts, assumptions: AestheticDCFAssumptions) -> float:
        """
        Binary search bisection solving for what long-run operating margin
        exactly justifies the current market stock price.
        """
        lo = -0.50
        hi = 1.50
        for _ in range(80):
            mid = (lo + hi) / 2.0
            test_a = with_long_run_margin(assumptions, mid)
            res = cls.calculate_dcf(facts, test_a)
            if res["value_per_share"] < facts.price:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2.0

    @classmethod
    def generate_sensitivity_grid(
        cls,
        facts: AestheticDCFFacts,
        assumptions: AestheticDCFAssumptions
    ) -> Dict[str, Any]:
        """
        Generates a 5x5 sensitivity grid of Intrinsic Value Per Share:
        Rows = WACC offsets (-1.5%, -0.75%, 0%, +0.75%, +1.5%)
        Cols = Long-Run Margin offsets (-5.0%, -2.5%, 0%, +2.5%, +5.0%)
        Also flags the current base cell and the cell nearest today's market price.
        """
        base_res = cls.calculate_dcf(facts, assumptions)
        base_wacc = base_res["wacc"]
        wd = base_res["wd"]

        w_offsets = [-0.015, -0.0075, 0.0, 0.0075, 0.015]
        m_offsets = [-0.05, -0.025, 0.0, 0.025, 0.05]

        matrix = []
        best_cell = None
        min_price_diff = float("inf")

        for r_idx, dw in enumerate(w_offsets):
            row_vals = []
            for c_idx, dm in enumerate(m_offsets):
                # Adjust cost of equity via country risk premium offset to precisely shift WACC
                crp_adj = assumptions.crp + (dw / (1.0 - wd)) if (1.0 - wd) > 0 else assumptions.crp
                shifted_a = AestheticDCFAssumptions(
                    beta=assumptions.beta,
                    erp=assumptions.erp,
                    crp=crp_adj,
                    kd=assumptions.kd,
                    tax=assumptions.tax,
                    tax_t=assumptions.tax_t,
                    inv=assumptions.inv,
                    tg=assumptions.tg,
                    roic=assumptions.roic,
                    lr=assumptions.lr + dm,
                    g=list(assumptions.g),
                    m=assumptions.m,
                    bear_lr=assumptions.bear_lr
                )
                shifted_a = with_long_run_margin(shifted_a, assumptions.lr + dm)
                dcf_out = cls.calculate_dcf(facts, shifted_a)
                val = dcf_out["value_per_share"] if dcf_out["valid"] else None
                row_vals.append(round(val, 2) if val is not None else None)

                if val is not None:
                    diff = abs(val - facts.price)
                    if diff < min_price_diff:
                        min_price_diff = diff
                        best_cell = (r_idx, c_idx)

            matrix.append(row_vals)

        return {
            "wacc_headers": [round((base_wacc + dw) * 100, 2) for dw in w_offsets],
            "margin_headers": [round((assumptions.lr + dm) * 100, 1) for dm in m_offsets],
            "matrix": matrix,
            "center_cell": (2, 2),
            "nearest_market_price_cell": best_cell,
        }
