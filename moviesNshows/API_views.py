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

from myutils import recommendation
from myutils.api_mixins import BaseCRUDMixin, RecommendationMixin
from myutils.ExtraTools import get_cached_or_queryset
from RecAnthology.custom_throttles import AdminThrottle

from .serializers import Genre, GenreSerializer, TvMedia, TvMediaSerializer


class AllGenres(BaseCRUDMixin, APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    model = Genre
    serializer = GenreSerializer

    def get(self, request):
        return self.handle_list("tvmedia_genres")


class CreateGenre(BaseCRUDMixin, APIView):
    model = Genre
    serializer = GenreSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    throttle_classes = [AdminThrottle]

    def post(self, request):
        return self.handle_create(request)


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


class PublicRecommendTvMedia(RecommendationMixin, APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    model = TvMedia
    serializer = TvMediaSerializer
    item_type_key = "media"
    allowed_types = ("tvmedia",)

    def post(self, request):
        return self.handle_public_recommendation(request, Genre)


class PrivateRecommendTvMedia(RecommendationMixin, APIView):
    throttle_classes = [UserRateThrottle]
    model = TvMedia
    serializer = TvMediaSerializer
    permission_classes = [IsAuthenticated]
    item_type_key = "media"
    allowed_types = ("tvmedia",)

    def get(self, request):
        from users.models import UserTvMediaRating

        return self.handle_private_recommendation(
            request=request,
            genre_prefs_fn=request.user.get_media_genre_preferences,
            interaction_model=UserTvMediaRating,
            item_field="tvmedia",
            cache_key=f"private_tvmedia_recommendation_user_{request.user.pk}",
        )
