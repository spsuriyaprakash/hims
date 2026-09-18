from rest_framework import serializers
from abdm.models import AbdmConfig, AbdmPatient, AbhaTransaction, HipApiLog


class AbdmConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AbdmConfig
        fields = [
            "id",
            "client_id",
            "bridge_url",
            "callback_base_url",
            "facility_id",
            "facility_name",
            "hip_name",
            "is_hip",
            "is_hiu",
            "x_cm_id",
            "is_active",
        ]


class AbdmPatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = AbdmPatient
        fields = [
            "id",
            "mrn",
            "checspro_ref",
            "full_name",
            "gender",
            "year_of_birth",
            "mobile",
            "abha_number",
            "abha_address",
            "kyc_verified",
            "profile_json",
            "created_at",
            "modified_at",
        ]


class AadhaarOtpRequestSerializer(serializers.Serializer):
    aadhaar_number = serializers.CharField(max_length=12, min_length=12, help_text="12-digit Aadhaar number")


class AadhaarOtpVerifySerializer(serializers.Serializer):
    txn_id = serializers.CharField(max_length=64)
    otp = serializers.CharField(max_length=6, min_length=6)
    mrn = serializers.CharField(max_length=64, required=False, allow_blank=True)


class MobileOtpRequestSerializer(serializers.Serializer):
    mobile_number = serializers.CharField(max_length=10, min_length=10)


class MobileOtpVerifySerializer(serializers.Serializer):
    txn_id = serializers.CharField(max_length=64)
    otp = serializers.CharField(max_length=6, min_length=6)


class CreateAbhaAddressSerializer(serializers.Serializer):
    txn_id = serializers.CharField(max_length=64)
    abha_address = serializers.CharField(max_length=128)
    preferred = serializers.BooleanField(default=True)


class VerifyAbhaNumberRequestSerializer(serializers.Serializer):
    abha_number = serializers.CharField(max_length=19, help_text="14-digit ABHA number with/without dashes")


class VerifyAbhaNumberOtpSerializer(serializers.Serializer):
    txn_id = serializers.CharField(max_length=64)
    otp = serializers.CharField(max_length=6)


class HipApiLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = HipApiLog
        fields = "__all__"


class UnifiedOtpRequestSerializer(serializers.Serializer):
    """
    Unified OTP Request - Accepts payload for all 3 methods
    Frontend sends: loginHint, loginId, scope, otpSystem
    """
    loginHint = serializers.CharField(
        max_length=32,
        help_text="aadhaar | abha-number | mobile"
    )
    loginId = serializers.CharField(
        max_length=64,
        help_text="Aadhaar (12 digits) | ABHA (14 digits) | Mobile (10 digits)"
    )
    scope = serializers.ListField(
        child=serializers.CharField(),
        help_text='["abha-enrol"] or ["abha-user-init"]'
    )
    otpSystem = serializers.CharField(
        max_length=32,
        help_text="aadhaar | abdm"
    )

    def validate(self, data):
        login_hint = data.get("loginHint", "").lower()
        login_id = data.get("loginId", "").strip()
        scope = data.get("scope", [])

        # Validate Aadhaar
        if login_hint == "aadhaar":
            if len(login_id.replace(" ", "")) != 12:
                raise serializers.ValidationError("Aadhaar must be 12 digits")
            if not login_id.isdigit():
                raise serializers.ValidationError("Aadhaar must contain only digits")
            if "abha-enrol" not in scope:
                raise serializers.ValidationError("Aadhaar must use scope 'abha-enrol'")

        # Validate ABHA Number
        elif login_hint == "abha-number":
            clean_abha = login_id.replace("-", "").strip()
            if len(clean_abha) != 14:
                raise serializers.ValidationError("ABHA must be 14 digits (with or without hyphens)")
            if not clean_abha.isdigit():
                raise serializers.ValidationError("ABHA must contain only digits")
            if "abha-user-init" not in scope:
                raise serializers.ValidationError("ABHA must use scope 'abha-user-init'")

        # Validate Mobile
        elif login_hint == "mobile":
            if len(login_id) != 10:
                raise serializers.ValidationError("Mobile must be 10 digits")
            if not login_id.isdigit():
                raise serializers.ValidationError("Mobile must contain only digits")
            if "abha-user-init" not in scope:
                raise serializers.ValidationError("Mobile must use scope 'abha-user-init'")

        else:
            raise serializers.ValidationError("loginHint must be 'aadhaar', 'abha-number', or 'mobile'")

        return data


class UnifiedOtpVerifySerializer(serializers.Serializer):
    """
    Unified OTP Verify - Accepts payload for all 3 methods
    """
    txn_id = serializers.CharField(max_length=64)
    otp = serializers.CharField(max_length=6, min_length=6)
    scope = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text='Optional. If passed, used to route verification. e.g. ["abha-enrol"] or ["abha-user-init"]'
    )
