from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import generics
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny
from .api.serializers import (
                                UserSerializer,CustomUser
                                ,BookRatingSerializer,UserBookRating
                                ,UserTvMediaRating, TvMediaRatingSerializer)
# Create your views here.

class Register(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        if 'email' in request.data:
            if CustomUser.objects.filter(email=request.data['email']).exists():
                return Response("There is already a user with this email",status=status.HTTP_409_CONFLICT)
        
        return super().create(request, *args, **kwargs)

class RateBook(generics.CreateAPIView):
    queryset = UserBookRating.objects.all()
    serializer_class = BookRatingSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class RateTvMedia(generics.CreateAPIView):
    queryset = UserTvMediaRating.objects.all()
    serializer_class = TvMediaRatingSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)