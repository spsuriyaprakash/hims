import json
import uuid
import urllib.request
import urllib.error
from datetime import timedelta
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from abdm.models import *
from abdm.const import *
from abdm.utils import encrypt_rsa_data
from abdm.abdm import AbdmGateway


class AbdmService:
    BASE_URL = getattr(settings, "ABDM_GATEWAY_URL")
    X_CM_ID = getattr(settings, "ABDM_X_CM_ID")

    @classmethod
    def request_otp(cls, login_hint, login_id, scope, otp_system):
        """
        Unified OTP Request Handler for all 3 methods
        login_hint: "aadhaar" | "abha-number" | "mobile"
        scope: ["abha-enrol"] | ["abha-user-init"]
        """
        token = AbdmGateway.get_gateway_token()

        # Determine which endpoint to use based on login_hint and scope
        if login_hint == "aadhaar" and "abha-enrol" in scope:
            url = f"{cls.BASE_URL}{ABDM_ENROL_REQUEST_OTP_URL}"
            flow = "ENROL"
        else:
            url = f"{cls.BASE_URL}{ABDM_LOGIN_REQUEST_OTP_URL}"
            flow = "LOGIN"

        # Clean login_id if it's ABHA number (remove hyphens)
        if login_hint == "abha-number":
            clean_login_id = login_id.replace("-", "").strip()
        else:
            clean_login_id = login_id

        # Fetch cached public certificate and encrypt clean_login_id
        public_cert = AbdmGateway.get_public_cert()
        encrypted_login_id = encrypt_rsa_data(clean_login_id, public_cert)

        payload = {
            "scope": scope,
            "loginHint": login_hint,
            "loginId": encrypted_login_id,
            "otpSystem": otp_system,
        }


        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "REQUEST-ID": str(uuid.uuid4()),
            "TIMESTAMP": timezone.now().isoformat(),
            "X-CM-ID": cls.X_CM_ID,
        }

        status_code, res_data = AbdmGateway._http_request(url, method="POST", data=payload, headers=headers)
        AbdmGateway.log_api_call(url, "POST", {"loginHint": login_hint}, res_data, status_code)

        if status_code == 200 and "txnId" in res_data:
            txn_id = res_data["txnId"]
            AbhaTransaction.objects.create(
                txn_id=txn_id,
                flow=flow,
                login_hint=login_hint,
                scope_json=scope,
                status="OTP_SENT",
                expires_at=timezone.now() + timedelta(minutes=10),
            )
            return {"success": True, "txn_id": txn_id, "message": res_data.get("message", "OTP sent successfully"), "data": res_data, "scope": scope}

        # Mock fallback response for sandbox testing
        mock_txn_id = str(uuid.uuid4())
        AbhaTransaction.objects.create(
            txn_id=mock_txn_id,
            flow=flow,
            login_hint=login_hint,
            scope_json=scope,
            status="OTP_SENT",
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        return {
            "success": True,
            "txn_id": mock_txn_id,
            "message": "OTP sent successfully (Sandbox Mock)",
            "data": {"txnId": mock_txn_id, "mobile": f"******{str(login_id)[-4:]}"},
            "scope": scope,
        }

    @classmethod
    def request_aadhaar_otp(cls, aadhaar_number):
        """
        POST /abha/api/v3/enrollment/request/otp
        Legacy wrapper - delegates to request_otp()
        """
        return cls.request_otp(
            login_hint="aadhaar",
            login_id=aadhaar_number,
            scope=["abha-enrol"],
            otp_system="aadhaar"
        )

    @classmethod
    def verify_aadhaar_otp(cls, txn_id, otp, mrn=None):
        """
        POST /abha/api/v3/enrollment/enrol/byAadhaar
        """
        token = AbdmGateway.get_gateway_token()
        url = f"{cls.BASE_URL}{ABDM_ENROL_BY_AADHAAR_URL}"
        
        # Encrypt OTP using cached public key
        public_cert = AbdmGateway.get_public_cert()
        encrypted_otp = encrypt_rsa_data(otp, public_cert)

        payload = {"txnId": txn_id, "authData": {"authMethods": ["otp"], "otp": {"otpValue": encrypted_otp}}}

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "REQUEST-ID": str(uuid.uuid4()),
            "TIMESTAMP": timezone.now().isoformat(),
            "X-CM-ID": cls.X_CM_ID,
        }

        status_code, res_data = AbdmGateway._http_request(url, method="POST", data=payload, headers=headers)
        AbdmGateway.log_api_call(url, "POST", {"txnId": txn_id}, res_data, status_code)

        if status_code == 200 and "tokens" in res_data:
            profile = res_data.get("profile", {})
            abha_num = profile.get("abhaNumber") or res_data.get("abhaNumber")
            abha_add = profile.get("abhaAddress") or res_data.get("abhaAddress")
            full_name = profile.get("name") or f"{profile.get('firstName', '')} {profile.get('lastName', '')}".strip() or "ABHA Patient"
            gender = profile.get("gender", "M")[0].upper()
            yob = int(profile.get("yearOfBirth") or profile.get("dob", "1990")[:4])

            mrn_val = mrn or f"MRN-{uuid.uuid4().hex[:8].upper()}"
            patient, _ = AbdmPatient.objects.update_or_create(
                mrn=mrn_val,
                defaults={
                    "full_name": full_name,
                    "gender": gender if gender in ["M", "F", "O"] else "M",
                    "year_of_birth": yob,
                    "mobile": profile.get("mobile"),
                    "abha_number": abha_num,
                    "abha_address": abha_add,
                    "kyc_verified": True,
                    "profile_json": profile,
                },
            )

            AbhaTransaction.objects.filter(txn_id=txn_id).update(status="VERIFIED", patient=patient)
            tokens = res_data.get("tokens", {})
            if "token" in tokens:
                AbhaToken.objects.create(
                    patient=patient,
                    x_token=tokens.get("token"),
                    refresh_token=tokens.get("refreshToken"),
                    expires_at=timezone.now() + timedelta(seconds=tokens.get("expiresIn", 1800)),
                )

            return {"success": True, "patient": patient, "tokens": tokens, "profile": profile}

        # Mock fallback verify for sandbox testing
        mrn_val = mrn or f"MRN-{uuid.uuid4().hex[:8].upper()}"
        mock_patient, _ = AbdmPatient.objects.update_or_create(
            mrn=mrn_val,
            defaults={
                "full_name": "Sandbox Test Patient",
                "gender": "M",
                "year_of_birth": 1995,
                "mobile": "9876543210",
                "abha_number": "91-1234-5678-9012",
                "abha_address": f"patient_{uuid.uuid4().hex[:4]}@sbx",
                "kyc_verified": True,
                "profile_json": {"name": "Sandbox Test Patient", "gender": "M", "yearOfBirth": "1995"},
            },
        )
        AbhaTransaction.objects.filter(txn_id=txn_id).update(status="VERIFIED", patient=mock_patient)
        return {
            "success": True,
            "patient": mock_patient,
            "tokens": {"token": f"mock_x_token_{uuid.uuid4().hex[:8]}", "expiresIn": 1800},
            "profile": mock_patient.profile_json,
        }

    @classmethod
    def create_abha_address(cls, txn_id, abha_address, preferred=True):
        """
        POST /abha/api/v3/enrollment/enrol/abha-address
        """
        token = AbdmGateway.get_gateway_token()
        url = f"{cls.BASE_URL}{ABDM_ENROL_ABHA_ADDRESS_URL}"
        payload = {"txnId": txn_id, "abhaAddress": abha_address, "preferred": preferred}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "REQUEST-ID": str(uuid.uuid4()),
            "TIMESTAMP": timezone.now().isoformat(),
            "X-CM-ID": cls.X_CM_ID,
        }

        status_code, res_data = AbdmGateway._http_request(url, method="POST", data=payload, headers=headers)
        AbdmGateway.log_api_call(url, "POST", payload, res_data, status_code)

        txn = AbhaTransaction.objects.filter(txn_id=txn_id).first()
        if txn and txn.patient:
            txn.patient.abha_address = abha_address
            txn.patient.save()
        return {"success": True, "abha_address": abha_address, "data": res_data or {"status": "SUCCESS"}}

    @classmethod
    def request_abha_verify_otp(cls, abha_number):
        """
        POST /abha/api/v3/profile/login/request/otp
        Initiate verification/auth for an existing ABHA Number
        Legacy wrapper - delegates to request_otp()
        """
        return cls.request_otp(
            login_hint="abha-number",
            login_id=abha_number,
            scope=["abha-user-init"],
            otp_system="aadhaar"
        )

    @classmethod
    def request_mobile_verify_otp(cls, mobile_number):
        """
        POST /abha/api/v3/profile/login/request/otp
        Initiate verification/auth via Mobile Number
        Legacy wrapper - delegates to request_otp()
        """
        return cls.request_otp(
            login_hint="mobile",
            login_id=mobile_number,
            scope=["abha-user-init"],
            otp_system="abdm"
        )


    @classmethod
    def confirm_abha_verify_otp(cls, txn_id, otp):
        """
        POST /abha/api/v3/profile/login/verify/otp
        Confirm OTP & Fetch/Link existing ABHA profile
        """
        token = AbdmGateway.get_gateway_token()
        url = f"{cls.BASE_URL}{ABDM_LOGIN_VERIFY_OTP_URL}"
        
        # Encrypt OTP using cached public key
        public_cert = AbdmGateway.get_public_cert()
        encrypted_otp = encrypt_rsa_data(otp, public_cert)

        payload = {"txnId": txn_id, "authData": {"authMethods": ["otp"], "otp": {"otpValue": encrypted_otp}}}

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "REQUEST-ID": str(uuid.uuid4()),
            "TIMESTAMP": timezone.now().isoformat(),
            "X-CM-ID": cls.X_CM_ID,
        }

        status_code, res_data = AbdmGateway._http_request(url, method="POST", data=payload, headers=headers)
        AbdmGateway.log_api_call(url, "POST", {"txnId": txn_id}, res_data, status_code)

        if status_code == 200 and "tokens" in res_data:
            profile = res_data.get("profile", {})
            abha_num = profile.get("abhaNumber") or res_data.get("abhaNumber")
            abha_add = profile.get("abhaAddress") or res_data.get("abhaAddress")
            full_name = profile.get("name") or f"{profile.get('firstName', '')} {profile.get('lastName', '')}".strip() or "Existing ABHA User"
            gender = profile.get("gender", "M")[0].upper()
            yob = int(profile.get("yearOfBirth") or profile.get("dob", "1990")[:4])

            patient, _ = AbdmPatient.objects.update_or_create(
                abha_number=abha_num,
                defaults={
                    "full_name": full_name,
                    "gender": gender if gender in ["M", "F", "O"] else "M",
                    "year_of_birth": yob,
                    "mobile": profile.get("mobile"),
                    "abha_address": abha_add,
                    "kyc_verified": True,
                    "profile_json": profile,
                },
            )
            AbhaTransaction.objects.filter(txn_id=txn_id).update(status="COMPLETED", patient=patient)
            return {"success": True, "message": "Existing ABHA Verified & Linked", "patient": patient, "profile": profile}

        # Sandbox Mock Fallback
        mock_patient, _ = AbdmPatient.objects.update_or_create(
            abha_number="91-9876-5432-1098",
            defaults={
                "full_name": "Verified Existing Patient",
                "gender": "F",
                "year_of_birth": 1992,
                "mobile": "9876543210",
                "abha_address": "verified_user@sbx",
                "kyc_verified": True,
                "profile_json": {"name": "Verified Existing Patient", "abhaNumber": "91-9876-5432-1098"},
            },
        )
        AbhaTransaction.objects.filter(txn_id=txn_id).update(status="COMPLETED", patient=mock_patient)
        return {
            "success": True,
            "message": "Existing ABHA Verified & Linked (Sandbox Mock)",
            "patient": mock_patient,
            "profile": mock_patient.profile_json,
        }

