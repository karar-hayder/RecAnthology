"""
Cold-Start Strategies
=====================

Handles the cold-start problem for both new users and new items.

New Users:
    Users with no or few ratings receive genre-weighted popularity recommendations.
    If no genre preferences exist at all, global popularity is used as a fallback.

New Items:
    Items with fewer than ``min_ratings`` user ratings receive a genre-affinity
    bonus when they match the user's top genres, preventing them from being
    permanently buried by well-established items.
"""

from typing import Any, Dict, List, Sequence, Tuple, Type

from django.db.models import Count, Model


def get_popular_by_genre(
    item_model: Type[Model],
    genre_prefs: Dict[Any, float],
    allowed_types: Sequence[str] = ("books",),
    limit: int = 100,
) -> List[Tuple[float, Any]]:
    """
    Return popular items filtered by the user's genre preferences.

    If ``genre_prefs`` is empty, falls back to global popularity.

    Args:
        item_model: Django model class (Book or TvMedia).
        genre_prefs: Mapping of Genre instances → preference scores.
        allowed_types: Not used directly here but kept for API consistency.
        limit: Maximum number of items to return.

    Returns:
        List of (score, item) tuples sorted by score descending.
        Score is a simple popularity metric (0–100).
    """
    if hasattr(item_model, "likedPercent"):
        order_field = "-likedPercent"
        score_field = "likedPercent"
    else:
        order_field = "-startyear"
        score_field = "startyear"

    if genre_prefs:
        genre_ids = [g.pk for g in genre_prefs.keys()]
        items = (
            item_model.objects.filter(genre__pk__in=genre_ids)
            .distinct()
            .order_by(order_field)[:limit]
        )
    else:
        items = item_model.objects.order_by(order_field)[:limit]

    results: List[Tuple[float, Any]] = []
    for item in items:
        raw = getattr(item, score_field, 0) or 0
        # Normalize startyear to a 0-100 scale (1970–2026 range)
        if score_field == "startyear":
            score = min(max((raw - 1970) / (2026 - 1970) * 100, 0), 100)
        else:
            score = float(raw)
        results.append((round(score, 2), item))

    return sorted(results, key=lambda x: x[0], reverse=True)


def boost_new_items(
    recommendations: List[Tuple[float, Any]],
    interaction_model: Type[Model],
    item_field: str,
    genre_prefs: Dict[Any, float],
    item_model: Type[Model],
    min_ratings: int = 5,
    boost_factor: float = 15.0,
    max_boosted: int = 10,
) -> List[Tuple[float, Any]]:
    """
    Boost under-rated items that match the user's genre preferences.

    Items with fewer than ``min_ratings`` ratings receive a score bonus
    proportional to genre affinity, ensuring new content surfaces.

    Args:
        recommendations: Existing scored recommendations [(score, item), ...].
        interaction_model: Rating model (UserBookRating or UserTvMediaRating).
        item_field: FK field name on the rating model (e.g. "book", "tvmedia").
        genre_prefs: User's genre preference mapping.
        item_model: Django model class for the items.
        min_ratings: Threshold below which an item is considered "new".
        boost_factor: Maximum bonus score added to new items.
        max_boosted: Maximum number of new items to inject.

    Returns:
        Updated list of (score, item) tuples, re-sorted.
    """
    if not genre_prefs:
        return recommendations

    existing_pks = {item.pk for _, item in recommendations}

    # Find items with few ratings using the interaction model's reverse relation
    # e.g. Book → UserBookRating reverse is "userbookrating"
    reverse_name = interaction_model.__name__.lower()
    low_rated_items = (
        item_model.objects.annotate(rating_count=Count(reverse_name))
        .filter(rating_count__lt=min_ratings)
        .prefetch_related("genre")
        .order_by("-rating_count")[: max_boosted * 3]
    )

    user_genre_pks = {g.pk for g in genre_prefs.keys()}
    boosted = []

    for item in low_rated_items:
        if item.pk in existing_pks:
            continue
        item_genre_pks = set(item.genre.values_list("pk", flat=True))
        overlap = len(item_genre_pks & user_genre_pks)
        if overlap > 0:
            # Bonus proportional to genre overlap
            bonus = boost_factor * (overlap / max(len(item_genre_pks), 1))
            boosted.append((round(bonus, 2), item))
            existing_pks.add(item.pk)
            if len(boosted) >= max_boosted:
                break

    combined = list(recommendations) + boosted
    return sorted(combined, key=lambda x: x[0], reverse=True)
