from rest_framework import authentication, exceptions

from .services import validate_admin_token


class AdminTokenAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        user = validate_admin_token(request.headers.get("Authorization", ""))
        if user is None:
            raise exceptions.AuthenticationFailed("invalid or missing admin token")

        return user, None
