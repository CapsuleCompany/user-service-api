from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import serializers
from .utils.auth.token import generate_token_payload
from .models import *
import re

User = get_user_model()


class BaseUserSerializer(serializers.ModelSerializer):
    """Base serializer containing shared user validation logic."""

    class Meta:
        model = User
        fields = ["email", "phone_number", "first_name", "last_name"]
        extra_kwargs = {
            "email": {"required": False},
            "phone_number": {"required": False},
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate(self, data):
        """
        Validate that at least one of `email` or `phone_number` is provided.
        """
        errors = {}

        if not data.get("email") and not data.get("phone_number"):
            errors["email_or_phone"] = "Either email or phone number must be provided."

        if "phone_number" in data and not self.is_valid_phone(data["phone_number"]):
            errors["phone_number"] = "Invalid phone number format."

        if User.objects.filter(email=data.get("email")).exists():
            errors["email"] = "A user with this email already exists."

        if data.get("phone_number") and User.objects.filter(phone_number=data.get("phone_number")).exists():
            errors["phone_number"] = "A user with this phone number already exists."

        if errors:
            raise serializers.ValidationError(errors)

        return data

    @staticmethod
    def is_valid_phone(phone_number):
        """Validate phone number format."""
        import re
        return re.match(r"^\+?1?\d{9,15}$", phone_number) is not None


class GetTokenPairSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    refresh = serializers.CharField(read_only=True)
    access = serializers.CharField(read_only=True)

    def validate(self, attrs):
        email_or_phone = attrs.get("email_or_phone")
        password = attrs.get("password")

        if not email_or_phone or not password:
            raise AuthenticationFailed("Email/Phone number and password are required.")

        # Determine if input is email or phone number
        if self.is_valid_email(email_or_phone):
            user = User.objects.filter(email=email_or_phone).first()
        elif self.is_valid_phone(email_or_phone):
            user = User.objects.filter(phone_number=email_or_phone).first()
        else:
            raise AuthenticationFailed("Invalid email or phone number format.")

        if user is None or not user.check_password(password):
            raise AuthenticationFailed("Invalid credentials")

        refresh = generate_token_payload(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": user,
        }

    @staticmethod
    def is_valid_email(email):
        """Validate email format."""
        return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

    @staticmethod
    def is_valid_phone(phone_number):
        """Validate phone number format."""
        return re.match(r"^\+?1?\d{9,15}$", phone_number) is not None


class UserCreationSerializer(BaseUserSerializer):
    """Serializer for user self-registration (or logs in if user exists)."""

    password = serializers.CharField(write_only=True, required=True)

    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + ["password"]

    def create(self, validated_data):
        """
        If the user exists and the password is correct, log in and return tokens.
        Otherwise, create a new user and return tokens.
        """
        email = validated_data.get("email")
        phone_number = validated_data.get("phone_number")
        password = validated_data["password"]

        # Check if a user already exists
        user = User.objects.filter(email=email).first() or User.objects.filter(phone_number=phone_number).first()

        if user:
            # Authenticate user
            if not user.check_password(password):
                raise AuthenticationFailed("Email or Phone Number already in use")

            # Generate tokens for existing user
            refresh = generate_token_payload(user)
            return {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }

        # If user does not exist, create a new one
        user = User.objects.create_user(
            username=email,
            email=email,
            phone_number=phone_number,
            password=password,
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )

        # Generate JWT tokens for new user
        refresh = generate_token_payload(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }


class UserSerializer(BaseUserSerializer):
    """Serializer for admin users creating new users (no JWT tokens)."""

    password = serializers.CharField(write_only=True, required=False)

    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + ["password"]

    def create(self, validated_data):
        """
        Admin creates a user; password is optional.
        """
        password = validated_data.pop("password", None)
        user = User.objects.create_user(**validated_data)

        if password:
            user.set_password(password)
            user.save()

        return UserSerializer(user).data


class UserTenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserOrganization
        fields = "__all__"

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        return validated_data

    def update(self, instance, validated_data):
        instance.save()
        return instance

    def create(self, validated_data):
        user_org = UserOrganization.objects.create(**validated_data)
        return user_org


class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        exclude = ["updated_at"]


class UserLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLocation
        fields = [
            "ip_address",
            "latitude",
            "longitude",
            "city",
            "state",
            "country",
            "timezone",
            "is_proxy",
        ]

    def to_internal_value(self, data):
        if "ip" in data and "address" not in data:
            set_transformed_data = {"ip_address": data.get("ip")}
        else:
            if data.get("meta", {}).get("code") != 200:
                raise serializers.ValidationError("Invalid response code in metadata.")

            address = data.get("address", {})
            timezone_info = address.get("timeZone", {})

            set_transformed_data = {
                "ip_address": data.get("ip"),
                "latitude": address.get("latitude"),
                "longitude": address.get("longitude"),
                "city": address.get("city"),
                "state": address.get("state"),
                "country": address.get("country"),
                "timezone": timezone_info.get("id"),
                "is_proxy": data.get("proxy", False),
            }

        return super().to_internal_value(set_transformed_data)

    def create(self, validated_data):
        user = self.context["request"].user

        location, created = UserLocation.objects.get_or_create(
            user=user,
            ip_address=validated_data.get("ip_address"),
            is_proxy=validated_data.get("is_proxy"),
            defaults={
                "latitude": validated_data.get("latitude"),
                "longitude": validated_data.get("longitude"),
                "city": validated_data.get("city"),
                "state": validated_data.get("state"),
                "country": validated_data.get("country"),
                "timezone": validated_data.get("timezone"),
            },
        )
        return location
