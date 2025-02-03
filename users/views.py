from django.utils import timezone
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .utils import generate_token_payload
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db.models import Q
from rest_framework import status
from .serializers import (
    UserSerializer,
    UserSettingsSerializer,
    GetTokenPairSerializer,
    UserCreationSerializer,
    UserTenantSerializer,
)
from .models import UserSettings, UserOrganization


User = get_user_model()


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        """Fully update user profile (all fields required)."""
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        print('-here-')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            settings = UserSettings.objects.get(user=request.user)
            serializer = UserSettingsSerializer(settings)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserSettings.DoesNotExist:
            return Response(
                {"error": "User settings not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    def put(self, request):
        """Allow both partial and full updates."""
        try:
            settings = UserSettings.objects.get(user=request.user)
            serializer = UserSettingsSerializer(settings, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except UserSettings.DoesNotExist:
            return Response(
                {"error": "User settings not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class UserCreationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserCreationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                # Generate refresh and access tokens
                refresh = generate_token_payload(user)

                return Response(
                    {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    },
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                return Response(
                    {"error": f"User creation failed: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        return Response(
            {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Extract the refresh token from the request body
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Attempt to blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"message": "Successfully logged out"},
                status=status.HTTP_205_RESET_CONTENT,
            )
        except AttributeError:
            # Raised if blacklisting is not enabled or supported
            return Response(
                {"error": "Token blacklisting is not enabled in your settings"},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )
        except Exception as e:
            # Handle invalid tokens or unexpected errors
            return Response(
                {"error": f"Invalid token - {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LoginView(TokenObtainPairView):
    serializer_class = GetTokenPairSerializer

    def post(self, request, *args, **kwargs):
        """
        Handle the login process and generate JWT tokens with custom claims.
        """
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        user = validated_data["user"]
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        response_data = {
            "refresh": validated_data["refresh"],
            "access": validated_data["access"],
        }

        return Response(response_data, status=status.HTTP_200_OK)


class RetrieveUserView(APIView):
    """
    Retrieve a user by email, UUID, or phone number.
    This endpoint is only available in DEBUG mode.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        if not settings.DEBUG:
            return Response(
                {"error": "This endpoint is only available in DEBUG mode."},
                status=status.HTTP_403_FORBIDDEN,
            )

        email = request.data.get("email")
        uuid = request.data.get("uuid")
        phone = request.data.get("phone")

        if not any([email, uuid, phone]):
            return Response(
                {"error": "You must provide an email, uuid, or phone number."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        filters = Q()
        if email:
            filters |= Q(email=email)
        if uuid:
            filters |= Q(id=uuid)
        if phone:
            filters |= Q(phone=phone)

        user = User.objects.filter(filters).first()
        if not user:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserTenantView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """
        Retrieves the tenant information associated with the authenticated user.
        """
        tenants = UserOrganization.objects.filter(user=request.user)
        serializer = UserTenantSerializer(tenants, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        """
        Allows updating user tenant information.
        """
        try:
            tenant = UserOrganization.objects.get(user=request.user, tenant_id=request.data.get("tenant_id"))
            serializer = UserTenantSerializer(tenant, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except UserOrganization.DoesNotExist:
            return Response(
                {"error": "User organization not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    def post(self, request):
        """
        Adds a user to a tenant.
        """
        serializer = UserTenantSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(request.data)
        return Response(
            {"error": "User creation failed", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, tenant_id=None):
        """
        Removes the user from one or more tenants.
        Expects a `tenant_id` in the URL or a `tenant_id` / list of `tenant_ids` in the request data.
        """
        tenant_ids = [tenant_id] if tenant_id else request.data.get("tenant_id") or request.data.get("tenant_ids")

        if not tenant_ids:
            return Response(
                {"error": "No tenant_id or tenant_ids provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if isinstance(tenant_ids, str):
            tenant_ids = [tenant_ids]

        deleted_count, _ = UserOrganization.objects.filter(tenant_id__in=tenant_ids).delete()

        if deleted_count == 0:
            return Response(
                {"error": "No matching tenants found for deletion"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {"message": f"Successfully removed {deleted_count} tenant(s)"},
            status=status.HTTP_200_OK,
        )