from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter
# from rest_framework_nested.routers import NestedDefaultRouter
from .views import (
    UserProfileView,
    UserCreationView,
    LoginView,
    LogoutView,
    UserSettingsView,
    UserTenantView,
    UserViewSet,
)


router = DefaultRouter()
router.register(r"users", UserViewSet, basename="service")


urlpatterns = [
    path("", include(router.urls)),
    path("token/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="refresh"),
    # path("profile/", UserProfileView.as_view(), name="profile"),
    # path("profile/settings/", UserSettingsView.as_view(), name="settings"),
    path("register/", UserCreationView.as_view(), name="create"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("users/tenant/", UserTenantView.as_view(), name="tenant"),
    path("users/tenant/<str:tenant_id>/", UserTenantView.as_view(), name="user-tenant-detail"),
]
