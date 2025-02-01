from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
import uuid
from .assets.choices import (LANGUAGE_CHOICES, TIMEZONE_CHOICES, ACCOUNT_STATUS_CHOICES,
                             COUNTRY_CHOICES, ROLE_CHOICES, PAYOUT_FREQUENCY_CHOICES,
                             PAYMENT_ACCOUNT_TYPE_CHOICES, PAYMENT_PREFERENCE_CHOICES,
                             validate_choice)


class AuthUser(AbstractUser):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique ID for the user."
    )
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True, unique=True)
    address = models.TextField(blank=True, null=True)
    country = models.CharField(
        max_length=2,
        blank=True,
        choices=COUNTRY_CHOICES,
        validators=[lambda value: validate_choice(value, COUNTRY_CHOICES)],
        default="US"
    )
    profile_picture = models.URLField(blank=True, null=True, help_text="Profile picture URL.")
    organization_id = models.UUIDField(
        blank=True,
        null=True,
        help_text="Organization the user belongs to (if applicable)."
    )
    account_status = models.CharField(
        max_length=50,
        choices=ACCOUNT_STATUS_CHOICES,
        default="active",
        validators=[lambda value: validate_choice(value, ACCOUNT_STATUS_CHOICES)],
        help_text="The status of the user's account."
    )
    role = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES,
        default="client",
        validators=[lambda value: validate_choice(value, ROLE_CHOICES)],
        help_text="The user's role in the system."
    )
    last_login = models.DateTimeField(blank=True, null=True, help_text="Last login timestamp.")
    language = models.CharField(
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default="en",
        validators=[lambda value: validate_choice(value, LANGUAGE_CHOICES)],
        help_text="Preferred language of the user (e.g., 'en', 'es')."
    )
    timezone = models.CharField(
        max_length=50,
        default="UTC",
        choices=TIMEZONE_CHOICES,
        validators=[lambda value: validate_choice(value, TIMEZONE_CHOICES)],
        help_text="User's timezone."
    )
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["phone_number"]

    @property
    def is_verified(self):
        return self.is_email_verified and self.is_phone_verified

    def clean(self):
        """Ensure validation of user before saving."""
        validate_choice(self.country, COUNTRY_CHOICES)
        validate_choice(self.account_status, ACCOUNT_STATUS_CHOICES)
        validate_choice(self.role, ROLE_CHOICES)
        validate_choice(self.language, LANGUAGE_CHOICES)
        validate_choice(self.timezone, TIMEZONE_CHOICES)

    def __str__(self):
        return self.email


class UserSettings(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique ID for the user."
    )


    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="settings",
        help_text="The user associated with these settings."
    )

    # General Settings
    is_dark = models.BooleanField(
        default=False,
        help_text="Enable or disable dark mode for the user."
    )
    language = models.CharField(
        max_length=10,
        default="en",
        choices=LANGUAGE_CHOICES,
        validators=[lambda value: validate_choice(value, LANGUAGE_CHOICES)],
        help_text="Preferred language of the user (e.g., 'en', 'es')."
    )

    # Notification Settings
    email_notifications = models.BooleanField(
        default=True,
        help_text="Enable or disable email notifications."
    )
    sms_notifications = models.BooleanField(
        default=False,
        help_text="Enable or disable SMS notifications."
    )
    push_notifications = models.BooleanField(
        default=True,
        help_text="Enable or disable push notifications."
    )

    # Payment Settings
    payment_preference = models.CharField(
        max_length=50,
        choices=PAYMENT_PREFERENCE_CHOICES,
        default="platform",
        validators=[lambda value: validate_choice(value, PAYMENT_PREFERENCE_CHOICES)],
        help_text="Preferred payout method ('platform' or 'stripe')."
    )
    default_payment_method = models.CharField(
        max_length=50,
        blank=True,
        help_text="User's default payment method (e.g., 'credit_card', 'paypal')."
    )
    payment_reminders = models.BooleanField(
        default=True,
        help_text="Enable or disable payment reminders."
    )

    # Privacy Settings
    is_profile_public = models.BooleanField(
        default=False,
        help_text="Indicates if the user's profile is public."
    )
    allow_marketing_emails = models.BooleanField(
        default=False,
        help_text="Allow or disallow marketing emails."
    )

    # Stripe Payout Information (optional if using platform payout)
    stripe_account_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="The Stripe account ID associated with the user for payouts."
    )
    bank_account_number = models.CharField(
        max_length=255,
        blank=True,
        help_text="The user's bank account number for Stripe payouts."
    )
    bank_routing_number = models.CharField(
        max_length=255,
        blank=True,
        help_text="The routing number of the user's bank."
    )
    bank_account_holder_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Name of the bank account holder."
    )
    bank_account_holder_type = models.CharField(
        max_length=50,
        choices=PAYMENT_ACCOUNT_TYPE_CHOICES,
        blank=True,
        validators=[lambda value: validate_choice(value, PAYMENT_ACCOUNT_TYPE_CHOICES)],
        help_text="Type of account holder (individual or company)."
    )
    payout_frequency = models.CharField(
        max_length=50,
        choices=PAYOUT_FREQUENCY_CHOICES,
        validators=[lambda value: validate_choice(value, PAYOUT_FREQUENCY_CHOICES)],
        default="weekly",
        help_text="Preferred payout frequency."
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """Ensure validation of settings before saving."""
        validate_choice(self.language, LANGUAGE_CHOICES)
        validate_choice(self.payment_preference, PAYMENT_PREFERENCE_CHOICES)
        validate_choice(self.payout_frequency, PAYOUT_FREQUENCY_CHOICES)
        validate_choice(self.bank_account_holder_type, PAYMENT_ACCOUNT_TYPE_CHOICES)

    def __str__(self):
        return f"Settings for {self.user.email}"
