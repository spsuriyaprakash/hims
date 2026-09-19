from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from abdm.abdm import AbdmGateway
from abdm.models import *
from abdm.serializers import *
from abdm.services import *


class AbdmConfigView(APIView):
    """
    Get or update ABDM Sandbox Configuration
    """
    permission_classes = [AllowAny]

    def get(self, request):
        config = AbdmGateway.get_config()
        serializer = AbdmConfigSerializer(config)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        config = AbdmGateway.get_config()
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
        cert = AbdmGateway.get_public_cert()
        return Response({"success": True, "certificate": cert}, status=status.HTTP_200_OK)


class UnifiedOtpRequestView(APIView):
    """
    POST /api/v1/abdm/m1/send-otp/
    Unified OTP Request for all 3 methods (Aadhaar, ABHA, Mobile)
    Frontend sends flexible payload with loginHint, loginId, scope, otpSystem
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UnifiedOtpRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        login_hint = serializer.validated_data["loginHint"].lower()
        login_id = serializer.validated_data["loginId"]
        scope = serializer.validated_data["scope"]
        otp_system = serializer.validated_data["otpSystem"].lower()

        result = AbdmService.request_otp(
            login_hint=login_hint,
            login_id=login_id,
            scope=scope,
            otp_system=otp_system
        )
        return Response(result, status=status.HTTP_200_OK if result.get("success") else status.HTTP_400_BAD_REQUEST)


class UnifiedOtpVerifyView(APIView):
    """
    POST /api/v1/abdm/m1/verify-otp/
    Unified OTP Verify for all 3 methods (Aadhaar, ABHA, Mobile)
    Frontend passes back txn_id, otp, and the scope they received from send-otp
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UnifiedOtpVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        txn_id = serializer.validated_data["txn_id"]
        otp = serializer.validated_data["otp"]
        scope = serializer.validated_data.get("scope", [])

        # Fallback to DB if frontend didn't pass scope
        if not scope:
            txn = AbhaTransaction.objects.filter(txn_id=txn_id).first()
            if txn and txn.scope_json:
                scope = txn.scope_json
            else:
                return Response({"error": "Scope is required or transaction not found"}, status=status.HTTP_400_BAD_REQUEST)

        # Route verification based on scope
        if "abha-enrol" in scope:
            result = AbdmService.verify_aadhaar_otp(txn_id, otp)
        else:
            result = AbdmService.confirm_abha_verify_otp(txn_id, otp)
            if result.get("success"):
                patient = result["patient"]
                patient_data = AbdmPatientSerializer(patient).data
                return Response(
                    {
                        "success": True,
                        "message": "Existing ABHA Verified & Linked Successfully",
                        "patient": patient_data,
                        "profile": result.get("profile"),
                    },
                    status=status.HTTP_200_OK,
                )

        return Response(result, status=status.HTTP_200_OK if result.get("success") else status.HTTP_400_BAD_REQUEST)


class AadhaarOtpRequestView(APIView):
    """
    POST /api/v1/abdm/m1/enrol/aadhaar/send-otp/
    M1 API: Request OTP for ABHA Creation via Aadhaar
    Legacy endpoint - delegates to UnifiedOtpRequestView
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


class VerifyAbhaSendOtpView(APIView):
    """
    POST /api/v1/abdm/m1/verify/abha-number/send-otp/
    M1 API: Request OTP to verify an existing ABHA Number
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyAbhaNumberRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        abha_number = serializer.validated_data["abha_number"]
        result = AbdmService.request_abha_verify_otp(abha_number)
        return Response(result, status=status.HTTP_200_OK if result.get("success") else status.HTTP_400_BAD_REQUEST)


class VerifyMobileSendOtpView(APIView):
    """
    POST /api/v1/abdm/m1/verify/mobile/send-otp/
    M1 API: Request OTP to verify via Mobile Number
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = MobileOtpRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        mobile_number = serializer.validated_data["mobile_number"]
        result = AbdmService.request_mobile_verify_otp(mobile_number)
        return Response(result, status=status.HTTP_200_OK if result.get("success") else status.HTTP_400_BAD_REQUEST)



class VerifyAbhaConfirmOtpView(APIView):
    """
    POST /api/v1/abdm/m1/verify/confirm-otp/
    M1 API: Confirm OTP to verify & link existing ABHA Number
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyAbhaNumberOtpSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        txn_id = serializer.validated_data["txn_id"]
        otp = serializer.validated_data["otp"]

        result = AbdmService.confirm_abha_verify_otp(txn_id, otp)
        if result.get("success"):
            patient = result["patient"]
            patient_data = AbdmPatientSerializer(patient).data
            return Response(
                {
                    "success": True,
                    "message": "Existing ABHA Verified & Linked Successfully",
                    "patient": patient_data,
                    "profile": result.get("profile"),
                },
                status=status.HTTP_200_OK,
            )
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


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

