import numbers
import re
from collections import OrderedDict

from django.core.cache import cache
from django.db.models import Q
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from myutils import ExtraTools
from myutils.ExtraTools import get_cached_or_queryset
from RecAnthology.custom_throttles import AdminThrottle

from .serializers import Genre, GenreSerializer, TvMedia, TvMediaSerializer


class AllGenres(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    model = Genre
    serializer = GenreSerializer

    def get(self, request):
        data = get_cached_or_queryset(
            "tvmedia_genres", self.model.objects.all(), self.serializer, many=True
        )
        return Response({"data": data})


class CreateGenre(APIView):
    model = Genre
    serializer = GenreSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    throttle_classes = [AdminThrottle]

    def post(self, request):
        serializer = self.serializer(data=request.data)
        if serializer.is_valid():
            in_db = self.model.objects.filter(**serializer.validated_data)
            if in_db.exists():
                return Response(
                    {"data": self.serializer(in_db.first()).data},
                    status=status.HTTP_200_OK,
                )
            new_genre = serializer.save()
            return Response(
                {"data": self.serializer(new_genre).data},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AllTvMedia(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    model = TvMedia
    serializer = TvMediaSerializer

    def get(self, request):
        data = get_cached_or_queryset(
            "all_tvmedia",
            self.model.objects.all().order_by("-startyear")[:50],
            self.serializer,
            many=True,
        )
        return Response({"data": data})


class CreateTvMedia(APIView):
    model = TvMedia
    serializer = TvMediaSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    throttle_classes = [AdminThrottle]

    def post(self, request: Request):
        serializer = self.serializer(data=request.data)
        if serializer.is_valid():
            in_db = self.model.objects.filter(**serializer.validated_data)
            if in_db.exists():
                return Response(
                    {"data": self.serializer(in_db.first()).data},
                    status=status.HTTP_200_OK,
                )
            new_media = serializer.save()
            return Response(
                {"data": self.serializer(new_media).data},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetTvMedia(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    model = TvMedia
    serializer = TvMediaSerializer

    def get(self, request, id_query):
        if not id_query:
            return Response(
                {"error": "TV Media id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            tv_media = self.model.objects.get(id=id_query)
        except self.model.DoesNotExist:
            return Response(
                {"error": "TV Media not found."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response({"data": self.serializer(tv_media).data})


class FilterTvMedia(APIView):
    model = TvMedia
    serializer = TvMediaSerializer
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request):
        title = request.GET.get("title")
        media_id = request.GET.get("id")
        media_type = request.GET.get("media_type")
        genre = request.GET.get("genre")
        startyear = request.GET.get("start_year")
        endyear = request.GET.get("end_year")
        rated = request.GET.get("rated")  # "true" or "false" as string

        query = Q()
        if title:
            query &= Q(original_title__icontains=title)
        if media_id:
            query &= Q(id__icontains=media_id)
        if media_type:
            query &= Q(media_type__icontains=media_type)
        if genre:
            query &= Q(genre__name__icontains=genre)
        if startyear:
            try:
                query &= Q(startyear__gte=int(startyear))
            except (ValueError, TypeError):
                return Response(
                    {"error": "start_year must be an integer."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if endyear:
            try:
                query &= Q(startyear__lte=int(endyear))
            except (ValueError, TypeError):
                return Response(
                    {"error": "end_year must be an integer."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        base_qs = (
            self.model.objects.filter(query).order_by("-startyear")
            if query
            else self.model.objects.order_by("-startyear")[:50]
        )

        # Filtering by rating status
        user = request.user if request.user.is_authenticated else None
        if rated is not None and user is not None:
            from users.models import UserTvMediaRating

            if rated.lower() == "true":
                # Rated by current user
                rated_ids = UserTvMediaRating.objects.filter(user=user).values_list(
                    "tvmedia_id", flat=True
                )
                base_qs = base_qs.filter(id__in=rated_ids)
            elif rated.lower() == "false":
                # Not rated by current user
                rated_ids = UserTvMediaRating.objects.filter(user=user).values_list(
                    "tvmedia_id", flat=True
                )
                base_qs = base_qs.exclude(id__in=rated_ids)

        serialized = self.serializer(base_qs, many=True).data
        return Response({"data": serialized})


####### Recommendation Section ######
## Move into a better place than views
def _sort_and_select_top_genres(needed, max_genres, default_needed):
    """
    Returns a list of top genres limited to max_genres, sorted by preference.
    """
    genre_scores = []
    for genre, value in needed.items():
        try:
            score = float(value)
        except Exception:
            score = default_needed
        genre_scores.append((score, genre))
    genre_scores.sort(key=lambda tup: tup[0], reverse=True)
    top_genres = [g for _, g in genre_scores[:max_genres]]
    return top_genres


def _compute_media_rt_score(media, needed, scale_func, default_needed):
    """
    Compute the recommendation score for a media based on associated genres and user preferences.
    """
    genres = list(media.genre.all())
    if not genres:
        return 0, len(genres)
    rt_score = 0
    for g in genres:
        needed_value = needed.get(g, default_needed)
        try:
            needed_value = float(needed_value)
        except Exception:
            needed_value = default_needed
        rt_score += scale_func(needed_value)
    rt_score = max(rt_score, 0)
    return rt_score, len(genres)


def _collect_suggestions_with_scores(
    top_genres, needed, max_media_per_genre, scale_func, default_needed
):
    """
    For the given top genres, collect unique media and compute their recommendation scores.
    Returns:
        tuple (suggestions_with_rtscore, max_rt_score)
    """
    media_seen = set()
    suggestions_with_rtscore = []
    max_rt_score = 0

    for genre in top_genres:
        if not hasattr(genre, "tvmedia"):
            continue  # skip malformed
        related_qs = genre.tvmedia.all().prefetch_related("genre")[:max_media_per_genre]
        for media in related_qs:
            if media.pk in media_seen:
                continue
            rt_score, genres_count = _compute_media_rt_score(
                media, needed, scale_func, default_needed
            )
            suggestions_with_rtscore.append((rt_score, media, genres_count))
            if rt_score > max_rt_score:
                max_rt_score = rt_score
            media_seen.add(media.pk)
    return suggestions_with_rtscore, max_rt_score


def _normalize_and_format_suggestions(
    suggestions_with_rtscore, max_rt_score, relativity_round
):
    """
    Normalize recommendation scores out of 100 and return final list as (score, media).
    """
    if max_rt_score == 0:
        max_rt_score = 1  # avoid division by zero
    suggestions = []
    for rt_score, media, genres_count in suggestions_with_rtscore:
        score = round((rt_score / max_rt_score) * 100, relativity_round)
        score = min(max(score, 0), 100)
        suggestions.append((score, media))
    return suggestions


def _build_media_recommendation(
    needed,
    max_genres,
    max_media_per_genre,
    scale_func,
    relativity_round=2,
    default_needed=6,
):
    """
    Generate media recommendations based on user genre preferences.

    Args:
        needed (dict): {Genre: preference_value}
        max_genres (int): Max number of genres to use.
        max_media_per_genre (int): Max media to fetch per genre.
        scale_func (callable): Function that maps preference_value to weight.
        relativity_round (int): Decimals for relativity.
        default_needed (int|float): Fallback preference value.

    Returns:
        list: [(score, media), ...], where score is out of 100
    """
    if not needed:
        return []

    top_genres = _sort_and_select_top_genres(needed, max_genres, default_needed)
    suggestions_with_rtscore, max_rt_score = _collect_suggestions_with_scores(
        top_genres, needed, max_media_per_genre, scale_func, default_needed
    )
    suggestions = _normalize_and_format_suggestions(
        suggestions_with_rtscore, max_rt_score, relativity_round
    )
    return suggestions


####


class PublicRecommendTvMedia(APIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes = [AllowAny]

    class InputSerializer(serializers.Serializer):
        def to_internal_value(self, data):
            # Accepts a mapping of genre_name -> numeric value
            if not isinstance(data, dict):
                raise serializers.ValidationError(
                    "Input must be a dict of {genre: value}."
                )
            internal = {}
            for k, v in data.items():
                if not isinstance(k, str):
                    raise serializers.ValidationError(
                        "Each genre key must be a string."
                    )
                if not (isinstance(v, numbers.Number) and not isinstance(v, bool)):
                    raise serializers.ValidationError(
                        f"Value for genre '{k}' must be a number."
                    )
                internal[k] = v
            return internal

    def _get_all_genres(self):
        return list(Genre.objects.all())

    def _resolve_genres(self, needed):
        """
        Map each key from needed (untrusted genre names) to Genre instances.
        Case-insensitive + simple normalization.
        Raises a ValidationError if input is ambiguous or missing.
        """
        all_genres = self._get_all_genres()
        # Build normalized maps for fuzzy lookup
        # 1st priority: lowercase match, 2nd: normalized (alnum) match, 3rd: substring
        lower_map = {g.name.lower(): g for g in all_genres}
        alnum_map = {re.sub(r"[^a-z0-9]", "", g.name.lower()): g for g in all_genres}

        resolved = OrderedDict()
        missing = []
        ambiguous = []

        for user_key, value in needed.items():
            skey = (user_key or "").strip().lower()
            nkey = re.sub(r"[^a-z0-9]", "", skey)
            matches = [g for g in all_genres if g.name.lower() == skey]
            if not matches:
                # Try normalized match
                matches = [g for norm, g in alnum_map.items() if norm == nkey]
            if not matches:
                # Try substring match (final fallback)
                matches = [g for g in all_genres if skey and skey in g.name.lower()]
            # Disambiguation
            if len(matches) == 1:
                resolved[matches[0]] = value
            elif len(matches) == 0:
                missing.append(user_key)
            else:
                ambiguous.append(user_key)
        if missing or ambiguous:
            err = {}
            if missing:
                err["not_found"] = missing
            if ambiguous:
                err["ambiguous"] = ambiguous
            raise serializers.ValidationError(
                {
                    "error": "Some genres could not be resolved, see details.",
                    "detail": err,
                    "available_genres": sorted({g.name for g in all_genres}),
                }
            )
        return resolved

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )
        needed_raw = serializer.validated_data

        # Usage limits
        if len(needed_raw) > 20:
            return Response(
                {
                    "error": f"Too many genres supplied ({len(needed_raw)}). Max 20 allowed."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            genre_objs = self._resolve_genres(needed_raw)
        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_406_NOT_ACCEPTABLE)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_406_NOT_ACCEPTABLE)

        max_genres = 5
        max_media = 6

        def scale_func(val):
            try:
                v = max(1.0, min(10.0, float(val)))
            except Exception:
                v = 6.0
            return ExtraTools.scale(v, (1, 10), (-5, 5)) * 20

        suggestions = _build_media_recommendation(
            genre_objs,
            max_genres=max_genres,
            max_media_per_genre=max_media,
            scale_func=scale_func,
            relativity_round=1,
            default_needed=6,
        )

        sorted_suggestions = sorted(suggestions, key=lambda tup: tup[0], reverse=True)
        final_media = [b for _, b in sorted_suggestions][:100]
        relativity_list = [s[0] for s in sorted_suggestions][:100]

        media_data = TvMediaSerializer(final_media, many=True).data
        response_data = {
            str(idx): {"relativity": rel, "media": entry}
            for idx, (rel, entry) in enumerate(zip(relativity_list, media_data))
        }

        return Response(
            {
                "length": len(final_media),
                "data": response_data,
            }
        )


class PrivateRecommendTvMedia(APIView):
    throttle_classes = [UserRateThrottle]
    model = TvMedia
    serializer = TvMediaSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cache_key = f"private_tvmedia_recommendation_user_{request.user.pk}"
        data = cache.get(cache_key)
        if isinstance(data, dict):
            return Response({"length": len(data), "data": data})

        needed = request.user.get_media_genre_preferences()
        if not needed:
            # Fallback: latest media.
            tv_media = self.model.objects.order_by("-startyear")[:100]
            media_data = self.serializer(tv_media, many=True).data
            response_data = {
                str(idx): {"relativity": None, "media": entry}
                for idx, entry in enumerate(media_data)
            }
            return Response({"length": len(media_data), "data": response_data})

        max_genres = 10
        max_media = 21

        def scale_func(val):
            try:
                return float(val) * 20
            except Exception:
                return 0.0

        suggestions = _build_media_recommendation(
            needed,
            max_genres=max_genres,
            max_media_per_genre=max_media,
            scale_func=scale_func,
            relativity_round=4,
            default_needed=0,
        )

        sorted_suggestions = sorted(suggestions, key=lambda tup: tup[0], reverse=True)
        final_media = [b for _, b in sorted_suggestions][:100]
        relativity_list = [s[0] for s in sorted_suggestions][:100]

        media_data = self.serializer(final_media, many=True).data
        response_data = {
            str(idx): {"relativity": rel, "media": entry}
            for idx, (rel, entry) in enumerate(zip(relativity_list, media_data))
        }

        cache.set(cache_key, response_data, 60 * 60)  # 1 hour cache
        return Response({"length": len(response_data), "data": response_data})
