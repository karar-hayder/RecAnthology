from django.urls import path

from users.API_views import RateTvMedia

from . import API_views, views

urlpatterns = [
    #### Main ####
    path(
        "tvmedia/explore/", views.ExploreTVMediaPage.as_view(), name="explore tvmedia"
    ),
    path("tvmedia/rate/", views.RateTVMediaPage.as_view(), name="tvmedia-rate-page"),
    path(
        "tvmedia/recommendations/",
        views.RecommendationPage.as_view(),
        name="tvmedia-rec-page",
    ),
    #### API ####
    path(
        "api/tvmedia/genres/", API_views.AllGenres.as_view(), name="tvmedia-all-genres"
    ),
    path("api/tvmedia/", API_views.AllTvMedia.as_view(), name="tvmedia-all"),
    path(
        "api/tvmedia/<uuid:id_query>/",
        API_views.GetTvMedia.as_view(),
        name="tvmedia-detail",
    ),
    path(
        "api/tvmedia/filter/", API_views.FilterTvMedia.as_view(), name="tvmedia-filter"
    ),
    path(
        "api/tvmedia/genre/create/",
        API_views.CreateGenre.as_view(),
        name="tvmedia-create-genre",
    ),
    path(
        "api/tvmedia/create/", API_views.CreateTvMedia.as_view(), name="tvmedia-create"
    ),
    path(
        "api/tvmedia/recommend/public/",
        API_views.PublicRecommendTvMedia.as_view(),
        name="tvmedia-recommend-public",
    ),
    path(
        "api/tvmedia/recommend/private/",
        API_views.PrivateRecommendTvMedia.as_view(),
        name="tvmedia-recommend-private",
    ),
    path("api/tvmedia/rate/", RateTvMedia.as_view(), name="tvmedia-rate"),
]
