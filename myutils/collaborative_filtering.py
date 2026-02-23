import math
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, Type

from django.core.cache import cache
from django.db.models import Model

# Cache TTL for similarity results (6 hours)
SIMILARITY_CACHE_TTL = 60 * 60 * 6


def _similarity_cache_key(item_field: str, item_id: Any) -> str:
    """Generate a Redis cache key for item similarity data."""
    return f"item_sim:{item_field}:{item_id}"


def invalidate_similarity_cache(item_field: str, item_id: Any) -> None:
    """
    Invalidate the cached similarity data for a specific item.

    Should be called when a new rating is created/updated for the item.
    """
    cache.delete(_similarity_cache_key(item_field, item_id))


def calculate_cosine_similarity(
    ratings1: Dict[int, float], ratings2: Dict[int, float]
) -> float:
    """
    Calculates cosine similarity between two items based on user ratings.
    ratings: Dict[user_id, rating_value]
    """
    common_users = set(ratings1.keys()) & set(ratings2.keys())
    if not common_users:
        return 0.0

    dot_product = sum(float(ratings1[u]) * float(ratings2[u]) for u in common_users)
    norm1 = math.sqrt(sum(float(r) ** 2 for r in ratings1.values()))
    norm2 = math.sqrt(sum(float(r) ** 2 for r in ratings2.values()))

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)


def get_item_similarities(
    item_id: Any,
    interaction_model: Type[Model],
    item_field: str,
    use_cache: bool = True,
    shrinkage: float = 25.0,  # Regularization term λ
) -> List[Tuple[float, Any]]:
    """
    Calculates similarities with shrinkage regularization:
    shrunk_sim = (n / (n + lambda)) * sim
    where n is the number of co-ratings.
    """
    # Check cache first
    if use_cache:
        cache_key = _similarity_cache_key(item_field, f"{item_id}_shrunk_{shrinkage}")
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

    # Get all users who rated this item
    users_who_rated = interaction_model.objects.filter(
        **{item_field: item_id}
    ).values_list("user_id", flat=True)

    # Get all ratings for these users
    related_ratings = interaction_model.objects.filter(
        user_id__in=users_who_rated
    ).select_related(item_field)

    item_ratings: Dict[Any, Dict[int, float]] = defaultdict(dict)
    for r in related_ratings:
        iid = getattr(r, f"{item_field}_id")
        rating = getattr(r, "rating")
        user_id = getattr(r, "user_id")
        item_ratings[iid][user_id] = float(rating)

    target_ratings = item_ratings.get(item_id, {})
    if not target_ratings:
        return []

    similarities = []
    for other_id, other_ratings in item_ratings.items():
        if other_id == item_id:
            continue

        common_users = set(target_ratings.keys()) & set(other_ratings.keys())
        n = len(common_users)
        if n == 0:
            continue

        sim = calculate_cosine_similarity(target_ratings, other_ratings)

        # Apply shrinkage
        shrunk_sim = (float(n) / (float(n) + shrinkage)) * sim

        if shrunk_sim > 0:
            similarities.append((shrunk_sim, other_id))

    result = sorted(similarities, key=lambda x: x[0], reverse=True)

    # Store in cache
    if use_cache:
        cache.set(cache_key, result, SIMILARITY_CACHE_TTL)

    return result


def get_collaborative_recommendations(
    user: Any,
    interaction_model: Type[Model],
    item_model: Type[Model],
    item_field: str,
    top_n: int = 10,
    already_rated: Optional[set[Any]] = None,
) -> List[Tuple[float, Any]]:
    """
    Generates collaborative recommendations with candidate pool limiting.
    """
    # Get user's high-rated items (rating >= 7)
    user_interactions = interaction_model.objects.filter(
        user=user, rating__gte=7
    ).values_list(item_field, "rating")
    if not user_interactions:
        return []

    item_scores: Dict[Any, float] = defaultdict(float)
    item_weights: Dict[Any, float] = defaultdict(float)

    # Candidate pool limiting: only consider items similar to the user's top-N rated items
    # to reduce noise and increase signal-to-noise ratio.
    sorted_interactions = sorted(user_interactions, key=lambda x: x[1], reverse=True)[
        :10
    ]

    for item_id, user_rating in sorted_interactions:
        similarities = get_item_similarities(item_id, interaction_model, item_field)
        # Limit similarity candidates per item to further reduce noise
        for sim, sim_item_id in similarities[:50]:
            item_scores[sim_item_id] += float(sim) * float(user_rating)
            item_weights[sim_item_id] += float(sim)

    # Normalize scores and fetch objects
    recommendations = []
    if already_rated is None:
        already_rated = set(
            interaction_model.objects.filter(user=user).values_list(
                item_field, flat=True
            )
        )

    for item_id, total_score in item_scores.items():
        if item_id in already_rated:
            continue
        weight = item_weights[item_id]
        avg_score = total_score / weight if weight > 0 else 0
        recommendations.append((avg_score, item_id))

    recommendations.sort(key=lambda x: x[0], reverse=True)

    top_recommendations = recommendations[:top_n]
    top_ids = [iid for _, iid in top_recommendations]

    items_map = {obj.pk: obj for obj in item_model.objects.filter(pk__in=top_ids)}

    final_results = []
    for score, iid in top_recommendations:
        if iid in items_map:
            normalized_score = min(max(float(score) * 10, 0), 100)
            final_results.append((normalized_score, items_map[iid]))

    return final_results
