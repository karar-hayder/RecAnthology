"""
Evaluation Metrics for Recommendation Quality
==============================================

Pure-function implementations of standard offline recommendation metrics.
These have no Django ORM dependency and operate on plain Python data structures.

Supported metrics:
    - Precision@K
    - Recall@K
    - NDCG@K (Normalized Discounted Cumulative Gain)
    - train_test_split for offline evaluation
"""

import math
import random
from typing import Any, Dict, List, Set, Tuple


def train_test_split(
    ratings: List[Tuple[Any, Any, float]],
    ratio: float = 0.8,
    seed: int = 42,
) -> Tuple[List[Tuple[Any, Any, float]], List[Tuple[Any, Any, float]]]:
    """
    Split user–item rating records into train and test sets.

    Args:
        ratings: List of (user_id, item_id, rating) tuples.
        ratio: Fraction of data to use for training (0.0 to 1.0).
        seed: Random seed for reproducibility.

    Returns:
        (train_set, test_set) tuple.
    """
    rng = random.Random(seed)
    shuffled = list(ratings)
    rng.shuffle(shuffled)
    split_idx = int(len(shuffled) * ratio)
    return shuffled[:split_idx], shuffled[split_idx:]


def precision_at_k(
    recommended: List[Any],
    relevant: Set[Any],
    k: int,
) -> float:
    """
    Compute Precision@K: fraction of top-K recommended items that are relevant.

    Args:
        recommended: Ordered list of recommended item IDs (best first).
        relevant: Set of item IDs that are relevant (ground truth).
        k: Number of top recommendations to consider.

    Returns:
        Precision score in [0.0, 1.0].
    """
    if k <= 0:
        return 0.0
    top_k = recommended[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for item in top_k if item in relevant)
    return hits / len(top_k)


def recall_at_k(
    recommended: List[Any],
    relevant: Set[Any],
    k: int,
) -> float:
    """
    Compute Recall@K: fraction of relevant items that appear in top-K.

    Args:
        recommended: Ordered list of recommended item IDs (best first).
        relevant: Set of item IDs that are relevant (ground truth).
        k: Number of top recommendations to consider.

    Returns:
        Recall score in [0.0, 1.0].
    """
    if k <= 0 or not relevant:
        return 0.0
    top_k = recommended[:k]
    hits = sum(1 for item in top_k if item in relevant)
    return hits / len(relevant)


def dcg_at_k(
    recommended: List[Any],
    relevant: Set[Any],
    k: int,
) -> float:
    """
    Compute Discounted Cumulative Gain for top-K items.

    Uses binary relevance (1 if relevant, 0 otherwise).
    DCG = Σ (rel_i / log2(i + 2)) for i in 0..k-1
    """
    score = 0.0
    for i, item in enumerate(recommended[:k]):
        if item in relevant:
            score += 1.0 / math.log2(i + 2)
    return score


def ndcg_at_k(
    recommended: List[Any],
    relevant: Set[Any],
    k: int,
) -> float:
    """
    Compute Normalized Discounted Cumulative Gain at K.

    NDCG = DCG@K / IDCG@K where IDCG is the ideal (perfect) ordering.

    Args:
        recommended: Ordered list of recommended item IDs (best first).
        relevant: Set of item IDs that are relevant (ground truth).
        k: Number of top recommendations to consider.

    Returns:
        NDCG score in [0.0, 1.0].
    """
    if k <= 0 or not relevant:
        return 0.0

    actual_dcg = dcg_at_k(recommended, relevant, k)

    # Ideal DCG: all relevant items at the top
    ideal_k = min(k, len(relevant))
    ideal_dcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_k))

    if ideal_dcg == 0:
        return 0.0

    return actual_dcg / ideal_dcg


def evaluate_recommendations(
    user_recommendations: Dict[Any, List[Any]],
    user_relevant: Dict[Any, Set[Any]],
    k: int = 10,
) -> Dict[str, float]:
    """
    Compute average evaluation metrics across all users.

    Args:
        user_recommendations: {user_id: [recommended_item_ids]} (ordered).
        user_relevant: {user_id: {relevant_item_ids}} (ground truth).
        k: Top-K cutoff for all metrics.

    Returns:
        Dictionary with average Precision@K, Recall@K, and NDCG@K.
    """
    precisions = []
    recalls = []
    ndcgs = []

    for user_id, recs in user_recommendations.items():
        rel = user_relevant.get(user_id, set())
        if not rel:
            continue
        precisions.append(precision_at_k(recs, rel, k))
        recalls.append(recall_at_k(recs, rel, k))
        ndcgs.append(ndcg_at_k(recs, rel, k))

    n = len(precisions)
    if n == 0:
        return {"precision_at_k": 0.0, "recall_at_k": 0.0, "ndcg_at_k": 0.0}

    return {
        "precision_at_k": round(sum(precisions) / n, 4),
        "recall_at_k": round(sum(recalls) / n, 4),
        "ndcg_at_k": round(sum(ndcgs) / n, 4),
    }
