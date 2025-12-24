from django.contrib.auth.views import LoginView
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import API_views

urlpatterns = [
    # Main ###
    path("login/", LoginView.as_view(template_name="users/login.html"), name="login"),
    # API
    path("api/register/", API_views.Register.as_view()),
    path("api/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/", include("rest_framework.urls")),
    path(
        "api/genre-preferences/",
        API_views.UserGenrePreferencesView.as_view(),
        name="user-genre-preferences",
    ),
]
