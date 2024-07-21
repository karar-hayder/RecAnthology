from django.urls import path,include
from .views import Register
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
urlpatterns = [
    path("register/",Register.as_view()),
    path("login",TokenObtainPairView.as_view(),name='token_obtain_pair'),
    path("token/refresh/",TokenRefreshView.as_view(),name='token_refresh'),
    path('api-auth/',include('rest_framework.urls'))


]


