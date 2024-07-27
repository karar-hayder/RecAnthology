from django.urls import path
from .views import (AllGenres
                    ,GetTvMedia
                    ,CreateTvMedia
                    ,CreateGenre)


urlpatterns = [
    path('api/tvmedia/genres/all/',AllGenres.as_view()),
    path('api/tvmedia/get/',GetTvMedia.as_view()),
    path('api/tvmedia/create/genre/',CreateGenre.as_view()),
    path('api/tvmedia/create/',CreateTvMedia.as_view()),
]