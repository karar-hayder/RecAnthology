"""
Hybrid Recommendation Engine
=============================

Combines content-based and collaborative filtering into a single ranked list.

Formal Hybrid Scoring Equation:
    FinalScore = α · C_content + (1 - α) · C_cf

Where:
    - C_content: Content-based score (normalized genre affinity, 0-100)
    - C_cf:      Collaborative filtering score (cosine similarity weighted, 0-100)
    - α (alpha): Weight parameter that adapts to user interaction density.
                 New users (few ratings) → α ≈ 1.0 (content-heavy).
                 Active users (many ratings) → α = 1 - cf_weight (hybrid).

Adaptive Alpha:
    α = 1.0 - min(rating_count / threshold, 1.0) * cf_weight
    Default threshold = 15 ratings, default cf_weight = 0.4.
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from Books.models import Genre as BookGenre
from moviesNshows.models import Genre as TvGenre

from .collaborative_filtering import get_collaborative_recommendations
from .content_based_filtering import get_content_based_recommendations


def compute_adaptive_alpha(
    rating_count: int,
    cf_weight: float = 0.4,
    threshold: int = 15,
) -> float:
    """
    Compute the content-based weight (α) that adapts to user rating density.

    - Users with few ratings get α close to 1.0 (mostly content-based).
    - Users with many ratings get α = 1.0 - cf_weight (full hybrid).

    Args:
        rating_count: Number of ratings the user has made.
        cf_weight: Maximum collaborative filtering weight (0.0 to 1.0).
        threshold: Number of ratings at which full CF influence is reached.

    Returns:
        α value in [1.0 - cf_weight, 1.0].
    """
    t = min(rating_count / max(threshold, 1), 1.0)
    return 1.0 - t * cf_weight


def get_hybrid_recommendation(
    user: Any,
    user_needed_genres: Dict[TvGenre | BookGenre, float],
    interaction_model: Any,
    item_model: Any,
    item_field: str,
    max_num_genres: int = 10,
    max_media_per_genre: int = 20,
    top_n: int = 100,
    cf_weight: float = 0.4,
    rating_count: Optional[int] = None,
) -> List[Tuple[float, Any]]:
    """
    Combines genre-based recommendations with collaborative filtering.

    When ``rating_count`` is provided the hybrid weight adapts automatically
    via ``compute_adaptive_alpha``.  Otherwise ``cf_weight`` is used directly.
    """
    # Determine effective alpha
    if rating_count is not None:
        alpha = compute_adaptive_alpha(rating_count, cf_weight)
    else:
        alpha = 1.0 - cf_weight

    # 1. Get genre-based recommendations
    if item_field == "tvmedia":
        allowed_types = ("tvmedia",)
    else:
        allowed_types = ("books",)

    genre_recs = get_content_based_recommendations(
        user_needed_genres,
        max_num_genres,
        max_media_per_genre,
        allowed_types=allowed_types,
        user=user,
        interaction_model=interaction_model,
        item_field=item_field,
    )

    # 2. Get collaborative recommendations
    cf_recs = get_collaborative_recommendations(
        user, interaction_model, item_model, item_field, top_n=top_n
    )

    # 3. Merge: FinalScore = α · C_content + (1 - α) · C_cf
    combined_scores = defaultdict(float)
    items_map = {}

    for score, item in genre_recs:
        combined_scores[item.pk] += score * alpha
        items_map[item.pk] = item

    for score, item in cf_recs:
        combined_scores[item.pk] += score * (1 - alpha)
        items_map[item.pk] = item

    final_list = []
    for pk, score in combined_scores.items():
        final_list.append((round(score, 2), items_map[pk]))

    return sorted(final_list, key=lambda x: x[0], reverse=True)[:top_n]
