---
title: OpenHeart Cyprus - User Management & Authentication Implementation Plan
version: 1.0
status: planning
created: 2026-01-22
description: >
  Comprehensive plan for implementing user management, authentication, and
  access control for OpenHeart Cyprus EMR, addressing the critical gap in
  the original implementation plan.
---

# User Management & Authentication Implementation Plan

## 1. Current Implementation Status

### 1.1 What Has Been Built

| Component | Status | Notes |
|-----------|--------|-------|
| **Infrastructure** | ✅ Complete | Docker Compose with PostgreSQL, Redis, MinIO, Orthanc |
| **Backend Framework** | ✅ Complete | FastAPI with async support, health checks |
| **Frontend Framework** | ✅ Complete | Next.js 14 with App Router, Tailwind CSS |
| **CDSS Module** | ✅ Complete | GRACE, CHA₂DS₂-VASc, HAS-BLED calculators with 40+ tests |
| **Clinical Notes** | ✅ Complete | CRUD, versioning, attachments, full-text search |
| **Security Infrastructure** | ⚠️ Partial | JWT tokens, RBAC skeleton, audit middleware, PII encryption |
| **Database** | ⚠️ Partial | Session management configured, models defined (needs Alembic) |
| **Login Page** | ✅ Placeholder | UI exists but not connected to backend |

### 1.2 Critical Gap Identified

**The original implementation plan assumed users exist without defining how they come into existence.**

Missing components:

- User registration/onboarding workflow
- Admin user management interface
- Password reset flow
- Session management implementation
- MFA setup flow
- Role assignment workflow
- First-time login experience
- Developer/testing access strategy

---

## 2. Legal & Compliance Requirements

### 2.1 GDPR (EU Regulation 2016/679)

| Requirement | Implementation |
|-------------|----------------|
| **Lawful Basis** | Healthcare providers process data under Article 9(2)(h) - medical diagnosis and treatment |
| **Role-Based Access Control** | Mandatory - only authorized users access data based on role |
| **Multi-Factor Authentication** | Required for accessing medical data |
| **Audit Logging** | Every access, modification, or sharing must be logged |
| **Data Encryption** | Mandatory in transit (TLS 1.3) and at rest (AES-256) |
| **Access Reviews** | Regular audits of user permissions required |

### 2.2 Cyprus Law 125(I)/2018

| Requirement | Implementation |
|-------------|----------------|
| **Genetic/Biometric Data** | Prohibited for insurance purposes; separate consent required |
| **Medical Record Retention** | 10 years (private practice) / 20 years (hospitals) |
| **Data Controller Registration** | Must register with Data Protection Commissioner |
| **Breach Notification** | 72 hours to Commissioner, without undue delay to patients |

### 2.3 European Health Data Space (EHDS) Regulation

| Requirement | Implementation |
|-------------|----------------|
| **Secure Processing Environment** | Production must meet highest privacy/cybersecurity standards |
| **No Re-identification** | Anonymized data must not be re-identifiable |
| **Interoperability** | EHR systems must meet harmonized security criteria |

---

## 3. User Roles & Permissions Matrix

### 3.1 Defined Roles

| Role | Code | Description |
|------|------|-------------|
| **System Administrator** | `SYSTEM_ADMIN` | Full system access, user management, configuration |
| **Clinic Administrator** | `CLINIC_ADMIN` | Manage users within their clinic, view audit logs |
| **Cardiologist** | `CARDIOLOGIST` | Full patient access, CDSS, DICOM, prescriptions |
| **Physician** | `PHYSICIAN` | Patient access, notes, basic CDSS |
| **Nurse** | `NURSE` | Limited patient access, vitals, basic notes |
| **Receptionist** | `RECEPTIONIST` | Appointments, demographics only - no clinical data |
| **Medical Secretary** | `MEDICAL_SECRETARY` | Reports, scheduling, limited patient view |
| **Auditor** | `AUDITOR` | Read-only access to audit logs, no patient data |

### 3.2 Permission Matrix

| Permission | SYS_ADMIN | CLINIC_ADMIN | CARDIOLOGIST | PHYSICIAN | NURSE | RECEPTIONIST |
|------------|:---------:|:------------:|:------------:|:---------:|:-----:|:------------:|
| Manage System Users | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Manage Clinic Users | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| View Audit Logs | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| View Patient Demographics | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| View Clinical Notes | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ |
| Write Clinical Notes | ❌ | ❌ | ✅ | ✅ | ⚠️* | ❌ |
| View DICOM Studies | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| Use CDSS Calculators | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| Manage Appointments | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Export Patient Data | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |

*Nurses can write vitals and basic observations only

---

## 4. User Journey Maps

### 4.1 System Bootstrap (First-Time Setup)

```
┌─────────────────────────────────────────────────────────────────┐
│                    SYSTEM BOOTSTRAP FLOW                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Docker Compose Up                                           │
│         │                                                       │
│         ▼                                                       │
│  2. Database Migration Runs                                     │
│         │                                                       │
│         ▼                                                       │
│  3. Seed Script Detects Empty Users Table                       │
│         │                                                       │
│         ▼                                                       │
│  4. Creates SYSTEM_ADMIN Account                                │
│     • Email: admin@openheart.local                              │
│     • Temp Password: Generated & printed to console             │
│     • Flag: must_change_password = true                         │
│         │                                                       │
│         ▼                                                       │
│  5. Admin Logs In → Forced Password Change                      │
│         │                                                       │
│         ▼                                                       │
│  6. Admin Sets Up MFA (Mandatory)                               │
│         │                                                       │
│         ▼                                                       │
│  7. Admin Creates First Clinic                                  │
│         │                                                       │
│         ▼                                                       │
│  8. Admin Invites Clinic Administrator                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Admin Invites New User

```
┌─────────────────────────────────────────────────────────────────┐
│                    INVITATION FLOW                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ADMIN SIDE:                                                    │
│  ───────────                                                    │
│  1. Navigate to User Management                                 │
│         │                                                       │
│         ▼                                                       │
│  2. Click "Invite User"                                         │
│         │                                                       │
│         ▼                                                       │
│  3. Enter: Email, Full Name, Role, Clinic Assignment            │
│         │                                                       │
│         ▼                                                       │
│  4. System Generates:                                           │
│     • Unique invitation token (expires 72 hours)                │
│     • Sends email with secure link                              │
│     • Logs invitation in audit trail                            │
│                                                                 │
│  ═══════════════════════════════════════════════════════════    │
│                                                                 │
│  INVITED USER SIDE:                                             │
│  ──────────────────                                             │
│  5. Receives Email with Link                                    │
│         │                                                       │
│         ▼                                                       │
│  6. Clicks Link → Invitation Page                               │
│         │                                                       │
│         ▼                                                       │
│  7. Sets Password (complexity enforced)                         │
│         │                                                       │
│         ▼                                                       │
│  8. Sets Up MFA (TOTP via authenticator app)                    │
│         │                                                       │
│         ▼                                                       │
│  9. Accepts Terms of Service & Privacy Policy                   │
│         │                                                       │
│         ▼                                                       │
│  10. Account Activated → Redirected to Dashboard                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 Daily Login Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    DAILY LOGIN FLOW                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. User Visits /login                                          │
│         │                                                       │
│         ▼                                                       │
│  2. Enters Email + Password                                     │
│         │                                                       │
│         ├──[Invalid]──► Show Error (generic: "Invalid           │
│         │               credentials" - never reveal which)      │
│         │                                                       │
│         ▼ [Valid]                                               │
│  3. MFA Challenge Screen                                        │
│         │                                                       │
│         ▼                                                       │
│  4. Enter TOTP Code from Authenticator                          │
│         │                                                       │
│         ├──[Invalid]──► Allow 3 attempts, then lockout 15min    │
│         │                                                       │
│         ▼ [Valid]                                               │
│  5. Session Created:                                            │
│     • JWT access token (15 min)                                 │
│     • Refresh token (7 days, stored in Redis)                   │
│     • Session logged to audit table                             │
│         │                                                       │
│         ▼                                                       │
│  6. Redirect to Role-Appropriate Dashboard                      │
│     • Cardiologist → Patient list + Today's appointments        │
│     • Receptionist → Appointments calendar                      │
│     • Admin → System overview                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.4 Password Reset Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    PASSWORD RESET FLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. User Clicks "Forgot Password"                               │
│         │                                                       │
│         ▼                                                       │
│  2. Enters Email Address                                        │
│         │                                                       │
│         ▼                                                       │
│  3. System ALWAYS shows: "If account exists, email sent"        │
│     (Never reveal whether email exists - prevents enumeration)  │
│         │                                                       │
│         ▼ [If email exists]                                     │
│  4. Generate Reset Token (expires 1 hour)                       │
│     Send Email with Secure Link                                 │
│     Log in audit trail                                          │
│         │                                                       │
│         ▼                                                       │
│  5. User Clicks Link → Reset Page                               │
│         │                                                       │
│         ▼                                                       │
│  6. Enter New Password (complexity enforced)                    │
│         │                                                       │
│         ▼                                                       │
│  7. Require MFA Verification (proves identity)                  │
│         │                                                       │
│         ▼                                                       │
│  8. Password Updated                                            │
│     All Other Sessions Invalidated                              │
│     Notification Email Sent                                     │
│         │                                                       │
│         ▼                                                       │
│  9. Redirect to Login                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Developer Testing Strategy

### 5.1 Seed Data for Development

**CRITICAL: Never use real patient data in development.**

```python
# Development seed configuration (app/core/seed.py)
SEED_CONFIG = {
    "environment": "development",  # Only runs when ENVIRONMENT=development
    "admin_user": {
        "email": "admin@openheart.local",
        "password": "DevAdmin123!",  # Only for local dev
        "role": "SYSTEM_ADMIN",
        "mfa_enabled": False,  # Disabled in dev for convenience
    },
    "test_users": [
        {"email": "cardiologist@test.local", "role": "CARDIOLOGIST", "clinic_id": "seed_clinic_1"},
        {"email": "nurse@test.local", "role": "NURSE", "clinic_id": "seed_clinic_1"},
        {"email": "reception@test.local", "role": "RECEPTIONIST", "clinic_id": "seed_clinic_1"},
    ],
    "synthetic_patients": 50,  # Generated via Synthea or custom faker
}
```

### 5.2 Environment-Specific Behavior

| Behavior | Development | Staging | Production |
|----------|-------------|---------|------------|
| Seed admin user | ✅ Auto-created | ❌ Manual only | ❌ Manual only |
| MFA required | ❌ Optional | ✅ Required | ✅ Required |
| Password complexity | ⚠️ Relaxed | ✅ Enforced | ✅ Enforced |
| Session timeout | 24 hours | 1 hour | 15 min (configurable) |
| Synthetic data | ✅ Auto-seeded | ✅ On request | ❌ Never |
| Debug endpoints | ✅ Enabled | ❌ Disabled | ❌ Disabled |

### 5.3 Test Credentials Display

In development mode only, the login page shows:

```
┌─────────────────────────────────────────────────────────────────┐
│  🔧 DEVELOPMENT MODE - Test Accounts                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  System Admin:      admin@openheart.local / DevAdmin123!        │
│  Cardiologist:      cardiologist@test.local / TestUser123!      │
│  Nurse:             nurse@test.local / TestUser123!             │
│  Receptionist:      reception@test.local / TestUser123!         │
│                                                                 │
│  ⚠️  These accounts only exist in development environment       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Password & Security Policies

### 6.1 Password Requirements

| Rule | Requirement |
|------|-------------|
| Minimum length | 12 characters |
| Complexity | At least: 1 uppercase, 1 lowercase, 1 number, 1 special |
| Hashing Algorithm | **Argon2id** (replacing bcrypt for higher GPU resistance) |
| History | Cannot reuse last 12 passwords (stored in `password_history`) |
| Expiration | 90 days for clinical users (GDPR best practice) |
| Lockout | 5 failed attempts → 15 min lockout |
| Breach check | Validate against HaveIBeenPwned API (hashed) |

### 6.2 Session Management

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Access token lifetime | 15 minutes | Short-lived for security |
| Refresh token lifetime | 7 days | Convenience for long shifts |
| Idle timeout | 15 minutes | Auto-logout if inactive (client-side timer + server check) |
| Absolute timeout | 12 hours | Force re-auth after shift |
| Concurrent sessions | 2 max | Prevent credential sharing |
| Rate Limiting | 10 req/min on auth endpoints | Redis-backed sliding window |

### 6.3 MFA Requirements

| User Type | MFA Requirement |
|-----------|-----------------|
| System Admin | Mandatory - TOTP or WebAuthn |
| Clinic Admin | Mandatory - TOTP or WebAuthn |
| Clinical Staff | Mandatory - TOTP |
| Receptionist | Optional (configurable by clinic) |
| Development accounts | Disabled (dev environment only) |

---

## 7. Database Schema Additions

### 7.1 New Tables Required

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    clinic_id UUID REFERENCES clinics(id),

    -- Status
    is_active BOOLEAN DEFAULT false,
    is_verified BOOLEAN DEFAULT false,
    must_change_password BOOLEAN DEFAULT true,

    -- MFA
    mfa_enabled BOOLEAN DEFAULT false,
    mfa_secret VARCHAR(255),  -- Encrypted TOTP secret
    mfa_backup_codes TEXT[],  -- Encrypted backup codes

    -- Security
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    last_login_at TIMESTAMP,
    last_password_change TIMESTAMP,
    password_history JSONB,  -- Hashed previous passwords

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),

    -- GDPR
    consent_given_at TIMESTAMP,
    terms_accepted_at TIMESTAMP
);

-- Invitations table
CREATE TABLE user_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    clinic_id UUID REFERENCES clinics(id),
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    invited_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sessions table (for Redis backup/audit)
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    refresh_token_hash VARCHAR(255) NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    revoked_at TIMESTAMP
);

-- Password reset tokens
CREATE TABLE password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 8. API Endpoints Required

### 8.1 Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/login` | Email + password login | No |
| POST | `/api/auth/mfa/verify` | Verify TOTP code | Partial (after login) |
| POST | `/api/auth/refresh` | Refresh access token | Refresh token |
| POST | `/api/auth/logout` | Invalidate session | Yes |
| POST | `/api/auth/password/reset-request` | Request password reset | No |
| POST | `/api/auth/password/reset` | Reset password with token | No |
| PUT | `/api/auth/password/change` | Change password (logged in) | Yes |

### 8.2 User Management Endpoints (Admin)

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/api/admin/users` | List users (paginated) | MANAGE_USERS |
| POST | `/api/admin/users/invite` | Send invitation | MANAGE_USERS |
| GET | `/api/admin/users/{id}` | Get user details | MANAGE_USERS |
| PUT | `/api/admin/users/{id}` | Update user | MANAGE_USERS |
| DELETE | `/api/admin/users/{id}` | Deactivate user | MANAGE_USERS |
| POST | `/api/admin/users/{id}/reset-mfa` | Reset user's MFA | MANAGE_USERS |
| GET | `/api/admin/invitations` | List pending invitations | MANAGE_USERS |
| DELETE | `/api/admin/invitations/{id}` | Revoke invitation | MANAGE_USERS |

### 8.3 User Self-Service Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/me` | Get current user profile | Yes |
| PUT | `/api/me` | Update profile (name only) | Yes |
| GET | `/api/me/sessions` | List active sessions | Yes |
| DELETE | `/api/me/sessions/{id}` | Revoke a session | Yes |
| POST | `/api/me/mfa/setup` | Begin MFA setup | Yes |
| POST | `/api/me/mfa/verify` | Complete MFA setup | Yes |
| DELETE | `/api/me/mfa` | Disable MFA (if allowed) | Yes + MFA |

### 8.4 Invitation Acceptance Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/invitations/{token}` | Validate invitation | No |
| POST | `/api/invitations/{token}/accept` | Complete registration | No |

---

## 9. Frontend Pages Required

### 9.1 Public Pages (No Auth)

| Route | Component | Description |
|-------|-----------|-------------|
| `/login` | LoginPage | Email + password form |
| `/login/mfa` | MfaChallengePage | TOTP verification |
| `/forgot-password` | ForgotPasswordPage | Request reset email |
| `/reset-password` | ResetPasswordPage | Set new password |
| `/invite/{token}` | InvitationPage | Accept invitation & setup |

### 9.2 Protected Pages (Auth Required)

| Route | Component | Permission |
|-------|-----------|------------|
| `/dashboard` | DashboardPage | Any authenticated user |
| `/profile` | ProfilePage | Any authenticated user |
| `/profile/security` | SecuritySettingsPage | Any authenticated user |
| `/admin/users` | UserManagementPage | MANAGE_USERS |
| `/admin/users/invite` | InviteUserPage | MANAGE_USERS |
| `/admin/audit-log` | AuditLogPage | VIEW_AUDIT_LOG |

---

## 10. Implementation Order

### Phase 1: Core Auth (Week 1)

1. User database model & migrations (Alembic)
2. Password hashing (Argon2id via `argon2-cffi`)
3. Login endpoint (email + password)
4. JWT token generation
5. Basic session management
6. Login page connected to backend

### Phase 2: User Management (Week 2)

1. Invitation system (backend)
2. Invitation acceptance flow
3. Admin user management page
4. User listing & details

### Phase 3: MFA (Week 3)

1. TOTP secret generation
2. MFA setup flow
3. MFA verification on login
4. Backup codes

### Phase 4: Security Hardening (Week 4)

1. Password reset flow
2. Account lockout
3. Session management UI
4. Password policies enforcement
5. Audit logging integration

### Phase 5: Developer Experience

1. Seed scripts for development
2. Test account auto-creation
3. Environment-specific configs
4. Documentation

---

## 11. Testing Requirements

### 11.1 Unit Tests

- Password hashing & verification
- Token generation & validation
- Permission checks
- Role hierarchy

### 11.2 Integration Tests

- Full login flow (email → password → MFA → dashboard)
- Invitation flow (create → email → accept → login)
- Password reset flow
- Session timeout behavior

### 11.3 Security Tests

- SQL injection on login
- Brute force protection (Rate limiter verification)
- Token expiration
- CSRF protection (SameSite cookie policies)
- Session fixation
- Privilege Escalation (verify Nurse cannot access Admin routes)

---

## 12. References

### Legal

- GDPR Regulation 2016/679 - Articles 9, 32
- Cyprus Law 125(I)/2018
- European Health Data Space (EHDS) Regulation

### Best Practices

- OWASP Authentication Cheat Sheet
- NIST Digital Identity Guidelines (SP 800-63B)
- NHS Digital Identity Standards

### Research Sources

- [GDPR Health Data Compliance](https://gdprlocal.com/gdpr-health-data-compliance-key-considerations-for-healthcare-providers/)
- [Healthcare Onboarding Best Practices](https://hrforhealth.com/blog/onboarding-best-practices-for-new-healthcare-employees)
- [EMR Development Guide 2025](https://wtt-solutions.com/blog/emr-development-complete-guide-to-building-electronic-medical-records-systems-in-2025)
