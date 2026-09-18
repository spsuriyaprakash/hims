from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from abdm.models import AbdmConfig, AbdmPatient, HipApiLog
from abdm.serializers import (
    AadhaarOtpRequestSerializer,
    AadhaarOtpVerifySerializer,
    AbdmConfigSerializer,
    AbdmPatientSerializer,
    CreateAbhaAddressSerializer,
    HipApiLogSerializer,
)
from abdm.services import AbdmService


class AbdmConfigView(APIView):
    """
    Get or update ABDM Sandbox Configuration
    """
    permission_classes = [AllowAny]

    def get(self, request):
        config = AbdmService.get_config()
        serializer = AbdmConfigSerializer(config)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        config = AbdmService.get_config()
        serializer = AbdmConfigSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PublicCertView(APIView):
    """
    GET /api/v1/abdm/m1/public-cert/
    Fetch ABDM Gateway Public RSA Certificate for encryption
    """
    permission_classes = [AllowAny]

    def get(self, request):
        cert = AbdmService.get_public_cert()
        return Response({"success": True, "certificate": cert}, status=status.HTTP_200_OK)


class AadhaarOtpRequestView(APIView):
    """
    POST /api/v1/abdm/m1/enrol/aadhaar/send-otp/
    M1 API: Request OTP for ABHA Creation via Aadhaar
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AadhaarOtpRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        aadhaar_number = serializer.validated_data["aadhaar_number"]
        result = AbdmService.request_aadhaar_otp(aadhaar_number)
        return Response(result, status=status.HTTP_200_OK if result.get("success") else status.HTTP_400_BAD_REQUEST)


class AadhaarOtpVerifyView(APIView):
    """
    POST /api/v1/abdm/m1/enrol/aadhaar/verify-otp/
    M1 API: Verify OTP & Create ABHA Patient record
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AadhaarOtpVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        txn_id = serializer.validated_data["txn_id"]
        otp = serializer.validated_data["otp"]
        mrn = serializer.validated_data.get("mrn")

        result = AbdmService.verify_aadhaar_otp(txn_id, otp, mrn)
        if result.get("success"):
            patient = result["patient"]
            patient_data = AbdmPatientSerializer(patient).data
            return Response(
                {
                    "success": True,
                    "message": "ABHA Verified & Patient Created Successfully",
                    "patient": patient_data,
                    "tokens": result.get("tokens"),
                },
                status=status.HTTP_200_OK,
            )
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


class CreateAbhaAddressView(APIView):
    """
    POST /api/v1/abdm/m1/enrol/create-abha-address/
    M1 API: Set / Create ABHA Address (PHR Handle)
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CreateAbhaAddressSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        txn_id = serializer.validated_data["txn_id"]
        abha_address = serializer.validated_data["abha_address"]
        preferred = serializer.validated_data.get("preferred", True)

        result = AbdmService.create_abha_address(txn_id, abha_address, preferred)
        return Response(result, status=status.HTTP_200_OK if result.get("success") else status.HTTP_400_BAD_REQUEST)


class PatientListView(APIView):
    """
    GET /api/v1/abdm/m1/patients/
    List all ABDM registered patients
    """
    permission_classes = [AllowAny]

    def get(self, request):
        patients = AbdmPatient.objects.all().order_by("-created_at")
        serializer = AbdmPatientSerializer(patients, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class HipApiLogListView(APIView):
    """
    GET /api/v1/abdm/m1/logs/
    List ABDM API Audit Logs
    """
    permission_classes = [AllowAny]

    def get(self, request):
        logs = HipApiLog.objects.all().order_by("-created_at")[:50]
        serializer = HipApiLogSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
