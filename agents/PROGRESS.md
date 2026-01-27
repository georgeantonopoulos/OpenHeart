# OpenHeart Cyprus - Implementation Progress

> Last updated: 2026-01-22

## Overview

Transforming OpenHeart Cyprus from an authentication-only shell into a **fully functional cardiology EMR**. The goal is for a cardiologist to log in and perform daily work: find patients, document encounters, use risk calculators, view imaging, and submit claims.

## Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14+ (App Router), TypeScript, Tailwind CSS |
| Backend | FastAPI (Python 3.11), Pydantic, SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Imaging | Orthanc (DICOM Server) + OHIF Viewer |
| DevOps | Docker Compose |

---

## Phase Completion Status

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 0** | Patient Management | ✅ Complete |
| **Phase 1** | Clinical Workflow (Encounters, Notes, CDSS) | ✅ Complete |
| **Phase 1.3** | Advanced CDSS (PREVENT, EuroSCORE II) | ✅ Complete |
| **Phase 2** | User Management (Invitations, MFA, Password Reset) | ✅ Complete |
| **Phase 2.4** | Enhanced Security (Sessions, Argon2id) | ✅ Complete |
| **Phase 3** | DICOM/Imaging Integration | ✅ Complete |
| **Phase 3.5** | Modality Worklist (MWL) | ✅ Complete |
| **Phase 4** | Gesy Integration | ✅ Complete |
| **Phase 4.5** | Medical Coding Tables | ✅ Complete |
| **Phase 5** | Appointments Module | ✅ Complete |

---

## Completed Work Details

### Phase 0: Patient Management ✅

**Backend:**

- `backend/app/modules/patient/service.py` - CRUD with PII encryption
- `backend/app/modules/patient/router.py` - REST endpoints
- `backend/app/modules/patient/schemas.py` - Pydantic models

**Frontend:**

- `frontend/src/app/patients/page.tsx` - Patient list with search
- `frontend/src/app/patients/new/page.tsx` - Add patient form
- `frontend/src/app/patients/[id]/page.tsx` - Patient profile
- `frontend/src/lib/api/patients.ts` - API client

### Phase 1: Clinical Workflow ✅

**Backend:**

- `backend/app/modules/encounter/` - Encounter service and router
- `backend/app/modules/notes/` - Clinical notes (already existed)

**Frontend:**

- `frontend/src/app/patients/[id]/notes/` - Notes list, create, view
- `frontend/src/app/cdss/` - Calculator selection
- `frontend/src/app/cdss/grace/page.tsx` - GRACE Score
- `frontend/src/app/cdss/cha2ds2vasc/page.tsx` - CHA₂DS₂-VASc
- `frontend/src/app/cdss/hasbled/page.tsx` - HAS-BLED

### Phase 1.3: Advanced CDSS ✅

**Backend:**

- `backend/app/modules/cardiology/cdss/prevent.py` - PREVENT equations
- `backend/app/modules/cardiology/cdss/euroscore.py` - EuroSCORE II

**Frontend:**

- `frontend/src/app/cdss/prevent/page.tsx` - PREVENT calculator
- `frontend/src/app/cdss/euroscore/page.tsx` - EuroSCORE II wizard

### Phase 2: User Management ✅

**Backend:**

- `backend/app/modules/auth/invitation.py` - Invitation system
- `backend/app/modules/auth/mfa.py` - MFA setup/verify
- `backend/app/modules/auth/password_reset.py` - Password reset flow

**Frontend:**

- `frontend/src/app/invite/[token]/page.tsx` - Accept invitation wizard
- `frontend/src/app/admin/users/` - User list and invite
- `frontend/src/app/forgot-password/page.tsx` - Request reset
- `frontend/src/app/reset-password/page.tsx` - Set new password
- `frontend/src/app/profile/security/page.tsx` - MFA setup

### Phase 2.4: Enhanced Security ✅

**Backend:**

- `backend/app/modules/auth/session_manager.py` - Server-side sessions
- `backend/app/core/security.py` - Argon2id hashing

**Frontend:**

- `frontend/src/app/profile/sessions/page.tsx` - Active sessions management

### Phase 3: DICOM/Imaging ✅

**Backend:**

- `backend/app/integrations/dicom/service.py` - Orthanc DICOMweb client
- `backend/app/integrations/dicom/router.py` - DICOM endpoints

**Frontend:**

- `frontend/src/app/patients/[id]/imaging/page.tsx` - Patient studies
- `frontend/src/app/viewer/page.tsx` - OHIF viewer integration
- `frontend/src/lib/api/imaging.ts` - API client

### Phase 3.5: Modality Worklist (MWL) ✅

**Backend:**

- `backend/app/integrations/dicom/mwl_models.py` - ScheduledProcedure, WorklistStation
- `backend/app/integrations/dicom/mwl_service.py` - Scheduling, worklist queries
- `backend/app/integrations/dicom/mwl_router.py` - REST endpoints at `/api/procedures`

**Frontend:**

- `frontend/src/lib/api/procedures.ts` - API client with types
- `frontend/src/components/procedures/StationSelector.tsx` - Equipment picker
- `frontend/src/app/procedures/schedule/page.tsx` - 3-step scheduling wizard
- `frontend/src/app/procedures/worklist/page.tsx` - Worklist view with filters
- `frontend/src/app/procedures/page.tsx` - Index redirect

**Navigation Updates:**

- Added "Worklist" link to main nav in `DashboardContent.tsx`
- Added "Schedule" to QuickActions in dashboard

### Phase 4: Gesy Integration ✅

**Backend:**

- `backend/app/core/permissions.py` (modified) - Added GESY_BENEFICIARY_READ, GESY_REFERRAL_READ/WRITE, GESY_CLAIM_READ/WRITE
- `backend/app/integrations/gesy/service.py` - Thin wrapper around IGesyProvider for DI
- `backend/app/integrations/gesy/router.py` - 11 endpoints: beneficiary, referrals, claims, specialties

**Frontend:**

- `frontend/src/lib/api/gesy.ts` - API client with types for all Gesy endpoints
- `frontend/src/app/referrals/incoming/page.tsx` - Received referrals list with filters
- `frontend/src/app/referrals/[id]/page.tsx` - Referral details with close action
- `frontend/src/app/billing/claims/page.tsx` - Claims console with rejection resolution panel

**Navigation Updates:**

- Added "Referrals" link to main nav in `DashboardContent.tsx`
- Added "Referrals" quick action in `QuickActions.tsx`

### Phase 4.5: Medical Coding Tables ✅

**Backend:**

- `backend/alembic/versions/20240102_0002_medical_coding_tables.py` - Migration with `unaccent` extension, 7 tables, GIN FTS indexes
- `backend/app/modules/coding/__init__.py`
- `backend/app/modules/coding/models.py` - SQLAlchemy models (ICD10, ICPC2, LOINC, ATC, CPT, HIO, GesyMedication)
- `backend/app/modules/coding/schemas.py` - Pydantic response schemas
- `backend/app/modules/coding/service.py` - Greek-aware search with `func.unaccent()` accent normalization
- `backend/app/modules/coding/router.py` - Search endpoints for all code types + medications
- `backend/scripts/seed_codes.py` - 53 ICD-10, 41 CPT, 20 HIO, 57 ATC, 30 LOINC, 57 Gesy medications

**Database tables:**

- `icd10_codes` - ICD-10 diagnosis codes (EN/EL descriptions)
- `icpc2_codes` - ICPC-2 (Primary Care)
- `loinc_codes` - Lab/Observation codes
- `atc_codes` - Medication classification codes
- `cpt_codes` - Procedure codes
- `hio_service_codes` - Cyprus HIO specific services with EUR pricing
- `gesy_medications` - HIO pharmaceutical products (brand/generic, hio_product_id → ATC mapping)

**Frontend:**

- `frontend/src/lib/api/coding.ts` - API client for all code types
- `frontend/src/components/coding/CodeSearchModal.tsx` - Generic modal with TypeScript generics
- `frontend/src/components/coding/DiagnosisPicker.tsx` - ICD-10 search (billable indicator, EN/EL)
- `frontend/src/components/coding/ProcedurePicker.tsx` - CPT/HIO toggle with pricing
- `frontend/src/components/coding/MedicationPicker.tsx` - Brand name search with pre-auth badge

### Phase 5: Appointments Module ✅

**Backend:**

- `backend/app/core/permissions.py` (modified) - Added APPOINTMENT_READ/WRITE/DELETE
- `backend/alembic/versions/20240103_0003_appointments.py` - Table with RLS, conflict detection indexes
- `backend/app/modules/appointment/__init__.py`
- `backend/app/modules/appointment/models.py` - AppointmentType/Status enums, EXPECTED_DURATIONS
- `backend/app/modules/appointment/schemas.py` - Create/Update/Response schemas, duration warning logic
- `backend/app/modules/appointment/service.py` - CRUD, conflict detection, slot finder, encounter handover
- `backend/app/modules/appointment/router.py` - CRUD + check-in, start-encounter, available slots

**Key Features:**

- Conflict detection: prevents overlapping appointments for same provider
- Duration warnings: non-blocking alert when scheduled < 75% of expected duration
- Encounter handover: `POST /appointments/{id}/start-encounter` creates linked encounter
- Available slots: finds gaps in provider's schedule for a given date

**Frontend:**

- `frontend/src/lib/api/appointments.ts` - Full API client with status colors, type formatters
- `frontend/src/components/calendar/WeekView.tsx` - 7-day grid (8:00-17:00) with today highlight
- `frontend/src/components/calendar/DayView.tsx` - Detail view with Check In/Start Encounter buttons
- `frontend/src/app/appointments/page.tsx` - Calendar with week/day toggle, date navigation
- `frontend/src/app/appointments/new/page.tsx` - 3-step booking wizard with duration warnings

---

## Router Registration

All routers registered in `backend/app/main.py`:

```python
app.include_router(auth_router, prefix="/api", tags=["Authentication"])
app.include_router(cdss_router, prefix="/api/cdss", tags=["CDSS"])
app.include_router(notes_router, prefix="/api", tags=["Clinical Notes"])
app.include_router(patient_router, prefix="/api", tags=["Patients"])
app.include_router(encounter_router, prefix="/api", tags=["Encounters"])
app.include_router(dicom_router, prefix="/api", tags=["DICOM/Imaging"])
app.include_router(mwl_router, prefix="/api", tags=["Modality Worklist"])
app.include_router(gesy_router, prefix="/api", tags=["Gesy"])
app.include_router(coding_router, prefix="/api", tags=["Medical Coding"])
app.include_router(appointment_router, prefix="/api", tags=["Appointments"])
```

---

## Database Migrations

| Migration | Description |
| --------- | ----------- |
| `0001_initial` | Core tables (users, clinics, patients, encounters, notes) |
| `0002_medical_coding_tables` | pg_trgm, unaccent extensions; 7 coding tables with FTS indexes |
| `0003_appointments` | Appointments table with RLS, conflict detection indexes |

---

## Testing Commands

```bash
# Backend tests
cd backend && pytest

# Frontend dev server
cd frontend && npm run dev

# Full stack with Docker
docker compose up

# Seed medical codes (after migration)
cd backend && python scripts/seed_codes.py
```

---

## Key Integration Points

1. **Gesy Medication → e-Prescription**: `gesy_medications.hio_product_id` maps to specific pharmaceutical products (HIO API requires this, not just ATC codes)
2. **Greek Text Search**: `unaccent` extension normalizes accents ("Καρδιά" matches "καρδια")
3. **Appointment → Encounter Handover**: "Start Encounter" creates linked encounter, pre-populates patient info and referral
4. **Duration Warnings**: Type-specific expected durations alert when scheduling appears too short
