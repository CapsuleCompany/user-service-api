from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True, unique=True)
    address = models.TextField(blank=True, null=True)
    country = models.CharField(max_length=2, blank=True, default="US")
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["phone_number"]


class UserSettings(models.Model):
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
