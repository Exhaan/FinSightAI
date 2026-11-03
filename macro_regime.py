"""
Macroeconomic Regime-Aware Recommendation Engine.

Dynamically shifts investment factor priorities based on macroeconomic regimes:
1. 'rising_rates_inflation': Focus on Free Cash Flow, low Debt-to-Equity, and high Pricing Power (Gross/Op Margins).
2. 'recession_late_cycle': Focus on Balance Sheet Safety, Low Beta, and Defensive Cash Generation.
3. 'expansion_bull': Focus on Revenue Growth, 3Y CAGR, and Capital Reinvestment (ROE/ROIC).
4. 'neutral': Standard balanced weights.
"""
from typing import Dict, Any


MACRO_REGIMES = {
    "neutral": {
        "name": "Neutral / Balanced Baseline",
        "description": "Standard market regime with balanced factor distribution.",
        "weight_multipliers": {
            "growth": 1.0,
            "profitability": 1.0,
            "financial_health": 1.0,
            "valuation": 1.0,
            "risk": 1.0,
            "esg": 1.0,
        },
        "regime_notes": "Balanced allocation across growth and quality metrics.",
    },
    "rising_rates_inflation": {
        "name": "Rising Rates & Inflationary Regime",
        "description": "Elevated central bank interest rates and high cost of capital.",
        "weight_multipliers": {
            "growth": 0.75,          # Speculative growth penalized by higher discount rates
            "profitability": 1.30,   # Pricing power and margin defense are paramount
            "financial_health": 1.40,# High leverage is punished by debt refinancing costs
            "valuation": 1.10,       # Intrinsic cash flow yield matters more than multiples
            "risk": 1.20,            # Safety / low leverage priority
            "esg": 0.85,
        },
        "regime_notes": "Prioritizes companies with low leverage, strong free cash flow yield, and high pricing power.",
    },
    "recession_late_cycle": {
        "name": "Late-Cycle / Recessionary Contraction",
        "description": "Economic slowdown with potential earnings compression.",
        "weight_multipliers": {
            "growth": 0.60,          # Cyclical growth slows
            "profitability": 1.15,   # Resilient margins
            "financial_health": 1.50,# Pristine balance sheets survive credit crunches
            "valuation": 1.15,       # Value and margin of safety
            "risk": 1.50,            # Low Beta / Low Volatility strongly favored
            "esg": 0.90,
        },
        "regime_notes": "Strong defensive bias: heavily rewards low-beta, high current-ratio, balance-sheet fortresses.",
    },
    "expansion_bull": {
        "name": "Early-Cycle / Expansionary Bull Market",
        "description": "Low interest rates, credit expansion, and accelerating corporate earnings.",
        "weight_multipliers": {
            "growth": 1.45,          # High reward for top-line revenue expansion and CAGR
            "profitability": 1.20,   # High ROIC / reinvestment efficiency
            "financial_health": 0.85,# Healthy leverage is tolerated to fund growth
            "valuation": 0.80,       # Market pays up for momentum and growth
            "risk": 0.80,            # Higher beta accepted for upside participation
            "esg": 1.00,
        },
        "regime_notes": "Aggressive growth orientation: maximizes top-line revenue acceleration and reinvestment returns.",
    },
}


def adjust_weights_for_macro_regime(base_weights: Dict[str, float], regime: str = "neutral") -> Dict[str, float]:
    """
    Applies regime-specific multipliers to factor weights and re-normalizes so sum == 1.0.
    """
    regime_key = regime.lower().replace(" ", "_").replace("&", "").replace("-", "_")
    config = MACRO_REGIMES.get(regime_key, MACRO_REGIMES["neutral"])
    multipliers = config["weight_multipliers"]

    adjusted = {}
    for factor, weight in base_weights.items():
        mult = multipliers.get(factor, 1.0)
        adjusted[factor] = weight * mult

    total = sum(adjusted.values())
    if total > 0:
        adjusted = {k: round(v / total, 4) for k, v in adjusted.items()}

    return adjusted


def get_macro_regime_info(regime: str = "neutral") -> Dict[str, Any]:
    """Returns metadata and rationale for a macro regime."""
    regime_key = regime.lower().replace(" ", "_").replace("&", "").replace("-", "_")
    return MACRO_REGIMES.get(regime_key, MACRO_REGIMES["neutral"])
