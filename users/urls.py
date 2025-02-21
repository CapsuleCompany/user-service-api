from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter
# from rest_framework_nested.routers import NestedDefaultRouter
from .views import *

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="service")


router = DefaultRouter()
router.register(r"users", UserViewSet, basename="service")

urlpatterns = [
    path("token/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("register/", UserCreationView.as_view(), name="create"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("users/location/", UserIPLocationView.as_view(), name="user-location"),  # custom path first
    path("users/tenant/", UserTenantView.as_view(), name="tenant"),
    path("users/tenant/<str:tenant_id>/", UserTenantView.as_view(), name="user-tenant-detail"),
    # path("profile/", UserProfileView.as_view(), name="profile"),
    # path("profile/settings/", UserSettingsView.as_view(), name="settings"),
    path("", include(router.urls)),
]