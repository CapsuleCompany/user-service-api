from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from common.models import BaseModel
from .assets.choices import *


class AuthUser(AbstractUser):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique ID for the user.",
    )
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True, unique=True)
    profile_picture = models.URLField(
        blank=True, null=True, help_text="Profile picture URL."
    )
    last_login = models.DateTimeField(
        blank=True, null=True, help_text="Last login timestamp."
    )
    timezone = models.CharField(
        max_length=50,
        default="UTC",
        choices=TIMEZONE_CHOICES,
        # validators=[lambda value: validate_choice(value, TIMEZONE_CHOICES)],
        help_text="User's timezone.",
    )
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["phone_number"]

    @property
    def is_verified(self):
        return self.is_email_verified and self.is_phone_verified

    # def clean(self):
    #     """Ensure validation of user before saving."""
    #     validate_choice(self.country, COUNTRY_CHOICES)
    #     validate_choice(self.account_status, ACCOUNT_STATUS_CHOICES)
    #     validate_choice(self.role, ROLE_CHOICES)
    #     validate_choice(self.language, LANGUAGE_CHOICES)
    #     validate_choice(self.timezone, TIMEZONE_CHOICES)

    def __str__(self):
        return self.email

    class Meta:
        db_table = "Users"


class UserSettings(BaseModel):
    user = models.ForeignKey(
        AuthUser,
        on_delete=models.CASCADE,
        related_name="settings",
        null=False,
        help_text="The user these settings belong to.",
    )

    # General Settings
    is_dark = models.BooleanField(
        default=False, help_text="Enable or disable dark mode for the user."
    )
    language = models.CharField(
        max_length=10,
        default="en",
        choices=LANGUAGE_CHOICES,
        # validators=[lambda value: validate_choice(value, LANGUAGE_CHOICES)],
        help_text="Preferred language of the user (e.g., 'en', 'es').",
    )

    # Notification Settings
    email_notifications = models.BooleanField(
        default=True, help_text="Enable or disable email notifications."
    )
    sms_notifications = models.BooleanField(
        default=False, help_text="Enable or disable SMS notifications."
    )
    push_notifications = models.BooleanField(
        default=True, help_text="Enable or disable push notifications."
    )

    # Payment Settings
    payment_preference = models.CharField(
        max_length=50,
        choices=PAYMENT_PREFERENCE_CHOICES,
        default="platform",
        # validators=[lambda value: validate_choice(value, PAYMENT_PREFERENCE_CHOICES)],
        help_text="Preferred payout method ('platform' or 'stripe').",
    )
    default_payment_method = models.CharField(
        max_length=50,
        blank=True,
        help_text="User's default payment method (e.g., 'credit_card', 'paypal').",
    )
    payment_reminders = models.BooleanField(
        default=True, help_text="Enable or disable payment reminders."
    )

    # Privacy Settings
    is_profile_public = models.BooleanField(
        default=False, help_text="Indicates if the user's profile is public."
    )
    allow_marketing_emails = models.BooleanField(
        default=False, help_text="Allow or disallow marketing emails."
    )

    # Stripe Payout Information (optional if using platform payout)
    stripe_account_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="The Stripe account ID associated with the user for payouts.",
    )
    bank_account_number = models.CharField(
        max_length=255,
        blank=True,
        help_text="The user's bank account number for Stripe payouts.",
    )
    bank_routing_number = models.CharField(
        max_length=255, blank=True, help_text="The routing number of the user's bank."
    )
    bank_account_holder_name = models.CharField(
        max_length=255, blank=True, help_text="Name of the bank account holder."
    )
    bank_account_holder_type = models.CharField(
        max_length=50,
        choices=PAYMENT_ACCOUNT_TYPE_CHOICES,
        blank=True,
        # validators=[lambda value: validate_choice(value, PAYMENT_ACCOUNT_TYPE_CHOICES)],
        help_text="Type of account holder (individual or company).",
    )
    payout_frequency = models.CharField(
        max_length=50,
        choices=PAYOUT_FREQUENCY_CHOICES,
        # validators=[lambda value: validate_choice(value, PAYOUT_FREQUENCY_CHOICES)],
        default="weekly",
        help_text="Preferred payout frequency.",
    )
    currency = models.CharField(max_length=50, null=False, default="USD")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # def clean(self):
    #     """Ensure validation of settings before saving."""
    #     validate_choice(self.language, LANGUAGE_CHOICES)
    #     validate_choice(self.payment_preference, PAYMENT_PREFERENCE_CHOICES)
    #     validate_choice(self.payout_frequency, PAYOUT_FREQUENCY_CHOICES)
    #     validate_choice(self.bank_account_holder_type, PAYMENT_ACCOUNT_TYPE_CHOICES)

    class Meta:
        db_table = "Settings"

    def __str__(self):
        return f"Settings for {self.user.email}"


class UserOrganization(BaseModel):
    """
    Links users to multiple organizations (tenants).
    """

    user = models.ForeignKey(
        "AuthUser", on_delete=models.CASCADE, related_name="organizations"
    )
    tenant_id = models.UUIDField(help_text="Tenant ID from the Tenant Service")
    role = models.UUIDField(help_text="User's role within this tenant.", null=True)

    class Meta:
        db_table = "UserOrganizations"
        unique_together = ("user", "tenant_id")

    def __str__(self):
        return f"{self.user.email} - {self.tenant_id}"


class UserAddress(BaseModel):
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE, related_name="address")
    address = models.UUIDField()
    is_primary = models.BooleanField(default=False)
    country = models.CharField(
        max_length=2,
        blank=True,
        choices=COUNTRY_CHOICES,
        # validators=[lambda value: validate_choice(value, COUNTRY_CHOICES)],
        default="US",
    )


class IpAddress(BaseModel):
    ip_address = models.GenericIPAddressField()
    is_proxy = models.BooleanField(null=True, blank=True)
    is_vpn = models.BooleanField(null=True, blank=True)


class UserLocation(BaseModel):
    user = models.ForeignKey(
        AuthUser, on_delete=models.CASCADE, related_name="locations"
    )
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    ip_address = models.ForeignKey(IpAddress, on_delete=models.CASCADE, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    timezone = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = "UserLocations"
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["ip_address"]),
        ]

    def __str__(self):
        return f"{self.user.email} from IP {self.ip_address} at {self.created_at}"


class UserSession(BaseModel):
    session_id = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE)
    refresh_token = models.TextField()
    expires_at = models.DateTimeField()
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.ForeignKey(IpAddress, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"Session {self.session_id} for {self.user.username}"

