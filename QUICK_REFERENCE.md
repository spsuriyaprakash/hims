# ABDM Unified Endpoint - Quick Reference

## 🚀 Single Endpoint (All 3 Methods)

**POST** `/api/v1/abdm/m1/send-otp/`

---

## 📋 Request Payloads

### **Aadhaar** (Create new ABHA)
```json
{
  "loginHint": "aadhaar",
  "loginId": "999999999999",
  "scope": ["abha-enrol"],
  "otpSystem": "aadhaar"
}
```

### **ABHA Number** (Link existing)
```json
{
  "loginHint": "abha-number",
  "loginId": "91-9876-5432-1098",
  "scope": ["abha-user-init"],
  "otpSystem": "aadhaar"
}
```

### **Mobile** (Mobile auth)
```json
{
  "loginHint": "mobile",
  "loginId": "9876543210",
  "scope": ["abha-user-init"],
  "otpSystem": "abdm"
}
```

---

## ✅ Response Format (All Methods)

```json
{
  "success": true,
  "txn_id": "b2c3d4e5-f6a7-8901-bcde-2345678901bc",
  "message": "OTP sent successfully",
  "data": {
    "txnId": "b2c3d4e5-f6a7-8901-bcde-2345678901bc",
    "mobile": "******9821"
  }
}
```

---

## 🔗 Next: Confirm OTP (Same for All)

**POST** `/api/v1/abdm/m1/verify/confirm-otp/`

```json
{
  "txn_id": "b2c3d4e5-f6a7-8901-bcde-2345678901bc",
  "otp": "123456"
}
```

---

## 💻 Frontend Code (React)

```javascript
async function sendAbhaOtp(method, value) {
  const payload = {
    aadhaar: { loginHint: 'aadhaar', loginId: value, scope: ['abha-enrol'], otpSystem: 'aadhaar' },
    abha: { loginHint: 'abha-number', loginId: value, scope: ['abha-user-init'], otpSystem: 'aadhaar' },
    mobile: { loginHint: 'mobile', loginId: value, scope: ['abha-user-init'], otpSystem: 'abdm' }
  };

  const res = await fetch('/api/v1/abdm/m1/send-otp/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload[method])
  });

  return await res.json();
}
```

---

## 🧪 Test with cURL

```bash
# Aadhaar
curl -X POST http://localhost:8000/api/v1/abdm/m1/send-otp/ \
  -H "Content-Type: application/json" \
  -d '{"loginHint":"aadhaar","loginId":"999999999999","scope":["abha-enrol"],"otpSystem":"aadhaar"}'

# ABHA
curl -X POST http://localhost:8000/api/v1/abdm/m1/send-otp/ \
  -H "Content-Type: application/json" \
  -d '{"loginHint":"abha-number","loginId":"91-9876-5432-1098","scope":["abha-user-init"],"otpSystem":"aadhaar"}'

# Mobile
curl -X POST http://localhost:8000/api/v1/abdm/m1/send-otp/ \
  -H "Content-Type: application/json" \
  -d '{"loginHint":"mobile","loginId":"9876543210","scope":["abha-user-init"],"otpSystem":"abdm"}'
```

---

## 📝 Database Models

| Model | Purpose |
|-------|---------|
| **AbdmPatient** | Patient master (MRN, ABHA, mobile, KYC status) |
| **AbhaTransaction** | OTP transaction tracking (txn_id, flow, status) |
| **AbhaToken** | X-Token storage for profile requests |
| **HipApiLog** | API audit trail |

---

## 🔄 Architecture

```
Frontend
  ↓
POST /api/v1/abdm/m1/send-otp/ {flexible payload}
  ↓
UnifiedOtpRequestView (validates payload)
  ↓
AbdmService.request_otp() (routes based on loginHint + scope)
  ↓
ABDM Gateway (/abha/api/v3/enrollment/request/otp or /profile/login/request/otp)
  ↓
Response with txn_id
  ↓
Frontend stores txn_id
  ↓
User enters OTP
  ↓
POST /api/v1/abdm/m1/verify/confirm-otp/ {txn_id, otp}
  ↓
Patient verified ✅
```

---

## 📌 Important Notes

- ✅ **Single unified endpoint** for all 3 methods
- ✅ **Flexible payload** - same structure for all methods
- ✅ **Automatic routing** - backend determines ABDM endpoint
- ✅ **Common confirm** - same endpoint for ABHA & mobile verification
- ✅ **Legacy endpoints** - old endpoints still work (backward compatible)
- ✅ **Mock fallback** - works in sandbox without ABDM gateway
- ✅ **10-min OTP expiry** - transactions expire automatically
- ⚠️ **HTTPS required** - production must use HTTPS

---

## 📚 Documentation Files

- `ABDM_IMPLEMENTATION_GUIDE.md` - Complete implementation details
- `ABDM_UNIFIED_ENDPOINT.md` - Unified endpoint specification
- `UNIFIED_ENDPOINT_SUMMARY.md` - What changed & how it works
- `test_unified_endpoint.sh` - Test script for all endpoints

---

## 🚨 Common Issues

| Error | Solution |
|-------|----------|
| "Aadhaar must be 12 digits" | Check `loginId` format (12 digits) |
| "ABHA must be 14 digits" | Check `loginId` format (14 digits, hyphens optional) |
| "Mobile must be 10 digits" | Check `loginId` format (10 digits) |
| "scope must be ['abha-enrol']" | Aadhaar requires `scope: ["abha-enrol"]` |
| "scope must be ['abha-user-init']" | ABHA & mobile require `scope: ["abha-user-init"]` |
| "Invalid otpSystem for method" | Aadhaar/ABHA use "aadhaar", Mobile uses "abdm" |

---

## ✨ What You Have Now

✅ Unified endpoint that accepts flexible payloads  
✅ Automatic routing to correct ABDM gateway  
✅ All 3 verification methods supported  
✅ Common OTP confirmation endpoint  
✅ Database transaction tracking  
✅ API audit logging  
✅ Mock fallback for sandbox  
✅ Backward compatibility with legacy endpoints  
✅ Complete validation & error handling  

Ready to integrate with your frontend! 🚀

