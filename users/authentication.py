from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework.authentication import BaseAuthentication
from rest_framework_simplejwt.tokens import AccessToken
from users.models import UserSession
from rest_framework.response import Response

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


# Custom Cookie Authentication for extracting JWT from HTTP-only cookies & managing sessions
class CookieAuthentication(BaseAuthentication):
    def authenticate(self, request):
        access_token = request.COOKIES.get("cc_access")
        session_id = request.COOKIES.get("session_id")

        print(session_id, "---auth---")
        request.user_session = None

        if session_id:
            print("session_id", session_id)
            try:
                session = UserSession.objects.get(session_id=session_id)

                # Check if the session is expired
                if session.is_expired:
                    print("Session expired")
                    return self.logout_user(request)

                request.user_session = session

            except UserSession.DoesNotExist:
                print("Session ID does not exist")
                return self.logout_user(request)

        if not access_token:
            return None

        try:
            decoded_token = AccessToken(access_token)
            user_id = decoded_token.payload.get("user_id")

            if not user_id:
                return self.logout_user(request)

            user_instance = User.objects.filter(id=user_id).first()

            if not user_instance:
                return self.logout_user(request)

            return user_instance, access_token
        except Exception as e:
            print(f"Token authentication failed: {str(e)}")
            return self.logout_user(request)

    def logout_user(self, request):
        """
        Logs out the user by removing session cookies.
        """
        response = Response({"detail": "Session expired or invalid. Logged out."}, status=401)
        response.delete_cookie("cc_access")
        response.delete_cookie("session_id")
        request.user_session = None
        return None
