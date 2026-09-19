from .base import *  # noqa: F401,F403

DEBUG = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True

# ABDM Production Environment Settings
ABDM_ENV = env("ABDM_ENV", default="prod")
ABDM_GATEWAY_URL = env("ABDM_GATEWAY_URL", default="https://gateway.abdm.gov.in")
ABDM_X_CM_ID = env("ABDM_X_CM_ID", default="abdm")
ABDM_CLIENT_ID = env("ABDM_CLIENT_ID", default="")
ABDM_CLIENT_SECRET = env("ABDM_CLIENT_SECRET", default="")
ABDM_CALLBACK_BASE_URL = env("ABDM_CALLBACK_BASE_URL", default="")


