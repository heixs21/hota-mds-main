import os

from django.contrib.auth import get_user_model
from django.core import signing


TOKEN_SALT = "admin-auth-token"
TOKEN_MAX_AGE_SECONDS = int(os.getenv("ADMIN_AUTH_TOKEN_MAX_AGE_SECONDS", "43200"))


def serialize_user(user):
    return {
        "id": user.pk,
        "username": user.get_username(),
        "displayName": user.get_full_name() or user.get_username(),
        "isStaff": user.is_staff,
    }


def issue_admin_token(user):
    return signing.dumps({"user_id": user.pk}, salt=TOKEN_SALT)


def extract_bearer_token(authorization_header):
    prefix = "Bearer "
    if not authorization_header.startswith(prefix):
        return None

    token = authorization_header[len(prefix):].strip()
    return token or None


def validate_admin_token(authorization_header):
    token = extract_bearer_token(authorization_header)
    if token is None:
        return None

    try:
        payload = signing.loads(token, salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE_SECONDS)
    except (signing.SignatureExpired, signing.BadSignature):
        return None

    return get_user_model().objects.filter(
        pk=payload.get("user_id"),
        is_active=True,
        is_staff=True,
    ).first()
