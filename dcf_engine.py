"""
Valuation Package — Full DCF Model, Terminal Value & Cited Equity Bridge (spec §7).

Integrates:
1. Enterprise Value (EV) = Sum(PV of Forecast FCFF) + PV of Terminal Value
2. Dual Terminal Value Methods:
   - Gordon Growth Model: TV = FCFF_{T+1} / (WACC - g)
   - Exit Multiple Method: TV = EBITDA_T * Exit_Multiple
   - Implied Cross-Check: Implied Multiple from Gordon, Implied g from Multiple
   - Guardrail: Warning if TV share of EV > 75-80%
3. Equity Bridge:
   Enterprise Value
   - Total Debt (including Leases)
   - Preferred Stock
   - Non-Controlling Interests (NCI)
   + Cash and Short-Term Investments
   = Equity Value
   / Diluted Shares Outstanding
   = Intrinsic Value Per Share
4. Upside / Downside vs. Current Market Price
5. Sensitivity Tables: (WACC x Terminal Growth) & (WACC x Exit Multiple)
6. Reverse DCF: Market-implied revenue growth rate given current share price
"""
import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import asdict

from valuation.wacc_calculator import calculate_wacc
from valuation.fcff_engine import DCFDrivers, project_fcff_series, YearlyFCFFProjection


class FullDCFModel:
    """
    Equity-research grade Discounted Cash Flow valuation engine.
    """

    def __init__(
        self,
        base_revenue: float,
        diluted_shares: float,
        current_share_price: float,
        cash_and_investments: float,
        total_debt: float,
        preferred_stock: float = 0.0,
        nci: float = 0.0,
        drivers: Optional[DCFDrivers] = None,
        beta: float = 1.0,
        risk_free_rate: float = 0.071,
        equity_risk_premium: float = 0.055,
        terminal_growth: float = 0.045,      # 4.5% long term GDP-aligned growth for India
        exit_multiple: float = 14.0,         # EV/EBITDA multiple
        forecast_years: int = 5,
        mid_year_discounting: bool = True,
    ):
        self.base_revenue = base_revenue
        self.diluted_shares = max(diluted_shares, 1.0)
        self.current_share_price = current_share_price
        self.cash_and_investments = cash_and_investments
        self.total_debt = total_debt
        self.preferred_stock = preferred_stock
        self.nci = nci
        self.drivers = drivers or DCFDrivers()
        self.beta = beta
        self.risk_free_rate = risk_free_rate
        self.equity_risk_premium = equity_risk_premium
        self.terminal_growth = terminal_growth
        self.exit_multiple = exit_multiple
        self.forecast_years = forecast_years
        self.mid_year_discounting = mid_year_discounting

    def compute_valuation(self) -> Dict[str, Any]:
        """
        Executes complete DCF valuation, equity bridge, cross-checks, and sensitivities.
        """
        market_cap = self.diluted_shares * self.current_share_price

        # 1. Compute WACC
        wacc_res = calculate_wacc(
            market_cap=market_cap,
            total_debt=self.total_debt,
            beta=self.beta,
            risk_free_rate=self.risk_free_rate,
            equity_risk_premium=self.equity_risk_premium,
            tax_rate=self.drivers.tax_rate,
        )
        wacc = wacc_res["wacc"]

        # Guardrail check
        if wacc <= self.terminal_growth:
            raise ValueError(
                f"WACC ({wacc:.1%}) must be strictly greater than terminal growth rate ({self.terminal_growth:.1%})."
            )

        # 2. Project 5-year FCFF
        fcff_projections = project_fcff_series(
            base_revenue=self.base_revenue,
            drivers=self.drivers,
            wacc=wacc,
            forecast_years=self.forecast_years,
            mid_year_discounting=self.mid_year_discounting,
        )
        pv_fcff_sum = sum(p.pv_fcff for p in fcff_projections)

        # 3. Terminal Value Calculations
        last_year = fcff_projections[-1]
        terminal_year_fcff = last_year.fcff * (1.0 + self.terminal_growth)

        # Method A: Gordon Growth
        tv_gordon = terminal_year_fcff / (wacc - self.terminal_growth)
        pv_tv_gordon = tv_gordon / ((1.0 + wacc) ** self.forecast_years)

        # Method B: Exit Multiple
        final_ebitda = last_year.ebit + last_year.dna
        tv_exit_mult = final_ebitda * self.exit_multiple
        pv_tv_exit_mult = tv_exit_mult / ((1.0 + wacc) ** self.forecast_years)

        # Cross-Checks: Implied Multiple from Gordon, Implied g from Exit Multiple
        implied_multiple_from_gordon = tv_gordon / final_ebitda if final_ebitda > 0 else 0.0
        # g = (TV * WACC - FCFF_T1) / (TV)
        implied_g_from_exit_mult = (tv_exit_mult * wacc - last_year.fcff) / (tv_exit_mult + last_year.fcff) if tv_exit_mult > 0 else 0.0

        # Enterprise Value (Gordon baseline)
        ev_gordon = pv_fcff_sum + pv_tv_gordon
        ev_exit_mult = pv_fcff_sum + pv_tv_exit_mult

        # TV Share of EV Check
        tv_share_ev = (pv_tv_gordon / ev_gordon) if ev_gordon > 0 else 0.0
        warnings = []
        if tv_share_ev > 0.75:
            warnings.append(
                f"High Terminal Value dependency: Terminal value represents {tv_share_ev:.1%} of Enterprise Value."
            )

        # 4. Equity Bridge (Gordon baseline)
        equity_value_gordon = (
            ev_gordon
            - self.total_debt
            - self.preferred_stock
            - self.nci
            + self.cash_and_investments
        )
        value_per_share_gordon = equity_value_gordon / self.diluted_shares
        upside_gordon = (value_per_share_gordon - self.current_share_price) / self.current_share_price

        # Equity Bridge (Exit Multiple baseline)
        equity_value_exit = (
            ev_exit_mult
            - self.total_debt
            - self.preferred_stock
            - self.nci
            + self.cash_and_investments
        )
        value_per_share_exit = equity_value_exit / self.diluted_shares
        upside_exit = (value_per_share_exit - self.current_share_price) / self.current_share_price

        # 5. Sensitivity Table (WACC vs. Terminal Growth)
        wacc_steps = [wacc - 0.01, wacc - 0.005, wacc, wacc + 0.005, wacc + 0.01]
        g_steps = [self.terminal_growth - 0.01, self.terminal_growth - 0.005, self.terminal_growth, self.terminal_growth + 0.005, self.terminal_growth + 0.01]
        
        sensitivity_matrix = []
        for w_s in wacc_steps:
            row = []
            for g_s in g_steps:
                if w_s > g_s:
                    tv_s = (last_year.fcff * (1.0 + g_s)) / (w_s - g_s)
                    pv_tv_s = tv_s / ((1.0 + w_s) ** self.forecast_years)
                    # Recompute PV of FCFF with step WACC
                    pv_fcff_s = sum(p.fcff / ((1.0 + w_s) ** ((p.year - 0.5) if self.mid_year_discounting else p.year)) for p in fcff_projections)
                    ev_s = pv_fcff_s + pv_tv_s
                    eq_s = ev_s - self.total_debt - self.preferred_stock - self.nci + self.cash_and_investments
                    vps_s = eq_s / self.diluted_shares
                    row.append(round(vps_s, 2))
                else:
                    row.append(None)
            sensitivity_matrix.append(row)

        # 6. Reverse DCF: Solve for revenue growth implied by current share price
        implied_rev_growth = self._solve_implied_growth(target_share_price=self.current_share_price, wacc=wacc)

        return {
            "enterprise_value_gordon": round(ev_gordon, 2),
            "enterprise_value_exit_multiple": round(ev_exit_mult, 2),
            "equity_bridge": {
                "enterprise_value": round(ev_gordon, 2),
                "less_total_debt": round(-self.total_debt, 2),
                "less_preferred_stock": round(-self.preferred_stock, 2),
                "less_nci": round(-self.nci, 2),
                "plus_cash_and_investments": round(self.cash_and_investments, 2),
                "implied_equity_value": round(equity_value_gordon, 2),
                "diluted_shares_count": round(self.diluted_shares, 2),
                "intrinsic_value_per_share": round(value_per_share_gordon, 2),
                "current_market_price": round(self.current_share_price, 2),
                "upside_potential": round(upside_gordon, 4),
            },
            "exit_multiple_valuation": {
                "enterprise_value": round(ev_exit_mult, 2),
                "intrinsic_value_per_share": round(value_per_share_exit, 2),
                "upside_potential": round(upside_exit, 4),
            },
            "terminal_value_cross_checks": {
                "pv_terminal_value": round(pv_tv_gordon, 2),
                "terminal_value_share_of_ev": round(tv_share_ev, 4),
                "implied_exit_multiple_from_gordon": round(implied_multiple_from_gordon, 2),
                "implied_terminal_growth_from_exit_multiple": round(implied_g_from_exit_mult, 4),
            },
            "wacc_details": wacc_res,
            "fcff_projections": [asdict(p) for p in fcff_projections],
            "sensitivity_table": {
                "wacc_headers": [round(w * 100, 2) for w in wacc_steps],
                "growth_headers": [round(g * 100, 2) for g in g_steps],
                "price_matrix": sensitivity_matrix,
            },
            "reverse_dcf": {
                "current_price": self.current_share_price,
                "implied_revenue_growth": round(implied_rev_growth, 4) if implied_rev_growth is not None else None,
                "assumed_growth": round(self.drivers.revenue_growth, 4),
            },
            "audit_warnings": warnings,
        }

    def _solve_implied_growth(self, target_share_price: float, wacc: float) -> Optional[float]:
        """
        Binary search to determine what revenue growth rate matches current market price.
        """
        low = -0.15
        high = 0.50
        target_equity_val = target_share_price * self.diluted_shares

        for _ in range(30):
            mid = (low + high) / 2.0
            test_drivers = DCFDrivers(
                revenue_growth=mid,
                operating_margin=self.drivers.operating_margin,
                tax_rate=self.drivers.tax_rate,
                dna_pct_rev=self.drivers.dna_pct_rev,
                capex_pct_rev=self.drivers.capex_pct_rev,
                nwc_pct_rev=self.drivers.nwc_pct_rev,
            )
            projections = project_fcff_series(self.base_revenue, test_drivers, wacc, self.forecast_years, self.mid_year_discounting)
            pv_f = sum(p.pv_fcff for p in projections)
            tv = (projections[-1].fcff * (1.0 + self.terminal_growth)) / (wacc - self.terminal_growth)
            pv_tv = tv / ((1.0 + wacc) ** self.forecast_years)
            ev = pv_f + pv_tv
            eq = ev - self.total_debt - self.preferred_stock - self.nci + self.cash_and_investments

            if abs(eq - target_equity_val) < 1.0:
                return mid
            elif eq < target_equity_val:
                low = mid
            else:
                high = mid

        return (low + high) / 2.0


class DCFValuationEngine:
    """
    Convenience wrapper class matching standard institutional equity research parameters.
    """

    def run_valuation(
        self,
        base_revenue: float,
        base_ebit: float,
        total_debt: float,
        cash_and_equivalents: float,
        diluted_shares: float,
        current_stock_price: float,
        growth_rates: Optional[List[float]] = None,
        operating_margin: Optional[float] = None,
        beta: float = 1.05,
        risk_free_rate: float = 0.071,
        erp: float = 0.055,
        terminal_growth: float = 0.05
    ) -> Dict[str, Any]:
        avg_growth = (sum(growth_rates) / len(growth_rates)) if growth_rates else 0.07
        op_margin = operating_margin if operating_margin is not None else (base_ebit / base_revenue if base_revenue else 0.20)
        
        drivers = DCFDrivers(
            revenue_growth=avg_growth,
            operating_margin=op_margin,
            tax_rate=0.25,
            dna_pct_rev=0.03,
            capex_pct_rev=0.035,
            nwc_pct_rev=0.02
        )

        model = FullDCFModel(
            base_revenue=base_revenue,
            diluted_shares=diluted_shares,
            current_share_price=current_stock_price,
            cash_and_investments=cash_and_equivalents,
            total_debt=total_debt,
            drivers=drivers,
            beta=beta,
            risk_free_rate=risk_free_rate,
            equity_risk_premium=erp,
            terminal_growth=terminal_growth
        )

        res = model.compute_valuation()
        bridge = res["equity_bridge"]
        wacc_details = res["wacc_details"]
        sens = res["sensitivity_table"]

        return {
            "wacc": wacc_details["wacc"],
            "terminal_growth_rate": terminal_growth,
            "pv_fcff": sum(p["pv_fcff"] for p in res["fcff_projections"]),
            "enterprise_value": bridge["enterprise_value"],
            "value_per_share": bridge["intrinsic_value_per_share"],
            "upside_pct": bridge["upside_potential"] * 100.0,
            "tv_share_of_ev": res["terminal_value_cross_checks"]["terminal_value_share_of_ev"],
            "equity_bridge": {
                "debt": self.total_debt if hasattr(self, 'total_debt') else total_debt,
                "cash": self.cash_and_equivalents if hasattr(self, 'cash_and_equivalents') else cash_and_equivalents,
                "equity_value": bridge["implied_equity_value"],
                "diluted_shares": bridge["diluted_shares_count"]
            },
            "wacc_breakdown": {
                "rf": wacc_details.get("assumptions", {}).get("risk_free_rate", 0.071),
                "erp": wacc_details.get("assumptions", {}).get("equity_risk_premium", 0.055),
                "beta": wacc_details.get("assumptions", {}).get("beta", 1.05)
            },
            "sensitivity_matrix": {
                "wacc_rates": [w / 100.0 for w in sens["wacc_headers"]],
                "growth_rates": [g / 100.0 for g in sens["growth_headers"]],
                "matrix": sens["price_matrix"]
            },
            "full_details": res
        }

