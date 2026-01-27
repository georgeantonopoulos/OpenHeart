# Implementation Plan: High-Priority Gaps

## Step 0: Authentication Blocker (Required First)

The auth service layer is already built (login, MFA, invitations, password reset, sessions). The blocker is missing DB tables and seed data.

### What Already Works (No Changes Needed)

| Component | Location |
|-----------|----------|
| Users/Clinics/Roles DB tables | `alembic/versions/20240101_0001` (lines 41-116) |
| Login endpoint (lockout + audit) | `modules/auth/router.py:69` |
| Token refresh | `modules/auth/router.py:153` |
| Logout + Redis blacklist | `modules/auth/router.py:250` |
| Invitation flow (create/validate/accept) | `modules/auth/router.py:309-487` |
| MFA (setup/verify/disable/backup) | `modules/auth/router.py:504-712` |
| Password reset (request/validate/reset) | `modules/auth/router.py:727+` |
| Email service (dev console fallback) | `core/email.py` (untracked) |
| Redis token blacklisting | `core/redis.py` (untracked) |
| Auth router registered | `main.py:180` |

### What's Missing (3 sub-steps)

#### 0.1: Alembic migration for auth-support tables

**New file:** `backend/alembic/versions/20240104_0004_auth_support_tables.py` (revision "0004", revises "0003")

Create 3 tables whose ORM models already exist but have no migration:

1. **`user_invitations`** — Model: `modules/auth/models.py:35`
   - invitation_id (PK), token (unique, indexed), email, first_name, last_name
   - clinic_id (FK→clinics), role, title, specialty, license_number
   - status, invited_by_user_id (FK→users), expires_at
   - accepted_at, accepted_user_id (FK→users), message, created_at
   - Indexes: email, status, clinic_id

2. **`password_reset_tokens`** — Model: `modules/auth/models.py:142`
   - token_id (PK), token (unique, indexed), user_id (FK→users)
   - is_used, used_at, expires_at, created_at

3. **`user_sessions`** — Model: `modules/auth/session_manager.py:23`
   - id (UUID PK), user_id (FK→users, indexed), token_hash (unique)
   - ip_address, user_agent, device_name
   - created_at, last_activity, expires_at, is_revoked, revoked_reason

#### 0.2: Create development seed script

**New file:** `backend/app/core/seed.py`

- Guard: only runs when `settings.environment == "development"`
- Guard: only runs when users table is empty
- Creates default clinic: name="OpenHeart Dev Clinic", code="OHC"
- Creates seed users (password hashed with `hash_password()` from `core/security.py`):
  - `admin@openheart.local` / `DevAdmin123!` → SYSTEM_ADMIN
  - `cardiologist@test.local` / `TestUser123!` → CARDIOLOGIST
  - `nurse@test.local` / `TestUser123!` → NURSE
  - `reception@test.local` / `TestUser123!` → RECEPTIONIST
- Creates `user_clinic_roles` entries (is_primary_clinic=True)
- Logs created credentials to console

**Integration:** Add startup call in `backend/app/main.py` lifespan/startup event

#### 0.3: Connect frontend login page

**File:** `frontend/src/app/page.tsx`

- Wire existing login form to `POST /api/auth/login`
- Store returned JWT via next-auth (already configured per git history)
- Redirect to `/dashboard` on success
- Display error messages on 401/403

---

## Step 1: Note Access Audit (no new tables)

**File:** `backend/app/core/audit.py`

- Add `_insert_note_access_to_db()` fire-and-forget function (follows `_insert_audit_to_db` at line 68)
- Import `NoteAccessLog` from `app.modules.notes.models`
- Update `log_note_access()` (line 346) to call `asyncio.create_task(_insert_note_access_to_db(...))`
- NoteAccessLog model + table already exist

---

## Step 2: CDSS Audit Logging (new table + model)

**File to modify:**

- `backend/app/core/audit.py` — Add `CDSSAuditLog` ORM model + `_insert_cdss_audit_to_db()` + update `log_cdss_calculation()`

**New file:**

- `backend/alembic/versions/20240105_0005_cdss_audit_log.py` (revision "0005", revises "0004")

**CDSSAuditLog columns:** log_id (PK), calculation_type, patient_id, clinician_id, clinic_id, input_parameters (JSONB), calculated_score, risk_category, recommendation, timestamp. Partitioned yearly 2024-2040.

---

## Step 3: DICOM Study Linking (new model + migration)

**New files:**

- `backend/app/integrations/dicom/models.py` — `PatientStudyLink` model
- `backend/alembic/versions/20240106_0006_patient_study_links.py` (revision "0006", revises "0005")

**PatientStudyLink columns:** id (PK), study_instance_uid, patient_id (FK→patients), encounter_id (FK→encounters, nullable), clinic_id (FK→clinics), linked_by_user_id (FK→users), link_reason, study_date, study_description, modality, created_at. Unique on (study_instance_uid, patient_id).

**File to modify:**

- `backend/app/integrations/dicom/router.py` — Update `link_study_to_patient()` (line 218):
  - Add `db: AsyncSession` dependency
  - Check existing link (409 if duplicate)
  - Create `PatientStudyLink` with cached study metadata
  - Commit

---

## Step 4: Patient Studies Retrieval (depends on Step 3)

**File to modify:**

- `backend/app/integrations/dicom/router.py` — Rewrite `get_patient_studies()` (line 262):
  - Add `db: AsyncSession` dependency
  - Load patient + PII via `selectinload(Patient.pii)`
  - Decrypt Cyprus ID using `decrypt_pii()` from `app.core.encryption`
  - Query Orthanc with decrypted Cyprus ID as DICOM Patient ID
  - Query `PatientStudyLink` table for manually linked studies
  - Merge + deduplicate by study_instance_uid
  - Return sorted combined list

---

## Step 5: Echo SR Parsing (new module + dependency)

**Scope:** Common measurements only (LVEF, LV dimensions, diastolic basics, TAPSE).

**File to modify:**

- `backend/pyproject.toml` — Add `pydicom>=2.4.0`

**New file:**

- `backend/app/integrations/dicom/sr_parser.py`:
  - `parse_sr_dataset(ds: Dataset) -> Optional[EchoMeasurements]`
  - `_traverse_content_tree()` — Recursive SR content traversal
  - `_extract_numeric_measurement()` — NUM item extraction
  - LOINC/SNOMED concept code mapping
  - Coverage: LVEF, LVIDd/s, IVSd, LVPWd, EDV, ESV, E/A, E/e', DT, TAPSE
  - Graceful `None` for unrecognized fields

**File to modify:**

- `backend/app/integrations/dicom/service.py` — Update `get_echo_measurements()` (line 410):
  - Fetch DICOM SR via WADO-RS (`Accept: application/dicom`)
  - Parse with `pydicom.dcmread(BytesIO(response.content))`
  - Call `sr_parser.parse_sr_dataset(ds)`
  - Return fallback EchoMeasurements if parsing yields nothing

---

## Verification

0. **Auth:** `docker compose up --build` → seed users printed → `POST /api/auth/login` with `admin@openheart.local` / `DevAdmin123!` → returns JWT
1. **Note access audit:** Access note endpoint → check `note_access_log` table
2. **CDSS audit:** Run calculator → check `cdss_audit_log` table
3. **Study linking:** `POST /dicom/studies/{uid}/link` → row in `patient_study_links`
4. **Patient studies:** `GET /dicom/patients/{id}/studies` → combined results
5. **Echo parsing:** `GET /dicom/studies/{uid}/echo-measurements` with SR → populated measurements
6. **Regression:** `cd backend && pytest` — all existing tests pass
