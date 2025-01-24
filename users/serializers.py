from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import AuthenticationFailed
from phonenumbers import parse, is_valid_number, NumberParseException
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
import re

User = get_user_model()


class CustomTokenObtainPairSerializer(serializers.Serializer):
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

        # Check if user exists and password is correct
        if user is None or not user.check_password(password):
            raise AuthenticationFailed("Invalid credentials")

        # Generate refresh and access tokens
        refresh = RefreshToken.for_user(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "email": user.email,
            "phone_number": user.phone_number,
            "username": user.username,
        }

    @staticmethod
    def is_valid_email(email):
        """Validate email format."""
        return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

    @staticmethod
    def is_valid_phone(phone_number):
        """Validate phone number format for supported regions."""
        # List of regions for English-speaking countries
        countries = [
            "US",
            "GB",
            "CA",
            "AU",
            "NZ",
            "IE",
            "ZA",
            "IN",
            "PH",
            "SG",
            "NG",
            "KE",
            "JM",
            "TT",
            "MT",
            "BB",
            "GH",
            "PK",
            "FJ",
            "BZ",
        ]

        for region in countries:
            try:
                parsed_number = parse(phone_number, region)
                if is_valid_number(parsed_number):
                    return True
            except NumberParseException:
                continue

        return False


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
            "password": {"write_only": True},
        }

    def create(self, validated_data):
        email_or_phone = validated_data.get("email") or validated_data.get("phone_number")
        username = (
            email_or_phone.split("@")[0] if "@" in email_or_phone else email_or_phone
        )

        try:
            # Check for duplicate email
            if validated_data.get("email") and User.objects.filter(email=validated_data.get("email")).exists():
                raise serializers.ValidationError({"email": "This email is already in use."})

            # Check for duplicate phone number
            if validated_data.get("phone_number") and User.objects.filter(phone_number=validated_data.get("phone_number")).exists():
                raise serializers.ValidationError({"phone_number": "This phone number is already in use."})

            # Create the user
            user = User.objects.create_user(
                username=username,
                email=validated_data.get("email"),
                phone_number=validated_data.get("phone_number"),
                password=validated_data.get("password"),
                first_name=validated_data.get("first_name"),
                last_name=validated_data.get("last_name"),
            )
            return user

        except serializers.ValidationError as e:
            # Raise validation errors for specific fields
            raise e
        except Exception as e:
            # Handle unexpected errors
            raise serializers.ValidationError({"error": f"An error occurred: {str(e)}"})


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
