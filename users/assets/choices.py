from django.core.exceptions import ValidationError


def validate_choice(value, choices):
    """Ensure the value exists in the defined choices."""
    valid_values = {choice[0] for choice in choices}
    if value not in valid_values:
        raise ValidationError(
            f"Invalid choice: {value}. Allowed values: {valid_values}"
        )


# Payment Frequency Choices
PAYOUT_FREQUENCY_CHOICES = [
    ("daily", "Daily"),
    ("weekly", "Weekly"),
    ("monthly", "Monthly"),
]

# Payment Preference Choices
PAYMENT_PREFERENCE_CHOICES = [
    ("platform", "Platform Payout"),
    ("stripe", "Stripe Payout"),
]

# Payment Account Type Choices
PAYMENT_ACCOUNT_TYPE_CHOICES = [
    ("individual", "Individual"),
    ("company", "Company"),
]

# Role Choices
ROLE_CHOICES = [
    ("client", "Client"),
    ("admin", "Admin"),
    ("provider", "Provider"),
]

# Language Choices
LANGUAGE_CHOICES = [
    ("en", "English"),
    ("es", "Spanish"),
    ("fr", "French"),
    ("de", "German"),
    ("it", "Italian"),
    ("nl", "Dutch"),
    ("pt", "Portuguese"),
    ("zh", "Chinese"),
    ("ja", "Japanese"),
    ("ko", "Korean"),
    ("hi", "Hindi"),
    ("ar", "Arabic"),
]

# Country Choices
COUNTRY_CHOICES = [
    ("US", "United States"),
    ("CA", "Canada"),
    ("GB", "United Kingdom"),
    ("AU", "Australia"),
    ("NZ", "New Zealand"),
    ("DE", "Germany"),
    ("FR", "France"),
    ("ES", "Spain"),
    ("IT", "Italy"),
    ("NL", "Netherlands"),
    ("BR", "Brazil"),
    ("MX", "Mexico"),
    ("IN", "India"),
    ("CN", "China"),
    ("JP", "Japan"),
    ("KR", "South Korea"),
    ("SG", "Singapore"),
    ("ZA", "South Africa"),
    ("AE", "United Arab Emirates"),
    ("SA", "Saudi Arabia"),
]

# Timezone Choices
TIMEZONE_CHOICES = [
    ("UTC", "UTC"),
    ("US/Pacific", "Pacific Time (US & Canada)"),
    ("US/Mountain", "Mountain Time (US & Canada)"),
    ("US/Central", "Central Time (US & Canada)"),
    ("US/Eastern", "Eastern Time (US & Canada)"),
    ("Europe/London", "London"),
    ("Europe/Berlin", "Berlin"),
    ("Europe/Paris", "Paris"),
    ("Asia/Tokyo", "Tokyo"),
    ("Asia/Shanghai", "Shanghai"),
    ("Asia/Seoul", "Seoul"),
    ("Asia/Dubai", "Dubai"),
    ("Australia/Sydney", "Sydney"),
    ("Africa/Johannesburg", "Johannesburg"),
    ("America/Sao_Paulo", "São Paulo"),
    ("America/Mexico_City", "Mexico City"),
    ("Asia/Kolkata", "Kolkata"),
    ("Asia/Jakarta", "Jakarta"),
]
