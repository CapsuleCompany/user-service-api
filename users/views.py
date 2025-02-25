from time import sleep

from django.utils import timezone
from rest_framework.status import *
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import generics, permissions, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .utils.location.client import get_client_ip, get_location_from_ip
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework import status
from .serializers import *
from .models import *
from django.conf import settings
import time
import uuid


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
            serializer = UserSettingsSerializer(
                settings, data=request.data, partial=True
            )

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
                serializer.save()
                response_data = {"message": "User created successfully"}
                response = Response(response_data, status=status.HTTP_201_CREATED)
                return response

            except Exception as e:
                return Response(
                    {"error": f"User creation failed: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class LogoutAllView(APIView):
    """Log out from all sessions"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        UserSession.objects.filter(user=request.user).delete()
        return Response({"message": "Logged out from all devices"}, status=200)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.COOKIES.get("refreshToken")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Attempt to blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()

            response = Response({"message": "Successfully logged out"}, status=status.HTTP_205_RESET_CONTENT)

            # Remove tokens from cookies
            response.delete_cookie("cc_access")
            response.delete_cookie("session_id")

            return response

        except AttributeError:
            return Response(
                {"error": "Token blacklisting is not enabled in your settings"},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )
        except Exception as e:
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

        refresh = validated_data["refresh"]
        session_id = uuid.uuid4()
        access_token = validated_data["access"]
        response_data = {"message": "Login successful"}

        ipaddress, _ = IpAddress.objects.get_or_create(
            ip_address=get_client_ip(request)
        )

        UserSession.objects.create(
            user=user,
            session_id=session_id,
            refresh_token=refresh,
            expires_at=timezone.now() + settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
            user_agent=request.headers.get("User-Agent"),
            ip_address=ipaddress,
        )

        # Return tokens in DEBUG mode
        if settings.DEBUG:
            response_data.update({"access": access_token, "refresh": refresh})
        response = Response(response_data, status=status.HTTP_200_OK)

        response.set_cookie(
            key="cc_access",
            value=access_token,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
        )
        response.set_cookie(
            key="session_id",
            value=str(session_id),
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
        )

        return response


class UserTenantView(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = UserTenantSerializer
    queryset = UserOrganization.objects.all()

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        tenants = self.get_queryset()
        serializer = self.get_serializer(tenants, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"user": request.user}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None, *args, **kwargs):
        try:
            tenant = self.get_queryset().get(tenant_id=pk)
        except UserOrganization.DoesNotExist:
            return Response(
                {"error": "User organization not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(tenant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, pk=None, *args, **kwargs):
        tenant_ids = [pk] if pk else request.data.get("tenant_ids")

        if not tenant_ids:
            return Response(
                {"error": "No tenant_id or tenant_ids provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if isinstance(tenant_ids, str):
            tenant_ids = [tenant_ids]

        deleted_count, _ = self.get_queryset().filter(tenant_id__in=tenant_ids).delete()

        if deleted_count == 0:
            return Response(
                {"error": "No matching tenants found for deletion"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {"message": f"Successfully removed {deleted_count} tenant(s)"},
            status=status.HTTP_200_OK,
        )


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return User.objects.all()

    @action(detail=False, methods=["get"], url_path="filter")
    def filter_users(self, request):
        """Filter Users based on query parameters"""
        username = request.query_params.get("username", None)
        email = request.query_params.get("email", None)
        is_active = request.query_params.get("is_active", None)

        filters = {}
        if username:
            filters["username__icontains"] = username
        if email:
            filters["email__icontains"] = email
        if is_active is not None:
            filters["is_active"] = is_active.lower() == "true"

        users = User.objects.filter(**filters)
        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        print(request.user.id)
        print(request.user)
        print(request.headers)
        # print(request.user.email)
        sleep(2)
        queryset = self.get_queryset().order_by("-date_joined")
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """Create a new user from Organization"""
        time.sleep(2)
        serializer = self.get_serializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=HTTP_201_CREATED)
            except Exception as e:
                return Response(
                    {"error": f"User creation failed: {str(e)}"},
                    status=HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None, *args, **kwargs):
        """Delete a user by ID."""
        sleep(3)
        try:
            user = self.get_queryset().get(pk=pk)
            user.delete()
            return Response(
                {"message": "User deleted successfully"}, status=HTTP_204_NO_CONTENT
            )
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to delete user: {str(e)}"},
                status=HTTP_400_BAD_REQUEST,
            )

class UserIPLocationView(APIView):
    permission_classes = [permissions.AllowAny]
    # permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = UserLocationSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({"message": "added"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
