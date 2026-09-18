from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db import connection
from django.core.cache import cache

from .permissions import HasApiPermission, HasApplicationAccess
from .services import extract_roles, permissions_for_roles


class HealthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        db_ok = True
        redis_ok = True
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            db_ok = False
        try:
            cache.set("healthcheck", "ok", 10)
            redis_ok = (cache.get("healthcheck") == "ok")
        except Exception:
            redis_ok = False
        status_code = 200 if db_ok and redis_ok else 503
        return Response({"database": db_ok, "redis": redis_ok}, status=status_code)


class MeView(APIView):
    permission_classes = [IsAuthenticated, HasApplicationAccess]
    required_permission = None

    def get(self, request):
        identity = request.user_identity
        payload = getattr(request, "keycloak_payload", {}) or {}
        roles = extract_roles(payload)
        facilities = [
            {
                "code": link.facility.code,
                "name": link.facility.name,
                "is_primary": link.is_primary,
            }
            for link in identity.facilities.filter(is_active=True).select_related("facility")
        ]
        applications = [
            {
                "code": link.application.code,
                "name": link.application.name,
                "app_kind": link.application.app_kind,
                "base_url": link.application.base_url,
            }
            for link in identity.applications.filter(is_active=True).select_related("application")
        ]
        return Response(
            {
                "id": str(identity.id),
                "user_id": str(identity.user_id),
                "keycloak_sub": identity.keycloak_sub,
                "username": identity.username,
                "email": identity.email,
                "full_name": identity.full_name,
                "is_active": identity.is_active,
                "token_roles": roles,
                "permissions": permissions_for_roles(roles),
                "applications": applications,
                "facilities": facilities,
            }
        )


class PermissionProbeView(APIView):
    """Example protected endpoint: doctors can create encounters, receptionists cannot."""

    permission_classes = [IsAuthenticated, HasApplicationAccess, HasApiPermission]
    required_permission = "encounter.create"

    def get(self, request):
        return Response({"allowed": True, "permission": self.required_permission})
