from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class EmailOrPhoneBackend(BaseBackend):
    """
    Custom authentication backend that allows users to log in with either their email or phone number.
    """

    def authenticate(self, request, email_or_phone=None, password=None, **kwargs):
        try:
            # Check if the user exists with the given email or phone number
            user = User.objects.filter(
                Q(email=email_or_phone) | Q(phone_number=email_or_phone)
            ).first()

            # Verify the password
            if user and user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except (InvalidToken, TokenError, AuthenticationFailed):
            return None
