from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import CustomTokenObtainPairSerializer
from .views import UserProfileView, UserCreationView, LogoutView, CustomTokenObtainPairView

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(serializer_class=CustomTokenObtainPairSerializer), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('create/', UserCreationView.as_view(), name='user_create'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
