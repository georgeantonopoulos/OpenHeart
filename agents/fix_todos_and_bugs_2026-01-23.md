# Fix TODOs and Bugs Plan

## Issues Identified

### TODOs (5 found)

1. `frontend/src/lib/auth-options.ts:11` - Docker URL configuration note
2. `frontend/src/lib/api/auth.ts:7` - Fixed bug note leftover
3. `frontend/src/app/layout.tsx:11` - Missing favicon (but `favicon.svg` already exists in `public/`)
4. `frontend/src/app/procedures/worklist/page.tsx:1-3` - Endpoint returns 500 (no table)
5. `backend/app/integrations/dicom/mwl_router.py:22-24` - No Alembic migration for `scheduled_procedures`

### Bugs (5 reported)

1. Create Patient: succeeds in DB but shows 500 error
2. Edit Patient: frontend page missing entirely
3. Create Note: fails (likely same pattern as patient)
4. Appointment creation: only accepts numeric Patient ID
5. Notifications: fake red badge on non-functional bell icon

---

## Root Cause Analysis

### Bug #6 & #8: Patient/Note creation "succeeds but shows error"

**Root cause (Patient):** In `backend/app/modules/patient/service.py:122-138`, the PII object is added to the session via FK column assignment (`PatientPII(patient_id=patient.patient_id)`), NOT via relationship assignment (`patient.pii = pii`). The relationship is never populated in-memory. After commit + refresh, when `build_patient_response` accesses `patient.pii` (line 461), it triggers async lazy loading which raises `MissingGreenlet` in async SQLAlchemy → 500 error. The patient is already committed to DB at that point.

**Root cause (Note):** In `backend/app/modules/notes/router.py:93-107`, after the note is created and committed, `log_access()` is called. This commits a SECOND time in the same session. If `log_access` encounters any issue (e.g., the `ip_address` column uses PostgreSQL `INET` type but the fallback value `"unknown"` is invalid), it raises an exception AFTER the note is persisted → user sees 500 but note exists. Additionally, the frontend `onError` handler shows `error.message` ("API Error: 500") instead of the useful `error.detail`.

### Bug #7: Edit Patient fails

**Root cause:** `frontend/src/app/patients/[id]/edit/page.tsx` doesn't exist. The PatientHeader has an "Edit" link to this route, but the page was never created. Backend `PUT /api/patients/{id}` endpoint is fully implemented.

---

## Implementation Plan

### 1. Remove stale TODO comments (auth-options.ts, auth.ts)

- `auth-options.ts:11` - Code already uses env var correctly. Remove TODO.
- `auth.ts:7` - Bug was already fixed. Remove comment.

### 2. Fix favicon TODO (layout.tsx)

- `favicon.svg` already exists in `frontend/public/`
- Remove the TODO comment from `layout.tsx`
- Ensure `metadata` in layout exports proper favicon reference (Next.js App Router handles `/favicon.svg` automatically if it's in public)

### 3. Fix Patient creation 500 (backend)

**File:** `backend/app/modules/patient/service.py`

In `create_patient()` (around line 133), after creating the PII object, explicitly set the relationship:

```python
pii = PatientPII(patient_id=patient.patient_id, ...)
self.db.add(pii)
patient.pii = pii  # <-- ADD THIS: populate relationship in-memory
await self.db.commit()
await self.db.refresh(patient)
```

This ensures `build_patient_response` can access `patient.pii` without triggering async lazy loading.

### 4. Fix Note creation failure (backend)

**File:** `backend/app/modules/notes/router.py`

Two fixes:

1. Wrap `log_access` in try/except so audit logging failure doesn't crash the response:

```python
try:
    await service.log_access(...)
except Exception:
    logger.warning("Failed to log note access", exc_info=True)
```

1. Change `ip_address` fallback from `"unknown"` to `"0.0.0.0"` (valid INET value):

```python
ip_address=request.client.host if request.client else "0.0.0.0",
```

### 5. Fix frontend error handling (patient + note forms)

**Files:**

- `frontend/src/app/patients/new/page.tsx`
- `frontend/src/app/patients/[id]/notes/new/page.tsx`

Import `ApiClientError` and extract `.detail`:

```typescript
onError: (error: Error) => {
  const message = 'detail' in error ? (error as ApiClientError).detail : error.message;
  setErrors({ form: message });
},
```

### 6. Create Edit Patient page

**File:** `frontend/src/app/patients/[id]/edit/page.tsx` (NEW)

- Fetch patient data using `getPatient()`
- Pre-populate form with current values (first_name, last_name, phone, email, gender, etc.)
- Submit via `updatePatient()` from `@/lib/api/patients`
- Handle validation errors (422) with field-level error display
- Redirect to `/patients/{id}` on success
- Match existing form styling from `patients/new/page.tsx`

### 7. Fix Appointment: Add patient search

**File:** `frontend/src/app/appointments/new/page.tsx`

Replace the numeric Patient ID input in Step 1 with a searchable patient selector:

- Add a text input for patient name/MRN search
- Debounce input (300ms) and call `searchPatients()` from `@/lib/api/patients`
- Show results as a dropdown list (name, MRN, DOB for identification)
- On selection, store `patient_id` and display patient name
- Allow clearing selection to search again
- Remove the numeric-only input type restriction

### 8. Remove fake notification badge

**File:** `frontend/src/app/dashboard/DashboardContent.tsx` (line 170)

Remove the red badge dot:

```html
<!-- REMOVE THIS LINE -->
<span className="absolute top-1.5 right-1.5 w-2 h-2 bg-rose-500 rounded-full" />
```

### 9. Create migration for scheduled_procedures

**File:** `backend/alembic/versions/20240107_0007_scheduled_procedures.py` (NEW)

Tables to create (from `mwl_models.py`):

- `scheduled_procedures` - with all columns, FKs, and indexes
- `worklist_stations` - with all columns, FKs, and indexes

Remove TODO comments from:

- `frontend/src/app/procedures/worklist/page.tsx` (lines 1-3)
- `backend/app/integrations/dicom/mwl_router.py` (lines 22-24)

---

## Files Summary

| File | Action |
|------|--------|
| `frontend/src/lib/auth-options.ts` | Remove TODO comment |
| `frontend/src/lib/api/auth.ts` | Remove TODO comment |
| `frontend/src/app/layout.tsx` | Remove TODO comment |
| `frontend/src/app/procedures/worklist/page.tsx` | Remove TODO comment |
| `backend/app/integrations/dicom/mwl_router.py` | Remove TODO comment |
| `backend/app/modules/patient/service.py` | Fix: set `patient.pii = pii` |
| `backend/app/modules/notes/router.py` | Fix: wrap log_access, fix INET fallback |
| `frontend/src/app/patients/new/page.tsx` | Fix error handling |
| `frontend/src/app/patients/[id]/notes/new/page.tsx` | Fix error handling |
| `frontend/src/app/patients/[id]/edit/page.tsx` | **CREATE**: patient edit form |
| `frontend/src/app/appointments/new/page.tsx` | Replace ID input with patient search |
| `frontend/src/app/dashboard/DashboardContent.tsx` | Remove fake notification badge |
| `backend/alembic/versions/20240107_0007_scheduled_procedures.py` | **CREATE**: migration |

---

## Verification

1. `grep -r "TODO" frontend/src/lib/ frontend/src/app/layout.tsx frontend/src/app/procedures/ backend/app/integrations/dicom/mwl_router.py` → no results
2. Create patient → should redirect to patient profile without error
3. Edit patient → form pre-populated → submit → redirects back to profile
4. Create note → should redirect to note detail without error
5. Create appointment → type patient name → see search results → select → proceed
6. Dashboard → bell icon has no red badge
7. `docker compose up --build` → worklist page loads without 500
