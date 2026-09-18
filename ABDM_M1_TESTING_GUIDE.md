# ABDM Milestone 1 (M1) API Testing Guide & Flow

This document provides a step-by-step guide for testing **ABDM M1 (ABHA Creation & Enrolment)** APIs in HIMS, including API endpoints, request bodies, expected responses, and database verification details.

---

## 🌐 Network Requirements: Localhost vs Ngrok

| Milestone | Communication Type | Network Requirement |
| :--- | :--- | :--- |
| **M1 (ABHA Creation & Enrolment)** | **Synchronous Direct Calls** (Client → HIMS → ABDM Gateway) | **`localhost` is sufficient.** No Ngrok required. |
| **M2 & M3 (Consent & Health Record Transfer)** | **Asynchronous Callbacks/Webhooks** (ABDM Gateway → HIMS Callback URL) | **`ngrok` (Public URL) is mandatory.** |

---

## 🧪 M1 Step-by-Step API Testing Flow

### Step 1: Fetch ABDM Gateway Public Certificate

Fetch the RSA public key used for encrypting sensitive user demographic information.

- **Endpoint:** `GET /api/v1/abdm/m1/public-cert/`
- **Full URL:** `http://localhost:8000/api/v1/abdm/m1/public-cert/`
- **Headers:** `Content-Type: application/json`
- **Request Body:** *None*

#### Expected Response (`200 OK`)
```json
{
  "success": true,
  "certificate": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA..."
}
```

#### Database Verification
- **Table:** `abdm_hipapilog`
- **Check:** A log entry recording the `POST/GET` request to ABDM Gateway.

---

### Step 2: Request Aadhaar OTP

Initiate ABHA registration by sending the patient's Aadhaar number to trigger an OTP.

- **Endpoint:** `POST /api/v1/abdm/m1/enrol/aadhaar/send-otp/`
- **Full URL:** `http://localhost:8000/api/v1/abdm/m1/enrol/aadhaar/send-otp/`
- **Headers:** `Content-Type: application/json`

#### Request Body
```json
{
  "aadhaar_number": "123456789012"
}
```

#### Expected Response (`200 OK`)
```json
{
  "success": true,
  "txn_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
  "message": "OTP sent successfully"
}
```

#### Database Verification
- **Table:** `abdm_abhatransaction`
- **Verification Query:**
  ```sql
  SELECT txn_id, aadhaar_hash, status, created_at 
  FROM abdm_abhatransaction 
  ORDER BY created_at DESC LIMIT 1;
  ```
- **Expected Values:**
  - `status`: `'OTP_SENT'`
  - `txn_id`: Matches `txn_id` returned in response.

---

### Step 3: Verify Aadhaar OTP & Create Patient Record

Verify the OTP sent to the patient's mobile number, complete enrolment, and provision local patient records.

- **Endpoint:** `POST /api/v1/abdm/m1/enrol/aadhaar/verify-otp/`
- **Full URL:** `http://localhost:8000/api/v1/abdm/m1/enrol/aadhaar/verify-otp/`
- **Headers:** `Content-Type: application/json`

#### Request Body
```json
{
  "txn_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
  "otp": "123456",
  "mrn": "MRN-1001"
}
```

#### Expected Response (`200 OK`)
```json
{
  "success": true,
  "message": "ABHA Verified & Patient Created Successfully",
  "patient": {
    "id": 1,
    "mrn": "MRN-1001",
    "abha_number": "12-3456-7890-1234",
    "abha_address": "",
    "name": "Ramesh Kumar",
    "gender": "M",
    "dob": "1990-01-01",
    "mobile": "9876543210"
  },
  "tokens": {
    "token": "eyJhbGciOi...",
    "expires_in": 86400
  }
}
```

#### Database Verification
- **Table 1:** `abdm_abdmpatient`
  ```sql
  SELECT id, mrn, abha_number, name, gender, mobile FROM abdm_abdmpatient WHERE mrn = 'MRN-1001';
  ```
  - **Check:** `abha_number`, `name`, `gender`, `dob`, `mobile` populated from ABDM payload.

- **Table 2:** `abdm_abhatoken`
  ```sql
  SELECT * FROM abdm_abhatoken ORDER BY created_at DESC LIMIT 1;
  ```
  - **Check:** `x_token` and `refresh_token` stored for patient session authorization.

- **Table 3:** `abdm_abhatransaction`
  ```sql
  SELECT status FROM abdm_abhatransaction WHERE txn_id = 'a1b2c3d4-e5f6-7890-abcd-1234567890ab';
  ```
  - **Check:** `status` updated to `'COMPLETED'`.

---

### Step 4: Create ABHA Address (PHR Handle)

Assign a unique custom ABHA address (e.g. `username@sbx`) to the patient's ABHA profile.

- **Endpoint:** `POST /api/v1/abdm/m1/enrol/create-abha-address/`
- **Full URL:** `http://localhost:8000/api/v1/abdm/m1/enrol/create-abha-address/`
- **Headers:** `Content-Type: application/json`

#### Request Body
```json
{
  "txn_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
  "abha_address": "ramesh123@sbx",
  "preferred": true
}
```

#### Expected Response (`200 OK`)
```json
{
  "success": true,
  "message": "ABHA Address created successfully",
  "abha_address": "ramesh123@sbx"
}
```

#### Database Verification
- **Table:** `abdm_abdmpatient`
  ```sql
  SELECT abha_number, abha_address FROM abdm_abdmpatient WHERE abha_number = '12-3456-7890-1234';
  ```
  - **Check:** `abha_address` column is updated to `'ramesh123@sbx'`.

---

### Step 5: Query Registered Patients & Audit Logs

#### A. List All ABDM Patients
- **Endpoint:** `GET /api/v1/abdm/m1/patients/`
- **Full URL:** `http://localhost:8000/api/v1/abdm/m1/patients/`
- **Response:** Array of all created `AbdmPatient` objects.

#### B. View Audit Logs
- **Endpoint:** `GET /api/v1/abdm/m1/logs/`
- **Full URL:** `http://localhost:8000/api/v1/abdm/m1/logs/`
- **Response:** List of the 50 most recent ABDM Gateway HTTP API request & response payload logs (`HipApiLog`).

---

## 📊 Complete M1 Flow & Database State Diagram

```text
[ Client / Postman ]
       │
       │ 1. POST /m1/enrol/aadhaar/send-otp/
       ▼
[ Django ABDM View ] ──► Calls ABDM Gateway (/v3/enrollment/request/otp)
       │
       ├─► Inserts Record into DB: abdm_abhatransaction (status='OTP_SENT')
       └─► Returns txn_id to Client
       │
       │ 2. POST /m1/enrol/aadhaar/verify-otp/
       ▼
[ Django ABDM View ] ──► Calls ABDM Gateway (/v3/enrollment/enrol/byAadhaar)
       │
       ├─► Creates DB Record: abdm_abdmpatient
       ├─► Creates DB Record: abdm_abhatoken
       └─► Updates DB Record: abdm_abhatransaction (status='COMPLETED')
       │
       │ 3. POST /m1/enrol/create-abha-address/
       ▼
[ Django ABDM View ] ──► Calls ABDM Gateway (/v3/enrollment/link/abha-address)
       │
       └─► Updates DB Record: abdm_abdmpatient (abha_address='ramesh123@sbx')
```
