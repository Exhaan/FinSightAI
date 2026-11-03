"""
Valuation Package — Free Cash Flow to Firm (FCFF) Driver Engine (spec §7).

Projects FCFF over a 5-year forecast horizon:
FCFF = EBIT * (1 - t) + D&A - CapEx - Change_in_NWC

Forecast Drivers:
- Revenue Growth Rate (defaults to historical median)
- Operating Margin (EBIT / Revenue)
- Effective Tax Rate (t)
- D&A as % of Revenue
- CapEx as % of Revenue
- Change in Net Working Capital (ΔNWC) as % of Revenue
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class DCFDrivers:
    revenue_growth: float = 0.08      # 8.0%
    operating_margin: float = 0.22    # 22.0%
    tax_rate: float = 0.25            # 25.0%
    dna_pct_rev: float = 0.03         # 3.0% of revenue
    capex_pct_rev: float = 0.035      # 3.5% of revenue
    nwc_pct_rev: float = 0.015        # 1.5% of revenue


@dataclass
class YearlyFCFFProjection:
    year: int
    revenue: float
    ebit: float
    nopat: float
    dna: float
    capex: float
    delta_nwc: float
    fcff: float
    discount_factor: float
    pv_fcff: float


def project_fcff_series(
    base_revenue: float,
    drivers: DCFDrivers,
    wacc: float,
    forecast_years: int = 5,
    mid_year_discounting: bool = True,
) -> List[YearlyFCFFProjection]:
    """
    Generates year-by-year projected FCFF and discounted present values.
    """
    projections = []
    current_rev = base_revenue

    for t in range(1, forecast_years + 1):
        # Revenue projection
        current_rev *= (1.0 + drivers.revenue_growth)
        ebit = current_rev * drivers.operating_margin
        nopat = ebit * (1.0 - drivers.tax_rate)
        dna = current_rev * drivers.dna_pct_rev
        capex = current_rev * drivers.capex_pct_rev
        delta_nwc = current_rev * drivers.nwc_pct_rev

        # FCFF formula
        fcff = nopat + dna - capex - delta_nwc

        # Discount factor (mid-year discounting uses t - 0.5)
        period = (t - 0.5) if mid_year_discounting else float(t)
        disc_factor = 1.0 / ((1.0 + wacc) ** period)
        pv_fcff = fcff * disc_factor

        projections.append(YearlyFCFFProjection(
            year=t,
            revenue=round(current_rev, 2),
            ebit=round(ebit, 2),
            nopat=round(nopat, 2),
            dna=round(dna, 2),
            capex=round(capex, 2),
            delta_nwc=round(delta_nwc, 2),
            fcff=round(fcff, 2),
            discount_factor=round(disc_factor, 4),
            pv_fcff=round(pv_fcff, 2),
        ))

    return projections
