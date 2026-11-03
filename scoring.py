"""
Category-Level Scoring & Multi-Factor Weighted Scoring Engine (spec §19 & §20).

Calculates 6 category-level scores (0–100) for every company:
1. Growth Score (Revenue Growth, CAGR, FCF Growth)
2. Profitability Score (ROE, ROIC, Operating Margin, Net Margin, Gross Margin)
3. Financial Health Score (Debt-to-Equity, Current Ratio, Debt-to-Assets, Free Cash Flow)
4. Valuation Score (P/E, EV/EBITDA, DCF Upside)
5. Risk Score (Beta, Historical Volatility, Leverage — higher score = safer/lower risk)
6. ESG Score (Overall, Environmental, Social, Governance)

Combines these with configurable weights into a final Investment Score (0–100).
"""

# Default weights from spec §19
DEFAULT_WEIGHTS = {
    "growth": 0.20,
    "profitability": 0.20,
    "financial_health": 0.15,
    "valuation": 0.15,
    "risk": 0.10,
    "esg": 0.10,
    "user_preference_match": 0.10,
}

# Reference bands for normalization: {poor: val_for_0, excellent: val_for_100}
BENCHMARKS = {
    # Growth
    "revenue_growth": {"poor": -0.10, "excellent": 0.30},
    "revenue_cagr": {"poor": -0.05, "excellent": 0.25},
    "fcf_growth": {"poor": -0.15, "excellent": 0.35},

    # Profitability
    "gross_margin": {"poor": 0.15, "excellent": 0.65},
    "operating_margin": {"poor": 0.05, "excellent": 0.35},
    "net_margin": {"poor": 0.02, "excellent": 0.25},
    "roe": {"poor": 0.05, "excellent": 0.30},
    "roic": {"poor": 0.05, "excellent": 0.25},

    # Health (inverted where high is bad)
    "debt_to_equity": {"poor": 3.0, "excellent": 0.2, "invert": True},
    "debt_to_assets": {"poor": 0.70, "excellent": 0.15, "invert": True},
    "current_ratio": {"poor": 0.8, "excellent": 2.5},

    # Valuation (lower P/E is better value; higher DCF upside is better)
    "pe_ratio": {"poor": 45.0, "excellent": 12.0, "invert": True},
    "ev_ebitda": {"poor": 30.0, "excellent": 8.0, "invert": True},
    "dcf_upside": {"poor": -0.30, "excellent": 0.40},

    # Risk (lower beta and volatility = higher risk score / safer)
    "beta": {"poor": 2.2, "excellent": 0.6, "invert": True},
    "volatility": {"poor": 0.55, "excellent": 0.15, "invert": True},

    # ESG
    "esg_score": {"poor": 40.0, "excellent": 95.0},
}


def _norm(val: float | None, benchmark_key: str) -> float | None:
    """Normalizes a single metric to [0, 100] based on reference benchmarks."""
    if val is None:
        return None
    bm = BENCHMARKS.get(benchmark_key)
    if not bm:
        return None

    poor = bm["poor"]
    excellent = bm["excellent"]
    invert = bm.get("invert", False)

    if invert:
        # poor is high value (e.g. D/E=3.0), excellent is low (e.g. D/E=0.2)
        frac = (poor - val) / (poor - excellent)
    else:
        frac = (val - poor) / (excellent - poor)

    clamped = max(0.0, min(1.0, frac))
    return round(clamped * 100, 1)


def _avg_scores(scores: list[float | None]) -> float | None:
    valid = [s for s in scores if s is not None]
    if not valid:
        return None
    return round(sum(valid) / len(valid), 1)


# ---------------------------------------------------------------- Category Scores
def compute_growth_score(ratios: dict) -> float:
    scores = [
        _norm(ratios.get("revenue_growth"), "revenue_growth"),
        _norm(ratios.get("revenue_cagr"), "revenue_cagr"),
        _norm(ratios.get("fcf_growth"), "fcf_growth"),
    ]
    return _avg_scores(scores) or 50.0


def compute_profitability_score(ratios: dict) -> float:
    scores = [
        _norm(ratios.get("gross_margin"), "gross_margin"),
        _norm(ratios.get("operating_margin"), "operating_margin"),
        _norm(ratios.get("net_margin"), "net_margin"),
        _norm(ratios.get("roe"), "roe"),
        _norm(ratios.get("roic"), "roic"),
    ]
    return _avg_scores(scores) or 50.0


def compute_health_score(ratios: dict) -> float:
    scores = [
        _norm(ratios.get("debt_to_equity"), "debt_to_equity"),
        _norm(ratios.get("debt_to_assets"), "debt_to_assets"),
        _norm(ratios.get("current_ratio"), "current_ratio"),
    ]
    # FCF sign bonus
    fcf = ratios.get("free_cash_flow")
    if fcf is not None:
        scores.append(85.0 if fcf > 0 else 20.0)
    return _avg_scores(scores) or 50.0


def compute_valuation_score(ratios: dict) -> float:
    scores = [
        _norm(ratios.get("pe_ratio"), "pe_ratio"),
        _norm(ratios.get("ev_ebitda"), "ev_ebitda"),
        _norm(ratios.get("dcf_upside"), "dcf_upside"),
    ]
    return _avg_scores(scores) or 50.0


def compute_risk_score(ratios: dict) -> float:
    """Higher score = lower risk / safer."""
    scores = [
        _norm(ratios.get("beta"), "beta"),
        _norm(ratios.get("volatility"), "volatility"),
        _norm(ratios.get("debt_to_equity"), "debt_to_equity"),
    ]
    return _avg_scores(scores) or 50.0


def compute_esg_score(ratios: dict) -> float:
    esg_raw = ratios.get("esg_score", 75.0)
    return _norm(esg_raw, "esg_score") or 70.0


def compute_category_scores(ratios: dict) -> dict[str, float]:
    """Computes all 6 category scores (0–100) — spec §20."""
    return {
        "growth_score": compute_growth_score(ratios),
        "profitability_score": compute_profitability_score(ratios),
        "financial_health_score": compute_health_score(ratios),
        "valuation_score": compute_valuation_score(ratios),
        "risk_score": compute_risk_score(ratios),
        "esg_score": compute_esg_score(ratios),
    }


def score_company(
    ratios: dict,
    user_similarity: float | None = None,
    weights: dict | None = None,
) -> dict:
    """
    Computes category breakdown and final weighted investment score (0–100) — spec §19.
    """
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    categories = compute_category_scores(ratios)

    user_match_score = (user_similarity * 100.0) if user_similarity is not None else 80.0
    categories["user_preference_match"] = round(user_match_score, 1)

    weighted_sum = (
        categories["growth_score"] * w.get("growth", 0.20) +
        categories["profitability_score"] * w.get("profitability", 0.20) +
        categories["financial_health_score"] * w.get("financial_health", 0.15) +
        categories["valuation_score"] * w.get("valuation", 0.15) +
        categories["risk_score"] * w.get("risk", 0.10) +
        categories["esg_score"] * w.get("esg", 0.10) +
        categories["user_preference_match"] * w.get("user_preference_match", 0.10)
    )

    total_w = sum([
        w.get("growth", 0.20),
        w.get("profitability", 0.20),
        w.get("financial_health", 0.15),
        w.get("valuation", 0.15),
        w.get("risk", 0.10),
        w.get("esg", 0.10),
        w.get("user_preference_match", 0.10),
    ])

    final_score = round(weighted_sum / total_w, 1) if total_w > 0 else 50.0

    return {
        "score": final_score,
        "categories": categories,
        "weights": w,
    }
