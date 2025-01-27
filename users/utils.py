from rest_framework_simplejwt.tokens import RefreshToken

def generate_token_payload(user):
    refresh = RefreshToken.for_user(user)
    refresh["role"] = user.role
    refresh["is_dark"] = user.settings.is_dark if hasattr(user, 'settings') else False
    refresh["email"] = user.email
    refresh["full_name"] = f"{user.first_name} {user.last_name}"
    refresh["organization_id"] = str(user.organization_id) if user.organization_id else None
    refresh["account_status"] = user.account_status
    refresh["profile_picture"] = user.profile_picture
    refresh["language"] = user.language
    refresh["timezone"] = user.timezone
    refresh["is_verified"] = user.is_verified
    refresh["last_login"] = user.last_login.isoformat() if user.last_login else None
    return refresh