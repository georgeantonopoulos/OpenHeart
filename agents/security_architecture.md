---
title: Security Architecture & GDPR Compliance
version: 1.0
status: planning
created: 2026-01-21
description: Security patterns for OpenHeart Cyprus EMR based on GDPR, Cyprus Law 125(I)/2018, and healthcare industry best practices.
---

# Security Architecture & GDPR Compliance

## 1. Regulatory Framework

### Cyprus Law 125(I)/2018 Requirements

- **Genetic/Biometric Data**: Stricter than base GDPR - processing for life/health insurance is **prohibited**.
- **Consent**: Separate and specific consent required for any further processing of genetic/biometric data.
- **Retention Period**: Health data must be retained for **15 years** after the patient's death or last clinical record (Commissioner for Personal Data Protection decision 2018).
- **Record-Keeping**: Failure to maintain Article 30 records is a **criminal offense** (up to 3 years imprisonment, EUR 30,000 fine).
- **Breach Notification**: Failure to notify data subjects of breaches is a criminal offense.

### Lawful Bases for Processing Health Data

Processing permitted for:

- Preventive or occupational medicine
- Assessing working capacity
- Medical diagnosis
- Health/social care provision and treatment
- Management of healthcare systems and services

## 2. Database Security with PostgreSQL Row-Level Security

### Multi-Tenant Patient Data Isolation

```sql
-- Enable RLS on patient tables
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;

-- Schema with tenant isolation
CREATE TABLE patients (
    patient_id SERIAL PRIMARY KEY,
    clinic_id INT NOT NULL,  -- Tenant identifier (clinic/practice)
    arc_number VARCHAR(20),  -- Alien Registration Certificate
    id_card VARCHAR(20),     -- Cyprus ID Card
    patient_name TEXT,
    date_of_birth DATE,
    phone VARCHAR(20),       -- +357 format
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for RLS performance
CREATE INDEX idx_patients_clinic ON patients (clinic_id);

-- Read policy: clinicians can only see their clinic's patients
CREATE POLICY patient_read ON patients
FOR SELECT USING (clinic_id = current_setting('app.clinic_id', true)::int);

-- Write policy: enforce tenant on mutations
CREATE POLICY patient_write ON patients
FOR ALL USING (clinic_id = current_setting('app.clinic_id', true)::int)
WITH CHECK (clinic_id = current_setting('app.clinic_id', true)::int);
```

### Setting Tenant Context in FastAPI

```python
# middleware/tenant_context.py
from fastapi import Request
from sqlalchemy.orm import Session

async def set_tenant_context(request: Request, db: Session):
    """Set PostgreSQL session variable for RLS."""
    clinic_id = request.state.user.clinic_id
    db.execute(f"SET app.clinic_id = '{clinic_id}'")
```

## 3. Audit Logging

### Security Audit Table Schema

```sql
-- Partition audit logs by month/year for performance
CREATE TABLE security_audit (
    audit_id BIGSERIAL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    -- ... other columns (see implementation)
    PRIMARY KEY (audit_id, timestamp)
) PARTITION BY RANGE (timestamp);

-- Example Partition
CREATE TABLE security_audit_2026_01 PARTITION OF security_audit
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

-- Indexes for common queries
CREATE INDEX idx_audit_timestamp ON security_audit (timestamp DESC);
CREATE INDEX idx_audit_user ON security_audit (user_id);
CREATE INDEX idx_audit_resource ON security_audit (resource_type, resource_id);
CREATE INDEX idx_audit_clinic ON security_audit (clinic_id);
```

### FastAPI Audit Middleware

```python
# middleware/audit.py
from fastapi import Request, Response
from datetime import datetime
import json

async def audit_middleware(request: Request, call_next):
    """Log all requests to security_audit table for GDPR compliance."""

    # Capture request details
    user = getattr(request.state, 'user', None)

    response = await call_next(request)

    # Log to audit table
    audit_entry = {
        "timestamp": datetime.utcnow(),
        "user_id": user.id if user else None,
        "user_email": user.email if user else None,
        "ip_address": request.client.host,
        "user_agent": request.headers.get("user-agent"),
        "action": _map_method_to_action(request.method),
        "resource_type": _extract_resource_type(request.url.path),
        "resource_id": _extract_resource_id(request.url.path),
        "clinic_id": user.clinic_id if user else None,
        "request_path": str(request.url.path),
        "request_method": request.method,
        "response_status": response.status_code,
    }

    # Async insert to avoid blocking
    await insert_audit_log(audit_entry)

    return response

def _map_method_to_action(method: str) -> str:
    return {
        "GET": "READ",
        "POST": "CREATE",
        "PUT": "UPDATE",
        "PATCH": "UPDATE",
        "DELETE": "DELETE"
    }.get(method, "UNKNOWN")
```

## 4. Encryption

### Data at Rest

```python
# config/encryption.py
from cryptography.fernet import Fernet
import os

# Store key in environment variable or secrets manager
ENCRYPTION_KEY = os.environ.get("PII_ENCRYPTION_KEY")

def encrypt_pii(plaintext: str) -> str:
    """Encrypt personally identifiable information."""
    f = Fernet(ENCRYPTION_KEY)
    return f.encrypt(plaintext.encode()).decode()

def decrypt_pii(ciphertext: str) -> str:
    """Decrypt personally identifiable information."""
    f = Fernet(ENCRYPTION_KEY)
    return f.decrypt(ciphertext.encode()).decode()
```

### PostgreSQL Column-Level Encryption

```sql
-- Using pgcrypto extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypted PII columns
CREATE TABLE patient_pii (
    patient_id INT PRIMARY KEY REFERENCES patients(patient_id),
    encrypted_ssn BYTEA,  -- Social security or ARC
    encrypted_address BYTEA,
    encryption_key_id INT  -- For key rotation
);

-- Encrypt on insert
INSERT INTO patient_pii (patient_id, encrypted_ssn)
VALUES (1, pgp_sym_encrypt('123456789', current_setting('app.encryption_key')));

-- Decrypt on select
SELECT pgp_sym_decrypt(encrypted_ssn, current_setting('app.encryption_key'))
FROM patient_pii WHERE patient_id = 1;
```

## 5. Data Subject Rights Implementation

### Right to Access (Data Portability)

```python
# services/gdpr.py
async def export_patient_data(patient_id: int, format: str = "json") -> bytes:
    """Export all patient data for GDPR Article 20 compliance."""

    patient = await get_patient(patient_id)
    records = await get_medical_records(patient_id)
    appointments = await get_appointments(patient_id)

    export_data = {
        "export_date": datetime.utcnow().isoformat(),
        "patient": patient.dict(),
        "medical_records": [r.dict() for r in records],
        "appointments": [a.dict() for a in appointments],
    }

    if format == "json":
        return json.dumps(export_data, indent=2).encode()
    elif format == "fhir":
        return convert_to_fhir_bundle(export_data)
```

### Right to Erasure (with Medical Retention Exceptions)

```python
async def process_erasure_request(patient_id: int) -> dict:
    """
    Process GDPR Article 17 erasure request.
    Note: Medical records may be retained for legal/archival purposes.
    """

    # Check retention requirements
    retention_period = await get_retention_period(patient_id)

    if retention_period.still_required:
        return {
            "status": "partial",
            "message": "Medical records retained for legal archival purposes",
            "anonymized_fields": await anonymize_patient_pii(patient_id)
        }

    # Full erasure if retention period expired
    await delete_patient_data(patient_id)
    return {"status": "complete", "message": "All data erased"}
```

## 6. Authentication & Authorization

### Multi-Factor Authentication (MFA)

All clinical accounts must use MFA. Implementation should support:

- **TOTP**: Authenticator apps (Google Authenticator, Authy).
- **WebAuthn**: Hardware keys (Yubico) or Biometric (TouchID/FaceID).

```python
# auth/mfa.py
async def verify_mfa_token(user_id: int, token: str) -> bool:
    """Verify TOTP token for user."""
    # ... implementation using pyotp
    pass
```

### Role-Based Access Control (RBAC)

| Role | Permissions |
|------|-------------|
| Admin | Full access to clinic data, user management |
| Cardiologist | Full access to assigned patients, CDSS tools |
| Nurse | Read/update vitals, appointments |
| Receptionist | Patient demographics, scheduling only |
| Auditor | Read-only access to audit logs |

### SMART on FHIR OAuth2 Flow

For FHIR interoperability, implement SMART on FHIR authorization:

```python
# auth/smart_fhir.py
FHIR_SCOPES = [
    "patient/*.read",
    "patient/*.write",
    "user/*.read",
    "launch/patient"
]
```

## 7. Security Checklist

- [ ] PostgreSQL RLS enabled on all patient-related tables
- [ ] Audit logging middleware capturing all data access (partitioned tables)
- [ ] Multi-Factor Authentication (MFA) enforced for all users
- [ ] PII encryption at rest (AES-256)
- [ ] PII encryption managed keys (rotational)
- [ ] TLS 1.3 for all connections
- [ ] JWT tokens with short expiry (15 minutes)
- [ ] Refresh token rotation with session invalidation
- [ ] Rate limiting on API endpoints (Redis-backed)
- [ ] Input validation with Pydantic
- [ ] SQL injection prevention via SQLAlchemy ORM
- [ ] XSS prevention in frontend (React auto-escaping)
- [ ] CORS configured for specific origins only
- [ ] Security headers (CSP, X-Frame-Options, etc.)
- [ ] Regular automated vulnerability scans (Bandit/Snyk)
