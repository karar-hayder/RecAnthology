from django.urls import path
from .views import (AllGenres
                    ,AllTvMedia
                    ,GetTvMedia
                    ,FilterTvMedia
                    ,CreateTvMedia
                    ,CreateGenre
                    ,PublicRecommendTvMedia
                    ,PrivateRecommendTvMedia)

from users.views import RateTvMedia

urlpatterns = [
    path('api/tvmedia/genres/all/',AllGenres.as_view()),
    path('api/tvmedia/get/all/',AllTvMedia.as_view()),
    path('api/tvmedia/get/',GetTvMedia.as_view()),
    path('api/tvmedia/filter/',FilterTvMedia.as_view()),
    path('api/tvmedia/create/genre/',CreateGenre.as_view()),
    path('api/tvmedia/create/',CreateTvMedia.as_view()),
    path('api/tvmedia/recommend/public/',PublicRecommendTvMedia.as_view()),
    path('api/tvmedia/recommend/private/',PrivateRecommendTvMedia.as_view()),
    path('api/tvmedia/rate/',RateTvMedia.as_view()),
]