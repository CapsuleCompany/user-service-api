"""
This module contains a utility function to generate a token payload for a user using Django REST Framework's SimpleJWT.

Functions:
    generate_token_payload(user): Generates a refresh token with custom payload attributes for the given user.

    - Parameters:
        user (User): A user object for which the token is generated. The user object is expected to have the following attributes:
            - role (str): The role of the user.
            - settings (optional): A related object containing user-specific settings, including the `is_dark` theme setting.
            - email (str): The email address of the user.
            - first_name (str): The user's first name.
            - last_name (str): The user's last name.
            - organization_id (UUID or None): The ID of the organization the user belongs to, if any.
            - account_status (str): The account status of the user.
            - profile_picture (str): A URL or path to the user's profile picture.
            - language (str): The preferred language of the user.
            - timezone (str): The timezone of the user.
            - is_verified (bool): Whether the user's email is verified.
            - last_login (datetime or None): The last login time of the user.

    - Returns:
        RefreshToken: A JWT refresh token object with a custom payload.

    - Payload attributes:
        - role (str): The user's role.
        - is_dark (bool): Indicates whether the user has enabled dark mode.
        - email (str): The user's email address.
        - full_name (str): The full name of the user (first and last names concatenated).
        - organization_id (str or None): The user's organization ID as a string, or None if not applicable.
        - account_status (str): The status of the user's account.
        - profile_picture (str): The user's profile picture URL or path.
        - language (str): The user's preferred language.
        - timezone (str): The user's timezone.
        - is_verified (bool): Indicates if the user's email is verified.
        - last_login (str or None): ISO 8601 formatted timestamp of the user's last login, or None if unavailable.

Example Usage:
    from rest_framework_simplejwt.tokens import RefreshToken
    from your_app.models import User

    user = User.objects.get(email="example@example.com")
    token = generate_token_payload(user)
    print(str(token))  # Outputs the generated JWT as a string.
"""
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import UserSettings


def get_user_settings(user):
    """
    Retrieve the appropriate UserSettings for the given user.
    If the user belongs to an organization, return the organization's settings.
    Otherwise, return the user's personal settings.
    """
    if user:
        settings = UserSettings.objects.filter(user=user).first()
    else:
        settings = UserSettings.objects.filter(user=user).first()

    return settings or UserSettings.objects.create(user=user)


def generate_token_payload(user):
    refresh = RefreshToken.for_user(user)
    settings = get_user_settings(user)
    organizations = user.organizations.all()

    refresh["is_dark"] = settings.is_dark if settings else False
    refresh["email"] = user.email
    refresh["first_name"] = user.first_name
    refresh["last_name"] = user.last_name
    refresh["profile_picture"] = user.profile_picture
    refresh["language"] = settings.language if settings else user.language
    refresh["timezone"] = user.timezone
    refresh["is_verified"] = user.is_verified
    refresh["last_login"] = user.last_login.isoformat() if user.last_login else None
    refresh["is_active"] = user.is_active
    refresh["is_superuser"] = user.is_superuser
    refresh["tenants"] = [str(tenant_id) for tenant_id in organizations.values_list("tenant_id", flat=True)]
    return refresh
