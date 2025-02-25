from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework.authentication import BaseAuthentication
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

# Custom authentication backend for email or phone authentication
class EmailOrPhoneBackend(BaseBackend):
    """
    Custom authentication backend that allows users to log in with either their email or phone number.
    """

    def authenticate(self, request, email_or_phone=None, password=None, **kwargs):
        user = User.objects.filter(
            Q(email=email_or_phone) | Q(phone_number=email_or_phone)
        ).first()

        # Verify the password
        if user and user.check_password(password):
            return user

        return None

    def get_user(self, user_id):
        return User.objects.filter(pk=user_id).first()


# Custom JWT Authentication to handle token errors properly
class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except (InvalidToken, TokenError, AuthenticationFailed):
            return None


# Custom Cookie Authentication for extracting JWT from HTTP-only cookies
class CookieAuthentication(BaseAuthentication):
    def authenticate(self, request):
        access_token = request.COOKIES.get("cc_access")

        if not access_token:
            return None

        try:
            decoded_token = AccessToken(access_token)
            user_id = decoded_token.payload.get("user_id")

            if not user_id:
                return None

            user_instance = User.objects.filter(id=user_id).first()

            if not user_instance:
                return None

            return user_instance, access_token
        except Exception as e:
            print(f"Token authentication failed: {str(e)}")
            return None