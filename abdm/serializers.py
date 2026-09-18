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
