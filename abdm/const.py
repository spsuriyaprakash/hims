"""
ABDM API Endpoint Constants
"""

# Gateway Sessions
ABDM_GATEWAY_SESSIONS_URL = "/api/hiecm/gateway/v3/sessions"

# Profile & Cert
ABDM_PUBLIC_CERT_URL = "/abha/api/v3/profile/public/certificate"

# Enrolment (ABHA Creation)
ABDM_ENROL_REQUEST_OTP_URL = "/abha/api/v3/enrollment/request/otp"
ABDM_ENROL_BY_AADHAAR_URL = "/abha/api/v3/enrollment/enrol/byAadhaar"
ABDM_ENROL_ABHA_ADDRESS_URL = "/abha/api/v3/enrollment/enrol/abha-address"

# Verification & Auth (Existing ABHA)
ABDM_LOGIN_REQUEST_OTP_URL = "/abha/api/v3/profile/login/request/otp"
ABDM_LOGIN_VERIFY_OTP_URL = "/abha/api/v3/profile/login/verify/otp"
