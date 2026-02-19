"""
Feature Signal Bonuses
======================

Compute per-item bonus scores from metadata attributes beyond genre.
Each signal returns a value in [0.0, 1.0] that is multiplied by its weight.
The orchestrator ``compute_signal_bonus`` sums all applicable signals and
caps the total at ``MAX_SIGNAL_BONUS`` (default 30) on the 0-100 scale.

Signals:
    1. Popularity      — Books: likedPercent
    2. Author Affinity  — Books: same-author preference
    3. Language Pref    — Books: user's preferred language
    4. Recency          — TvMedia: startyear
    5. Media Type Match — TvMedia: movie vs show preference
"""

from collections import Counter
from typing import Any, Dict, Optional, Type

from django.db.models import Avg, Count, Model

MAX_SIGNAL_BONUS = 30.0

# Default weights per signal
DEFAULT_WEIGHTS: Dict[str, float] = {
    "popularity": 10.0,
    "author_affinity": 12.0,
    "language_preference": 5.0,
    "recency": 8.0,
    "media_type_match": 8.0,
}


def compute_popularity_bonus(item: Any) -> float:
    """
    Popularity signal for Books (likedPercent field).

    Returns a value in [0.0, 1.0] representing how popular the item is.
    Items without likedPercent return 0.0.
    """
    liked = getattr(item, "likedPercent", None)
    if liked is None:
        return 0.0
    return max(0.0, min(float(liked) / 100.0, 1.0))


def compute_author_affinity(
    item: Any,
    user: Any,
    interaction_model: Type[Model],
    item_field: str,
    min_books: int = 2,
    min_avg_rating: float = 7.0,
) -> float:
    """
    Author affinity signal for Books.

    Returns 1.0 if the user has rated >= ``min_books`` books by the same
    author with an average rating >= ``min_avg_rating``.  Otherwise 0.0.
    """
    author = getattr(item, "author", None)
    if not author or item_field != "book":
        return 0.0

    # Import here to avoid circular imports
    from Books.models import Book

    same_author_ids = Book.objects.filter(author=author).values_list("pk", flat=True)

    agg = interaction_model.objects.filter(
        user=user, **{f"{item_field}__in": same_author_ids}
    ).aggregate(
        count=Count("pk"),
        avg_rating=Avg("rating"),
    )

    count = agg.get("count") or 0
    avg_rating = agg.get("avg_rating") or 0

    if count >= min_books and avg_rating >= min_avg_rating:
        return 1.0
    return 0.0


def compute_language_preference(
    item: Any,
    user: Any,
    interaction_model: Type[Model],
    item_field: str,
) -> float:
    """
    Language preference signal for Books.

    Returns 1.0 if the item's language matches the user's most-rated language
    among their high-rated books (rating >= 7).  Otherwise 0.0.
    """
    language = getattr(item, "language", None)
    if not language or item_field != "book":
        return 0.0

    from Books.models import Book

    high_rated_ids = interaction_model.objects.filter(
        user=user, rating__gte=7
    ).values_list(f"{item_field}_id", flat=True)

    if not high_rated_ids:
        return 0.0

    languages = Book.objects.filter(pk__in=high_rated_ids).values_list(
        "language", flat=True
    )
    if not languages:
        return 0.0

    lang_counts = Counter(languages)
    top_language = lang_counts.most_common(1)[0][0]

    return 1.0 if language.lower() == top_language.lower() else 0.0


def compute_recency_bonus(
    item: Any, min_year: int = 1970, max_year: int = 2026
) -> float:
    """
    Recency signal for TvMedia (startyear field).

    Returns a value in [0.0, 1.0] where newer content scores higher.
    Items without startyear return 0.0.
    """
    year = getattr(item, "startyear", None)
    if year is None:
        return 0.0
    year_range = max(max_year - min_year, 1)
    return max(0.0, min((float(year) - min_year) / year_range, 1.0))


def compute_media_type_bonus(
    item: Any,
    user: Any,
    interaction_model: Type[Model],
    item_field: str,
) -> float:
    """
    Media type preference signal for TvMedia.

    Returns 1.0 if the item's media_type matches the user's most-rated
    media type among their high-rated items.  Otherwise 0.0.
    """
    media_type = getattr(item, "media_type", None)
    if not media_type or item_field != "tvmedia":
        return 0.0

    from moviesNshows.models import TvMedia

    high_rated_ids = interaction_model.objects.filter(
        user=user, rating__gte=7
    ).values_list(f"{item_field}_id", flat=True)

    if not high_rated_ids:
        return 0.0

    types = TvMedia.objects.filter(pk__in=high_rated_ids).values_list(
        "media_type", flat=True
    )
    if not types:
        return 0.0

    type_counts = Counter(types)
    top_type = type_counts.most_common(1)[0][0]

    return 1.0 if media_type.lower() == top_type.lower() else 0.0


def compute_signal_bonus(
    item: Any,
    user: Optional[Any],
    interaction_model: Optional[Type[Model]],
    item_field: str,
    weights: Optional[Dict[str, float]] = None,
    max_bonus: float = MAX_SIGNAL_BONUS,
) -> float:
    """
    Orchestrator: sum all applicable signal bonuses for an item.

    Args:
        item: Book or TvMedia instance.
        user: The requesting user (None for public/anonymous).
        interaction_model: UserBookRating or UserTvMediaRating.
        item_field: "book" or "tvmedia".
        weights: Override default signal weights.
        max_bonus: Cap on total bonus (default 30).

    Returns:
        Total bonus in [0.0, max_bonus].
    """
    w = weights or DEFAULT_WEIGHTS
    bonus = 0.0

    # Signal 1: Popularity (Books only, no user needed)
    bonus += compute_popularity_bonus(item) * w.get("popularity", 0)

    # Signal 4: Recency (TvMedia only, no user needed)
    bonus += compute_recency_bonus(item) * w.get("recency", 0)

    # User-dependent signals require both user and interaction_model
    if user is not None and interaction_model is not None:
        # Signal 2: Author Affinity (Books only)
        bonus += compute_author_affinity(
            item, user, interaction_model, item_field
        ) * w.get("author_affinity", 0)

        # Signal 3: Language Preference (Books only)
        bonus += compute_language_preference(
            item, user, interaction_model, item_field
        ) * w.get("language_preference", 0)

        # Signal 5: Media Type Match (TvMedia only)
        bonus += compute_media_type_bonus(
            item, user, interaction_model, item_field
        ) * w.get("media_type_match", 0)

    return min(bonus, max_bonus)
