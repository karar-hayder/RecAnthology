from collections import defaultdict
from typing import Any, Dict, List, Tuple

from Books.models import Genre as BookGenre
from moviesNshows.models import Genre as TvGenre

from .collaborative_filtering import get_collaborative_recommendations
from .content_based_filtering import get_content_based_recommendations


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
) -> List[Tuple[float, Any]]:
    """
    Combines genre-based recommendations with collaborative filtering.
    """
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
    )

    # 2. Get collaborative recommendations
    cf_recs = get_collaborative_recommendations(
        user, interaction_model, item_model, item_field, top_n=top_n
    )

    # 3. Merge results
    combined_scores = defaultdict(float)
    items_map = {}

    # Genre scores weight
    for score, item in genre_recs:
        combined_scores[item.pk] += score * (1 - cf_weight)
        items_map[item.pk] = item

    # CF scores weight
    for score, item in cf_recs:
        combined_scores[item.pk] += score * cf_weight
        items_map[item.pk] = item

    final_list = []
    for pk, score in combined_scores.items():
        final_list.append((round(score, 2), items_map[pk]))

    return sorted(final_list, key=lambda x: x[0], reverse=True)[:top_n]
