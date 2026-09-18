#!/bin/bash

# ABDM Unified OTP Endpoint Test Script
# Tests all 3 methods with the single unified endpoint

API_URL="http://localhost:8000/api/v1/abdm"

echo "================================"
echo "ABDM Unified OTP Endpoint Tests"
echo "================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test 1: Aadhaar Verification
echo -e "\n${BLUE}Test 1: Aadhaar Verification${NC}"
echo "Sending OTP for Aadhaar: 999999999999"

AADHAAR_RESPONSE=$(curl -s -X POST "$API_URL/m1/send-otp/" \
  -H "Content-Type: application/json" \
  -d '{
    "loginHint": "aadhaar",
    "loginId": "999999999999",
    "scope": ["abha-enrol"],
    "otpSystem": "aadhaar"
  }')

echo "Response:"
echo "$AADHAAR_RESPONSE" | jq '.'

AADHAAR_TXN=$(echo "$AADHAAR_RESPONSE" | jq -r '.txn_id')
echo -e "${GREEN}✓ Aadhaar TXN ID: $AADHAAR_TXN${NC}"

# Test 2: ABHA Number Verification
echo -e "\n${BLUE}Test 2: ABHA Number Verification${NC}"
echo "Sending OTP for ABHA: 91-9876-5432-1098"

ABHA_RESPONSE=$(curl -s -X POST "$API_URL/m1/send-otp/" \
  -H "Content-Type: application/json" \
  -d '{
    "loginHint": "abha-number",
    "loginId": "91-9876-5432-1098",
    "scope": ["abha-user-init"],
    "otpSystem": "aadhaar"
  }')

echo "Response:"
echo "$ABHA_RESPONSE" | jq '.'

ABHA_TXN=$(echo "$ABHA_RESPONSE" | jq -r '.txn_id')
echo -e "${GREEN}✓ ABHA TXN ID: $ABHA_TXN${NC}"

# Test 3: Mobile Number Verification
echo -e "\n${BLUE}Test 3: Mobile Number Verification${NC}"
echo "Sending OTP for Mobile: 9876543210"

MOBILE_RESPONSE=$(curl -s -X POST "$API_URL/m1/send-otp/" \
  -H "Content-Type: application/json" \
  -d '{
    "loginHint": "mobile",
    "loginId": "9876543210",
    "scope": ["abha-user-init"],
    "otpSystem": "abdm"
  }')

echo "Response:"
echo "$MOBILE_RESPONSE" | jq '.'

MOBILE_TXN=$(echo "$MOBILE_RESPONSE" | jq -r '.txn_id')
echo -e "${GREEN}✓ Mobile TXN ID: $MOBILE_TXN${NC}"

# Test 4: Verify Aadhaar OTP
echo -e "\n${BLUE}Test 4: Verify Aadhaar OTP${NC}"
echo "Verifying OTP for Aadhaar with TXN: $AADHAAR_TXN"

VERIFY_AADHAAR=$(curl -s -X POST "$API_URL/m1/enrol/aadhaar/verify-otp/" \
  -H "Content-Type: application/json" \
  -d "{
    \"txn_id\": \"$AADHAAR_TXN\",
    \"otp\": \"123456\"
  }")

echo "Response:"
echo "$VERIFY_AADHAAR" | jq '.'

# Test 5: Verify ABHA OTP (using common endpoint)
echo -e "\n${BLUE}Test 5: Verify ABHA OTP${NC}"
echo "Verifying OTP for ABHA with TXN: $ABHA_TXN"

VERIFY_ABHA=$(curl -s -X POST "$API_URL/m1/verify/confirm-otp/" \
  -H "Content-Type: application/json" \
  -d "{
    \"txn_id\": \"$ABHA_TXN\",
    \"otp\": \"123456\"
  }")

echo "Response:"
echo "$VERIFY_ABHA" | jq '.'

# Test 6: Verify Mobile OTP (using common endpoint)
echo -e "\n${BLUE}Test 6: Verify Mobile OTP${NC}"
echo "Verifying OTP for Mobile with TXN: $MOBILE_TXN"

VERIFY_MOBILE=$(curl -s -X POST "$API_URL/m1/verify/confirm-otp/" \
  -H "Content-Type: application/json" \
  -d "{
    \"txn_id\": \"$MOBILE_TXN\",
    \"otp\": \"123456\"
  }")

echo "Response:"
echo "$VERIFY_MOBILE" | jq '.'

# Test 7: List all registered patients
echo -e "\n${BLUE}Test 7: List All Patients${NC}"

PATIENTS=$(curl -s "$API_URL/m1/patients/")
echo "Response:"
echo "$PATIENTS" | jq '.'

# Test 8: View API Logs
echo -e "\n${BLUE}Test 8: View API Logs${NC}"

LOGS=$(curl -s "$API_URL/m1/logs/")
echo "Response (Last 5 entries):"
echo "$LOGS" | jq '.[0:5]'

echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}All Tests Completed!${NC}"
echo -e "${GREEN}================================${NC}"
