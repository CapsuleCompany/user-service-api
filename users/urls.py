from django.urls import path, include
from rest_framework.routers import DefaultRouter

# from rest_framework_nested.routers import NestedDefaultRouter
from .views import *

router = DefaultRouter()
router.register(r"users/tenant", UserTenantView, basename="tenant")
router.register(r"users", UserViewSet, basename="service")


urlpatterns = [
    path("register/", UserCreationView.as_view(), name="create"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("logout/all", LogoutAllView.as_view(), name="logout_session"),
    path("token/refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("users/location/", UserIPLocationView.as_view(), name="user-location"),
    # path("users/tenant/<str:tenant_id>/", UserTenantView.as_view(), name="user-tenant-detail"),
    # path("profile/", UserProfileView.as_view(), name="profile"),
    # path("profile/settings/", UserSettingsView.as_view(), name="settings"),
    path("", include(router.urls)),
]
