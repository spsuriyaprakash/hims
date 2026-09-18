from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (
    ApiPermission,
    Application,
    Facility,
    LoginAudit,
    Role,
    RolePermission,
    User,
    UserApplication,
    UserFacility,
    UserIdentity,
    UserRoleSnapshot,
)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("username",)
    list_display = ("username", "email", "is_active", "is_staff")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "app_kind", "base_url", "is_active")
    search_fields = ("code", "keycloak_client_id")


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active")


@admin.register(UserIdentity)
class UserIdentityAdmin(admin.ModelAdmin):
    list_display = ("username", "keycloak_sub", "email", "is_active", "last_login_at")
    search_fields = ("username", "keycloak_sub", "email")


@admin.register(UserApplication)
class UserApplicationAdmin(admin.ModelAdmin):
    list_display = ("user_identity", "application", "is_active", "granted_at")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "source", "application", "is_active")


@admin.register(ApiPermission)
class ApiPermissionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "application", "http_method", "resource")


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ("role", "permission")


@admin.register(UserRoleSnapshot)
class UserRoleSnapshotAdmin(admin.ModelAdmin):
    list_display = ("user_identity", "role", "synced_at")


@admin.register(UserFacility)
class UserFacilityAdmin(admin.ModelAdmin):
    list_display = ("user_identity", "facility", "is_primary", "is_active")


@admin.register(LoginAudit)
class LoginAuditAdmin(admin.ModelAdmin):
    list_display = ("occurred_at", "keycloak_sub", "result", "application")
    readonly_fields = (
        "occurred_at",
        "keycloak_sub",
        "user_identity",
        "application",
        "result",
        "ip_address",
        "user_agent",
    )
