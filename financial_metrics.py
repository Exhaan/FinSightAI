"""
Financial Analytics & Feature Engineering Engine (spec §13).

Calculates standard corporate financial ratios across 5 key pillars:
1. Growth (Revenue Growth, Revenue CAGR, Net Income Growth, FCF Growth)
2. Profitability (Gross Margin, Operating Margin, Net Margin, ROE, ROIC)
3. Financial Health (Debt-to-Equity, Debt-to-Assets, Current Ratio, Interest Coverage, FCF)
4. Valuation (P/E, P/B, EV/EBITDA, Price-to-Sales, DCF Intrinsic Value & Upside)
5. Market Risk & ESG
"""
import math


# ---------------------------------------------------------------- Growth
def revenue_growth(current_revenue: float | None, previous_revenue: float | None) -> float | None:
    """(Current - Previous) / Previous — spec §13."""
    if current_revenue is None or previous_revenue in (None, 0):
        return None
    return (current_revenue - previous_revenue) / abs(previous_revenue)


def revenue_cagr(start_revenue: float | None, end_revenue: float | None, years: int) -> float | None:
    """CAGR = (End / Begin)**(1/years) - 1 — spec §13."""
    if start_revenue is None or end_revenue is None or start_revenue <= 0 or end_revenue <= 0 or years <= 0:
        return None
    try:
        return (end_revenue / start_revenue) ** (1.0 / years) - 1.0
    except (ValueError, ZeroDivisionError):
        return None


def net_income_growth(current_ni: float | None, previous_ni: float | None) -> float | None:
    if current_ni is None or previous_ni in (None, 0):
        return None
    return (current_ni - previous_ni) / abs(previous_ni)


def fcf_growth(current_fcf: float | None, previous_fcf: float | None) -> float | None:
    if current_fcf is None or previous_fcf in (None, 0):
        return None
    return (current_fcf - previous_fcf) / abs(previous_fcf)


# ---------------------------------------------------------------- Profitability
def gross_margin(gross_profit: float | None, revenue: float | None) -> float | None:
    """Gross Margin = Gross Profit / Revenue — spec §13."""
    if gross_profit is None or revenue in (None, 0):
        return None
    return gross_profit / revenue


def operating_margin(operating_income: float | None, revenue: float | None) -> float | None:
    """Operating Margin = Operating Income / Revenue — spec §13."""
    if operating_income is None or revenue in (None, 0):
        return None
    return operating_income / revenue


def net_margin(net_income: float | None, revenue: float | None) -> float | None:
    """Net Margin = Net Income / Revenue — spec §13."""
    if net_income is None or revenue in (None, 0):
        return None
    return net_income / revenue


def roe(net_income: float | None, equity: float | None) -> float | None:
    """Return on Equity = Net Income / Shareholders' Equity — spec §13."""
    if net_income is None or equity in (None, 0):
        return None
    return net_income / equity


def roic(operating_income: float | None, debt: float | None, equity: float | None,
         cash: float | None = 0.0, tax_rate: float = 0.21) -> float | None:
    """
    Return on Invested Capital (ROIC) = NOPAT / Invested Capital
    NOPAT = Operating Income * (1 - tax_rate)
    Invested Capital = Total Debt + Shareholders' Equity - Cash
    """
    if operating_income is None or debt is None or equity is None:
        return None
    invested_capital = debt + equity - (cash or 0.0)
    if invested_capital <= 0:
        return None
    nopat = operating_income * (1.0 - tax_rate)
    return nopat / invested_capital


# ---------------------------------------------------------------- Financial Health
def debt_to_equity(total_debt: float | None, equity: float | None) -> float | None:
    """Total Debt / Shareholders' Equity — spec §13."""
    if total_debt is None or equity in (None, 0):
        return None
    return total_debt / equity


def debt_to_assets(total_debt: float | None, assets: float | None) -> float | None:
    """Total Debt / Total Assets — spec §13."""
    if total_debt is None or assets in (None, 0):
        return None
    return total_debt / assets


def current_ratio(current_assets: float | None, current_liabilities: float | None) -> float | None:
    """Current Assets / Current Liabilities — spec §13."""
    if current_assets is None or current_liabilities in (None, 0):
        return None
    return current_assets / current_liabilities


def quick_ratio(current_assets: float | None, inventory: float | None, current_liabilities: float | None) -> float | None:
    """Quick Ratio = (Current Assets - Inventory) / Current Liabilities."""
    if current_assets is None or current_liabilities in (None, 0):
        return None
    quick_assets = current_assets - (inventory or 0.0)
    return quick_assets / current_liabilities


def assets_to_liabilities(assets: float | None, liabilities: float | None) -> float | None:
    """Assets upon Liabilities ratio = Total Assets / Total Liabilities."""
    if assets is None or liabilities in (None, 0):
        return None
    return assets / liabilities


def interest_coverage(operating_income: float | None, interest_expense: float | None) -> float | None:
    """Operating Income / Interest Expense — spec §13."""
    if operating_income is None or interest_expense in (None, 0):
        return None
    return operating_income / interest_expense


def free_cash_flow(operating_cash_flow: float | None, capex: float | None) -> float | None:
    """FCF = Operating Cash Flow - CapEx — spec §9/§13."""
    if operating_cash_flow is None or capex is None:
        return None
    return operating_cash_flow - abs(capex)


# ---------------------------------------------------------------- Valuation & DCF
def pe_ratio(market_cap: float | None, net_income: float | None) -> float | None:
    """Price-to-Earnings = Market Cap / Net Income — spec §13."""
    if market_cap is None or net_income in (None, 0) or net_income <= 0:
        return None
    return market_cap / net_income


def pb_ratio(market_cap: float | None, equity: float | None) -> float | None:
    """Price-to-Book = Market Cap / Shareholders' Equity — spec §13."""
    if market_cap is None or equity in (None, 0) or equity <= 0:
        return None
    return market_cap / equity


def ev_to_ebitda(market_cap: float | None, debt: float | None, cash: float | None,
                 ebitda: float | None) -> float | None:
    """
    EV / EBITDA = (Market Cap + Debt - Cash) / EBITDA — spec §13.
    """
    if market_cap is None or ebitda in (None, 0) or ebitda <= 0:
        return None
    ev = market_cap + (debt or 0.0) - (cash or 0.0)
    return ev / ebitda


def calculate_dcf_intrinsic_value(
    latest_fcf: float | None,
    growth_rate: float = 0.08,
    discount_rate: float = 0.09,
    terminal_growth: float = 0.025,
    forecast_years: int = 5,
) -> float | None:
    """
    Discounted Cash Flow (DCF) model — spec §13.
    Projects FCF for 5 years at growth_rate, discounts by discount_rate (WACC),
    and adds discounted terminal value.
    """
    if latest_fcf is None or latest_fcf <= 0 or discount_rate <= terminal_growth:
        return None

    pv_fcf = 0.0
    current_fcf = latest_fcf
    for year in range(1, forecast_years + 1):
        current_fcf *= (1.0 + growth_rate)
        pv_fcf += current_fcf / ((1.0 + discount_rate) ** year)

    # Terminal value in year 5
    terminal_fcf = current_fcf * (1.0 + terminal_growth)
    terminal_val = terminal_fcf / (discount_rate - terminal_growth)
    pv_terminal = terminal_val / ((1.0 + discount_rate) ** forecast_years)

    intrinsic_enterprise_value = pv_fcf + pv_terminal
    return intrinsic_enterprise_value


def dcf_upside(intrinsic_value: float | None, market_cap: float | None) -> float | None:
    """DCF Upside = (Intrinsic Value - Market Cap) / Market Cap — spec §13."""
    if intrinsic_value is None or market_cap in (None, 0) or market_cap <= 0:
        return None
    return (intrinsic_value - market_cap) / market_cap


# ---------------------------------------------------------------- Composite Ratios
def compute_all_ratios(
    current: dict,
    previous: dict | None = None,
    historical_start: dict | None = None,
    years_cagr: int = 2,
    market_data: dict | None = None,
) -> dict:
    """
    Computes the complete set of financial ratios across all pillars.
    """
    market = market_data or {}
    mcap = market.get("market_cap") or current.get("market_cap")
    beta_val = market.get("beta", 1.0)
    volatility_val = market.get("volatility", 0.25)
    esg_val = market.get("esg_score", 75.0)

    # Base figures
    rev = current.get("revenue")
    prev_rev = previous.get("revenue") if previous else None
    start_rev = historical_start.get("revenue") if historical_start else prev_rev
    
    ni = current.get("net_income")
    prev_ni = previous.get("net_income") if previous else None
    
    eq = current.get("equity")
    debt = current.get("debt")
    assets = current.get("assets")
    cash = current.get("cash", 0.0)
    curr_assets = current.get("current_assets")
    curr_liab = current.get("current_liabilities")
    
    gp = current.get("gross_profit")
    op_inc = current.get("operating_income") or current.get("ebit")
    ebitda = current.get("ebitda") or (op_inc * 1.15 if op_inc else None)
    
    ocf = current.get("operating_cash_flow")
    capex = current.get("capex")
    fcf = current.get("free_cash_flow") or free_cash_flow(ocf, capex)
    prev_fcf = previous.get("free_cash_flow") if previous else None

    # Compute DCF
    rev_g = revenue_growth(rev, prev_rev)
    growth_for_dcf = max(0.02, min(0.20, rev_g if rev_g is not None else 0.08))
    intrinsic_val = calculate_dcf_intrinsic_value(fcf, growth_rate=growth_for_dcf)
    upside = dcf_upside(intrinsic_val, mcap)

    return {
        # Growth
        "revenue_growth": rev_g,
        "revenue_cagr": revenue_cagr(start_rev, rev, years_cagr) if start_rev else rev_g,
        "net_income_growth": net_income_growth(ni, prev_ni),
        "fcf_growth": fcf_growth(fcf, prev_fcf),

        # Profitability
        "gross_margin": gross_margin(gp, rev),
        "operating_margin": operating_margin(op_inc, rev),
        "net_margin": net_margin(ni, rev),
        "roe": roe(ni, eq),
        "roic": roic(op_inc, debt, eq, cash),

        # Health & Liquidity
        "debt_to_equity": debt_to_equity(debt, eq),
        "debt_to_assets": debt_to_assets(debt, assets),
        "current_ratio": current_ratio(curr_assets, curr_liab),
        "quick_ratio": quick_ratio(curr_assets, current.get("inventories") or current.get("inventory"), curr_liab),
        "assets_to_liabilities": assets_to_liabilities(assets, current.get("liabilities")),
        "interest_coverage": interest_coverage(op_inc, current.get("interest_expense")),
        "free_cash_flow": fcf,

        # Valuation
        "pe_ratio": pe_ratio(mcap, ni),
        "pb_ratio": pb_ratio(mcap, eq),
        "ev_ebitda": ev_to_ebitda(mcap, debt, cash, ebitda),
        "dcf_intrinsic_value": intrinsic_val,
        "dcf_upside": upside,

        # Market & ESG
        "beta": beta_val,
        "volatility": volatility_val,
        "esg_score": esg_val,
    }


# Backwards compatibility for phase 1
def compute_ratios_for_company_year(current: dict, previous: dict | None = None) -> dict:
    return compute_all_ratios(current, previous)
