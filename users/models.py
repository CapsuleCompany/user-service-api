from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
import uuid


class AuthUser(AbstractUser):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique ID for the user."
    )
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("service_provider", "Service Provider"),
        ("client", "Client"),
    ]
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="client",
        help_text="The role of the user."
    )
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True, unique=True)
    address = models.TextField(blank=True, null=True)
    country = models.CharField(max_length=2, blank=True, default="US")
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    profile_picture = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Profile picture of the user."
    )
    bio = models.TextField(
        blank=True,
        null=True,
        help_text="A brief biography or description about the user."
    )
    date_of_birth = models.DateField(blank=True, null=True, help_text="User's date of birth.")
    is_active = models.BooleanField(default=True, help_text="Indicates if the user is active.")
    is_staff = models.BooleanField(default=False, help_text="Indicates if the user is staff.")
    is_superuser = models.BooleanField(default=False, help_text="Indicates if the user is a superuser.")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["phone_number", "first_name", "last_name"]

    @property
    def is_verified(self):
        return self.is_email_verified and self.is_phone_verified

    def __str__(self):
        return self.email


class UserSettings(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique ID for the user."
    )
    PAYMENT_PREFERENCE_CHOICES = [
        ("platform", "Platform Payout"),
        ("stripe", "Stripe Payout"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="settings",
        help_text="The user associated with these settings."
    )

    # General Settings
    dark_mode = models.BooleanField(
        default=False,
        help_text="Enable or disable dark mode for the user."
    )
    language = models.CharField(
        max_length=10,
        default="en",
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
        choices=[
            ("individual", "Individual"),
            ("company", "Company"),
        ],
        blank=True,
        help_text="Type of account holder (individual or company)."
    )
    payout_frequency = models.CharField(
        max_length=50,
        choices=[
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
        ],
        default="weekly",
        help_text="Preferred payout frequency."
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings for {self.user.email}"
