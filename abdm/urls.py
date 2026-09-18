from django.urls import path
from abdm.views import *

app_name = "abdm"

urlpatterns = [
    # path("config/", AbdmConfigView.as_view(), name="config"),
    path("m1/public-cert/", PublicCertView.as_view(), name="m1-public-cert"),

    # Unified OTP Request for all 3 methods
    path("m1/send-otp/", UnifiedOtpRequestView.as_view(), name="m1-unified-send-otp"),

    # 1. Verify / Enrol by Aadhaar Number
    path("m1/enrol/aadhaar/send-otp/", AadhaarOtpRequestView.as_view(), name="m1-aadhaar-send-otp"),
    path("m1/enrol/aadhaar/verify-otp/", AadhaarOtpVerifyView.as_view(), name="m1-aadhaar-verify-otp"),
    path("m1/enrol/create-abha-address/", CreateAbhaAddressView.as_view(), name="m1-create-abha-address"),

    # 2. Verify by ABHA Number
    path("m1/verify/abha-number/send-otp/", VerifyAbhaSendOtpView.as_view(), name="m1-verify-abha-send-otp"),

    # 3. Verify by Mobile Number
    path("m1/verify/mobile/send-otp/", VerifyMobileSendOtpView.as_view(), name="m1-verify-mobile-send-otp"),

    # Common Confirm OTP for Verification
    path("m1/verify/confirm-otp/", VerifyAbhaConfirmOtpView.as_view(), name="m1-verify-confirm-otp"),

    # Patients & Audit Logs
    path("m1/patients/", PatientListView.as_view(), name="m1-patients"),
    path("m1/logs/", HipApiLogListView.as_view(), name="m1-logs"),
]


