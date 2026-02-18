from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from .serializers import (BookRatingSerializer, CustomUser,
                          TvMediaRatingSerializer, UserBookRating,
                          UserSerializer, UserTvMediaRating)

# Create your views here.


class Register(generics.CreateAPIView):
    throttle_classes = [AnonRateThrottle]
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        if "email" in request.data:
            if CustomUser.objects.filter(email=request.data["email"]).exists():
                return Response(
                    "There is already a user with this email",
                    status=status.HTTP_409_CONFLICT,
                )

        return super().create(request, *args, **kwargs)


class RateBook(generics.CreateAPIView):
    throttle_classes = [UserRateThrottle]
    queryset = UserBookRating.objects.all()
    serializer_class = BookRatingSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        print("RateBook POST request data:", self.request.data)
        response = super().post(request, *args, **kwargs)
        # Print errors if any (for debugging)
        if hasattr(response, "data") and isinstance(response.data, dict):
            if response.status_code >= 400:
                print("RateBook Error response:", response.data)
        return response

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RateTvMedia(generics.CreateAPIView):
    throttle_classes = [UserRateThrottle]
    queryset = UserTvMediaRating.objects.all()
    serializer_class = TvMediaRatingSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        print("RateTvMedia POST request data:", self.request.data)
        response = super().post(request, *args, **kwargs)
        # Print errors if any (for debugging)
        print(response)
        if hasattr(response, "data") and isinstance(response.data, dict):
            if response.status_code >= 400:
                print("RateTvMedia Error response:", response.data)
        return response

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserGenrePreferencesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # Book genre preferences
        books_prefs = []
        for pref in user.books_genre_preferences.select_related("genre").order_by(
            "-preference"
        ):
            books_prefs.append(
                {
                    "genre": pref.genre.name,
                    "preference": pref.preference,
                }
            )

        # TV media genre preferences
        tvmedia_prefs = []
        for pref in user.media_genre_preferences.select_related("genre").order_by(
            "-preference"
        ):
            tvmedia_prefs.append(
                {
                    "genre": pref.genre.name,
                    "preference": pref.preference,
                }
            )

        return Response(
            {
                "books_genre_preferences": books_prefs,
                "tvmedia_genre_preferences": tvmedia_prefs,
            }
        )
