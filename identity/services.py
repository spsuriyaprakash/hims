from functools import lru_cache

import jwt
from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone
from jwt import PyJWKClient

from .models import (
    Application,
    LoginAudit,
    Role,
    RolePermission,
    User,
    UserApplication,
    UserIdentity,
    UserRoleSnapshot,
)


class TokenVerificationError(Exception):
    pass


@lru_cache(maxsize=1)
def _jwks_client():
    return PyJWKClient(settings.KEYCLOAK_JWKS_URL, cache_jwk_set=True, lifespan=3600)


def extract_roles(payload):
    roles = set(payload.get("realm_access", {}).get("roles", []))
    resource_access = payload.get("resource_access") or {}
    audience = settings.KEYCLOAK_AUDIENCE
    client_roles = resource_access.get(audience, {}).get("roles", [])
    roles.update(client_roles)
    ignored = {
        "default-roles-hims",
        "offline_access",
        "uma_authorization",
        "account",
    }
    return sorted(role for role in roles if role not in ignored)


def verify_access_token(token):
    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.KEYCLOAK_AUDIENCE,
            issuer=settings.KEYCLOAK_ISSUER,
            options={
                "require": ["exp", "iss"],
                "verify_aud": True,
            },
        )
    except jwt.PyJWTError as exc:
        raise TokenVerificationError(str(exc)) from exc

    if not payload.get("sub") and not payload.get("sid") and not payload.get("preferred_username"):
        raise TokenVerificationError("Token is missing user identifier")

    header = jwt.get_unverified_header(token)
    if header.get("alg") != "RS256":
        raise TokenVerificationError("Invalid token algorithm")
    return payload


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def record_login_audit(*, request, result, keycloak_sub=None, user_identity=None, application=None):
    LoginAudit.objects.create(
        keycloak_sub=keycloak_sub,
        user_identity=user_identity,
        application=application,
        result=result,
        ip_address=client_ip(request),
        user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:250],
    )


def permissions_for_roles(role_codes, application_code=None):
    application_code = application_code or settings.HIMS_API_APPLICATION_CODE
    return list(
        RolePermission.objects.filter(
            role__code__in=role_codes,
            role__is_active=True,
            permission__is_active=True,
            permission__application__code=application_code,
        )
        .values_list("permission__code", flat=True)
        .distinct()
    )


def get_or_create_user_from_payload(payload):
    sub = payload.get("sub") or payload.get("sid") or payload.get("preferred_username")
    username = payload.get("preferred_username") or payload.get("email") or sub
    email = payload.get("email") or ""
    full_name = payload.get("name") or ""
    first_name = payload.get("given_name") or ""
    last_name = payload.get("family_name") or ""
    if not full_name:
        full_name = " ".join(part for part in [first_name, last_name] if part).strip()

    identity = UserIdentity.objects.select_related("user").filter(keycloak_sub=sub).first()
    if identity:
        identity.username = username[:150]
        identity.email = email[:254]
        identity.full_name = full_name[:200]
        identity.last_login_at = timezone.now()
        identity.save(
            update_fields=["username", "email", "full_name", "last_login_at", "updated_at"]
        )
        user = identity.user
        user.email = email
        user.first_name = first_name[:150]
        user.last_name = last_name[:150]
        user.save(update_fields=["email", "first_name", "last_name"])
    else:
        local_username = username[:150]
        try:
            user = User.objects.create(
                username=local_username,
                email=email,
                first_name=first_name[:150],
                last_name=last_name[:150],
                is_active=True,
            )
        except IntegrityError:
            local_username = f"{username[:140]}-{sub[:8]}"
            user = User.objects.create(
                username=local_username,
                email=email,
                first_name=first_name[:150],
                last_name=last_name[:150],
                is_active=True,
            )
        user.set_unusable_password()
        user.save(update_fields=["password"])
        identity = UserIdentity.objects.create(
            user=user,
            keycloak_sub=sub,
            username=username[:150],
            email=email[:254],
            full_name=full_name[:200],
            last_login_at=timezone.now(),
        )

    application = Application.objects.filter(
        code=settings.HIMS_API_APPLICATION_CODE,
        is_active=True,
    ).first()
    if application:
        UserApplication.objects.get_or_create(
            user_identity=identity,
            application=application,
            defaults={"is_active": True},
        )
        web = Application.objects.filter(code="hims-web", is_active=True).first()
        if web:
            UserApplication.objects.get_or_create(
                user_identity=identity,
                application=web,
                defaults={"is_active": True},
            )

    _sync_role_snapshot(identity, extract_roles(payload))
    return identity


def _sync_role_snapshot(identity, role_codes):
    roles = list(Role.objects.filter(code__in=role_codes, is_active=True))
    role_ids = {role.id for role in roles}
    UserRoleSnapshot.objects.filter(user_identity=identity).exclude(role_id__in=role_ids).delete()
    for role in roles:
        UserRoleSnapshot.objects.update_or_create(
            user_identity=identity,
            role=role,
            defaults={},
        )
