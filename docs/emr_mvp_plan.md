# OpenHeart EMR MVP Plan: From CDSS Tool to Full Practice Management

## Context & Research Summary

This plan bridges the gap between OpenHeart (a cardiology-focused CDSS with modern stack) and the operational capabilities of mature EMR platforms like FreeMED and OpenEMR. The goal is to make OpenHeart a viable daily-driver for a Cypriot cardiologist running a private practice.

### What OpenHeart Already Has (Preserve These Strengths)
- **DICOM/OHIF Integration** - Superior to FreeMED's static file approach
- **Native CDSS** - 5 validated cardiac risk calculators (GRACE, CHA2DS2-VASc, HAS-BLED, PREVENT, EuroSCORE II)
- **Modern UX** - Next.js 14 + Tailwind + Shadcn vs. FreeMED's dated PHP interface
- **GDPR Compliance** - Encrypted PII, erasure lifecycle, audit logging
- **Gesy Adapter Pattern** - Ready for real HIO API swap
- **Appointment System** - Already has conflict detection, check-in, encounter handover
- **Encounter & Vitals** - Already tracks HR, BP, O2 sat, temp, BMI per encounter
- **Clinical Notes** - Version-controlled with attachments and FTS

### What's Missing (This Plan Addresses)
1. **Calendar UI** - Backend exists but frontend lacks day/week calendar views
2. **Prescription Module** - Entirely absent; critical for cardiology
3. **Revenue Cycle Backend** - Frontend UI exists but no API implementation
4. **Lab Interface** - No automated lab import; CDSS requires manual data entry
5. **Vitals Trending** - Data stored per encounter but no longitudinal visualization
6. **CDS-to-Action Workflow** - Risk calculators don't feed into prescriptions or orders

---

## Phase 1: Prescription Module (e-Prescribing)

**Rationale:** Anticoagulation and antiplatelet management is ~50% of a cardiologist's prescribing. Without this, OpenHeart cannot action CDSS recommendations.

### 1.1 Backend: Drug Reference Data

**Migration: `0009_prescriptions.py`**

```
Tables:
- drug_formulary: Local formulary based on Gesy drug list (already in ATC codes from migration 0002)
  - id, atc_code, trade_name, generic_name, form, strengths (JSONB),
    manufacturer, gesy_covered (bool), requires_prior_auth (bool)
  - Index on atc_code, generic_name for search

- prescriptions: Patient prescription records
  - id, patient_id (FK), encounter_id (FK), prescriber_id (FK), clinic_id (FK)
  - drug_formulary_id (FK, nullable - allows free-text for non-formulary drugs)
  - drug_name, atc_code, form, dosage, strength, quantity
  - frequency (ENUM: OD, BD, TDS, QDS, PRN, STAT, nocte, mane, custom)
  - frequency_custom (varchar, for custom schedules like "Mon/Wed/Fri")
  - route (ENUM: oral, sublingual, IV, IM, SC, topical, inhaled, transdermal)
  - duration_days (int, nullable for chronic meds)
  - refills_allowed (int), refills_used (int)
  - start_date, end_date (nullable)
  - status (ENUM: active, completed, discontinued, cancelled, on_hold)
  - discontinuation_reason (text, nullable)
  - is_chronic (bool) - for ongoing medications like statins
  - linked_diagnosis_icd10 (varchar) - ties Rx to diagnosis
  - notes (text) - prescriber notes
  - gesy_claim_id (FK, nullable) - for billing linkage
  - created_at, updated_at, deleted_at (soft delete)
  - Indexes: (patient_id, status), (patient_id, atc_code), (prescriber_id, created_at)

- prescription_interactions: Cached interaction alerts
  - id, prescription_id (FK), interacting_prescription_id (FK)
  - severity (ENUM: minor, moderate, major, contraindicated)
  - description (text), source (varchar)
  - acknowledged_by (FK user), acknowledged_at (timestamp)

- medication_history: Tracks all status changes
  - id, prescription_id (FK), previous_status, new_status
  - changed_by (FK user), changed_at, reason (text)
```

### 1.2 Backend: Prescription Service & API

**Location:** `backend/app/modules/prescription/`

```
prescription/
  __init__.py
  models.py          - SQLAlchemy models
  schemas.py         - Pydantic request/response schemas
  service.py         - Business logic (create, renew, discontinue, interaction check)
  router.py          - FastAPI endpoints
  interactions.py    - Drug interaction checking logic
  cardiology_drugs.py - Curated cardiology formulary (statins, antiplatelets,
                        anticoagulants, antihypertensives, antiarrhythmics)
```

**Key Endpoints:**
- `POST /patients/{id}/prescriptions` - Create prescription (with interaction check)
- `GET /patients/{id}/prescriptions` - List active/all prescriptions
- `GET /patients/{id}/prescriptions/active` - Current medication list
- `PUT /prescriptions/{id}/discontinue` - Discontinue with reason
- `PUT /prescriptions/{id}/renew` - Renew prescription (creates new record, links to original)
- `POST /prescriptions/{id}/hold` - Temporarily hold (e.g., pre-surgery)
- `GET /prescriptions/interactions/check` - Check drug-drug interactions for a set of meds
- `GET /formulary/search?q=` - Search drug formulary
- `GET /formulary/cardiology` - Curated cardiology drug list

**Interaction Checking Logic:**
- Use ATC classification hierarchy for therapeutic class overlap detection
- Hardcoded critical cardiology interactions:
  - Anticoagulant + Antiplatelet (bleeding risk)
  - Digoxin + Amiodarone (toxicity)
  - ACE-I + K-sparing diuretic (hyperkalemia)
  - Statin + Fibrate (rhabdomyolysis)
  - Beta-blocker + Verapamil/Diltiazem (heart block)
- Severity-based alerting (minor/moderate/major/contraindicated)
- Acknowledged interactions stored to prevent repeat alerts

### 1.3 Backend: Cardiology Drug Formulary Seed

**Curated categories:**
1. **Antiplatelets:** Aspirin, Clopidogrel, Ticagrelor, Prasugrel
2. **Anticoagulants:** Warfarin, Apixaban, Rivaroxaban, Edoxaban, Dabigatran, Enoxaparin
3. **Statins:** Atorvastatin, Rosuvastatin, Simvastatin, Pravastatin
4. **Beta-Blockers:** Bisoprolol, Metoprolol, Carvedilol, Nebivolol, Atenolol
5. **ACE-I:** Ramipril, Perindopril, Enalapril, Lisinopril
6. **ARBs:** Valsartan, Candesartan, Irbesartan, Losartan, Telmisartan
7. **CCBs:** Amlodipine, Nifedipine, Diltiazem, Verapamil
8. **Diuretics:** Furosemide, Bumetanide, Spironolactone, Eplerenone, Hydrochlorothiazide, Indapamide
9. **Antiarrhythmics:** Amiodarone, Flecainide, Dronedarone, Sotalol
10. **Nitrates:** GTN, ISDN, ISMN
11. **Heart Failure:** Sacubitril/Valsartan, Ivabradine, Dapagliflozin, Empagliflozin, Hydralazine
12. **Antihypertensives (other):** Doxazosin, Moxonidine

Each drug entry includes: ATC code, available forms, standard strengths, default dosing, Gesy coverage status.

### 1.4 Frontend: Prescription UI

**Pages:**
- `/patients/[id]/prescriptions` - Medication list (active + history)
- `/patients/[id]/prescriptions/new` - New prescription form
- `/patients/[id]/prescriptions/[rxId]` - Prescription detail with renewal/discontinue actions

**Components:**
- `DrugSearch.tsx` - Autocomplete search of formulary with ATC grouping
- `PrescriptionForm.tsx` - Dosage, frequency, duration, refills
- `InteractionAlert.tsx` - Warning dialog for detected interactions
- `MedicationList.tsx` - Active medications with status badges
- `MedicationTimeline.tsx` - Chronological view of medication changes
- `PrescriptionPrint.tsx` - Print-ready prescription format (Cyprus standards)

**Key UX Decisions:**
- Default to cardiology formulary (searchable, categorized)
- Show current patient medications prominently when prescribing
- Interaction alerts are modal for major/contraindicated, inline for minor/moderate
- One-click renewal for chronic medications
- Print layout matches Cyprus prescription pad format

### 1.5 Permissions

Add to `permissions.py`:
- `PRESCRIBE_MEDICATION` - Create/renew prescriptions (Cardiologist, Nurse with restrictions)
- `DISCONTINUE_MEDICATION` - Discontinue/cancel (Cardiologist only)
- `VIEW_PRESCRIPTIONS` - View medication list (All clinical roles)
- `OVERRIDE_INTERACTION` - Acknowledge and override drug interactions (Cardiologist only)

---

## Phase 2: Enhanced Calendar & Scheduling UI

**Rationale:** The backend scheduling is functional but the frontend needs a proper calendar view for daily use.

### 2.1 Frontend: Calendar Views

**Note:** Backend appointment APIs already exist with conflict detection, check-in, and available slots.

**New Components:**
- `WeekView.tsx` - 7-column grid with 15-min slot rows, provider filter
- `DayView.tsx` - Single-day detailed view with appointment cards
- `MonthView.tsx` - Month grid with appointment counts per day
- `AppointmentCard.tsx` - Color-coded by status (scheduled/confirmed/checked-in/no-show)
- `QuickBook.tsx` - Slide-over panel for rapid appointment creation
- `PatientCheckIn.tsx` - Check-in workflow with vitals prompt

**Calendar Features:**
- Provider-column layout (for multi-doctor clinics)
- Drag-and-drop rescheduling (PATCH appointment endpoint already exists)
- Color coding: Blue=scheduled, Green=confirmed, Orange=checked-in, Red=no-show, Gray=cancelled
- Click-to-book on empty slot
- Today indicator with current-time line
- Recurring appointment support (new backend endpoint needed)

### 2.2 Backend: Recurring Appointments

**New endpoint:** `POST /appointments/recurring`

```python
class RecurringAppointmentRequest(BaseModel):
    patient_id: UUID
    provider_id: UUID
    start_date: date
    time: time
    duration_minutes: int = 30
    recurrence: RecurrencePattern  # weekly, biweekly, monthly
    occurrences: int  # max 52 (one year of weekly)
    appointment_type: str
    notes: Optional[str]
```

Creates individual appointment records with a `recurrence_group_id` linking them. Conflict detection runs against each generated slot.

### 2.3 Backend: No-Show Tracking

**Enhancement to existing appointment model:**
- Add `no_show_count` to patient profile (denormalized counter)
- Add `POST /appointments/{id}/no-show` endpoint
- Track no-show patterns for scheduling decisions
- Optional: Auto-flag frequent no-shows on booking screen

### 2.4 Frontend: Appointment Reminders (Future)

- SMS/email reminder integration (via Twilio or local SMS gateway)
- Configurable reminder windows (24h, 2h before)
- Reminder status tracking per appointment

---

## Phase 3: Revenue Cycle Management (Billing Backend)

**Rationale:** Frontend billing UI already exists. Backend needs to support Gesy claim lifecycle.

### 3.1 Backend: Billing Service

**Location:** `backend/app/modules/billing/`

```
billing/
  __init__.py
  models.py      - Invoice, InvoiceLineItem, Payment, ClaimSubmission
  schemas.py     - Pydantic schemas
  service.py     - Invoice generation, payment recording, claim lifecycle
  router.py      - API endpoints
  gesy_claims.py - Gesy-specific claim formatting
```

**Migration: `0010_billing.py`**

```
Tables:
- invoices:
  - id, patient_id (FK), encounter_id (FK), clinic_id (FK)
  - invoice_number (unique, auto-generated: OH-YYYY-NNNNN)
  - issue_date, due_date
  - subtotal, tax_amount, total_amount, amount_paid, balance
  - status (ENUM: draft, issued, partially_paid, paid, overdue, cancelled, written_off)
  - payment_method (ENUM: cash, card, bank_transfer, gesy, insurance)
  - gesy_claim_id (nullable, FK to gesy_claims)
  - notes, created_at, updated_at

- invoice_line_items:
  - id, invoice_id (FK)
  - description, cpt_code (nullable), hio_service_code (nullable)
  - quantity, unit_price, total_price
  - is_gesy_covered (bool)

- payments:
  - id, invoice_id (FK), patient_id (FK)
  - amount, payment_date, payment_method
  - reference_number (for bank transfers/card receipts)
  - notes, created_at

- gesy_claims:
  - id, invoice_id (FK), patient_id (FK), encounter_id (FK)
  - gesy_beneficiary_id, gesy_referral_id (nullable)
  - claim_number (Gesy-assigned, nullable until submitted)
  - status (ENUM: draft, submitted, accepted, rejected, paid, appealed)
  - submission_date, response_date
  - rejection_reason (text, nullable)
  - appeal_notes (text, nullable)
  - amount_claimed, amount_approved (nullable)
  - hio_service_codes (JSONB array)
  - created_at, updated_at
```

### 3.2 Key Billing Endpoints

- `POST /encounters/{id}/invoice` - Generate invoice from encounter (auto-populate from services rendered)
- `GET /invoices` - List with filters (status, date range, patient)
- `GET /invoices/{id}` - Invoice detail with line items and payments
- `POST /invoices/{id}/payment` - Record payment
- `POST /invoices/{id}/submit-gesy` - Submit to Gesy (uses IGesyProvider adapter)
- `GET /billing/dashboard` - Revenue summary (today, week, month, outstanding)
- `GET /billing/aging-report` - Overdue invoices grouped by age (30/60/90 days)

### 3.3 Gesy Claim Workflow

```
Encounter Complete
      |
      v
Invoice Generated (draft)
      |
      v
[If Gesy beneficiary]
      |
      v
Gesy Claim Created (draft)
      |
      v
Submit Claim (via IGesyProvider.submit_claim)
      |
      +--> Accepted --> Paid
      |
      +--> Rejected --> [View reason] --> Appeal or Write-off
```

### 3.4 Frontend: Wire Existing Billing UI

The billing UI at `/billing/claims` already exists with:
- Claims list with status filters
- Rejection resolution panel

**Additions needed:**
- Wire to real API endpoints (currently uses mock data)
- Add invoice creation flow from encounter page
- Add payment recording modal
- Add billing dashboard with revenue charts
- Add aging report view

---

## Phase 4: Lab Interface & Longitudinal Vitals

**Rationale:** Cardiology tracks Troponin, CK-MB, Lipid Panels, INR, BNP over time. Manual entry is error-prone and slow.

### 4.1 Backend: Lab Results Module

**Location:** `backend/app/modules/labs/`

**Migration: `0011_lab_results.py`**

```
Tables:
- lab_orders:
  - id, patient_id (FK), encounter_id (FK), ordering_provider_id (FK)
  - order_date, status (ENUM: ordered, collected, processing, resulted, cancelled)
  - lab_facility (varchar) - external lab name
  - priority (ENUM: routine, urgent, stat)
  - clinical_notes (text)
  - placer_order_number (varchar) - HL7 OBR-2 equivalent
  - filler_order_number (varchar) - HL7 OBR-3 equivalent
  - created_at, updated_at

- lab_results:
  - id, lab_order_id (FK), patient_id (FK)
  - test_code (varchar) - LOINC code
  - test_name (varchar) - human-readable name
  - value (varchar) - result value (varchar to handle qualitative results)
  - numeric_value (float, nullable) - for trending
  - unit (varchar)
  - reference_range_low (float, nullable)
  - reference_range_high (float, nullable)
  - reference_range_text (varchar) - e.g., "<0.04 ng/mL"
  - abnormal_flag (ENUM: normal, low, high, critical_low, critical_high, abnormal)
  - result_status (ENUM: preliminary, final, corrected, cancelled)
  - result_datetime (timestamp)
  - performing_lab (varchar)
  - notes (text)
  - created_at

- lab_panels: (predefined cardiology panels)
  - id, name, description, loinc_codes (JSONB array)
  - is_cardiology_default (bool)
```

### 4.2 Cardiology Lab Panels (Seed Data)

| Panel | LOINC Codes | Use Case |
|-------|-------------|----------|
| Cardiac Markers | Troponin-I (10839-9), Troponin-T (6598-7), CK-MB (13969-1), BNP (30934-4), NT-proBNP (33762-6) | ACS workup, HF monitoring |
| Lipid Panel | Total Chol (2093-3), LDL (13457-7), HDL (2085-9), Triglycerides (2571-8), Non-HDL (43396-1) | ASCVD risk, statin monitoring |
| Coagulation | INR (6301-6), PT (5902-2), aPTT (3173-2), Anti-Xa (3200-3) | Anticoagulation monitoring |
| Renal Function | Creatinine (2160-0), eGFR (33914-3), BUN (3094-0), K+ (2823-3), Na+ (2951-2) | Drug dosing, HF monitoring |
| Thyroid | TSH (3016-3), Free T4 (3024-7) | Amiodarone monitoring, AF workup |
| Liver Function | ALT (1742-6), AST (1920-8), ALP (6768-6), Bilirubin (1975-2) | Statin monitoring |
| HbA1c | HbA1c (4548-4) | CV risk factor |
| CBC | Hb (718-7), WBC (6690-2), Platelets (777-3) | Bleeding risk, pre-procedure |

### 4.3 Lab Import Mechanisms

**Priority 1: Manual Entry with Smart Defaults**
- Form pre-populated with cardiology panel templates
- Numeric validation against reference ranges
- Auto-flag abnormal results
- Batch entry for multi-test panels

**Priority 2: CSV/PDF Import**
- Upload lab report PDF or CSV from external lab
- Parse structured data (common Cyprus lab formats)
- Review and confirm before saving
- Map external test names to LOINC codes

**Priority 3: HL7 v2 Interface (Future)**
- HL7 v2.x ORU (Observation Result) message parser
- Listener service for lab system integration
- Auto-map OBX segments to lab_results records
- LOINC code translation layer

### 4.4 Vitals Trending & Visualization

**Backend Endpoint:**
- `GET /patients/{id}/vitals/trend?metric=bp_systolic&from=&to=` - Time-series data
- `GET /patients/{id}/labs/trend?loinc=6301-6&from=&to=` - Lab value trends
- `GET /patients/{id}/clinical-summary` - Aggregate latest vitals + labs + active meds

**Frontend Components:**
- `VitalsTrendChart.tsx` - Line chart (BP, HR, weight over time) using a charting library
- `LabResultsPanel.tsx` - Tabular view with sparkline trends and abnormal highlighting
- `ClinicalDashboard.tsx` - Patient-level dashboard combining vitals + labs + meds
- `LabEntryForm.tsx` - Panel-based lab entry with smart defaults
- `LabImportUpload.tsx` - CSV/PDF upload with mapping UI

**Key UX:**
- BP chart shows both systolic and diastolic as a range band
- Overlay medication changes on vitals charts (e.g., "Started Amlodipine 5mg" marker)
- Critical values highlighted in red with visual alerts
- Quick-view of latest labs on patient header

---

## Phase 5: CDS-to-Action Integration

**Rationale:** The CDSS calculators currently produce a risk score and recommendation text. They need to feed into actionable workflows (prescriptions, orders, scheduling).

### 5.1 Architecture: Action-Enabled CDSS

```
Patient Data (Labs + Vitals + Meds)
          |
          v
    CDSS Calculator
    (Auto-populated from patient record)
          |
          v
    Risk Score + Recommendation
          |
          v
    Suggested Actions:
    +-- Pre-filled Prescription (one-click to prescribe)
    +-- Lab Order suggestion
    +-- Follow-up appointment suggestion
    +-- Alert/flag on patient record
```

### 5.2 Backend: CDSS Auto-Population

**New endpoint:** `GET /patients/{id}/cdss/auto-populate/{calculator}`

For each calculator, pull latest values from patient record:

**GRACE Score:**
- Age → patient.date_of_birth
- Heart Rate → latest encounter vitals
- Systolic BP → latest encounter vitals
- Creatinine → latest lab (LOINC 2160-0)
- Killip Class → latest encounter assessment
- Cardiac Arrest → encounter data
- ST Deviation → encounter/ECG data
- Elevated Cardiac Markers → latest Troponin lab

**CHA2DS2-VASc:**
- Age → patient.date_of_birth
- Sex → patient.sex
- CHF history → problem list (ICD-10 I50.x)
- Hypertension → problem list (ICD-10 I10-I15) or BP readings
- Diabetes → problem list (ICD-10 E10-E14) or HbA1c
- Stroke/TIA → problem list (ICD-10 I63.x, G45.x)
- Vascular disease → problem list (ICD-10 I70.x, I21.x)

**HAS-BLED:**
- Hypertension → BP readings or problem list
- Renal function → eGFR or Creatinine lab
- Liver function → ALT/AST labs
- Stroke history → problem list
- Bleeding history → problem list
- Labile INR → INR lab trend (TTR calculation)
- Age → patient.date_of_birth
- Medications → active prescriptions (antiplatelets, NSAIDs)
- Alcohol → social history

### 5.3 Backend: CDSS Action Recommendations

**New schema:** `CDSSActionRecommendation`

```python
class CDSSActionRecommendation(BaseModel):
    calculator: str
    score: int | float
    risk_level: str  # low, moderate, high, very_high
    recommendations: list[str]  # text recommendations (existing)
    suggested_actions: list[SuggestedAction]

class SuggestedAction(BaseModel):
    action_type: str  # "prescribe", "order_lab", "schedule_followup", "flag"
    priority: str  # "immediate", "soon", "routine"
    description: str
    # For prescriptions:
    drug_suggestion: Optional[DrugSuggestion]
    # For lab orders:
    lab_panel: Optional[str]
    # For follow-up:
    followup_interval_days: Optional[int]
```

**Clinical Logic Examples:**

| Calculator | Score | Suggested Actions |
|-----------|-------|-------------------|
| CHA2DS2-VASc >= 2 (male) / >= 3 (female) | High | Prescribe: Apixaban 5mg BD or Rivaroxaban 20mg OD |
| CHA2DS2-VASc = 1 (male) / = 2 (female) | Moderate | Consider: Anticoagulation (present options, no auto-fill) |
| HAS-BLED >= 3 | High Bleeding Risk | Flag: Review anticoagulation dose, Order: CBC + Coag panel, Schedule: 4-week review |
| GRACE > 140 | High ACS Risk | Prescribe: DAPT (Aspirin + Ticagrelor), Order: Serial Troponin, Flag: Consider invasive strategy |
| PREVENT 10yr >= 20% | High ASCVD | Prescribe: High-intensity statin (Atorvastatin 40-80mg or Rosuvastatin 20-40mg) |

### 5.4 Frontend: Integrated CDSS Workflow

**Enhanced CDSS Pages:**
- Auto-populate button: "Fill from patient record" (calls auto-populate endpoint)
- After calculation: Show action cards below the result
- Each action card has:
  - Description of recommendation
  - "Prescribe" button → opens PrescriptionForm pre-filled
  - "Order Labs" button → opens lab order pre-filled
  - "Schedule Follow-up" button → opens appointment booking
- Track which recommendations were actioned vs. dismissed (with reason)

**Patient Dashboard Integration:**
- "Risk Alerts" section showing any calculators with concerning scores
- Quick-action buttons on alerts
- Historical CDSS scores trended over time

### 5.5 Audit: CDSS-to-Action Tracking

Extend existing `CDSSAuditLog`:
- Add `actions_suggested` (JSONB) - what was recommended
- Add `actions_taken` (JSONB) - what the clinician did
- Add `actions_dismissed` (JSONB) - what was dismissed and why
- Enables quality metrics: "% of high CHA2DS2-VASc patients on anticoagulation"

---

## Phase 6: Interoperability & External Integrations

**Rationale:** Long-term viability requires data exchange with external systems.

### 6.1 HL7 v2 Lab Interface

**Components:**
- `backend/app/integrations/hl7/` - HL7 v2 message parser
- MLLP (Minimal Lower Layer Protocol) listener for lab system connections
- Message types: ORU^R01 (results), ORM^O01 (orders), ADT^A01 (patient registration)
- Mapping layer: HL7 OBX segments → lab_results table
- Acknowledgment: ACK messages for reliable delivery

**Implementation:**
- Use `python-hl7` or `hl7apy` library for message parsing
- Async listener service (can run as separate Docker container)
- Configuration: per-lab mapping profiles for test code translation
- Error queue for failed message processing

### 6.2 FHIR R4 Resources

**Extend existing stub at `backend/app/integrations/fhir/`:**

Priority resources for cardiology:
- `Patient` - Demographics mapping
- `Observation` - Vitals and lab results
- `MedicationRequest` - Prescriptions
- `Condition` - Problem list / diagnoses
- `Encounter` - Visit records
- `Appointment` - Scheduling
- `DiagnosticReport` - Lab panels
- `DocumentReference` - Clinical notes
- `ImagingStudy` - DICOM study references

**Use cases:**
- Export patient summary as FHIR Bundle (patient transfer)
- Import patient data from other FHIR-compliant systems
- Future: SMART on FHIR apps integration

### 6.3 Gesy Real Integration

**Replace MockGesyProvider with RealGesyProvider:**
- OAuth2 authentication with HIO portal
- Real beneficiary verification API calls
- Claim submission in HIO-specified format
- Status polling for submitted claims
- Referral validation against HIO specialty codes

### 6.4 Cyprus Lab Integrations

**Common Cyprus labs to target:**
- Bioanalytica (largest private lab chain)
- NIPD Genetics
- Yiannoukas Medical Labs
- Hospital lab systems (Limassol General, Nicosia General)

**Integration approach:**
- Start with CSV/PDF import for all labs
- HL7 interface for labs that support it
- API integration where available

---

## Implementation Priority & Dependencies

```
Phase 1 (Prescriptions) ─────────────────────────────────────────────┐
    No dependencies. Start immediately.                               |
                                                                      |
Phase 2 (Calendar UI) ───────────────────────────────────────────────┐|
    No dependencies. Can run in parallel with Phase 1.                ||
                                                                      ||
Phase 3 (Billing) ───────────────────────────────────────────────────┐||
    Depends on: Encounter system (exists), Gesy adapter (exists)      |||
    Can start in parallel with Phases 1-2.                            |||
                                                                      |||
Phase 4 (Labs & Vitals) ─────────────────────────────────────────────┤||
    Depends on: Patient module (exists)                               |||
    Can start in parallel, but Phase 5 needs it.                      |||
                                                                      |||
Phase 5 (CDS-to-Action) ─────────────────────────────────────────────┤|
    Depends on: Phase 1 (prescriptions), Phase 4 (labs)               ||
    Start after Phases 1 & 4 are complete.                            ||
                                                                      ||
Phase 6 (Interoperability) ──────────────────────────────────────────-┘|
    Depends on: Phase 4 (labs for HL7), Phase 3 (billing for Gesy)     |
    Start after Phases 3 & 4.                                          |
                                                                       |
 MVP Complete ─────────────────────────────────────────────────────────┘
```

### Parallel Execution Strategy

**Stream A (Clinical):** Phase 1 → Phase 5
**Stream B (Operations):** Phase 2 + Phase 3 (parallel)
**Stream C (Data):** Phase 4 → Phase 6

All three streams can execute concurrently with Phase 5 as the convergence point.

---

## Technical Decisions & Patterns

### Drug Database Choice

FreeMED uses Multum, OpenEMR uses First Databank via WENO. For Cyprus:
- **Decision:** Build a curated cardiology formulary seeded from the Gesy drug list (already have ATC codes in migration 0002)
- **Rationale:** Cyprus has a limited formulary (~2000 drugs on Gesy). A focused cardiology subset (~100-150 drugs) provides better UX than a full national formulary
- **Future:** Can integrate with Gesy's drug database API when available

### Interaction Checking

- **Decision:** Rule-based interaction checking using ATC therapeutic class analysis + hardcoded critical pairs
- **Rationale:** Full DrugBank/Multum integration is expensive and overkill for a specialty EMR. The critical cardiology interactions are well-defined and finite
- **Future:** Can plug in an external interaction API (e.g., RxNav) later

### Calendar Library

- **Decision:** Build custom calendar grid using Shadcn + date-fns (no heavy calendar library)
- **Rationale:** Medical scheduling has unique requirements (provider columns, status colors, encounter linking) that generic calendar components don't support well
- **Components:** Grid layout with Tailwind, drag-drop via @dnd-kit, time slots as CSS grid rows

### Lab Trending

- **Decision:** Recharts or Chart.js for vitals/lab visualization
- **Rationale:** Lightweight, React-native, sufficient for time-series line charts with annotations
- **Features needed:** Multi-series, date axis, reference range bands, event annotations

### Billing Engine

- **Decision:** Keep billing integrated (not separated like FreeMED's REMITT)
- **Rationale:** Cyprus billing is simpler than US healthcare. One payer (Gesy) + private pay. No need for clearinghouse complexity
- **Future:** If multi-payer support needed, extract to adapter pattern (already designed with IGesyProvider)

---

## Testing Strategy

Each phase includes:
1. **Unit tests** for service layer (calculators, interaction checking, claim validation)
2. **Integration tests** for API endpoints (FastAPI TestClient)
3. **Seed data** for development (extend existing `seed.py`)

**Critical test scenarios:**
- Prescription: Drug interaction detection, duplicate therapy, renal dose adjustment flags
- Billing: Invoice generation from encounter, Gesy claim lifecycle
- Labs: Abnormal value flagging, trend calculation, panel completion
- CDSS: Auto-population from partial data, action generation logic

---

## Security & Compliance Additions

### Prescription-Specific
- All prescription actions logged to security_audit (who prescribed what, when)
- Controlled substance prescriptions require additional confirmation (future)
- Prescription printing includes prescriber registration number and clinic stamp

### Lab Results
- Lab results classified as sensitive medical data (PII adjacent)
- Access logging for lab views (extend note_access_log pattern)
- Critical value alerts generate audit trail

### Billing
- Invoice access restricted by role (BILLING_STAFF, CLINIC_ADMIN, SYSTEM_ADMIN)
- Payment recording requires dual confirmation for amounts > threshold
- Gesy claim data encrypted at rest (contains beneficiary IDs)

---

## Migration Path from Current State

### Immediate (Phase 1 + 2):
1. Create migration 0009 for prescription tables
2. Build prescription module (models, service, router)
3. Seed cardiology formulary
4. Build frontend prescription pages
5. Enhance calendar frontend with day/week views
6. Add recurring appointment support

### Short-term (Phase 3 + 4):
1. Create migration 0010 for billing tables
2. Wire existing billing UI to real endpoints
3. Create migration 0011 for lab tables
4. Build lab entry and trending
5. Add vitals visualization to patient profile

### Medium-term (Phase 5):
1. Build CDSS auto-population from patient data
2. Create action recommendation engine
3. Integrate prescriptions with CDSS results
4. Build quality metrics dashboard

### Long-term (Phase 6):
1. HL7 v2 listener for lab import
2. FHIR resource mappings
3. Real Gesy API integration
4. Cyprus lab-specific import profiles
