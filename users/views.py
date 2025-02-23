from django.utils import timezone
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST
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
from .models import UserSettings, UserOrganization, UserLocation


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
                user = serializer.save()
                return Response(user, status=status.HTTP_201_CREATED)
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
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """Create a new user from Organization"""
        print(request.data)
        print('here')
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                return Response(serializer.data, status=HTTP_201_CREATED)
            except Exception as e:
                print(e)
                return Response(
                    {"error": f"User creation failed: {str(e)}"},
                    status=HTTP_400_BAD_REQUEST,
                )
        else:
            print('error')
            print(serializer.errors)
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


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
