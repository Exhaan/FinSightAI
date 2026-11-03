"""
Explainable AI Engine (spec §23 & §25).

Generates grounded, transparent investment rationale:
- Strengths anchored directly to calculated financial metrics
- Key risks anchored to valuation, leverage, or volatility metrics
- Cluster archetype interpretation
- Exact data traceability citations (source page, table name, confidence)
- Portfolio Diversification & Correlation impact
- Qualitative 10-K Sentiment & MD&A Excerpt Grounding
- Macroeconomic Regime context

CRITICAL RULE (spec §23): All text is deterministic and grounded strictly in calculated facts.
"""
from typing import Dict, List, Any, Optional


def _describe_rating(score: float) -> str:
    if score >= 80:
        return "Excellent"
    elif score >= 65:
        return "Strong"
    elif score >= 50:
        return "Moderate"
    elif score >= 35:
        return "Weak"
    else:
        return "Poor"


def build_explanation(
    company_name: str,
    ratios: dict,
    score_result: dict,
    archetype: Optional[str] = None,
    rank: Optional[int] = None,
    citations: Optional[List[dict]] = None,
    diversification_info: Optional[Dict[str, Any]] = None,
    qualitative_info: Optional[Dict[str, Any]] = None,
    macro_info: Optional[Dict[str, Any]] = None,
) -> dict:
    """
    Constructs a fully explainable, transparent recommendation output.
    """
    strengths = []
    risks = []
    categories = score_result.get("categories", {})

    # 1. Growth Insights
    rg = ratios.get("revenue_growth")
    if rg is not None:
        if rg > 0.15:
            strengths.append(f"Strong top-line expansion with Revenue Growth of {rg:.1%}.")
        elif rg < 0:
            risks.append(f"Top-line contraction: Revenue declined by {abs(rg):.1%}.")

    cagr = ratios.get("revenue_cagr")
    if cagr is not None and cagr > 0.12 and cagr != rg:
        strengths.append(f"Sustained medium-term revenue CAGR of {cagr:.1%}.")

    # 2. Profitability Insights
    roe_val = ratios.get("roe")
    if roe_val is not None:
        if roe_val > 0.20:
            strengths.append(f"High capital efficiency: Return on Equity (ROE) is strong at {roe_val:.1%}.")
        elif roe_val < 0.08:
            risks.append(f"Subdued equity return: ROE is currently modest at {roe_val:.1%}.")

    net_m = ratios.get("net_margin")
    if net_m is not None:
        if net_m > 0.20:
            strengths.append(f"High bottom-line profitability with a Net Margin of {net_m:.1%}.")
        elif net_m < 0.05:
            risks.append(f"Thin profit margins: Net Margin stands at {net_m:.1%}.")

    # 3. Financial Health & Leverage Insights
    de = ratios.get("debt_to_equity")
    if de is not None:
        if de < 0.5:
            strengths.append(f"Conservative balance sheet leverage with Debt-to-Equity of {de:.2f}.")
        elif de > 1.5:
            risks.append(f"Elevated financial leverage: Debt-to-Equity is high at {de:.2f}.")

    fcf = ratios.get("free_cash_flow")
    if fcf is not None:
        if fcf > 0:
            strengths.append(f"Healthy cash flow generation: Positive Free Cash Flow of ${fcf:,.0f}M.")
        else:
            risks.append(f"Cash burn risk: Free Cash Flow is negative at -${abs(fcf):,.0f}M.")

    cr = ratios.get("current_ratio")
    if cr is not None and cr < 1.0:
        risks.append(f"Short-term liquidity pressure: Current Ratio is below 1.0 ({cr:.2f}).")

    # 4. Valuation Insights
    pe = ratios.get("pe_ratio")
    if pe is not None:
        if pe < 16.0:
            strengths.append(f"Attractive valuation: P/E multiple is low at {pe:.1f}x earnings.")
        elif pe > 40.0:
            risks.append(f"Premium valuation: P/E is elevated at {pe:.1f}x earnings.")

    upside = ratios.get("dcf_upside")
    if upside is not None:
        if upside > 0.15:
            strengths.append(f"DCF intrinsic valuation suggests an estimated upside of {upside:.1%}.")
        elif upside < -0.15:
            risks.append(f"DCF valuation indicates market price is trading at a premium over intrinsic cash flows.")

    # 5. Market Risk & ESG Insights
    beta_val = ratios.get("beta")
    if beta_val is not None:
        if beta_val > 1.4:
            risks.append(f"High market sensitivity: Beta of {beta_val:.2f} implies above-average price volatility.")
        elif beta_val < 0.8:
            strengths.append(f"Defensive risk profile: Low Beta of {beta_val:.2f} provides downside resilience.")

    esg_val = ratios.get("esg_score")
    if esg_val is not None and esg_val > 80.0:
        strengths.append(f"Superior corporate sustainability: ESG Score of {esg_val:.1f}/100.")

    # 6. Portfolio Diversification Insights
    if diversification_info:
        div_insight = diversification_info.get("insights")
        if div_insight:
            if diversification_info.get("concentration_flag"):
                risks.append(f"Portfolio Warning: {div_insight}")
            elif diversification_info.get("diversification_score", 0) >= 75:
                strengths.append(f"Portfolio Diversification: {div_insight}")

    # 7. Qualitative NLP Disclosures
    if qualitative_info:
        for r_flag in qualitative_info.get("risk_flags", []):
            risks.append(f"10-K Qualitative Disclosure: {r_flag}")
        if qualitative_info.get("composite_qualitative_score", 0) >= 80:
            strengths.append(f"Management MD&A: {qualitative_info.get('sentiment_label')} with strong operational momentum.")

    if not strengths:
        strengths.append("Company metrics are in line with broad market averages with no outstanding positive outliers.")
    if not risks:
        risks.append("No critical balance sheet or operational risk flags detected in extracted metrics.")

    profile_summary = {
        "Growth": _describe_rating(categories.get("growth_score", 50)),
        "Profitability": _describe_rating(categories.get("profitability_score", 50)),
        "Financial Health": _describe_rating(categories.get("financial_health_score", 50)),
        "Valuation": _describe_rating(categories.get("valuation_score", 50)),
        "Risk": "Low / Safe" if categories.get("risk_score", 50) >= 70 else ("Moderate" if categories.get("risk_score", 50) >= 45 else "High"),
        "ESG": _describe_rating(categories.get("esg_score", 70)),
    }

    return {
        "company": company_name,
        "rank": rank,
        "investment_match_score": score_result.get("score"),
        "archetype": archetype or "General Corporate Profile",
        "financial_profile": profile_summary,
        "strengths": strengths,
        "risks": risks,
        "category_scores": categories,
        "traceability_citations": citations or [],
        "diversification": diversification_info,
        "qualitative_nlp": qualitative_info,
        "macro_regime": macro_info,
        "grounding_statement": "This analysis is derived entirely from verified financial statement extractions, textual disclosures, and quantitative models.",
    }
