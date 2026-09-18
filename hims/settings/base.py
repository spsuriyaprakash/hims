from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(  
    DJANGO_DEBUG=(bool, True),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1", "*"]),
)

environ.Env.read_env(BASE_DIR / ".env", overwrite=False)

SECRET_KEY = env("DJANGO_SECRET_KEY", default="django-insecure-hims-default-local-secret-key-change-in-prod")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "identity.apps.IdentityConfig",
    "abdm.apps.AbdmConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "hims.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "hims.wsgi.application"
ASGI_APPLICATION = "hims.asgi.application"

DATABASES = {
    "default": env.db("DATABASE_URL"),
}

AUTH_USER_MODEL = "identity.User"

REDIS_URL = env("REDIS_URL", default="redis://127.0.0.1:6379/0")
CACHE_OPTIONS = {"CLIENT_CLASS": "django_redis.client.DefaultClient"}
if REDIS_URL.startswith("rediss://"):
    CACHE_OPTIONS["CONNECTION_POOL_KWARGS"] = {"ssl_cert_reqs": None}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": CACHE_OPTIONS,
        "KEY_PREFIX": "hims",
        "TIMEOUT": 300,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:3000", "http://127.0.0.1:3000"],
)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "identity.authentication.KeycloakJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

KEYCLOAK_ISSUER = env("KEYCLOAK_ISSUER", default="http://localhost:8080/realms/hims")
KEYCLOAK_AUDIENCE = env("KEYCLOAK_AUDIENCE", default="hims-api")
KEYCLOAK_JWKS_URL = env(
    "KEYCLOAK_JWKS_URL",
    default=f"{KEYCLOAK_ISSUER}/protocol/openid-connect/certs",
)
HIMS_API_APPLICATION_CODE = "hims-api"

# ABDM Configurations
ABDM_ENV = env("ABDM_ENV", default="sandbox")
ABDM_GATEWAY_URL = env("ABDM_GATEWAY_URL", default="https://dev.abdm.gov.in")
ABDM_X_CM_ID = env("ABDM_X_CM_ID", default="sbx")
ABDM_CLIENT_ID = env("ABDM_CLIENT_ID", default="SBX_TEST_CLIENT")
ABDM_CLIENT_SECRET = env("ABDM_CLIENT_SECRET", default="SBX_SECRET_MOCK")

