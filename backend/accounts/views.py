from django.contrib.auth import authenticate
from rest_framework.decorators import api_view

from backoffice.audit import log_operation
from hota_mds.responses import error_response, success_response
from .services import TOKEN_MAX_AGE_SECONDS, issue_admin_token, serialize_user, validate_admin_token


def _authenticate_admin_token(request):
    user = validate_admin_token(request.headers.get("Authorization", ""))
    if user is None:
        return None, error_response("UNAUTHORIZED", "invalid or missing admin token", 401)

    return user, None


@api_view(["POST"])
def admin_login(request):
    username = str(request.data.get("username", "")).strip()
    password = str(request.data.get("password", ""))

    if not username or not password:
        return error_response("INVALID_INPUT", "username and password are required", 400)

    user = authenticate(request, username=username, password=password)
    if user is None:
        return error_response("INVALID_CREDENTIALS", "invalid username or password", 401)

    if not user.is_active or not user.is_staff:
        return error_response("FORBIDDEN", "admin permission required", 403)

    token = issue_admin_token(user)
    log_operation(
        actor=user,
        action="LOGIN",
        target_type="admin_auth",
        target_id=user.pk,
        target_label=user.get_username(),
        request=request,
        change_summary={},
    )
    return success_response(
        "login successful",
        {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": TOKEN_MAX_AGE_SECONDS,
            "user": serialize_user(user),
        },
    )


@api_view(["POST"])
def admin_logout(request):
    user, error = _authenticate_admin_token(request)
    if error is not None:
        return error

    log_operation(
        actor=user,
        action="LOGOUT",
        target_type="admin_auth",
        target_id=user.pk,
        target_label=user.get_username(),
        request=request,
        change_summary={},
    )
    return success_response("logout successful", None)


@api_view(["GET"])
def admin_me(request):
    user, error = _authenticate_admin_token(request)
    if error is not None:
        return error

    return success_response("current admin loaded", {"user": serialize_user(user)})
