from django.conf import settings
from rest_framework.permissions import BasePermission

from .models import LoginAudit, UserApplication
from .services import extract_roles, permissions_for_roles, record_login_audit


class HasApiPermission(BasePermission):
    """Allow if the Keycloak token roles map to the view's required_permission."""

    def has_permission(self, request, view):
        required = getattr(view, "required_permission", None)
        if not required:
            return True
        if not request.user or not request.user.is_authenticated:
            return False

        identity = getattr(request, "user_identity", None)
        payload = getattr(request, "keycloak_payload", {}) or {}
        roles = extract_roles(payload)
        allowed = permissions_for_roles(roles)
        if required in allowed:
            return True

        record_login_audit(
            request=request,
            result=LoginAudit.Result.FORBIDDEN_ROLE,
            keycloak_sub=payload.get("sub"),
            user_identity=identity,
        )
        return False


class HasApplicationAccess(BasePermission):
    def has_permission(self, request, view):
        identity = getattr(request, "user_identity", None)
        if identity is None:
            return False
        allowed = UserApplication.objects.filter(
            user_identity=identity,
            application__code=settings.HIMS_API_APPLICATION_CODE,
            application__is_active=True,
            is_active=True,
        ).exists()
        if allowed:
            return True
        payload = getattr(request, "keycloak_payload", {}) or {}
        record_login_audit(
            request=request,
            result=LoginAudit.Result.FORBIDDEN_APP,
            keycloak_sub=payload.get("sub"),
            user_identity=identity,
        )
        return False
