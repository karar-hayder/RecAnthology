import math
from collections import defaultdict
from typing import Any, Dict, List, Set, Tuple, Type

from django.db.models import Model, QuerySet


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
    item_id: Any, interaction_model: Type[Model], item_field: str
) -> List[Tuple[float, Any]]:
    """
    Calculates similarities between a target item and all other items that share at least one user rating.
    """
    # Get all users who rated this item
    users_who_rated = interaction_model.objects.filter(
        **{item_field: item_id}
    ).values_list("user_id", flat=True)

    # Get all ratings for these users (to build item profiles)
    related_ratings = interaction_model.objects.filter(
        user_id__in=users_who_rated
    ).select_related(item_field)

    # item_ratings[item_id][user_id] = rating
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
        sim = calculate_cosine_similarity(target_ratings, other_ratings)
        if sim > 0:
            similarities.append((sim, other_id))

    return sorted(similarities, key=lambda x: x[0], reverse=True)


def get_collaborative_recommendations(
    user: Any,
    interaction_model: Type[Model],
    item_model: Type[Model],
    item_field: str,
    top_n: int = 10,
) -> List[Tuple[float, Any]]:
    """
    Generates collaborative recommendations for a user based on their high-rated items.
    """
    # Get user's high-rated items (e.g., rating >= 7)
    user_interactions = interaction_model.objects.filter(
        user=user, rating__gte=7
    ).values_list(item_field, "rating")
    if not user_interactions:
        return []

    item_scores: Dict[Any, float] = defaultdict(float)
    item_weights: Dict[Any, float] = defaultdict(float)

    for item_id, user_rating in user_interactions:
        similarities = get_item_similarities(item_id, interaction_model, item_field)
        for sim, sim_item_id in similarities:
            # Simple weighted average of similarities
            item_scores[sim_item_id] += float(sim) * float(user_rating)
            item_weights[sim_item_id] += float(sim)

    # Normalize scores and fetch objects
    recommendations = []
    already_rated = set(
        interaction_model.objects.filter(user=user).values_list(item_field, flat=True)
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

    # Fetch actual objects and retain scores
    items_map = {obj.pk: obj for obj in item_model.objects.filter(pk__in=top_ids)}

    final_results = []
    for score, iid in top_recommendations:
        if iid in items_map:
            # Normalize score to 0-100 (assuming max rating is 10)
            normalized_score = min(max(float(score) * 10, 0), 100)
            final_results.append((normalized_score, items_map[iid]))

    return final_results
