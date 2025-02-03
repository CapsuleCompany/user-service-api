from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserProfileView,
    UserCreationView,
    LoginView,
    LogoutView,
    RetrieveUserView,
    UserSettingsView,
    UserTenantView,
)

urlpatterns = [
    path("token/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("profile/settings/", UserSettingsView.as_view(), name="settings"),
    path("register/", UserCreationView.as_view(), name="create"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("users/retrieve/", RetrieveUserView.as_view(), name="retrieve"),
    path("users/tenant/", UserTenantView.as_view(), name="tenant"),
    path("users/tenant/<str:tenant_id>/", UserTenantView.as_view(), name="user-tenant-detail"),
]
