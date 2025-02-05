from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import serializers
from .utils import generate_token_payload
from .models import UserSettings, UserOrganization
import re

User = get_user_model()


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


class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        exclude = ["updated_at"]


class UserCreationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "phone_number", "password", "first_name", "last_name"]
        extra_kwargs = {
            "email": {"required": False},
            "phone_number": {"required": False},
            "password": {"write_only": True, "required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate(self, data):
        """
        Validate that at least one of `email` or `phone_number` is provided.
        """
        errors = {}

        # Ensure at least one of email or phone number is provided
        if not data.get("email") and not data.get("phone_number"):
            errors["email_or_phone"] = "Either email or phone number must be provided."

        # Validate phone number format
        phone_number = data.get("phone_number")
        if phone_number and not self.is_valid_phone(phone_number):
            errors["phone_number"] = "Invalid phone number format."

        # Check for duplicate phone number
        if phone_number and User.objects.filter(phone_number=phone_number).exists():
            errors["phone_number"] = "A user with this phone number already exists."

        # Check for duplicate email
        email = data.get("email")
        if email and User.objects.filter(email=email).exists():
            errors["email"] = "A user with this email already exists."

        if errors:
            raise serializers.ValidationError(errors)

        return data

    @staticmethod
    def is_valid_phone(phone_number):
        """Validate phone number format."""
        import re

        return re.match(r"^\+?1?\d{9,15}$", phone_number) is not None

    def create(self, validated_data):
        """
        Create a new user instance with the validated data.
        """
        return User.objects.create_user(
            username=validated_data.get("email"),
            email=validated_data.get("email"),
            phone_number=validated_data.get("phone_number"),
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )


class UserTenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserOrganization
        fields = '__all__'

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        return validated_data

    def update(self, instance, validated_data):
        instance.save()
        return instance

    def create(self, validated_data):
        user_org = UserOrganization.objects.create(**validated_data)
        return user_org


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = [
            "password",
            "is_staff",
            "username",
            "timezone",
            "groups",
            "user_permissions",
        ]
        read_only_fields = ["id"]

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        return validated_data

    def update(self, instance, validated_data):
        settings_data = validated_data.pop("settings", None)
        if settings_data:
            settings_instance = instance.settings
            for attr, value in settings_data.items():
                setattr(settings_instance, attr, value)
            settings_instance.save()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
