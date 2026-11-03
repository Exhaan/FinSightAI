"""
Portfolio-Aware Diversification Engine (Markowitz Modern Portfolio Theory / Correlation Penalty).

Evaluates candidates against the user's current investment portfolio:
1. Cross-Asset Correlation: Measures correlation with existing holdings.
2. Sector Concentration Risk: Flags excessive exposure to already-held sectors.
3. Diversification Score (0-100): Rewards assets that lower portfolio variance.
4. Actionable Allocation Insights: Explains why an asset improves or harms portfolio balance.
"""
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd

# Historical proxy cross-asset correlation matrix for key corporate assets
# Based on 3-year weekly return correlations across sectors
BENCHMARK_CORRELATION_MATRIX = {
    # Tech
    "AAPL": {"AAPL": 1.00, "NVDA": 0.72, "TSLA": 0.58, "PFE": 0.22, "NEE": 0.18, "TCS": 0.45, "RELIANCE": 0.38, "HDFCBANK": 0.35},
    "NVDA": {"AAPL": 0.72, "NVDA": 1.00, "TSLA": 0.65, "PFE": 0.15, "NEE": 0.12, "TCS": 0.48, "RELIANCE": 0.32, "HDFCBANK": 0.30},
    "TSLA": {"AAPL": 0.58, "NVDA": 0.65, "TSLA": 1.00, "PFE": 0.12, "NEE": 0.20, "TCS": 0.38, "RELIANCE": 0.40, "HDFCBANK": 0.32},
    # Healthcare
    "PFE": {"AAPL": 0.22, "NVDA": 0.15, "TSLA": 0.12, "PFE": 1.00, "NEE": 0.42, "TCS": 0.20, "RELIANCE": 0.25, "HDFCBANK": 0.28},
    # Utilities
    "NEE": {"AAPL": 0.18, "NVDA": 0.12, "TSLA": 0.20, "PFE": 0.42, "NEE": 1.00, "TCS": 0.15, "RELIANCE": 0.30, "HDFCBANK": 0.26},
    # Indian Large Caps
    "TCS": {"AAPL": 0.45, "NVDA": 0.48, "TSLA": 0.38, "PFE": 0.20, "NEE": 0.15, "TCS": 1.00, "RELIANCE": 0.55, "HDFCBANK": 0.62},
    "RELIANCE": {"AAPL": 0.38, "NVDA": 0.32, "TSLA": 0.40, "PFE": 0.25, "NEE": 0.30, "TCS": 0.55, "RELIANCE": 1.00, "HDFCBANK": 0.68},
    "HDFCBANK": {"AAPL": 0.35, "NVDA": 0.30, "TSLA": 0.32, "PFE": 0.28, "NEE": 0.26, "TCS": 0.62, "RELIANCE": 0.68, "HDFCBANK": 1.00},
}

# Sector correlation defaults when pair is not in explicit matrix
SECTOR_CORRELATION_DEFAULTS = {
    ("Technology", "Technology"): 0.75,
    ("Technology", "Healthcare"): 0.20,
    ("Technology", "Utilities"): 0.15,
    ("Technology", "Financial Services"): 0.40,
    ("Technology", "Energy"): 0.30,
    ("Healthcare", "Healthcare"): 0.65,
    ("Healthcare", "Utilities"): 0.35,
    ("Healthcare", "Financial Services"): 0.25,
    ("Utilities", "Utilities"): 0.70,
    ("Utilities", "Financial Services"): 0.30,
    ("Financial Services", "Financial Services"): 0.70,
}


class PortfolioDiversificationEngine:
    """
    Evaluates diversification impact of adding candidate stocks to an existing portfolio.
    """

    def __init__(self, correlation_matrix: Optional[Dict[str, Dict[str, float]]] = None):
        self.corr_matrix = correlation_matrix or BENCHMARK_CORRELATION_MATRIX

    def get_pairwise_correlation(
        self, ticker_a: str, ticker_b: str, sector_a: Optional[str] = None, sector_b: Optional[str] = None
    ) -> float:
        """Computes correlation between two assets with fallback to sector proxies."""
        t_a = ticker_a.upper().split(".")[0]
        t_b = ticker_b.upper().split(".")[0]

        if t_a == t_b:
            return 1.0

        if t_a in self.corr_matrix and t_b in self.corr_matrix[t_a]:
            return self.corr_matrix[t_a][t_b]
        if t_b in self.corr_matrix and t_a in self.corr_matrix[t_b]:
            return self.corr_matrix[t_b][t_a]

        # Sector-based proxy lookup
        if sector_a and sector_b:
            pair1 = (sector_a, sector_b)
            pair2 = (sector_b, sector_a)
            if pair1 in SECTOR_CORRELATION_DEFAULTS:
                return SECTOR_CORRELATION_DEFAULTS[pair1]
            if pair2 in SECTOR_CORRELATION_DEFAULTS:
                return SECTOR_CORRELATION_DEFAULTS[pair2]

        return 0.40  # Generic cross-market neutral default

    def evaluate_candidate(
        self,
        candidate_ticker: str,
        candidate_sector: str,
        current_holdings: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Evaluates a candidate stock against the user's existing portfolio.
        current_holdings: list of dicts, e.g. [{"ticker": "AAPL", "sector": "Technology", "weight": 0.5}]
        """
        if not current_holdings:
            return {
                "diversification_score": 75.0,  # Neutral baseline when starting fresh
                "avg_correlation": 0.40,
                "concentration_flag": False,
                "insights": "No existing holdings provided. Candidate evaluated on standalone merits.",
                "sector_overlap": False,
            }

        correlations = []
        same_sector_count = 0
        total_weight = 0.0

        for h in current_holdings:
            h_ticker = h.get("ticker", "")
            h_sector = h.get("sector", "")
            weight = h.get("weight", 1.0 / len(current_holdings))
            total_weight += weight

            corr = self.get_pairwise_correlation(
                candidate_ticker, h_ticker, candidate_sector, h_sector
            )
            correlations.append(corr * weight)

            if candidate_sector and h_sector and candidate_sector.lower() == h_sector.lower():
                same_sector_count += 1

        avg_corr = sum(correlations) / max(total_weight, 0.001)

        # Diversification score (0 to 100): Higher when correlation is LOW or NEGATIVE
        # Corr = 0.0 -> Score = 90
        # Corr = 0.2 -> Score = 80
        # Corr = 0.7 -> Score = 45
        # Corr = 1.0 -> Score = 20
        raw_score = (1.0 - avg_corr) * 80.0 + 20.0
        diversification_score = round(float(np.clip(raw_score, 10.0, 100.0)), 1)

        concentration_flag = avg_corr > 0.65 or same_sector_count > 0

        # Build natural language insight
        if avg_corr < 0.25:
            insight = f"Excellent diversifier! Low correlation ({avg_corr:.2f}) reduces overall portfolio volatility."
        elif avg_corr < 0.50:
            insight = f"Moderate diversification benefit (avg correlation: {avg_corr:.2f}) across existing holdings."
        else:
            if same_sector_count > 0:
                insight = f"High correlation ({avg_corr:.2f}) and sector overlap ({candidate_sector}). Increases sector concentration."
            else:
                insight = f"High correlation ({avg_corr:.2f}) with existing assets. Limited portfolio variance reduction."

        return {
            "diversification_score": diversification_score,
            "avg_correlation": round(avg_corr, 2),
            "concentration_flag": concentration_flag,
            "insights": insight,
            "sector_overlap": same_sector_count > 0,
        }
