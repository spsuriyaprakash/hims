from .base import *  # noqa: F401,F403

DEBUG = True

# ABDM Sandbox Environment Settings (Local)
ABDM_ENV = env("ABDM_ENV", default="sandbox")
ABDM_GATEWAY_URL = env("ABDM_GATEWAY_URL", default="https://dev.abdm.gov.in")
ABDM_X_CM_ID = env("ABDM_X_CM_ID", default="sbx")
ABDM_CLIENT_ID = env("ABDM_CLIENT_ID", default="SBX_TEST_CLIENT")
ABDM_CLIENT_SECRET = env("ABDM_CLIENT_SECRET", default="SBX_SECRET_MOCK")

