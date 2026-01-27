---
title: OpenHeart Cyprus - Comprehensive Implementation Plan
version: 2.0
status: planning
created: 2026-01-22
description: >
  Complete implementation plan addressing ALL functionality required for a working
  cardiology EMR. This supersedes partial implementations and ensures nothing is missed.
---

# Comprehensive Implementation Plan

## Executive Summary

**Problem**: The previous implementation delivered authentication infrastructure but left the cardiologist with an empty dashboard. A cardiologist cannot:

- Add or view patients
- Write clinical notes
- Use CDSS calculators (UI missing)
- View imaging studies
- Submit Gesy claims
- Do anything useful

**Solution**: This plan covers EVERY feature needed for a functional cardiology EMR, organized by user workflow priority, with a focus on **Premium UI/UX** and **Cyprus Regulatory Compliance**.

---

## Technology Stack & Infrastructure

To ensure scalability and clinical safety, OpenHeart Cyprus uses a modern, specialized stack:

### 1. Frontend: Next.js 14+ (App Router)

- **Styling**: Vanilla CSS + Glassmorphism utilities.
- **State Management**: React Context / SWR for clinical data fetching.
- **Imaging**: `@ohif/viewer` integration for DICOM review.

### 2. Backend: FastAPI (Python 3.11+)

- **Async Engine**: `httpx` for DICOMweb and Gesy integration.
- **Auth**: NextAuth.js (Frontend) + JWT (Backend) with TOTP-based MFA.
- **Calculators**: Pre-validated cardiology engines (GRACE, HAS-BLED, CHA₂DS₂-VASc).

### 3. Database: PostgreSQL 15+

- **Security**: Row-Level Security (RLS) for multi-tenant clinic isolation.
- **Governance**: Partitioned audit logs for GDPR/Cyprus Law 15-year retention.
- **Encryption**: `pgcrypto` for PII (AES-256).

### 4. Specialized Services

- **Orthanc**: DICOM Server (PACS) with DICOMweb/MWL support.
- **FHIR R4**: Standardized interoperability layer for national data exchange.

---

## Design Language & Aesthetics

To ensure a "WOW" factor and premium feel, the application will adhere to the following design principles:

### 1. Visual Theme

- **Glassmorphism**: Use translucent backgrounds for overlays, sidebars, and cards to create depth.
- **Vibrant Accent Colors**: A "Cardiology Red" (#E11D48) for critical alerts balanced with "Stability Blue" (#1E293B) and "Healing Teal" (#0D9488).
- **Dark Mode First**: The interface will be optimized for clinical environments with high-contrast dark modes to reduce eye strain.

### 2. Micro-interactions

- **Animated Page Transitions**: Smooth slide-ins for patient records and fade-ins for CDSS results.
- **Live Scoring**: CDSS calculators will update results in real-time with "pulse" animations on risk indicators.
- **Haptic Context**: (For mobile/touch) subtle feedback on success/failure of critical actions.

### 3. Typography

- **Primary**: *Inter* or *Outfit* for modern readability.
- **Mono**: *JetBrains Mono* for clinical data, lab values, and audit logs.

---

---

## Current State Analysis

### What Exists (Backend Only)

| Component            | Backend | Frontend | Notes                                                         |
| -------------------- | :-----: | :------: | ------------------------------------------------------------- |
| Authentication       |   ✅    |    ✅    | Phase 1 only - missing MFA, password reset, user management   |
| CDSS Calculators     |   ✅    |    ❌    | GRACE, CHA₂DS₂-VASc, HAS-BLED - no UI                         |
| Clinical Notes       |   ✅    |    ❌    | Full CRUD API exists - no UI                                  |
| Patient Model        |   ✅    |    ❌    | Database model exists - no API, no UI                         |
| Audit Logging        |   ✅    |   N/A    | Middleware logs requests                                      |
| Gesy Integration     |   ✅    |    ❌    | Mock adapter exists - no UI                                   |
| DICOM Service        |   ⚠️    |    ❌    | Orthanc configured - no service layer, no UI                  |

### What's Completely Missing

| Component | Priority | Notes |
|-----------|:--------:|-------|
| Patient CRUD API | CRITICAL | Cannot add or view patients |
| Patient UI | CRITICAL | No patient list, search, profile |
| Encounter/Visit System | CRITICAL | No way to record visits |
| CDSS Calculator UI | HIGH | Backend exists, needs forms |
| Clinical Notes UI | HIGH | Backend exists, needs forms |
| Dashboard (real) | HIGH | Currently useless placeholder |
| DICOM Viewer | MEDIUM | OHIF integration needed |
| Appointments/Scheduling | MEDIUM | No scheduling system |
| User Management UI | CRITICAL | Phases 2-5 of auth plan - Needs "WOW" factor |
| Gesy Workflow UI | HIGH | Referrals, claims, e-Rx |
| i18n (Greek/English) | MEDIUM | Required for Cyprus market |
| Reports/Analytics | LOW | Trend analysis, exports |

---

## Implementation Phases

### Phase 0: Fix Critical Gaps (Immediate)

**Objective**: Make the dashboard useful TODAY.

#### 0.1 Patient Management API

Create `backend/app/modules/patient/`:

```bash
patient/
├── __init__.py
├── models.py        # Already exists - verify completeness
├── schemas.py       # Pydantic models for API
├── service.py       # Business logic
└── router.py        # API endpoints
```

**Endpoints Required**:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/patients` | List patients (paginated, searchable) |
| POST | `/api/patients` | Create new patient |
| GET | `/api/patients/{id}` | Get patient details |
| PUT | `/api/patients/{id}` | Update patient |
| DELETE | `/api/patients/{id}` | Soft-delete patient |
| GET | `/api/patients/{id}/timeline` | Get patient history |
| GET | `/api/patients/search` | Full-text search |

**Patient Fields (Cyprus-specific)**:

```python
class PatientCreate(BaseModel):
    # Identity
    id_type: Literal["cyprus_id", "arc", "passport"]  # ARC = Alien Registration Certificate
    id_number: str  # Cyprus ID format: 7 digits

    # Demographics
    first_name: str
    last_name: str
    first_name_greek: Optional[str]  # Greek spelling
    last_name_greek: Optional[str]
    date_of_birth: date
    sex: Literal["male", "female"]

    # Contact
    phone_mobile: str  # +357 format
    phone_home: Optional[str]
    email: Optional[EmailStr]
    address: Optional[str]
    city: Optional[str]
    postal_code: Optional[str]

    # Medical
    blood_type: Optional[str]
    allergies: Optional[list[str]]

    # Personal Doctor / PD-ID
    personal_doctor_id: Optional[str]

    # Security Metadata
    clinic_id: int  # Required for RLS isolation
```

**Cyprus Regulatory Requirements (Law 125(I)/2018)**:

- **15-Year Retention**: Records must be retained for 15 years post-death or last activity.
- **Genetic Data Prohibition**: Direct processing of genetic/biometric data for insurance purposes is strictly prohibited in-app.
- **Tenant Isolation**: PostgreSQL Row-Level Security (RLS) is MANDATORY on the `patients` table to prevent cross-clinic data leaks.

#### 0.2 Patient List & Search UI (Functional)

Create `frontend/src/app/patients/`:

```bash
patients/
├── page.tsx              # Patient list with search
├── [id]/
│   ├── page.tsx          # Patient profile/chart
│   ├── timeline/
│   │   └── page.tsx      # Patient history
│   └── components/
│       ├── PatientHeader.tsx
│       ├── VitalsPanel.tsx
│       ├── MedicationsList.tsx
│       └── RecentNotes.tsx
└── new/
    └── page.tsx          # Add new patient form

**Patient Search & Global Commands**:
- **Magic Search (Cmd+K)**: Instant-access search bar overlay with glassmorphism, allowing search by Name, ARC/Cyprus ID, or Phone.
- **Passive Clinical Banners**: Real-time risk markers (e.g., "High CV Risk" or "Pending Labs") displayed at the top of the patient profile, replacing intrusive pop-ups.
```

**Patient Search Implementation**:

- Must support **Greek and Latin** character mapping (e.g., searching "Nikos" should find "Νίκος").
- Search by `id_number` must validate against Cyprus checksums.

**Patient List Features**:

- Search by name, ID, phone
- Filter by last visit date
- Sort by name, last visit
- Quick actions: View, Add Note, Schedule

#### 0.3 Functional Dashboard

Replace the placeholder with:

```tsx
// Dashboard sections for Cardiologist role
<Dashboard>
  {/* Row 1: Today's Overview */}
  <TodayAppointments />      {/* Clickable list */}
  <QuickStats />             {/* Patients seen today, pending notes */}

  {/* Row 2: Quick Actions */}
  <QuickActions>
    <SearchPatient />        {/* Cmd+K global search */}
    <NewPatient />           {/* Add patient button */}
    <CDSSCalculators />      {/* Links to calculators */}
  </QuickActions>

  {/* Row 3: Recent Activity */}
  <RecentPatients />         {/* Last 5 viewed */}
  <PendingTasks />           {/* Unsigned notes, pending results */}
</Dashboard>
```

---

### Phase 1: Clinical Workflow (Week 1-2)

**Objective**: Enable core clinical documentation.

#### 1.1 Encounter/Visit System

Create `backend/app/modules/encounter/`:

```python
class Encounter(BaseModel):
    encounter_id: int
    patient_id: int
    clinic_id: int
    provider_id: int  # The doctor

    encounter_type: Literal["outpatient", "inpatient", "emergency", "telehealth"]
    encounter_date: datetime
    chief_complaint: Optional[str]

    # Status
    status: Literal["scheduled", "in_progress", "completed", "cancelled"]

    # Gesy
    referral_id: Optional[str]  # If patient came via referral

    # Billing
    billed: bool = False
    claim_id: Optional[str]
```

**Endpoints**:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/encounters` | List encounters (filterable) |
| POST | `/api/encounters` | Start new encounter |
| GET | `/api/encounters/{id}` | Get encounter details |
| PUT | `/api/encounters/{id}` | Update encounter |
| POST | `/api/encounters/{id}/complete` | Mark complete |

#### 1.2 Clinical Notes UI

Connect to existing backend (`/api/notes`):

```bash
frontend/src/app/patients/[id]/notes/
├── page.tsx              # List of notes for patient
├── new/
│   └── page.tsx          # Create note (with templates)
└── [noteId]/
    ├── page.tsx          # View note
    └── edit/
        └── page.tsx      # Edit note
```

**Note Templates (Cardiology-Specific)**:

1. **SOAP Note** - General visit
2. **Echo Report** - Structured echo findings
3. **Cath Report** - Angiography/PCI report
4. **Device Check** - Pacemaker/ICD interrogation
5. **Pre-Op Cardiac Clearance** - Surgery clearance
6. **Heart Failure Visit** - HF-specific template

**SOAP Note Fields**:

```typescript
interface CardioSOAPNote {
  // Subjective
  chief_complaint: string;
  history_present_illness: string;
  symptoms: {
    chest_pain: boolean;
    dyspnea: boolean;
    palpitations: boolean;
    syncope: boolean;
    edema: boolean;
  };
  nyha_class: 1 | 2 | 3 | 4;

  // Objective
  vitals: {
    bp_systolic: number;
    bp_diastolic: number;
    heart_rate: number;
    weight_kg: number;
    spo2: number;
  };
  physical_exam: {
    jugular_venous_distension: boolean;
    lung_sounds: string;
    heart_sounds: string;
    peripheral_edema: string;
  };

  // Assessment (Cyprus Codification)
  diagnoses: Array<{
    code: string;       // ICD-10 (Specialist) or ICPC-2 (PD)
    system: "ICD-10" | "ICPC-2" | "ICD-10-CY";
    description: string;
    is_primary: boolean;
  }>;

  // Plan
  medications_changed: Array<MedicationChange>;
  orders: Array<Order>; // Mapping to LOINC for labs
  follow_up: string;
}
```

**Codification Matrix (Gesy Mandatory)**:

| Context                   | Code System  | Terminology Source        |
| ------------------------- | ------------ | ------------------------- |
| Outpatient Diagnoses      | ICD-10 / HIO | GHS Codification          |
| Personal Doctor Diagnoses | ICPC-II      | Primary Care Standard     |
| Procedures                | CPT          | Specialist Service Codes  |
| Lab Orders/Results        | LOINC        | Standard interoperability |
| Pharmaceuticals           | ATC + HIO ID | E-Prescription system     |

#### 1.3 CDSS Calculator UI

Create `frontend/src/app/cdss/`:

```bash
cdss/
├── page.tsx              # Calculator selection
├── grace/
│   └── page.tsx          # GRACE Score form
├── cha2ds2vasc/
│   └── page.tsx          # CHA₂DS₂-VASc form
├── hasbled/
│   └── page.tsx          # HAS-BLED form
└── components/
    ├── ScoreResult.tsx   # Display result with recommendations
    ├── RiskBanner.tsx    # Color-coded risk indicator with pulse animation
    └── SaveToPatient.tsx # Option to save to patient record

**Advanced Calculators (Clinical Logic)**:

1. **GRACE Score**: Risk thresholds (≤108: Low, 109-140: Int, >140: High). High scores prompt "Urgent Invasive strategy (<24h)".
2. **CHA₂DS₂-VASc**: Recommendation thresholds (Male ≥2, Female ≥3: "OAC Recommended").
3. **HAS-BLED**: Bleeding risk modifiers check. Score ≥3: "High risk, address modifiable factors".
4. **PREVENT Equations (Modern Standard)**: Replace 2013 ASCVD as default. Includes HF risk prediction and eGFR/UACR kidney health.
5. **EuroSCORE II**: Interactive wizard for perioperative mortality risk prediction.

**CDSS Audit Trail (Required)**:
Every calculation must log the `clinician_id`, `input_parameters`, `calculated_score`, and `clinician_override_reason` to the partitioned audit logs.

---

### Phase 2: User Management Completion (Week 2-3)

**Objective**: Complete Phases 2-5 of `user_management_plan.md`.

#### 2.1 Invitation System & Onboarding UI

To prevent the gaps of the previous plan, the invitation flow will be a high-engagement experience:

```python
# backend/app/modules/auth/invitation.py

class UserInvitation(BaseModel):
    invitation_id: UUID
    email: EmailStr
    role: str
    clinic_id: int
    invited_by: int
    token: str  # Secure random token
    expires_at: datetime
    accepted_at: Optional[datetime]
```

**Invitation Endpoints**:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/admin/users/invite` | Create invitation |
| GET | `/api/admin/invitations` | List pending invitations |
| DELETE | `/api/admin/invitations/{id}` | Revoke invitation |
| GET | `/api/invitations/{token}` | Validate invitation (public) |
| POST | `/api/invitations/{token}/accept` | Complete registration (public) |

**Invitation Flow (Frontend Structure)**:

```bash
frontend/src/app/
├── invite/
│   └── [token]/
│       └── page.tsx      # Accept invitation, set password
└── admin/
    └── users/
        ├── page.tsx      # User list
        ├── invite/
        │   └── page.tsx  # Invite user form
        └── [id]/
            └── page.tsx  # Edit user
```

- **Admin Invite Portal**: A sleek dashboard card showing "Active Invitations" with countdown timers for expiration.
- **Invite Preview**: Before sending, admins see the exact "Welcome to OpenHeart" email the user will receive.
- **The "Welcome" Journey**: The `/invite/[token]` page will be a beautifully crafted onboarding wizard:
  1. **Identity Confirmation**: Greeting the user by name.
  2. **Security Setup**: Argon2id password creation with a real-time "Strength Meter".
  3. **MFA Onboarding**: Animated QR code setup for TOTP, with "Backup Code" download as a distinct, mandatory step.
  4. **Legal Consent**: Integrated review of GDPR and Cyprus Law 125(I)/2018 terms.

#### 2.2 Security Architecture (PostgreSQL RLS & Partitioning)

To ensure clinic-level isolation and **Law 125(I)/2018** compliance:

```sql
-- 1. Clinic Data Isolation (RLS)
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
CREATE POLICY clinic_isolation ON patients
FOR ALL USING (clinic_id = current_setting('app.clinic_id', true)::int);

-- 2. Audit Log Partitioning (15-Year Retention)
CREATE TABLE security_audit (
    audit_id BIGSERIAL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    action TEXT,
    user_id INT,
    clinic_id INT,
    PRIMARY KEY (audit_id, timestamp)
) PARTITION BY RANGE (timestamp);

-- Example: Automatic Partitioning for 2026 Q1
CREATE TABLE security_audit_2026_q1 PARTITION OF security_audit
FOR VALUES FROM ('2026-01-01') TO ('2026-04-01');
```

#### 2.3 Role & Permission Matrix UI

```python
# backend/app/modules/auth/mfa.py

class MFASetup:
    """TOTP-based MFA using pyotp."""

    async def generate_secret(self, user_id: int) -> dict:
        """Generate TOTP secret and QR code URL."""
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name="OpenHeart Cyprus"
        )
        return {
            "secret": secret,  # Store encrypted
            "qr_url": provisioning_uri
        }

    async def verify_code(self, user_id: int, code: str) -> bool:
        """Verify TOTP code."""
        secret = await get_user_mfa_secret(user_id)
        totp = pyotp.TOTP(secret)
        return totp.verify(code)
```

**MFA Endpoints**:

| Method | Endpoint                  | Description                          |
| ------ | ------------------------- | ------------------------------------ |
| POST   | `/api/me/mfa/setup`       | Start MFA setup, get QR code         |
| POST   | `/api/me/mfa/verify`      | Verify code, enable MFA              |
| POST   | `/api/auth/mfa/challenge` | Verify MFA during login              |
| DELETE | `/api/me/mfa`             | Disable MFA (requires verification)  |

- **Role Customization**: A visual matrix where admins can see exactly what `CARDIOLOGIST` vs `NURSE` can access.
- **Emergency Access (Break-Glass)**: Special UI for temporary permission elevation (logged as high-priority audit events).

---

### Phase 3: Imaging Integration (Week 3-4)

**Objective**: View Echo/Angio studies from DICOM.

#### 3.1 DICOM Service Layer

Create `backend/app/integrations/dicom/`:

```python
# service.py
class DicomService:
    """Interface with Orthanc via DICOMweb."""

    async def search_studies(
        self,
        patient_id: Optional[str] = None,
        modality: Optional[str] = None,
        date_range: Optional[tuple[date, date]] = None
    ) -> list[DicomStudy]:
        """Query studies from Orthanc."""
        pass

    async def get_study_metadata(self, study_uid: str) -> dict:
        """Get detailed study metadata."""
        pass

    async def get_viewer_url(self, study_uid: str) -> str:
        """Generate OHIF viewer URL."""
        pass
```

#### 3.2 OHIF Viewer Integration

```bash
frontend/src/app/
├── viewer/
│   └── page.tsx          # Standalone OHIF viewer page
└── patients/[id]/imaging/
    └── page.tsx          # Patient's imaging studies
```

- **Seamless Overlay**: The OHIF viewer will open in a high-performance "Cinema Mode" overlay, dimming the rest of the EMR to focus on the study.
- **Side-by-Side Comparison**: Allow two studies (e.g., current Echo vs. 6 months ago) to be viewed side-by-side with synchronized scrolling.
- **Annotation Overlay**: Measurements made in OHIF (e.g., LVIDd) will visually "fly" into the EMR form when saved.

**Implementation**: Use the OHIF v3 viewer with a custom OpenHeart theme to match our glassmorphism aesthetics.

#### 3.3 Advanced Cardiology Imaging Specs

- **Modality Worklist (MWL)**: Automated patient data sync with Echo/Cath machines to prevent manual entry errors. Echo machine queries Orthanc via C-FIND.
- **Cine-Loop Optimization**: Cardiology studies (Echo/Angio) contain high-frame-rate loops. Use WADO-RS streaming (`multipart/related`) to stream frames without loading entire files.
- **Cardiology Modalities (Standardized)**:
  - **US**: Echocardiogram (TTE/TEE)
  - **XA**: X-Ray Angiography (Coronary/PCI)
  - **CT/MR**: Cardiac CT/MRI

#### 3.4 Structured Report (DICOM SR) Import

```python
async def import_echo_measurements(study_uid: str) -> dict:
    """
    Parse DICOM SR (0040,A730) to extract Echo measurements.

    Returns:
        {
            "lvef": 55,
            "lvidd": 48,
            "lvids": 32,
            "la_size": 38,
            # ... etc
        }
    """
    pass
```

- **Metadata Support**: Extract tags like (0018,0010) Contrast Agent for Angio and (0018,1020) Software Versions (e.g., GE EchoPAC).
- **Auto-Extraction Hub**: A specialized panel that detects measurements (LVEF, Volumes, Pressures) from DICOM SR files.
- **Approval Workflow**: Doctors see a list of extracted values and "Approve All" or "Edit" before they are committed to the clinical note.
- **Trend Visualization**: Extracted measurements automatically update "Trend Lines" in the patient profile (e.g., LVEF over the last 3 visits).

#### 3.4 Password Reset Flow (Functional)

```bash
frontend/src/app/
├── forgot-password/
│   └── page.tsx          # Request reset email
└── reset-password/
    └── page.tsx          # Set new password
```

**Password Reset Endpoints**:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/password/reset-request` | Send reset email |
| POST | `/api/auth/password/reset` | Reset with token |
| PUT | `/api/auth/password/change` | Change password (logged in) |

---

### Phase 4: Gesy Workflow (Week 4-5)

**Objective**: Enable claims, referrals, e-Prescriptions.

#### 4.1 Referral Management & Beneficiary Verification

```python
class BeneficiaryStatus(BaseModel):
    is_active: bool
    personal_doctor_id: Optional[str]
    coverage_start_date: date

async def verify_gesy_beneficiary(patient_id: str) -> BeneficiaryStatus:
    """Check active coverage before initiating specialist encounter."""
    pass
```

1. **Gatekeeping**: System verifies referral from Personal Doctor (PD) using `referral_id`.
2. **Clinical Summary**: Closing an encounter requires submitting a summary report back to Gesy to mark the referral as "Closed".

#### 4.2 FHIR R4 Interoperability

To ensure national and international compatibility:

- **Patient Resource**: Map all demographics to FHIR R4 standard.
- **Observations (Cardiology LOINC)**:
  - **LVEF**: 10230-1
  - **BP Panel**: 85354-9
  - **Heart Rate**: 8867-4
- **GDPR Portability**: Support `$everything` operation for full patient data export in FHIR JSON format.

#### 4.3 e-Prescription (HIO / Gesy)

```python
class Prescription(BaseModel):
    patient_id: int
    prescriber_id: int
    medications: list[PrescribedMedication]
    diagnosis_codes: list[str]  # Justification

class PrescribedMedication(BaseModel):
    medication_name: str
    atc_code: str  # Anatomical Therapeutic Chemical
    hio_id: str  # Gesy medication ID
    dosage: str
    frequency: str
    duration_days: int
    quantity: int
    instructions: str
    substitution_allowed: bool
```

- **ATC Search**: Search medications by name or ATC code with "Quick Action" buttons for common cardiology drugs (Statins, Beta-blockers).
- **Substitution Logic**: Visual toggle for "Substitution Allowed" with HIO-compliant warnings.
- **Digital Sign-off**: A premium "Signing" animation when the prescription is submitted to the Gesy HIO portal.

#### 4.4 Claims Console

- **Status Badges**: Real-time status for claims: `PENDING_HIO`, `ACCEPTED`, `REJECTED`, `PAID`.
- **Rejection Resolution**: If a claim is rejected (e.g., invalid ICD-10), a side-panel opens with "Suggestions" to fix and re-submit.

---

### Phase 5: Appointments & Scheduling (Week 5-6)

**Objective**: Basic scheduling system.

#### 5.1 Appointment Model

```python
class Appointment(BaseModel):
    appointment_id: int
    patient_id: int
    clinic_id: int
    provider_id: int

    scheduled_start: datetime
    scheduled_end: datetime
    duration_minutes: int

    appointment_type: str  # "new_patient", "follow_up", "echo", "stress_test"
    status: Literal["scheduled", "confirmed", "arrived", "in_progress", "completed", "no_show", "cancelled"]

    notes: Optional[str]
    referral_id: Optional[str]
```

#### 5.2 Calendar UI

```bash
frontend/src/app/
├── appointments/
│   ├── page.tsx          # Calendar view (day/week)
│   ├── new/
│   │   └── page.tsx      # Book appointment
│   └── [id]/
│       └── page.tsx      # Appointment details
└── patients/[id]/
    └── appointments/
        └── page.tsx      # Patient's appointments
```

**Calendar Requirements**:

- Day and week views
- Drag-and-drop rescheduling
- Color coding by appointment type
- Conflict detection
- Patient quick search to book

---

### Phase 6: Reports & Analytics (Week 6+)

**Objective**: Clinical and operational reporting.

#### 6.1 Clinical Reports

- Patient summary (for referrals)
- Encounter summary
- Medication list
- Lab results trend

#### 6.2 Operational Reports

- Patients seen per day/week/month
- Revenue by service type
- No-show rate
- Average wait time

#### 6.3 Quality Metrics

- LVEF improvement tracking
- Blood pressure control rates
- Medication adherence
- Readmission rates

---

## Database Migrations Required

### New Tables

```sql
-- 1. Patient table enhancements
ALTER TABLE patients ADD COLUMN id_type VARCHAR(20);
ALTER TABLE patients ADD COLUMN first_name_greek VARCHAR(100);
ALTER TABLE patients ADD COLUMN last_name_greek VARCHAR(100);
ALTER TABLE patients ADD COLUMN gesy_beneficiary_id VARCHAR(50);
ALTER TABLE patients ADD COLUMN personal_doctor_id VARCHAR(50);

-- 2. Encounters
CREATE TABLE encounters (
    encounter_id SERIAL PRIMARY KEY,
    patient_id INT REFERENCES patients(patient_id),
    clinic_id INT REFERENCES clinics(clinic_id),
    provider_id INT REFERENCES users(user_id),
    encounter_type VARCHAR(50) NOT NULL,
    encounter_date TIMESTAMPTZ NOT NULL,
    chief_complaint TEXT,
    status VARCHAR(50) NOT NULL,
    referral_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Appointments
CREATE TABLE appointments (
    appointment_id SERIAL PRIMARY KEY,
    patient_id INT REFERENCES patients(patient_id),
    clinic_id INT REFERENCES clinics(clinic_id),
    provider_id INT REFERENCES users(user_id),
    scheduled_start TIMESTAMPTZ NOT NULL,
    scheduled_end TIMESTAMPTZ NOT NULL,
    appointment_type VARCHAR(50),
    status VARCHAR(50) NOT NULL,
    notes TEXT,
    referral_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. User invitations (from user_management_plan.md)
CREATE TABLE user_invitations (
    invitation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    clinic_id INT REFERENCES clinics(clinic_id),
    invited_by INT REFERENCES users(user_id),
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    accepted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Password reset tokens
CREATE TABLE password_reset_tokens (
    token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INT REFERENCES users(user_id),
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Prescriptions
CREATE TABLE prescriptions (
    prescription_id SERIAL PRIMARY KEY,
    patient_id INT REFERENCES patients(patient_id),
    prescriber_id INT REFERENCES users(user_id),
    encounter_id INT REFERENCES encounters(encounter_id),
    status VARCHAR(50) NOT NULL,
    gesy_prescription_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE prescription_items (
    item_id SERIAL PRIMARY KEY,
    prescription_id INT REFERENCES prescriptions(prescription_id),
    medication_name VARCHAR(255) NOT NULL,
    atc_code VARCHAR(20),
    hio_id VARCHAR(50),
    dosage VARCHAR(100),
    frequency VARCHAR(100),
    duration_days INT,
    quantity INT,
    instructions TEXT,
    substitution_allowed BOOLEAN DEFAULT TRUE
);

-- 7. Code tables (ICD-10, LOINC, etc.)
CREATE TABLE icd10_codes (
    code VARCHAR(10) PRIMARY KEY,
    description_en TEXT NOT NULL,
    description_el TEXT,
    category VARCHAR(100)
);

CREATE TABLE loinc_codes (
    code VARCHAR(20) PRIMARY KEY,
    long_name TEXT NOT NULL,
    short_name VARCHAR(100),
    component VARCHAR(100)
);
```

#### 6.2 Healthcare Interoperability (FHIR Mapping)

Every OpenHeart entity must map to a corresponding FHIR R4 resource for national compliance:

| OpenHeart Entity  | FHIR R4 Resource    | Standardized Coding            |
| ----------------- | ------------------- | ------------------------------ |
| Patient Profile   | `Patient`           | Cyprus National ID OID         |
| Echo Measurements | `Observation`       | LOINC (e.g., 10230-1 for LVEF) |
| Clinical Consult  | `Encounter`         | ActCode (e.g., AMB)            |
| Lipid Panel       | `DiagnosticReport`  | LOINC (e.g., 2093-3 for Chol)  |
| Specialist Note   | `DocumentReference` | SNOMED CT                      |

---

## Clinical Decision Support (CDSS) Specs

All calculators must be validated against `cdss_algorithms.md`. **Required Inputs** for the high-priority "Magic Search" triggers:

- **CHA₂DS₂-VASc**: Triggered automatically if `Atrial Fibrillation` is in the patient's problem list.
- **GRACE**: Triggered in the Acute Care dashboard for `STEMI/NSTEMI` diagnoses.
- **PREVENT**: Annual trigger for primary prevention visits (includes eGFR/Kidney risk).

---

## Database Migrations & Retention Strategy

```

frontend/src/app/
├── (auth)/                       # Public auth pages
│   ├── login/
│   ├── forgot-password/
│   ├── reset-password/
│   └── invite/[token]/
│
├── (protected)/                  # Requires authentication
│   ├── dashboard/                # Role-specific dashboard
│   │
│   ├── patients/
│   │   ├── page.tsx             # Patient list
│   │   ├── new/                 # Add patient
│   │   └── [id]/
│   │       ├── page.tsx         # Patient profile
│   │       ├── timeline/        # History
│   │       ├── notes/           # Clinical notes
│   │       ├── imaging/         # DICOM studies
│   │       ├── labs/            # Lab results
│   │       ├── medications/     # Medication list
│   │       ├── appointments/    # Scheduling
│   │       └── referrals/       # Gesy referrals
│   │
│   ├── encounters/
│   │   ├── page.tsx             # Today's encounters
│   │   └── [id]/                # Encounter details
│   │
│   ├── appointments/
│   │   ├── page.tsx             # Calendar
│   │   └── new/                 # Book appointment
│   │
│   ├── cdss/
│   │   ├── page.tsx             # Calculator selection
│   │   ├── grace/
│   │   ├── cha2ds2vasc/
│   │   └── hasbled/
│   │
│   ├── viewer/                   # OHIF DICOM viewer
│   │
│   ├── prescriptions/
│   │   └── new/                 # Write prescription
│   │
│   ├── referrals/
│   │   ├── incoming/            # Received referrals
│   │   └── [id]/                # Referral details
│   │
│   ├── reports/
│   │   ├── clinical/            # Patient reports
│   │   └── operational/         # Clinic metrics
│   │
│   ├── admin/                    # Admin only
│   │   ├── users/
│   │   │   ├── page.tsx         # User list
│   │   │   ├── invite/          # Invite user
│   │   │   └── [id]/            # Edit user
│   │   ├── clinic/              # Clinic settings
│   │   └── audit/               # Audit logs
│   │
│   └── profile/
│       ├── page.tsx             # My profile
│       └── security/            # Password, MFA
│
├── api/
│   └── auth/[...nextauth]/      # NextAuth
│
└── middleware.ts                 # Route protection

```

---

## API Endpoint Summary

### Authentication (`/api/auth/`)

- POST `/login` ✅ (exists)
- POST `/refresh` ✅ (exists)
- POST `/logout` ✅ (exists)
- POST `/mfa/challenge` ❌ (needs implementation)
- POST `/password/reset-request` ❌
- POST `/password/reset` ❌

### Patients (`/api/patients/`)

- GET `/` ❌ (needs implementation)
- POST `/` ❌
- GET `/{id}` ❌
- PUT `/{id}` ❌
- DELETE `/{id}` ❌
- GET `/{id}/timeline` ❌
- GET `/search` ❌

### Encounters (`/api/encounters/`)

- GET `/` ❌
- POST `/` ❌
- GET `/{id}` ❌
- PUT `/{id}` ❌
- POST `/{id}/complete` ❌

### Clinical Notes (`/api/notes/`)

- ✅ Full CRUD exists (backend/app/modules/notes/)

### CDSS (`/api/cdss/`)

- POST `/grace` ✅ (exists)
- POST `/cha2ds2vasc` ✅ (exists)
- POST `/hasbled` ✅ (exists)

### DICOM (`/api/dicom/`)

- GET `/studies` ❌ (needs implementation)
- GET `/studies/{uid}` ❌
- GET `/studies/{uid}/viewer-url` ❌

### Gesy (`/api/gesy/`)

- GET `/beneficiary/{id}` ⚠️ (mock exists)
- GET `/referral/{id}` ⚠️
- POST `/referral` ⚠️
- POST `/claim` ⚠️
- POST `/prescription` ⚠️

### Appointments (`/api/appointments/`)

- GET `/` ❌
- POST `/` ❌
- GET `/{id}` ❌
- PUT `/{id}` ❌
- DELETE `/{id}` ❌

### Admin (`/api/admin/`)

- GET `/users` ❌
- POST `/users/invite` ❌
- GET `/users/{id}` ❌
- PUT `/users/{id}` ❌
- DELETE `/users/{id}` ❌
- GET `/invitations` ❌
- DELETE `/invitations/{id}` ❌

---

## Testing Strategy

### Unit Tests

- All CDSS calculations (✅ exists - 40+ tests).
- RLS Policy Validation: Ensure `app.clinic_id` session variables correctly isolate data.
- DICOM SR Extraction: Validate parsing of Echo findings into Pydantic models.
- Patient validation rules
- Encounter state transitions
- Permission checks

### Integration Tests

- Full patient creation → RLS verification → Search.
- Encounter → Notes → CDSS → Prescription workflow.
- Referral Verification → Encounter → Summary Report → Claim Submission.
- Login → MFA → Dashboard flow

### E2E Tests (Playwright)

- Login with MFA → Accept Legal Terms.
- Global Search (Cmd+K) for patient by ARC/Cyprus ID.
- View Echo study in Cinema Mode overlay.
- Add new patient
- Create encounter and note
- Use CDSS calculator
- View DICOM study

---

## Development Priority Order

1. **Week 1**: Patient API + Patient List UI + Functional Dashboard
2. **Week 2**: Encounter System + Clinical Notes UI + CDSS Calculator UI
3. **Week 3**: User Management (Invitation, MFA, Password Reset)
4. **Week 4**: DICOM Integration + OHIF Viewer
5. **Week 5**: Gesy Workflow (Referrals, Claims)
6. **Week 6**: Appointments + Scheduling
7. **Week 7+**: Reports, Analytics, Polish

---

## Success Criteria

### Minimum Viable Product (MVP)

A cardiologist can:

1. ✅ Log in with MFA
2. ✅ See a useful dashboard
3. ✅ Search and find a patient
4. ✅ Add a new patient
5. ✅ Start an encounter/visit
6. ✅ Write a clinical note
7. ✅ Use CDSS calculators (GRACE, CHA₂DS₂-VASc, HAS-BLED)
8. ✅ View Echo studies (DICOM)
9. ✅ Write a prescription
10. ✅ Submit a Gesy claim

### Phase 1 Complete When

- Patient CRUD works end-to-end
- Notes can be created with cardiology templates
- CDSS calculators have working UI
- Dashboard shows relevant information

---

## Files to Create/Modify

### Backend (New)

| File                            | Purpose                   |
| ------------------------------- | ------------------------- |
| `modules/patient/schemas.py`    | Pydantic models           |
| `modules/patient/service.py`    | Business logic            |
| `modules/patient/router.py`     | API endpoints             |
| `modules/encounter/__init__.py` | Encounter module          |
| `modules/encounter/models.py`   | SQLAlchemy model          |
| `modules/encounter/schemas.py`  | Pydantic models           |
| `modules/encounter/service.py`  | Business logic            |
| `modules/encounter/router.py`   | API endpoints             |
| `modules/appointment/__init__.py`| Appointment module        |
| `modules/appointment/models.py` | SQLAlchemy model          |
| `modules/appointment/schemas.py`| Pydantic models           |
| `modules/appointment/service.py`| Business logic            |
| `modules/appointment/router.py` | API endpoints             |
| `modules/auth/invitation.py`    | Invitation logic          |
| `modules/auth/mfa.py`           | MFA setup/verify          |
| `modules/auth/password_reset.py`| Password reset            |
| `integrations/dicom/service.py` | DICOM service             |
| `integrations/dicom/router.py`  | DICOM endpoints           |

### Backend (Modify)

| File                     | Change                      |
| ------------------------ | --------------------------- |
| `main.py`                 | Register new routers        |
| `modules/patient/models.py` | Add Cyprus-specific fields  |

### Frontend (New)

| File                          | Purpose                     |
| ----------------------------- | --------------------------- |
| `app/patients/page.tsx`       | Patient list                |
| `app/patients/new/page.tsx`   | Add patient                 |
| `app/patients/[id]/page.tsx`  | Patient profile             |
| `app/patients/[id]/notes/page.tsx` | Patient notes          |
| `app/patients/[id]/imaging/page.tsx` | Patient imaging      |
| `app/cdss/page.tsx`           | Calculator selection        |
| `app/cdss/grace/page.tsx`     | GRACE calculator            |
| `app/cdss/cha2ds2vasc/page.tsx` | CHA₂DS₂-VASc calculator   |
| `app/cdss/hasbled/page.tsx`   | HAS-BLED calculator         |
| `app/appointments/page.tsx`   | Calendar view               |
| `app/admin/users/page.tsx`    | User management             |
| `app/admin/users/invite/page.tsx` | Invite user             |
| `app/viewer/page.tsx`         | OHIF viewer                 |
| `app/forgot-password/page.tsx` | Password reset request     |
| `app/reset-password/page.tsx` | Password reset form         |
| `app/invite/[token]/page.tsx` | Accept invitation           |

### Frontend (Modify)

| File | Change |
|------|--------|
| `app/dashboard/page.tsx` | Complete redesign |
| `middleware.ts` | Add new protected routes |

### Migrations (New)

| Migration | Tables |
|-----------|--------|
| `20260122_001_encounters.py` | encounters |
| `20260122_002_appointments.py` | appointments |
| `20260122_003_user_invitations.py` | user_invitations, password_reset_tokens |
| `20260122_004_prescriptions.py` | prescriptions, prescription_items |
| `20260122_005_code_tables.py` | icd10_codes, loinc_codes |
| `20260122_006_patient_enhancements.py` | Alter patients table |

---

## Conclusion

This plan addresses the fundamental oversight: **a cardiologist needs to work with patients, not just log in**.

The implementation is organized around clinical workflows:

1. Find/add patient
2. Document encounter
3. Use decision support tools
4. Review imaging
5. Prescribe treatment
6. Submit for reimbursement

Each phase builds on the previous, ensuring the system is always usable at each checkpoint.
