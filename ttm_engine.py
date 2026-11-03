"""
Trailing Twelve Months (TTM) Calculation Engine (spec §5).

Computes standardized TTM metrics:
TTM = Latest 10-K/Annual Report + YTD(Current Interim Period) - YTD(Prior-Year Interim Period)
"""
from typing import Dict, Any, Optional


def compute_ttm_metric(
    annual_value: Optional[float],
    current_interim_ytd: Optional[float] = None,
    prior_interim_ytd: Optional[float] = None
) -> Optional[float]:
    """
    Computes TTM value.
    If interim periods are provided:
        TTM = Annual + Current_Interim - Prior_Interim
    If no interim filings are available, falls back to latest Annual figure.
    """
    if annual_value is None:
        return None

    if current_interim_ytd is not None and prior_interim_ytd is not None:
        return annual_value + current_interim_ytd - prior_interim_ytd

    return annual_value


def compute_ttm_financials(
    latest_annual: Dict[str, float],
    current_quarter_ytd: Optional[Dict[str, float]] = None,
    prior_quarter_ytd: Optional[Dict[str, float]] = None
) -> Dict[str, float]:
    """
    Computes a full set of TTM financial metrics from annual and interim dictionaries.
    """
    ttm_results = {}
    for metric, val in latest_annual.items():
        curr_q = current_quarter_ytd.get(metric) if current_quarter_ytd else None
        prior_q = prior_quarter_ytd.get(metric) if prior_quarter_ytd else None
        ttm_results[metric] = compute_ttm_metric(val, curr_q, prior_q)
    return ttm_results
