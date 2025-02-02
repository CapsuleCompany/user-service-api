from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserProfileView,
    UserCreationView,
    LoginView,
    LogoutView,
    RetrieveUserView,
    UserSettingsView
)

urlpatterns = [
    path("token/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("profile/settings/", UserSettingsView.as_view(), name="settings"),
    path("register/", UserCreationView.as_view(), name="create"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("users/retrieve/", RetrieveUserView.as_view(), name="retrieve"),
]
