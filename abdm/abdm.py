import json
import uuid
import urllib.request
import urllib.error
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from abdm.models import AbdmConfig, HipApiLog
from abdm.const import (
    ABDM_GATEWAY_SESSIONS_URL,
    ABDM_PUBLIC_CERT_URL,
    ABDM_DEFAULT_CALLBACK_BASE_URL,
)


class AbdmGateway:
    BASE_URL = getattr(settings, "ABDM_GATEWAY_URL", "https://dev.abdm.gov.in")
    X_CM_ID = getattr(settings, "ABDM_X_CM_ID", "sbx")
    SESSION_CACHE_KEY = "abdm_gateway_token"
    SESSION_CACHE_TIMEOUT = 18 * 60  # 18 minutes in seconds (1080 seconds)
    PUBLIC_CERT_CACHE_KEY = "abdm_public_cert"
    PUBLIC_CERT_CACHE_TIMEOUT = 60 * 60 * 24 * 90  # 90 days (7776000 seconds)

    @classmethod
    def get_config(cls):
        try:
            config = AbdmConfig.objects.filter(is_active=True).first()
            if config:
                return config
        except Exception as e:
            print(f"AbdmConfig query failed, using settings default: {e}")

        class DefaultConfig:
            client_id = getattr(settings, "ABDM_CLIENT_ID", "SBX_TEST_CLIENT")
            client_secret_enc = getattr(settings, "ABDM_CLIENT_SECRET", "SBX_SECRET_MOCK")
            bridge_url = cls.BASE_URL
            callback_base_url = getattr(
                settings,
                "ABDM_CALLBACK_BASE_URL",
                ABDM_DEFAULT_CALLBACK_BASE_URL,
            )
            facility_id = "IN1000000000"
            facility_name = "Checspro Hospital"
            hip_name = "Checspro"
            x_cm_id = cls.X_CM_ID
            is_active = True

        return DefaultConfig()

    @classmethod
    def log_api_call(cls, api_path, method, request_json, response_json, status_code, request_id=None, error_message=None):
        try:
            HipApiLog.objects.create(
                request_id=request_id or str(uuid.uuid4()),
                api_path=api_path,
                method=method,
                request_json=request_json or {},
                response_json=response_json or {},
                status_code=status_code,
                error_message=error_message,
            )
        except Exception as e:
            print(f"Failed to log ABDM API call: {e}")

    @classmethod
    def _http_request(cls, url, method="POST", data=None, headers=None):
        req_headers = headers or {}
        body_bytes = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=body_bytes, headers=req_headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                res_body = resp.read().decode("utf-8")
                return resp.status, json.loads(res_body) if res_body else {}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            try:
                err_json = json.loads(err_body)
            except Exception:
                err_json = {"error": err_body}
            return e.code, err_json
        except Exception as e:
            return 500, {"error": str(e)}

    @classmethod
    def get_gateway_token(cls):
        """
        Fetch or reuse cached ABDM Gateway session Bearer token from POST /sessions.
        Cached in Redis for 18 minutes (1080 seconds). Does NOT store in DB.
        """
        token = cache.get(cls.SESSION_CACHE_KEY)
        if token:
            return token

        config = cls.get_config()
        url = f"{cls.BASE_URL}{ABDM_GATEWAY_SESSIONS_URL}"
        payload = {
            "clientId": config.client_id,
            "clientSecret": config.client_secret_enc,
            "grantType": "client_credentials",
        }
        headers = {
            "Content-Type": "application/json",
            "REQUEST-ID": str(uuid.uuid4()),
            "TIMESTAMP": timezone.now().isoformat(),
            "X-CM-ID": config.x_cm_id,
        }

        status_code, res_data = cls._http_request(url, method="POST", data=payload, headers=headers)
        cls.log_api_call(url, "POST", payload, res_data, status_code)

        if status_code == 200 and "accessToken" in res_data:
            token = res_data["accessToken"]
            cache.set(cls.SESSION_CACHE_KEY, token, timeout=cls.SESSION_CACHE_TIMEOUT)
            return token

        # Mock fallback for offline sandbox testing
        mock_token = f"mock_bearer_token_{uuid.uuid4().hex[:16]}"
        cache.set(cls.SESSION_CACHE_KEY, mock_token, timeout=cls.SESSION_CACHE_TIMEOUT)
        return mock_token

    @classmethod
    def get_public_cert(cls):
        """
        GET /abha/api/v3/profile/public/certificate
        Cached in Redis for 3 months (90 days = 7,776,000 seconds).
        """
        cached_cert = cache.get(cls.PUBLIC_CERT_CACHE_KEY)
        if cached_cert:
            return cached_cert

        token = cls.get_gateway_token()
        url = f"{cls.BASE_URL}{ABDM_PUBLIC_CERT_URL}"
        headers = {
            "Authorization": f"Bearer {token}",
            "REQUEST-ID": str(uuid.uuid4()),
            "TIMESTAMP": timezone.now().isoformat(),
            "X-CM-ID": cls.X_CM_ID,
        }
        status_code, res_data = cls._http_request(url, method="GET", headers=headers)
        cls.log_api_call(url, "GET", {}, res_data, status_code)
        if status_code == 200:
            cert = res_data.get("certificate") or res_data.get("publicKey") or str(res_data)
            cache.set(cls.PUBLIC_CERT_CACHE_KEY, cert, timeout=cls.PUBLIC_CERT_CACHE_TIMEOUT)
            return cert
        return "MOCK_PUBLIC_RSA_CERTIFICATE_KEY"


# Module-level aliases for backwards compatibility
get_gateway_token = AbdmGateway.get_gateway_token
get_public_cert = AbdmGateway.get_public_cert
get_config = AbdmGateway.get_config
log_api_call = AbdmGateway.log_api_call
_http_request = AbdmGateway._http_request
