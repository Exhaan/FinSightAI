"""
Qualitative 10-K NLP & Sentiment Analyzer (spec MD&A & Risk Factors Intelligence).

Extracts qualitative alpha and sentiment signals from corporate text:
1. Management Discussion & Analysis (MD&A) forward-looking sentiment.
2. Item 1A Risk Factors severity and litigation exposure.
3. Supply chain and macroeconomic bottleneck detection using Loughran-McDonald financial lexicons.
4. Generates grounded text excerpts and qualitative scores (0-100).
"""
import re
from typing import Dict, List, Any, Optional

# Loughran-McDonald adapted financial sentiment lexicons
POSITIVE_TERMS = {
    "growth", "expand", "record", "innovative", "momentum", "tailwind", "surpass",
    "strength", "efficiency", "profitability", "opportunity", "upside", "resilient",
    "acceleration", "outperform", "dividend increase", "market share gain", "robust"
}

NEGATIVE_TERMS = {
    "decline", "impairment", "adverse", "recession", "deterioration", "deficit",
    "shortfall", "loss", "headwind", "downside", "decrease", "negative", "pressure",
    "weakness", "restructuring", "severance", "write-down", "slump"
}

UNCERTAINTY_TERMS = {
    "uncertain", "contingent", "fluctuate", "unpredictable", "volatility", "unforeseen",
    "approximate", "preliminary", "indefinite", "speculative", "varies", "pending"
}

LITIGATION_TERMS = {
    "litigation", "lawsuit", "investigation", "subpoena", "allegation", "regulatory fine",
    "infringement", "patent dispute", "arbitration", "penalty", "doj", "sec inquiry",
    "antitrust", "class action", "settlement"
}

SUPPLY_CHAIN_TERMS = {
    "shortage", "bottleneck", "supplier disruption", "geopolitical", "tariff",
    "export control", "freight cost", "component shortage", "raw material inflation",
    "sanction", "trade restriction"
}


class QualitativeDocumentScorer:
    """
    Performs NLP text analysis on extracted MD&A, Risk Factors, and Notes sections.
    """

    def analyze_text(self, text: str, page_number: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyzes a textual section or full document text.
        """
        if not text or len(text.strip()) < 30:
            return {
                "management_sentiment": 65.0,
                "litigation_safety": 85.0,
                "supply_resilience": 80.0,
                "composite_qualitative_score": 75.0,
                "sentiment_label": "Neutral / Stable",
                "key_excerpts": [],
                "risk_flags": [],
            }

        text_lower = text.lower()
        words = re.findall(r"\b[a-z]{3,}\b", text_lower)
        total_words = max(len(words), 1)

        # Count frequencies
        pos_count = sum(1 for w in words if w in POSITIVE_TERMS)
        neg_count = sum(1 for w in words if w in NEGATIVE_TERMS)
        unc_count = sum(1 for w in words if w in UNCERTAINTY_TERMS)
        lit_count = sum(1 for w in words if w in LITIGATION_TERMS)
        sup_count = sum(1 for w in words if w in SUPPLY_CHAIN_TERMS)

        # 1. Management Sentiment (0-100)
        # Ratio of positive vs negative words with baseline of 60
        net_tone = (pos_count - neg_count) / max((pos_count + neg_count), 5)
        management_sentiment = round(float(np_clip(60.0 + (net_tone * 35.0) - (unc_count / total_words * 500), 20.0, 95.0)), 1)

        # 2. Litigation Safety (0-100: Higher = Cleaner / Lower litigation risk)
        lit_density = (lit_count / total_words) * 1000
        litigation_safety = round(float(np_clip(90.0 - (lit_density * 18.0), 15.0, 95.0)), 1)

        # 3. Supply Chain Resilience (0-100: Higher = Lower disruption)
        sup_density = (sup_count / total_words) * 1000
        supply_resilience = round(float(np_clip(88.0 - (sup_density * 15.0), 20.0, 95.0)), 1)

        # 4. Composite Qualitative Health Score
        composite_score = round(
            0.45 * management_sentiment + 0.30 * litigation_safety + 0.25 * supply_resilience, 1
        )

        # Qualitative Sentiment Label
        if composite_score >= 78.0:
            sentiment_label = "Strong Bullish Outlook"
        elif composite_score >= 68.0:
            sentiment_label = "Constructive & Stable"
        elif composite_score >= 55.0:
            sentiment_label = "Cautious / Balanced"
        else:
            sentiment_label = "Elevated Risk Headwinds"

        # Extract Grounded Highlights & Quotes
        excerpts = []
        sentences = re.split(r"(?<=[.!?])\s+", text)
        for s in sentences:
            s_clean = s.strip()
            if len(s_clean) < 25 or len(s_clean) > 220:
                continue
            s_low = s_clean.lower()
            if any(t in s_low for t in ["record", "momentum", "tailwinds", "opportunity", "expand", "growth"]):
                excerpts.append({"type": "positive", "text": s_clean, "page": page_number or 2})
            elif any(t in s_low for t in ["litigation", "investigation", "tariff", "shortage", "headwinds", "adverse", "risk"]):
                excerpts.append({"type": "risk", "text": s_clean, "page": page_number or 2})

            if len(excerpts) >= 4:
                break

        # Detected textual risk flags
        risk_flags = []
        if lit_count >= 2:
            risk_flags.append("Disclosed active litigation or regulatory proceedings in filing")
        if sup_count >= 2:
            risk_flags.append("Identified supply chain constraints or material bottlenecks")
        if unc_count >= 5:
            risk_flags.append("Elevated forward-looking uncertainty language in MD&A")

        return {
            "management_sentiment": management_sentiment,
            "litigation_safety": litigation_safety,
            "supply_resilience": supply_resilience,
            "composite_qualitative_score": composite_score,
            "sentiment_label": sentiment_label,
            "key_excerpts": excerpts,
            "risk_flags": risk_flags,
            "word_counts": {
                "positive": pos_count,
                "negative": neg_count,
                "uncertainty": unc_count,
                "litigation": lit_count,
                "supply_chain": sup_count,
            }
        }


def np_clip(val: float, low: float, high: float) -> float:
    return max(low, min(high, val))
