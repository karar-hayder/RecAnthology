from django.core.cache import cache
from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from myutils import ExtraTools
from myutils.ExtraTools import get_cached_or_queryset
from RecAnthology.custom_throttles import AdminThrottle

from .api.serializers import Genre, GenreSerializer, TvMedia, TvMediaSerializer


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

        qs = (
            self.model.objects.filter(query).order_by("-startyear")
            if query
            else self.model.objects.order_by("-startyear")[:50]
        )
        serialized = self.serializer(qs, many=True).data
        return Response({"data": serialized})


def _build_media_recommendation(
    needed,
    max_genres,
    max_media_per_genre,
    scale_func,
    relativity_round=2,
    default_needed=6,
):
    needed_gens = ExtraTools.quickSort([(v, k) for k, v in needed.items()])[::-1][
        :max_genres
    ]
    media_seen = set()
    suggestions = []

    for rating, genre in needed_gens:
        related_media = genre.tvmedia.all().prefetch_related("genre")[
            :max_media_per_genre
        ]
        for media in related_media:
            if media.pk in media_seen:
                continue
            rt_score = 0
            genres = list(media.genre.all())
            for g in genres:
                needed_value = needed.get(g, default_needed)
                rt_score += scale_func(needed_value)
            score = (
                round(rt_score / (len(genres) * 100), relativity_round) if genres else 0
            )
            suggestions.append((score, media))
            media_seen.add(media.pk)
    return suggestions


class PublicRecommendTvMedia(APIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes = [AllowAny]

    def post(self, request):
        needed = request.data
        if not isinstance(needed, dict):
            return Response(
                {"error": "Request must be a dictionary of {genre: value}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            genre_objs = {
                Genre.objects.get(name=key): value for key, value in needed.items()
            }
        except Genre.DoesNotExist as e:
            return Response(
                {"error": f"Genre not found: {e}"},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_406_NOT_ACCEPTABLE)

        max_genres = 5
        max_media = 6  # per genre

        def scale_func(val):
            # Emulating the old scale: scale val from (1,10) to (-5,5) and *20
            return ExtraTools.scale(val, (1, 10), (-5, 5)) * 20

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
        response_data = {}
        for idx, (rel, media_entry) in enumerate(zip(relativity_list, media_data)):
            response_data[str(idx)] = {"relativity": rel, "media": media_entry}

        return Response({"length": len(final_media), "data": response_data})


class PrivateRecommendTvMedia(APIView):
    throttle_classes = [UserRateThrottle]
    model = TvMedia
    serializer = TvMediaSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cache_key = f"{request.user.pk}_media_recommendation"
        data = cache.get(cache_key)
        if data:
            return Response({"length": len(data), "data": data})

        needed = request.user.get_media_genre_preferences()
        if not needed:
            tv_media = self.model.objects.order_by("-startyear")[:100]
            media_data = self.serializer(tv_media, many=True).data
            return Response({"length": tv_media.count(), "data": media_data})

        max_genres = 10
        max_media = 21  # allow up to 21 media per genre for private

        def scale_func(val):
            return val * 20

        suggestions = _build_media_recommendation(
            needed,
            max_genres=max_genres,
            max_media_per_genre=max_media,
            scale_func=scale_func,
            relativity_round=3,
            default_needed=0,
        )

        sorted_suggestions = sorted(suggestions, key=lambda tup: tup[0], reverse=True)
        final_media = [b for _, b in sorted_suggestions][:100]
        relativity_list = [s[0] for s in sorted_suggestions][:100]

        media_data = self.serializer(final_media, many=True).data
        response_data = {}
        for idx, (rel, media_entry) in enumerate(zip(relativity_list, media_data)):
            response_data[str(idx)] = {"relativity": rel, "media": media_entry}

        cache.set(cache_key, response_data, 60 * 60)
        return Response({"length": len(response_data), "data": response_data})
