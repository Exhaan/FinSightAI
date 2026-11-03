"""
Data Validation (spec §11).

Flags suspicious values rather than silently accepting them. Applied after
extraction, before values are trusted/stored as "clean" financial_metrics.
"""

TOLERANCE = 0.10  # 10% relative tolerance for accounting identities


def _rel_diff(a: float, b: float) -> float:
    denom = max(abs(a), abs(b), 1e-9)
    return abs(a - b) / denom


def validate_balance_sheet(assets: float | None, liabilities: float | None,
                            equity: float | None) -> str | None:
    """Assets ≈ Liabilities + Equity (spec §11)."""
    if assets is None or liabilities is None or equity is None:
        return None
    expected = liabilities + equity
    if _rel_diff(assets, expected) > TOLERANCE:
        return (f"Balance sheet mismatch: Assets ({assets:,.0f}) != "
                f"Liabilities+Equity ({expected:,.0f})")
    return None


def validate_gross_profit(gross_profit: float | None, revenue: float | None,
                           cost_of_revenue: float | None) -> str | None:
    """Gross Profit ≈ Revenue - Cost of Revenue (spec §11)."""
    if gross_profit is None or revenue is None or cost_of_revenue is None:
        return None
    expected = revenue - cost_of_revenue
    if _rel_diff(gross_profit, expected) > TOLERANCE:
        return (f"Gross profit mismatch: reported ({gross_profit:,.0f}) != "
                f"Revenue-COGS ({expected:,.0f})")
    return None


def validate_free_cash_flow(fcf: float | None, ocf: float | None,
                             capex: float | None) -> str | None:
    """Free Cash Flow ≈ Operating Cash Flow - CapEx (spec §11)."""
    if fcf is None or ocf is None or capex is None:
        return None
    expected = ocf - abs(capex)  # capex is often reported as a positive outflow
    if _rel_diff(fcf, expected) > TOLERANCE:
        return (f"FCF mismatch: reported ({fcf:,.0f}) != OCF-CapEx ({expected:,.0f})")
    return None


def validate_positive(metric_name: str, value: float | None,
                       should_be_positive: bool = True) -> str | None:
    """Sanity check: metrics like Revenue/Assets shouldn't be negative."""
    if value is None:
        return None
    if should_be_positive and value < 0:
        return f"{metric_name} is unexpectedly negative ({value:,.0f}) — check bracket parsing."
    return None


def run_all_validations(metrics: dict) -> list[str]:
    """
    metrics: dict of metric_name -> value (float or None), e.g. the output of
    analytics.financial_metrics.metrics_dict_for_year()
    Returns a list of human-readable warning strings (empty list = clean).
    """
    warnings = []

    checks = [
        validate_balance_sheet(metrics.get("assets"), metrics.get("liabilities"),
                                metrics.get("equity")),
        validate_gross_profit(metrics.get("gross_profit"), metrics.get("revenue"),
                               metrics.get("cost_of_revenue")),
        validate_free_cash_flow(metrics.get("free_cash_flow"), metrics.get("operating_cash_flow"),
                                 metrics.get("capex")),
        validate_positive("Revenue", metrics.get("revenue")),
        validate_positive("Total Assets", metrics.get("assets")),
    ]
    warnings.extend([c for c in checks if c])
    return warnings
