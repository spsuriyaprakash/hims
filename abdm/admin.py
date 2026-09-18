from django.contrib import admin
from abdm.models import *

@admin.register(AbdmConfig)
class AbdmConfigAdmin(admin.ModelAdmin):
    list_display = ("client_id", "facility_id", "x_cm_id", "is_active", "created_at")
    list_filter = ("is_active", "x_cm_id")


@admin.register(GatewaySession)
class GatewaySessionAdmin(admin.ModelAdmin):
    list_display = ("id", "expires_at", "created_at")


@admin.register(AbdmPatient)
class AbdmPatientAdmin(admin.ModelAdmin):
    list_display = ("mrn", "full_name", "gender", "year_of_birth", "abha_number", "abha_address", "kyc_verified")
    search_fields = ("mrn", "full_name", "abha_number", "abha_address", "mobile")


@admin.register(AbhaTransaction)
class AbhaTransactionAdmin(admin.ModelAdmin):
    list_display = ("txn_id", "flow", "status", "expires_at", "created_at")
    search_fields = ("txn_id", "status")


@admin.register(AbhaToken)
class AbhaTokenAdmin(admin.ModelAdmin):
    list_display = ("patient", "expires_at", "created_at")


@admin.register(HipApiLog)
class HipApiLogAdmin(admin.ModelAdmin):
    list_display = ("request_id", "method", "api_path", "status_code", "created_at")
    search_fields = ("request_id", "api_path")
