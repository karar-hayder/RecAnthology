from django.urls import path
from .views import (
    AllGenres,
    AllTvMedia,
    GetTvMedia,
    FilterTvMedia,
    CreateTvMedia,
    CreateGenre,
    PublicRecommendTvMedia,
    PrivateRecommendTvMedia
)
from users.views import RateTvMedia

urlpatterns = [
    path('api/tvmedia/genres/', AllGenres.as_view(), name='tvmedia-all-genres'),
    path('api/tvmedia/', AllTvMedia.as_view(), name='tvmedia-all'),
    path('api/tvmedia/<uuid:id_query>/', GetTvMedia.as_view(), name='tvmedia-detail'),
    path('api/tvmedia/filter/', FilterTvMedia.as_view(), name='tvmedia-filter'),
    path('api/tvmedia/genre/create/', CreateGenre.as_view(), name='tvmedia-create-genre'),
    path('api/tvmedia/create/', CreateTvMedia.as_view(), name='tvmedia-create'),
    path('api/tvmedia/recommend/public/', PublicRecommendTvMedia.as_view(), name='tvmedia-recommend-public'),
    path('api/tvmedia/recommend/private/', PrivateRecommendTvMedia.as_view(), name='tvmedia-recommend-private'),
    path('api/tvmedia/rate/', RateTvMedia.as_view(), name='tvmedia-rate'),
]
