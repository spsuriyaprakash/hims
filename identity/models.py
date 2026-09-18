import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        db_table = "auth_user"


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Facility(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    timezone = models.CharField(max_length=64, default="Asia/Kolkata")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "facility"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} {self.name}"


class Application(TimestampedModel):
    class Kind(models.TextChoices):
        WEB = "web", "Web"
        API = "api", "API"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    keycloak_client_id = models.CharField(max_length=100, unique=True)
    app_kind = models.CharField(max_length=10, choices=Kind.choices)
    base_url = models.CharField(max_length=500)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "application"
        ordering = ["code"]

    def __str__(self):
        return self.code


class UserIdentity(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="identity",
    )
    keycloak_sub = models.CharField(max_length=64, unique=True)
    username = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    full_name = models.CharField(max_length=200, blank=True)
    employee_code = models.CharField(max_length=50, unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True, default="")
    is_active = models.BooleanField(default=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "user_identity"

    def __str__(self):
        return self.username


class UserApplication(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_identity = models.ForeignKey(
        UserIdentity,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="user_links",
    )
    is_active = models.BooleanField(default=True)
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_application"
        constraints = [
            models.UniqueConstraint(
                fields=["user_identity", "application"],
                name="uq_user_application",
            )
        ]


class Role(TimestampedModel):
    class Source(models.TextChoices):
        REALM = "realm", "Realm"
        CLIENT = "client", "Client"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="client_roles",
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=150)
    source = models.CharField(max_length=20, choices=Source.choices)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "role"
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(source="realm", application__isnull=True)
                    | models.Q(source="client", application__isnull=False)
                ),
                name="ck_role_source_app",
            ),
            models.UniqueConstraint(
                fields=["code"],
                condition=models.Q(application__isnull=True),
                name="uq_role_realm_code",
            ),
            models.UniqueConstraint(
                fields=["application", "code"],
                condition=models.Q(application__isnull=False),
                name="uq_role_client_code",
            ),
        ]

    def __str__(self):
        return self.code


class ApiPermission(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="permissions",
    )
    code = models.CharField(max_length=100)
    name = models.CharField(max_length=150)
    http_method = models.CharField(max_length=10, blank=True, default="")
    resource = models.CharField(max_length=50, blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "permission"
        constraints = [
            models.UniqueConstraint(
                fields=["application", "code"],
                name="uq_permission_app_code",
            )
        ]

    def __str__(self):
        return self.code


class RolePermission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(
        ApiPermission,
        on_delete=models.CASCADE,
        related_name="role_permissions",
    )

    class Meta:
        db_table = "role_permission"
        constraints = [
            models.UniqueConstraint(
                fields=["role", "permission"],
                name="uq_role_permission",
            )
        ]


class UserRoleSnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_identity = models.ForeignKey(
        UserIdentity,
        on_delete=models.CASCADE,
        related_name="role_snapshots",
    )
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_snapshots")
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_role_snapshot"
        constraints = [
            models.UniqueConstraint(
                fields=["user_identity", "role"],
                name="uq_user_role_snapshot",
            )
        ]


class UserFacility(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_identity = models.ForeignKey(
        UserIdentity,
        on_delete=models.CASCADE,
        related_name="facilities",
    )
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name="staff")
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_facility"
        constraints = [
            models.UniqueConstraint(
                fields=["user_identity", "facility"],
                name="uq_user_facility",
            ),
            models.UniqueConstraint(
                fields=["user_identity"],
                condition=models.Q(is_primary=True, is_active=True),
                name="uq_user_facility_one_primary",
            ),
        ]


class LoginAudit(models.Model):
    class Result(models.TextChoices):
        SUCCESS = "success", "Success"
        INVALID_TOKEN = "invalid_token", "Invalid token"
        INACTIVE_USER = "inactive_user", "Inactive user"
        FORBIDDEN_APP = "forbidden_app", "Forbidden application"
        FORBIDDEN_ROLE = "forbidden_role", "Forbidden role"

    id = models.BigAutoField(primary_key=True)
    occurred_at = models.DateTimeField(auto_now_add=True)
    keycloak_sub = models.CharField(max_length=64, blank=True, null=True)
    user_identity = models.ForeignKey(
        UserIdentity,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="login_audits",
    )
    application = models.ForeignKey(
        Application,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="login_audits",
    )
    result = models.CharField(max_length=20, choices=Result.choices)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=250, blank=True, default="")

    class Meta:
        db_table = "login_audit"
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["-occurred_at"], name="idx_login_audit_occurred"),
            models.Index(fields=["keycloak_sub"], name="idx_login_audit_sub"),
        ]
