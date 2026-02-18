from collections import defaultdict
from typing import Any, Callable, Dict, List, Literal, Sequence, Tuple, Union

from Books.models import Book
from Books.models import Genre as BookGenre
from moviesNshows.models import Genre as TvGenre
from moviesNshows.models import TvMedia



def _sort_and_select_top_genres(
    user_genre_prefs: Dict[TvGenre | BookGenre, float],
    max_top_genres: int,
    default_preference: float,
) -> List[TvGenre | BookGenre]:
    """
    Returns a list of the top genres limited to max_top_genres, sorted by user preference.
    """
    genre_with_scores: List[Tuple[float, TvGenre | BookGenre]] = []
    for genre_obj, preference in user_genre_prefs.items():
        try:
            pref_score: float = float(preference)
        except Exception:
            pref_score = default_preference
        genre_with_scores.append((pref_score, genre_obj))
    genre_with_scores.sort(key=lambda item: item[0], reverse=True)
    selected_top_genres: List[TvGenre | BookGenre] = [
        genre for _, genre in genre_with_scores[:max_top_genres]
    ]
    return selected_top_genres


def _calculate_media_recommendation_score(
    media_instance: TvMedia | Book,
    user_needed_genres: Dict[TvGenre | BookGenre, float],
    scoring_fn: Callable[[Any, float], float] = None,
    default_value: float = 0,
) -> Union[Tuple[Literal[0], Literal[0]], Tuple[float, int]]:
    """
    Calculate the total recommendation score for a single media based on all its genres and user needs.
    scoring_fn is optional: if not supplied, just use user_pref (after float conversion) as the score.
    """
    media_genres: List[TvGenre | BookGenre] = list(media_instance.genre.all())
    if not media_genres:
        return 0, 0
    total_score: float = 0
    for genre in media_genres:
        user_pref: float = user_needed_genres.get(genre, default_value)
        if scoring_fn is not None:
            total_score += float(scoring_fn(genre, user_pref))
        else:
            total_score += float(user_pref)
    total_score = max(total_score, 0)
    return total_score, len(media_genres)


def _gather_recommendation_candidates(
    relevant_genres: Sequence[TvGenre | BookGenre],
    user_needed_genres: Dict[TvGenre | BookGenre, float],
    max_per_genre: int,
    scoring_fn: Callable[[Any, float], float] = None,
    fallback_pref_score: float = 0,
    allowed_types: Sequence[str] = ("tvmedia", "books"),
) -> Tuple[List[Tuple[float, Any, int]], float]:
    """
    Given selected genres, gathers unique media or book items and calculates their raw recommendation score.
    Args:
        relevant_genres: genres to consider
        user_needed_genres: mapping Genre -> pref
        max_per_genre: max to fetch per genre per type
        scoring_fn: function to transform user rating -> score (optional)
        fallback_pref_score: value to use if rating missing
        allowed_types: tuple/list of allowed related_names (e.g., ('tvmedia',), ('books',), or both)
    Returns:
        tuple (recommendations_with_score, highest_score)
    """

    RELATED_NAMES: List[str] = [
        name for name in ("tvmedia", "books") if name in allowed_types
    ]

    already_recommended_obj_ids: set[int] = set()
    object_score_candidates: List[Tuple[float, Any, int]] = []
    greatest_found_score: float = 0

    for genre in relevant_genres:
        for related_name in RELATED_NAMES:
            if not hasattr(genre, related_name):
                continue
            related_queryset = (
                getattr(genre, related_name)
                .all()
                .prefetch_related("genre")[:max_per_genre]
            )
            for obj in related_queryset:
                if obj.pk in already_recommended_obj_ids:
                    continue
                score, genre_count = _calculate_media_recommendation_score(
                    obj, user_needed_genres, scoring_fn, fallback_pref_score
                )
                object_score_candidates.append((float(score), obj, int(genre_count)))
                if float(score) > greatest_found_score:
                    greatest_found_score = float(score)
                already_recommended_obj_ids.add(obj.pk)
    return object_score_candidates, greatest_found_score


def _normalize_and_format_scores(
    media_score_candidates: List[Tuple[float, Any, int]],
    max_possible_score: float,
    decimal_places: int,
) -> List[Tuple[float, Any]]:
    """
    Scale raw scores to a 0-100 relativity score and return a list of (score, media_obj).
    """
    if float(max_possible_score) == 0:
        max_possible_score = 1  # avoid division by zero
    normalized_suggestions: List[Tuple[float, Any]] = []
    for raw_score, media_obj, genre_count in media_score_candidates:
        relativity: float = round(
            (float(raw_score) / float(max_possible_score)) * 100, decimal_places
        )
        relativity = min(max(relativity, 0), 100)
        normalized_suggestions.append((relativity, media_obj))
    return normalized_suggestions


def get_content_based_recommendations(
    user_needed_genres: Dict[TvGenre | BookGenre, float],
    max_num_genres: int,
    max_media_per_genre: int,
    scoring_fn: Callable[[Any, float], float] = None,
    relativity_decimals: int = 2,
    default_preference_score: float = 6,
    allowed_types: Sequence[str] = ("tvmedia","books",),
) -> List[Tuple[float, Any]]:
    """
    Generate media (or book) recommendations based on user genre preferences.

    Args:
        user_needed_genres (dict): {Genre: preference_value}
        max_num_genres (int): Maximum number of genres to consider.
        max_media_per_genre (int): Maximum recommendations to fetch per genre.
        scoring_fn (callable|None): Function to score a user preference (optional).
        relativity_decimals (int): Decimal places for relativity scoring.
        default_preference_score (int|float): Default score to use if preference is missing.
        allowed_types (tuple|list): Allowed related_names for objects ('tvmedia', 'books'), default just 'tvmedia'.

    Returns:
        list of tuples: [(relativity_score (0-100), media_obj), ...]
    """
    if not user_needed_genres:
        return []

    relevant_genres: List[TvGenre | BookGenre] = _sort_and_select_top_genres(
        user_needed_genres, int(max_num_genres), float(default_preference_score)
    )
    media_score_candidates, greatest_score = _gather_recommendation_candidates(
        relevant_genres,
        user_needed_genres,
        int(max_media_per_genre),
        scoring_fn,
        float(default_preference_score),
        allowed_types=allowed_types,
    )
    final_suggestions: List[Tuple[float, Any]] = _normalize_and_format_scores(
        media_score_candidates, float(greatest_score), int(relativity_decimals)
    )
    return final_suggestions
