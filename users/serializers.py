from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import AuthenticationFailed
from phonenumbers import parse, is_valid_number, NumberParseException
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from users.utils import generate_token_payload
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
        user = None
        if self.is_valid_email(email_or_phone):
            user = User.objects.filter(email=email_or_phone).first()
        elif self.is_valid_phone(email_or_phone):
            user = User.objects.filter(phone_number=email_or_phone).first()
        else:
            raise AuthenticationFailed("Invalid email or phone number format.")

        # Check if user exists and password is correct
        if user is None or not user.check_password(password):
            raise AuthenticationFailed("Invalid credentials")

        # Generate refresh and access tokens
        refresh = generate_token_payload(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

    @staticmethod
    def is_valid_email(email):
        """Validate email format."""
        return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

    @staticmethod
    def is_valid_phone(phone_number):
        """Validate phone number format."""
        return re.match(r"^\+?1?\d{9,15}$", phone_number) is not None


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "phone_number", "address"]
        read_only_fields = ["id"]


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


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(label=_("Email or Phone"), required=True)
    password = serializers.CharField(
        label=_("Password"), style={"input_type": "password"}, trim_whitespace=False
    )

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        if username and password:
            user = authenticate(
                request=self.context.get("request"),
                username=username,
                password=password,
            )
            if not user:
                raise serializers.ValidationError(
                    _("Invalid credentials"), code="authorization"
                )
        else:
            raise serializers.ValidationError(
                _("Must include 'username' and 'password'"), code="authorization"
            )

        attrs["user"] = user
        return attrs
