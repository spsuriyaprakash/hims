from django.urls import path
from abdm.views import *

app_name = "abdm"

urlpatterns = [
    # path("config/", AbdmConfigView.as_view(), name="config"),
    path("m1/public-cert/", PublicCertView.as_view(), name="m1-public-cert"),
    path("m1/enrol/aadhaar/send-otp/", AadhaarOtpRequestView.as_view(), name="m1-aadhaar-send-otp"),
    path("m1/enrol/aadhaar/verify-otp/", AadhaarOtpVerifyView.as_view(), name="m1-aadhaar-verify-otp"),
    path("m1/enrol/create-abha-address/", CreateAbhaAddressView.as_view(), name="m1-create-abha-address"),
    path("m1/verify/send-otp/", VerifyAbhaSendOtpView.as_view(), name="m1-verify-send-otp"),
    path("m1/verify/confirm-otp/", VerifyAbhaConfirmOtpView.as_view(), name="m1-verify-confirm-otp"),
    path("m1/patients/", PatientListView.as_view(), name="m1-patients"),
    path("m1/logs/", HipApiLogListView.as_view(), name="m1-logs"),
]

