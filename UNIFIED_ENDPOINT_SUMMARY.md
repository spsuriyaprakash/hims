# Unified ABDM OTP Endpoint - Summary

## 🎯 What Changed

### **New Unified Endpoint**
```
POST /api/v1/abdm/m1/send-otp/
```

Accept flexible payload from frontend for **all 3 methods** with same structure:

```json
{
  "loginHint": "aadhaar" | "abha-number" | "mobile",
  "loginId": "user_value",
  "scope": ["scope_value"],
  "otpSystem": "aadhaar" | "abdm"
}
```

---

## 💻 Frontend Usage - All 3 Methods With Same Code

```javascript
async function sendOtp(loginHint, loginId) {
  const payloads = {
    'aadhaar': {
      loginHint: 'aadhaar',
      loginId: loginId,  // 12 digits
      scope: ['abha-enrol'],
      otpSystem: 'aadhaar'
    },
    'abha-number': {
      loginHint: 'abha-number',
      loginId: loginId,  // 14 digits (hyphens optional)
      scope: ['abha-user-init'],
      otpSystem: 'aadhaar'
    },
    'mobile': {
      loginHint: 'mobile',
      loginId: loginId,  // 10 digits
      scope: ['abha-user-init'],
      otpSystem: 'abdm'
    }
  };

  const response = await fetch('/api/v1/abdm/m1/send-otp/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payloads[loginHint])
  });

  return await response.json();
}

// Usage
await sendOtp('aadhaar', '999999999999');
await sendOtp('abha-number', '91-9876-5432-1098');
await sendOtp('mobile', '9876543210');
```

---

## 🔄 Internal Backend Routing

```
Frontend sends:
{
  "loginHint": "abha-number",
  "loginId": "91-9876-5432-1098",
  "scope": ["abha-user-init"],
  "otpSystem": "aadhaar"
}
    ↓
UnifiedOtpRequestView.post()
    ↓
UnifiedOtpRequestSerializer.validate()
    ↓
AbdmService.request_otp(
  login_hint="abha-number",
  login_id="91-9876-5432-1098",
  scope=["abha-user-init"],
  otp_system="aadhaar"
)
    ↓
Automatically routes to:
ABDM Gateway: POST /abha/api/v3/profile/login/request/otp
    ↓
Response with txn_id
```

---

## 📋 Validation Rules

| Method | loginHint | loginId | scope | otpSystem |
|--------|-----------|---------|-------|-----------|
| **Aadhaar** | `"aadhaar"` | 12 digits | `["abha-enrol"]` | `"aadhaar"` |
| **ABHA** | `"abha-number"` | 14 digits (hyphens ok) | `["abha-user-init"]` | `"aadhaar"` |
| **Mobile** | `"mobile"` | 10 digits | `["abha-user-init"]` | `"abdm"` |

---

## 📝 Code Changes

### 1. **services.py** - New `request_otp()` method
```python
@classmethod
def request_otp(cls, login_hint, login_id, scope, otp_system):
    # Unified OTP handler for all 3 methods
    # Automatically determines ABDM endpoint based on login_hint + scope
    # Handles ABHA number cleanup (removes hyphens)
    # Creates AbhaTransaction record
```

### 2. **serializers.py** - New validator
```python
class UnifiedOtpRequestSerializer(serializers.Serializer):
    # Validates loginHint, loginId, scope, otpSystem
    # Ensures correct format for each method
    # Prevents invalid combinations
```

### 3. **views.py** - New unified view
```python
class UnifiedOtpRequestView(APIView):
    # POST /api/v1/abdm/m1/send-otp/
    # Accepts flexible payload
    # Delegates to AbdmService.request_otp()
```

### 4. **urls.py** - New endpoint
```python
path("m1/send-otp/", UnifiedOtpRequestView.as_view(), name="m1-unified-send-otp")
```

---

## ✅ Example Requests with cURL

### **Aadhaar**
```bash
curl -X POST http://localhost:8000/api/v1/abdm/m1/send-otp/ \
  -H "Content-Type: application/json" \
  -d '{
    "loginHint": "aadhaar",
    "loginId": "999999999999",
    "scope": ["abha-enrol"],
    "otpSystem": "aadhaar"
  }'
```

### **ABHA Number**
```bash
curl -X POST http://localhost:8000/api/v1/abdm/m1/send-otp/ \
  -H "Content-Type: application/json" \
  -d '{
    "loginHint": "abha-number",
    "loginId": "91-9876-5432-1098",
    "scope": ["abha-user-init"],
    "otpSystem": "aadhaar"
  }'
```

### **Mobile**
```bash
curl -X POST http://localhost:8000/api/v1/abdm/m1/send-otp/ \
  -H "Content-Type: application/json" \
  -d '{
    "loginHint": "mobile",
    "loginId": "9876543210",
    "scope": ["abha-user-init"],
    "otpSystem": "abdm"
  }'
```

---

## 📌 Next Steps

1. **OTP Confirmation** - Use existing endpoint:
   ```
   POST /api/v1/abdm/m1/verify/confirm-otp/
   {
     "txn_id": "response_txn_id",
     "otp": "123456"
   }
   ```

2. **Patient Data** - Get verified patient:
   ```
   GET /api/v1/abdm/m1/patients/
   ```

3. **API Logs** - Check all requests:
   ```
   GET /api/v1/abdm/m1/logs/
   ```

---

## 🔗 References

- 📖 Full implementation guide: `ABDM_IMPLEMENTATION_GUIDE.md`
- 🎨 Frontend examples: `ABDM_FRONTEND_INTEGRATION.md`
- 📋 Unified endpoint details: `ABDM_UNIFIED_ENDPOINT.md`

