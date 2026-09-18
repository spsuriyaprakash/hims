from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from .models import LoginAudit
from .services import (
    TokenVerificationError,
    get_or_create_user_from_payload,
    record_login_audit,
    verify_access_token,
)


class KeycloakJWTAuthentication(BaseAuthentication):
    www_authenticate_realm = "hims-api"

    def authenticate(self, request):
        header = get_authorization_header(request).decode("utf-8")
        if not header:
            return None
        parts = header.split()
        if parts[0].lower() != "bearer":
            return None
        if len(parts) != 2:
            raise AuthenticationFailed("Invalid Authorization header")

        token = parts[1]
        try:
            payload = verify_access_token(token)
        except TokenVerificationError as exc:
            record_login_audit(
                request=request,
                result=LoginAudit.Result.INVALID_TOKEN,
                keycloak_sub=None,
            )
            raise AuthenticationFailed(str(exc)) from exc

        identity = get_or_create_user_from_payload(payload)
        if not identity.is_active or not identity.user.is_active:
            record_login_audit(
                request=request,
                result=LoginAudit.Result.INACTIVE_USER,
                keycloak_sub=payload.get("sub"),
                user_identity=identity,
            )
            raise AuthenticationFailed("User is inactive")

        request.keycloak_payload = payload
        request.user_identity = identity
        record_login_audit(
            request=request,
            result=LoginAudit.Result.SUCCESS,
            keycloak_sub=payload.get("sub"),
            user_identity=identity,
        )
        return identity.user, token

    def authenticate_header(self, request):
        return f'Bearer realm="{self.www_authenticate_realm}"'
