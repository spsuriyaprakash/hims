from django.conf import settings
from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    """
    Common abstract model providing audit fields for all ABDM models:
    created_at, modified_at, system_time, created_by, modified_by.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    system_time = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created",
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_modified",
    )

    class Meta:
        abstract = True


class AbdmConfig(BaseModel):
    """
    ABDM Environment Configuration (Sandbox / Production).
    Matches abdm.config table in abdm_postgres.sql
    """
    client_id = models.CharField(max_length=64, help_text="NHA software client ID (e.g. SBX_XXXX)")
    client_secret_enc = models.TextField(help_text="Encrypted client secret")
    bridge_url = models.CharField(max_length=512, default="https://dev.abdm.gov.in")
    callback_base_url = models.CharField(max_length=512, help_text="Public HTTPS endpoint for callbacks")
    facility_id = models.CharField(max_length=16, help_text="HFR facility ID (IN1000000000)")
    facility_name = models.CharField(max_length=128, default="Checspro Hospital")
    hip_name = models.CharField(max_length=15, default="Checspro")
    is_hip = models.BooleanField(default=True)
    is_hiu = models.BooleanField(default=False)
    x_cm_id = models.CharField(max_length=8, default="sbx", help_text="sbx for sandbox, abdm for prod")
    is_active = models.BooleanField(default=True)

    
    def __str__(self):
        return f"ABDM Config ({self.client_id}) - {'Active' if self.is_active else 'Inactive'}"


class GatewaySession(BaseModel):
    """
    Cached Gateway Session Access Token from POST /sessions.
    Matches abdm.gateway_session table in abdm_postgres.sql
    """
    access_token = models.TextField()
    refresh_token = models.TextField(null=True, blank=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return self.expires_at > timezone.now()

    def __str__(self):
        return f"GatewaySession (Expires: {self.expires_at})"


class AbdmPatient(BaseModel):
    """
    M1 Output: ABDM Patient Identity.
    Matches abdm.patient table in abdm_postgres.sql
    """
    GENDER_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Other"),
    ]

    mrn = models.CharField(max_length=64, unique=True, help_text="Hospital MRN / Patient Ref")
    checspro_ref = models.CharField(max_length=64, null=True, blank=True)
    full_name = models.CharField(max_length=128)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    year_of_birth = models.SmallIntegerField()
    mobile = models.CharField(max_length=15, null=True, blank=True)
    abha_number = models.CharField(max_length=19, null=True, blank=True, db_index=True)
    abha_address = models.CharField(max_length=128, unique=True, null=True, blank=True)
    kyc_verified = models.BooleanField(default=False)
    profile_json = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.full_name} ({self.abha_number or self.abha_address or self.mrn})"


class AbhaTransaction(BaseModel):
    """
    In-flight M1 OTP Transaction Chain.
    Matches abdm.abha_transaction table in abdm_postgres.sql
    """
    FLOW_CHOICES = [
        ("ENROL", "Enrollment"),
        ("LOGIN", "Login/Verification"),
        ("PROFILE", "Profile Fetch"),
        ("FORGOT", "Forgot ABHA"),
        ("USER_LINK", "User Link"),
    ]

    txn_id = models.CharField(max_length=64, unique=True)
    patient = models.ForeignKey(AbdmPatient, on_delete=models.SET_NULL, null=True, blank=True)
    flow = models.CharField(max_length=16, choices=FLOW_CHOICES)
    login_hint = models.CharField(max_length=32, null=True, blank=True)
    scope_json = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=32, default="OTP_SENT")
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Txn {self.txn_id} [{self.flow}] - {self.status}"


class AbhaToken(BaseModel):
    """
    User X-Token after M1 verification.
    Matches abdm.abha_token table in abdm_postgres.sql
    """
    patient = models.ForeignKey(AbdmPatient, on_delete=models.CASCADE, related_name="abha_tokens")
    x_token = models.TextField()
    refresh_token = models.TextField(null=True, blank=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"AbhaToken for {self.patient.full_name} (Expires: {self.expires_at})"


class HipApiLog(BaseModel):
    """
    ABDM M1 API Request & Response Audit Log.
    Matches hip_api_logs table in Claim repo / abdm_postgres.sql
    """
    request_id = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    api_path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    request_json = models.JSONField(default=dict, blank=True)
    response_json = models.JSONField(default=dict, blank=True)
    status_code = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"[{self.method}] {self.api_path} - Status: {self.status_code}"
