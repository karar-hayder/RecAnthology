from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from .serializers import (
    BookRatingSerializer,
    CustomUser,
    TvMediaRatingSerializer,
    UserBookRating,
    UserSerializer,
    UserTvMediaRating,
)

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

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RateTvMedia(generics.CreateAPIView):
    throttle_classes = [UserRateThrottle]
    queryset = UserTvMediaRating.objects.all()
    serializer_class = TvMediaRatingSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
