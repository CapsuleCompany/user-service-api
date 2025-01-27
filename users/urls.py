from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserProfileView,
    UserCreationView,
    CustomTokenObtainPairView,
    LogoutView,
)

urlpatterns = [
    path("token/", CustomTokenObtainPairView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("profile/", UserProfileView.as_view(), name="user_profile"),
    path("register/", UserCreationView.as_view(), name="user_create"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
