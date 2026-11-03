"""
Recommendation Evaluation Metrics Suite (spec §4B).

Evaluates recommender accuracy, ranking quality, and portfolio diversity:
1. Precision@K = (Relevant Recommended Items) / K
2. Recall@K = (Relevant Recommended Items) / (Total Relevant Items)
3. NDCG@K (Normalized Discounted Cumulative Gain at K)
4. MAP (Mean Average Precision)
5. Catalog Coverage: Unique recommended items / Total catalog size
6. Intra-List Diversity: Average pairwise cosine distance between recommended items
7. Comparison against Popularity Baseline
"""
import numpy as np
from typing import List, Dict, Any, Set


def precision_at_k(recommended: List[str], ground_truth: Set[str], k: int = 5) -> float:
    """
    Precision@K
    """
    if k <= 0 or not recommended:
        return 0.0
    rec_k = recommended[:k]
    hits = sum(1 for item in rec_k if item in ground_truth)
    return hits / float(k)


def recall_at_k(recommended: List[str], ground_truth: Set[str], k: int = 5) -> float:
    """
    Recall@K
    """
    if not ground_truth or not recommended:
        return 0.0
    rec_k = recommended[:k]
    hits = sum(1 for item in rec_k if item in ground_truth)
    return hits / float(len(ground_truth))


def ndcg_at_k(recommended: List[str], ground_truth: Set[str], k: int = 5) -> float:
    """
    Normalized Discounted Cumulative Gain at K.
    Binary relevance: 1 if item in ground_truth, 0 otherwise.
    """
    if not recommended or not ground_truth or k <= 0:
        return 0.0

    rec_k = recommended[:k]
    dcg = 0.0
    for idx, item in enumerate(rec_k):
        rel = 1.0 if item in ground_truth else 0.0
        dcg += rel / np.log2(idx + 2.0)

    # Ideal DCG
    ideal_hits = min(len(ground_truth), k)
    idcg = sum(1.0 / np.log2(idx + 2.0) for idx in range(ideal_hits))

    return (dcg / idcg) if idcg > 0 else 0.0


def catalog_coverage(all_recommendations: List[List[str]], catalog_size: int) -> float:
    """
    Catalog Coverage: % of unique items recommended across all users/queries.
    """
    if catalog_size <= 0:
        return 0.0
    unique_items = set()
    for rec_list in all_recommendations:
        unique_items.update(rec_list)
    return len(unique_items) / float(catalog_size)


def intra_list_diversity(
    recommended_vectors: np.ndarray
) -> float:
    """
    Intra-List Diversity: Mean pairwise cosine distance (1 - cosine_similarity)
    between items in the recommendation list.
    """
    if len(recommended_vectors) <= 1:
        return 0.0

    from sklearn.metrics.pairwise import cosine_similarity
    sim_matrix = cosine_similarity(recommended_vectors)
    n = len(recommended_vectors)
    # Average off-diagonal distance
    dist_sum = 0.0
    pairs_count = 0
    for i in range(n):
        for j in range(i + 1, n):
            dist_sum += (1.0 - sim_matrix[i, j])
            pairs_count += 1

    return (dist_sum / pairs_count) if pairs_count > 0 else 0.0
