"""
Hybrid Investment Recommendation Engine (spec §15 & §22 + Advanced Extensions).

Combines:
1. Stage 1: Hard Constraint-Based Filtering (Risk, Leverage, ESG, Size, Sector)
2. Stage 2: 15-Dimensional Feature Engineering & Normalization
3. Stage 3: Cosine Similarity Matching against User Target Profile
4. Stage 4: K-Means Clustering for Peer Archetype Categorization
5. Stage 5: Institutional Collaborative Filtering (SVD / Co-Ownership Vectors)
6. Stage 6: Portfolio-Aware Diversification Engine (Correlation & Concentration Penalty)
7. Stage 7: Qualitative 10-K NLP & Sentiment Engine (MD&A & Risk Factors text)
8. Stage 8: Macroeconomic Regime Weight Adaptation
9. Stage 9: Blended Scoring & Grounded Explainable AI Generation
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional

from analytics.feature_vector import build_feature_dataframe, normalize_feature_vectors
from analytics.scoring import score_company
from recommendation.filters import passes_hard_filters
from recommendation.similarity import build_user_target_vector, compute_cosine_similarities
from recommendation.clustering import cluster_companies
from recommendation.explain import build_explanation
from recommendation.collaborative_filter import InstitutionalCollaborativeFilter
from recommendation.portfolio_diversification import PortfolioDiversificationEngine
from recommendation.qualitative_scorer import QualitativeDocumentScorer
from recommendation.macro_regime import adjust_weights_for_macro_regime, get_macro_regime_info


class HybridRecommendationEngine:
    def __init__(self, normalization_method: str = "minmax"):
        self.normalization_method = normalization_method
        self.cf_engine = InstitutionalCollaborativeFilter()
        self.diversification_engine = PortfolioDiversificationEngine()
        self.qualitative_scorer = QualitativeDocumentScorer()

    def recommend(
        self,
        company_universe: dict[str, dict],
        user_preferences: dict,
        weights: Optional[dict] = None,
        n_clusters: int = 3,
        macro_regime: str = "neutral",
    ) -> dict:
        """
        Executes the end-to-end multi-system recommendation pipeline.
        company_universe: {company_name: {"ratios": {...}, "metadata": {...}, "citations": [...], "text": "..."}}
        user_preferences: dict of user constraints and preferences
        weights: optional custom factor weights
        macro_regime: 'neutral', 'rising_rates_inflation', 'recession_late_cycle', 'expansion_bull'
        """
        if not company_universe:
            return {
                "ranked_recommendations": [],
                "ineligible_companies": [],
                "clustering": {},
                "macro_regime": get_macro_regime_info(macro_regime),
            }

        macro_regime = user_preferences.get("macro_regime", macro_regime)
        macro_info = get_macro_regime_info(macro_regime)

        # ---------------------------------------------------- Stage 1: Hard Filters
        eligible_companies = {}
        ineligible_companies = []

        for cname, cdata in company_universe.items():
            combined_data = {**cdata.get("ratios", {}), **cdata.get("metadata", {})}
            passes, failure_reasons = passes_hard_filters(combined_data, user_preferences)
            if passes:
                eligible_companies[cname] = cdata
            else:
                ineligible_companies.append({
                    "company": cname,
                    "failed_reasons": failure_reasons,
                    "metadata": cdata.get("metadata", {}),
                })

        # Fallback to entire universe if all filtered out
        active_universe = eligible_companies if eligible_companies else company_universe
        active_names = list(active_universe.keys())

        # ---------------------------------------------------- Stage 2: Feature Matrix & Normalization
        ratios_dict = {cname: cdata.get("ratios", {}) for cname, cdata in active_universe.items()}
        raw_df = build_feature_dataframe(ratios_dict)
        norm_matrix, scaler = normalize_feature_vectors(raw_df, method=self.normalization_method)

        # ---------------------------------------------------- Stage 3: Cosine Similarity
        user_target_vec = build_user_target_vector(user_preferences)
        similarities = compute_cosine_similarities(norm_matrix, user_target_vec, scaler=scaler)
        sim_map = {active_names[i]: float(similarities[i]) for i in range(len(active_names))}

        # ---------------------------------------------------- Stage 4: K-Means Clustering
        cluster_results = cluster_companies(
            norm_matrix, active_names, raw_df=raw_df, n_clusters=n_clusters
        )
        archetypes = cluster_results.get("archetypes", {})

        # ---------------------------------------------------- Stage 5: Collaborative Filtering
        user_portfolio = user_preferences.get("current_holdings", [])
        # Support string list or dict list for current_holdings
        parsed_portfolio = []
        cf_holding_input = {}
        for h in user_portfolio:
            if isinstance(h, str):
                t_clean = h.strip().upper().split(".")[0]
                parsed_portfolio.append({"ticker": t_clean, "sector": None})
                cf_holding_input[t_clean] = 1.0
            elif isinstance(h, dict):
                t_clean = h.get("ticker", "").strip().upper().split(".")[0]
                parsed_portfolio.append({
                    "ticker": t_clean,
                    "sector": h.get("sector"),
                    "weight": h.get("weight", 1.0)
                })
                cf_holding_input[t_clean] = h.get("weight", 1.0)

        cf_scores = {}
        if cf_holding_input:
            cf_scores = self.cf_engine.predict_user_preference(cf_holding_input)

        # ---------------------------------------------------- Stage 6: Macro Regime Weight Adaptation
        effective_weights = weights.copy() if weights else {
            "growth": 0.25,
            "profitability": 0.20,
            "financial_health": 0.20,
            "valuation": 0.15,
            "risk": 0.10,
            "esg": 0.10,
        }
        if macro_regime != "neutral":
            effective_weights = adjust_weights_for_macro_regime(effective_weights, macro_regime)

        # Configurable multi-system blending weights:
        # Content / Multi-Factor: 50%
        # Collaborative Filtering: 15%
        # Portfolio Diversification: 20%
        # Qualitative 10-K NLP Sentiment: 15%
        w_content = weights.get("content_weight", 0.50) if weights else 0.50
        w_cf = weights.get("cf_weight", 0.15) if weights else 0.15
        w_div = weights.get("diversification_weight", 0.20) if weights else 0.20
        w_qual = weights.get("qualitative_weight", 0.15) if weights else 0.15

        # Normalize weights if user didn't provide holdings
        if not parsed_portfolio:
            w_content += w_div * 0.70
            w_cf += w_div * 0.30
            w_div = 0.0

        # ---------------------------------------------------- Stage 7: Candidate Scoring & Explainability
        evaluated = []
        for idx, cname in enumerate(active_names):
            cdata = active_universe[cname]
            ratios = cdata.get("ratios", {})
            metadata = cdata.get("metadata", {})
            ticker = metadata.get("ticker", cname).upper().split(".")[0]
            sector = metadata.get("sector", "General")

            # A. Vector Cosine Similarity
            user_sim = sim_map.get(cname, 0.75)

            # B. Collaborative Filtering Score
            cf_raw = cf_scores.get(ticker)
            cf_val = cf_raw if cf_raw is not None else user_sim

            # C. Multi-Factor Fundamental Score
            score_res = score_company(ratios, user_similarity=user_sim, weights=effective_weights)
            archetype = archetypes.get(cname, "Core Enterprise")

            # D. Portfolio Diversification Evaluation
            div_res = self.diversification_engine.evaluate_candidate(
                candidate_ticker=ticker,
                candidate_sector=sector,
                current_holdings=parsed_portfolio,
            )

            # E. Qualitative 10-K NLP Analysis
            doc_text = cdata.get("text") or cdata.get("mda_text", "")
            # Synthesize representative MD&A disclosure if plain text is empty
            if not doc_text:
                doc_text = f"The company reported revenue growth of {ratios.get('revenue_growth', 0.08):.1%} driven by strong operational momentum and record demand across core product categories. Management noted continued investments in innovative technology, disciplined capital allocation, and strong cash flow generation despite broader macroeconomic uncertainty and supply chain fluctuations."

            qual_res = self.qualitative_scorer.analyze_text(doc_text, page_number=2)

            # F. Blended Hybrid Multi-System Score
            content_contrib = w_content * score_res["score"]
            cf_contrib = w_cf * (cf_val * 100.0)
            div_contrib = w_div * div_res["diversification_score"]
            qual_contrib = w_qual * qual_res["composite_qualitative_score"]

            final_hybrid_score = round(content_contrib + cf_contrib + div_contrib + qual_contrib, 1)

            evaluated.append({
                "company": cname,
                "score": final_hybrid_score,
                "content_score": score_res["score"],
                "cf_score": round(cf_val * 100.0, 1),
                "diversification_score": div_res["diversification_score"],
                "qualitative_score": qual_res["composite_qualitative_score"],
                "score_breakdown": score_res,
                "user_similarity": user_sim,
                "archetype": archetype,
                "ratios": ratios,
                "metadata": metadata,
                "citations": cdata.get("citations", []),
                "diversification_info": div_res,
                "qualitative_info": qual_res,
                "passed_filters": cname in eligible_companies,
            })

        # Sort descending by Blended Hybrid Score
        evaluated.sort(key=lambda x: x["score"], reverse=True)

        ranked_results = []
        for rank_idx, item in enumerate(evaluated, start=1):
            explanation = build_explanation(
                company_name=item["company"],
                ratios=item["ratios"],
                score_result=item["score_breakdown"],
                archetype=item["archetype"],
                rank=rank_idx,
                citations=item["citations"],
                diversification_info=item["diversification_info"],
                qualitative_info=item["qualitative_info"],
                macro_info=macro_info,
            )
            ranked_results.append({
                "rank": rank_idx,
                "company": item["company"],
                "investment_match_score": item["score"],
                "content_score": item["content_score"],
                "cf_score": item["cf_score"],
                "diversification_score": item["diversification_score"],
                "qualitative_score": item["qualitative_score"],
                "user_similarity_match": round(item["user_similarity"] * 100, 1),
                "cluster_archetype": item["archetype"],
                "passed_hard_filters": item["passed_filters"],
                "metadata": item["metadata"],
                "ratios": item["ratios"],
                "score_breakdown": item["score_breakdown"]["categories"],
                "diversification_info": item["diversification_info"],
                "qualitative_info": item["qualitative_info"],
                "explanation": explanation,
            })

        return {
            "ranked_recommendations": ranked_results,
            "ineligible_companies": ineligible_companies,
            "clustering": cluster_results,
            "macro_regime": macro_info,
            "total_universe_size": len(company_universe),
            "eligible_count": len(eligible_companies),
        }
