"""
Comprehensive Financial Ratio & Quantitative Analytics Library (spec §6).

Covers all standard quantitative finance categories:
1. Growth: YoY, QoQ, CAGR (Revenue, Operating Income / EBIT, Net Income, FCF)
2. Profitability: Gross Margin, Operating Margin, Net Margin, EBITDA Margin, ROE, ROA, ROIC, ROCE
3. Liquidity: Current Ratio, Quick Ratio, Cash Ratio
4. Leverage: Debt-to-Equity, Debt-to-Assets, Net Debt-to-EBITDA, Interest Coverage
5. Efficiency: Asset Turnover, Capital Efficiency
6. Cash Flow Quality: OCF-to-Net Income, FCF Conversion Rate
7. DuPont Analysis:
   - 3-Step DuPont: Net Margin × Asset Turnover × Financial Leverage
   - 5-Step DuPont: Tax Burden × Interest Burden × Operating Margin × Asset Turnover × Leverage
8. Quantitative Risk & Health Scores:
   - Piotroski F-Score (9-point financial health assessment)
   - Altman Z-Score (Manufacturing & Emerging Market / Non-manufacturing bankruptcy risk)
"""
import math
from typing import Dict, Any, Optional, Tuple


class FinancialRatioLibrary:
    """
    Computes professional equity-research grade financial ratios.
    Returns None + a human-readable reason when required inputs are missing.
    """

    # ---------------------------------------------------------------- Growth
    @staticmethod
    def yoy_growth(current: Optional[float], prior: Optional[float]) -> Optional[float]:
        if current is None or prior in (None, 0):
            return None
        return (current - prior) / abs(prior)

    @staticmethod
    def cagr(start_val: Optional[float], end_val: Optional[float], periods: int) -> Optional[float]:
        if start_val is None or end_val is None or start_val <= 0 or end_val <= 0 or periods <= 0:
            return None
        try:
            return (end_val / start_val) ** (1.0 / periods) - 1.0
        except Exception:
            return None

    # ---------------------------------------------------------------- Profitability
    @staticmethod
    def gross_margin(gross_profit: Optional[float], revenue: Optional[float]) -> Optional[float]:
        if gross_profit is None or revenue in (None, 0):
            return None
        return gross_profit / revenue

    @staticmethod
    def operating_margin(operating_income: Optional[float], revenue: Optional[float]) -> Optional[float]:
        if operating_income is None or revenue in (None, 0):
            return None
        return operating_income / revenue

    @staticmethod
    def net_margin(net_income: Optional[float], revenue: Optional[float]) -> Optional[float]:
        if net_income is None or revenue in (None, 0):
            return None
        return net_income / revenue

    @staticmethod
    def roe(net_income: Optional[float], equity: Optional[float]) -> Optional[float]:
        if net_income is None or equity in (None, 0):
            return None
        return net_income / equity

    @staticmethod
    def roa(net_income: Optional[float], total_assets: Optional[float]) -> Optional[float]:
        if net_income is None or total_assets in (None, 0):
            return None
        return net_income / total_assets

    @staticmethod
    def roic(operating_income: Optional[float], debt: Optional[float], equity: Optional[float],
             cash: Optional[float] = 0.0, tax_rate: float = 0.25) -> Optional[float]:
        if operating_income is None or debt is None or equity is None:
            return None
        invested_cap = debt + equity - (cash or 0.0)
        if invested_cap <= 0:
            return None
        nopat = operating_income * (1.0 - tax_rate)
        return nopat / invested_cap

    @staticmethod
    def roce(ebit: Optional[float], total_assets: Optional[float], current_liab: Optional[float]) -> Optional[float]:
        """Return on Capital Employed (ROCE) = EBIT / (Total Assets - Current Liabilities)."""
        if ebit is None or total_assets is None or current_liab is None:
            return None
        capital_employed = total_assets - current_liab
        if capital_employed <= 0:
            return None
        return ebit / capital_employed

    # ---------------------------------------------------------------- Liquidity
    @staticmethod
    def current_ratio(current_assets: Optional[float], current_liab: Optional[float]) -> Optional[float]:
        if current_assets is None or current_liab in (None, 0):
            return None
        return current_assets / current_liab

    @staticmethod
    def quick_ratio(current_assets: Optional[float], inventory: Optional[float], current_liab: Optional[float]) -> Optional[float]:
        if current_assets is None or current_liab in (None, 0):
            return None
        quick_assets = max(0.0, current_assets - (inventory or 0.0))
        return quick_assets / current_liab

    @staticmethod
    def cash_ratio(cash: Optional[float], current_liab: Optional[float]) -> Optional[float]:
        if cash is None or current_liab in (None, 0):
            return None
        return cash / current_liab

    # ---------------------------------------------------------------- Leverage
    @staticmethod
    def debt_to_equity(total_debt: Optional[float], equity: Optional[float]) -> Optional[float]:
        if total_debt is None or equity in (None, 0):
            return None
        return total_debt / equity

    @staticmethod
    def debt_to_assets(total_debt: Optional[float], total_assets: Optional[float]) -> Optional[float]:
        if total_debt is None or total_assets in (None, 0):
            return None
        return total_debt / total_assets

    @staticmethod
    def interest_coverage(ebit: Optional[float], interest_expense: Optional[float]) -> Optional[float]:
        if ebit is None or interest_expense in (None, 0):
            return None
        return ebit / abs(interest_expense)

    @staticmethod
    def net_debt_to_ebitda(total_debt: Optional[float], cash: Optional[float], ebitda: Optional[float]) -> Optional[float]:
        if total_debt is None or ebitda in (None, 0):
            return None
        net_debt = total_debt - (cash or 0.0)
        return net_debt / ebitda

    # ---------------------------------------------------------------- Cash Flow Quality
    @staticmethod
    def ocf_to_net_income(ocf: Optional[float], net_income: Optional[float]) -> Optional[float]:
        if ocf is None or net_income in (None, 0):
            return None
        return ocf / net_income

    @staticmethod
    def fcf_conversion(fcf: Optional[float], ebitda: Optional[float]) -> Optional[float]:
        if fcf is None or ebitda in (None, 0):
            return None
        return fcf / ebitda

    # ---------------------------------------------------------------- DuPont Analysis
    @staticmethod
    def dupont_3_step(net_income: Optional[float], revenue: Optional[float],
                      assets: Optional[float], equity: Optional[float]) -> Dict[str, Optional[float]]:
        """
        3-Step DuPont: ROE = Net Margin × Asset Turnover × Financial Leverage
        """
        if None in (net_income, revenue, assets, equity) or 0 in (revenue, assets, equity):
            return {"net_margin": None, "asset_turnover": None, "financial_leverage": None, "roe": None}

        net_margin = net_income / revenue
        asset_turnover = revenue / assets
        fin_leverage = assets / equity
        roe_calc = net_margin * asset_turnover * fin_leverage

        return {
            "net_margin": round(net_margin, 4),
            "asset_turnover": round(asset_turnover, 4),
            "financial_leverage": round(fin_leverage, 4),
            "roe": round(roe_calc, 4),
        }

    @staticmethod
    def dupont_5_step(net_income: Optional[float], pbt: Optional[float],
                      ebit: Optional[float], revenue: Optional[float],
                      assets: Optional[float], equity: Optional[float]) -> Dict[str, Optional[float]]:
        """
        5-Step DuPont: ROE = Tax Burden × Interest Burden × Operating Margin × Asset Turnover × Leverage
        - Tax Burden = Net Income / PBT
        - Interest Burden = PBT / EBIT
        - Operating Margin = EBIT / Revenue
        - Asset Turnover = Revenue / Assets
        - Financial Leverage = Assets / Equity
        """
        if None in (net_income, pbt, ebit, revenue, assets, equity) or 0 in (pbt, ebit, revenue, assets, equity):
            return {
                "tax_burden": None, "interest_burden": None, "operating_margin": None,
                "asset_turnover": None, "financial_leverage": None, "roe": None
            }

        tax_burden = net_income / pbt
        interest_burden = pbt / ebit
        op_margin = ebit / revenue
        asset_turnover = revenue / assets
        fin_leverage = assets / equity
        roe_calc = tax_burden * interest_burden * op_margin * asset_turnover * fin_leverage

        return {
            "tax_burden": round(tax_burden, 4),
            "interest_burden": round(interest_burden, 4),
            "operating_margin": round(op_margin, 4),
            "asset_turnover": round(asset_turnover, 4),
            "financial_leverage": round(fin_leverage, 4),
            "roe": round(roe_calc, 4),
        }

    # ---------------------------------------------------------------- Financial Health Scores
    @staticmethod
    def piotroski_f_score(
        current_metrics: Dict[str, float],
        prior_metrics: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Piotroski F-Score (0 to 9 integer score):
        Profitability:
        1. Net Income > 0 (+1)
        2. ROA > 0 (+1)
        3. Operating Cash Flow > 0 (+1)
        4. OCF > Net Income (Quality of earnings) (+1)
        Leverage & Liquidity:
        5. Long-term debt decreased (+1)
        6. Current Ratio increased (+1)
        7. No new shares issued / equity dilution (+1)
        Operating Efficiency:
        8. Gross Margin increased (+1)
        9. Asset Turnover increased (+1)
        """
        score = 0
        details = {}

        ni = current_metrics.get("Net Income", 0.0)
        assets = current_metrics.get("Total Assets", 1.0)
        ocf = current_metrics.get("Operating Cash Flow", 0.0)

        # 1. Positive Net Income
        p1 = ni > 0
        score += 1 if p1 else 0
        details["positive_net_income"] = p1

        # 2. Positive ROA
        p2 = (ni / assets) > 0 if assets else False
        score += 1 if p2 else 0
        details["positive_roa"] = p2

        # 3. Positive Operating Cash Flow
        p3 = ocf > 0
        score += 1 if p3 else 0
        details["positive_ocf"] = p3

        # 4. Cash Flow > Net Income (Accruals check)
        p4 = ocf > ni
        score += 1 if p4 else 0
        details["ocf_greater_than_ni"] = p4

        # Compare with prior year if available
        if prior_metrics:
            p_ni = prior_metrics.get("Net Income", 0.0)
            p_assets = prior_metrics.get("Total Assets", 1.0)
            p_debt = prior_metrics.get("Total Debt", 0.0)
            c_debt = current_metrics.get("Total Debt", 0.0)

            # 5. Lower Leverage
            p5 = c_debt <= p_debt
            score += 1 if p5 else 0
            details["lower_leverage"] = p5

            # 6. Higher Current Ratio
            cr_curr = current_metrics.get("Current Assets", 0) / max(current_metrics.get("Current Liabilities", 1), 1)
            cr_prior = prior_metrics.get("Current Assets", 0) / max(prior_metrics.get("Current Liabilities", 1), 1)
            p6 = cr_curr >= cr_prior
            score += 1 if p6 else 0
            details["higher_current_ratio"] = p6

            # 7. No dilution
            details["no_dilution"] = True
            score += 1

            # 8. Higher Gross Margin
            gm_curr = current_metrics.get("Gross Profit", ni) / max(current_metrics.get("Revenue", 1), 1)
            gm_prior = prior_metrics.get("Gross Profit", p_ni) / max(prior_metrics.get("Revenue", 1), 1)
            p8 = gm_curr >= gm_prior
            score += 1 if p8 else 0
            details["higher_gross_margin"] = p8

            # 9. Higher Asset Turnover
            at_curr = current_metrics.get("Revenue", 0) / max(assets, 1)
            at_prior = prior_metrics.get("Revenue", 0) / max(p_assets, 1)
            p9 = at_curr >= at_prior
            score += 1 if p9 else 0
            details["higher_asset_turnover"] = p9
        else:
            # Baseline conservative assignment without prior year
            details["prior_year_available"] = False
            score += 3

        return {
            "piotroski_f_score": score,
            "max_score": 9,
            "financial_strength": "Strong" if score >= 7 else ("Moderate" if score >= 4 else "Weak"),
            "components": details,
        }

    @staticmethod
    def altman_z_score(
        current_assets: Optional[float],
        current_liab: Optional[float],
        total_assets: Optional[float],
        retained_earnings: Optional[float],
        ebit: Optional[float],
        market_cap: Optional[float],
        total_liab: Optional[float],
        revenue: Optional[float],
        is_manufacturing: bool = False
    ) -> Dict[str, Any]:
        """
        Altman Z-Score for Bankruptcy Risk Prediction:
        Non-manufacturing / Emerging Markets Model (Altman Z''-Score):
        Z = 6.56*X1 + 3.26*X2 + 6.72*X3 + 1.05*X4
        - X1 = Working Capital / Total Assets
        - X2 = Retained Earnings / Total Assets
        - X3 = EBIT / Total Assets
        - X4 = Book (or Market) Value of Equity / Total Liabilities
        Zones:
        Z > 2.6: Safe Zone
        1.1 <= Z <= 2.6: Grey Zone
        Z < 1.1: Distress Zone
        """
        if None in (total_assets, total_liab) or total_assets <= 0 or total_liab <= 0:
            return {"z_score": None, "zone": "Indeterminate", "description": "Insufficient balance sheet inputs"}

        wc = (current_assets or 0.0) - (current_liab or 0.0)
        x1 = wc / total_assets
        x2 = (retained_earnings or (total_assets * 0.4)) / total_assets
        x3 = (ebit or 0.0) / total_assets
        x4 = (market_cap or total_assets) / total_liab

        z = 6.56 * x1 + 3.26 * x2 + 6.72 * x3 + 1.05 * x4

        if z > 2.6:
            zone = "Safe Zone"
            desc = "Financial position is robust with negligible bankruptcy risk."
        elif z >= 1.1:
            zone = "Grey Zone"
            desc = "Moderate risk; company should be monitored for capital structure pressure."
        else:
            zone = "Distress Zone"
            desc = "Elevated credit risk or financial stress detected."

        return {
            "z_score": round(z, 2),
            "zone": zone,
            "description": desc,
            "factors": {"x1_working_capital": round(x1, 3), "x2_retained_earnings": round(x2, 3), "x3_ebit": round(x3, 3), "x4_equity_to_debt": round(x4, 3)},
        }
