# Phase 5: CDS-to-Action Integration

## Priority: CRITICAL (Convergence Phase) | Dependencies: Phase 1 (Prescriptions) + Phase 4 (Labs) | Start After Both Complete

---

## Executive Summary

This is the convergence phase that transforms OpenHeart from a collection of modules into an integrated clinical workflow. Currently, CDSS calculators produce risk scores and text recommendations but cannot: (1) auto-populate inputs from patient data, (2) suggest specific prescriptions, (3) trigger lab orders, or (4) schedule follow-ups. This phase connects the dots: patient data flows into CDSS, and CDSS results flow into actionable clinical orders.

---

## Existing Infrastructure (What We Already Have)

### CDSS Calculators (5 Complete)
| Calculator | Location | Input Fields | Output |
|-----------|----------|-------------|--------|
| GRACE | `cdss/calculators.py:40-196` | age, HR, SBP, creatinine, Killip, arrest, ST, enzymes | Score 0-372, mortality %, category |
| CHA2DS2-VASc | Same | age, sex, CHF, HTN, DM, stroke, vascular | Score 0-9, annual stroke risk %, Rx recommendation |
| HAS-BLED | Same | 9 boolean factors | Score 0-9, annual bleed rate %, modifiable factors |
| PREVENT | Same | age, sex, SBP, chol, HDL, eGFR, DM, smoking, Rx, HbA1c, UACR | 10yr ASCVD %, HF %, total CVD %, statin benefit |
| EuroSCORE II | Same | 22 params (patient/cardiac/operation) | Predicted mortality %, surgical candidacy |

### CDSS API & Audit
| Feature | Location | Status |
|---------|----------|--------|
| 5 POST endpoints | `cdss/router.py` | All return CDSSResult with recommendations |
| Optional patient_id | All endpoints | Links calculation to patient record |
| CDSSAuditLog | `core/audit.py` | Stores input_params, score, risk_category, recommendation |
| Partitioned storage | Migration 0005 | 15-year retention (2024-2040) |
| Fire-and-forget | `audit.py` | Non-blocking async logging |

### CDSS Frontend
| Feature | Location | Status |
|---------|----------|--------|
| Calculator hub | `frontend/src/app/cdss/page.tsx` | Lists all 5 with descriptions |
| Individual pages | `frontend/src/app/cdss/{calculator}/page.tsx` | Form + results display |
| Risk category colors | `frontend/src/lib/api/cdss.ts` | getRiskCategoryColor() helper |
| API client | `cdss.ts` | All 5 calculate functions |

### CDSS Input Schemas (Manual Entry Only)
```python
# GRACEInput
age: int                         # → patient.date_of_birth
heart_rate: int                  # → latest vitals
systolic_bp: int                 # → latest vitals
creatinine_mg_dl: float          # → latest lab (LOINC 2160-0)
killip_class: KillipClass        # → encounter assessment (manual)
cardiac_arrest_at_admission: bool # → encounter data (manual)
st_segment_deviation: bool       # → ECG finding (manual)
elevated_cardiac_enzymes: bool   # → latest troponin lab

# CHA2DS2VAScInput
age: int                         # → patient.date_of_birth
sex: Sex                         # → patient.sex
congestive_heart_failure: bool   # → problem list (ICD-10 I50.x)
hypertension: bool               # → problem list OR BP readings
diabetes: bool                   # → problem list OR HbA1c
stroke_tia_te: bool              # → problem list (ICD-10 I63.x, G45.x)
vascular_disease: bool           # → problem list (ICD-10 I70.x, I21.x)

# HASBLEDInput
uncontrolled_hypertension: bool  # → BP readings (SBP > 160)
renal_dysfunction: bool          # → eGFR < 60 or Cr > 2.3
liver_dysfunction: bool          # → ALT/AST > 3× ULN
stroke_history: bool             # → problem list
bleeding_history: bool           # → problem list (manual)
labile_inr: bool                 # → INR trend (TTR < 60%)
age_over_65: bool                # → patient.date_of_birth
drugs: bool                      # → active prescriptions (antiplatelets, NSAIDs)
alcohol: bool                    # → social history (manual)

# PREVENTInput
age: int                         # → patient.date_of_birth
sex: Sex                         # → patient.sex
systolic_bp: int                 # → latest vitals
total_cholesterol: float         # → latest lab (LOINC 2093-3)
hdl_cholesterol: float           # → latest lab (LOINC 2085-9)
egfr: float                      # → latest lab (LOINC 33914-3)
diabetes: bool                   # → problem list OR HbA1c
current_smoker: bool             # → social history (manual)
on_bp_treatment: bool            # → active prescriptions (ATC C02-C09)
on_statin: bool                  # → active prescriptions (ATC C10AA)
hba1c: Optional[float]          # → latest lab (LOINC 4548-4)
uacr: Optional[float]           # → latest lab (manual)
```

### Encounter Diagnoses (Partial Problem List)
| Feature | Location | Status |
|---------|----------|--------|
| Diagnoses array | `encounter/models.py` | JSONB list of {code, description, type, confirmed} |
| ICD-10 search | `coding/router.py` | Full search with Greek support |
| Encounter completion | `encounter/schemas.py` | Captures diagnoses on discharge |
| Timeline display | Patient timeline | Shows encounter events |

### What Phase 1 Provides (Prerequisites)
- Prescription model with ATC codes
- Active medications list per patient
- Drug interaction checking
- Medication search and creation

### What Phase 4 Provides (Prerequisites)
- Lab results storage with LOINC codes
- Latest labs per patient (by LOINC code)
- Lab trending for trend analysis (e.g., labile INR detection)
- Vitals trending with historical data

---

## What's Missing (Implementation Required)

### 1. Patient Problem List Model

**Currently:** Diagnoses are stored per-encounter only. No persistent patient-level problem list.

**New table (add to migration 0011 or create 0012):**
```sql
CREATE TABLE patient_problems (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    clinic_id INTEGER NOT NULL REFERENCES clinics(id),

    -- Diagnosis
    icd10_code VARCHAR(10) NOT NULL,
    description VARCHAR(500) NOT NULL,
    description_el VARCHAR(500), -- Greek translation

    -- Classification
    problem_type VARCHAR(20) NOT NULL DEFAULT 'diagnosis',
        -- diagnosis, symptom, risk_factor, procedure_history, family_history
    severity VARCHAR(20), -- mild, moderate, severe

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'active',
        -- active, resolved, inactive, ruled_out

    -- Dates
    onset_date DATE,            -- When problem first identified
    resolved_date DATE,         -- When resolved (if applicable)
    recorded_date DATE NOT NULL DEFAULT CURRENT_DATE,

    -- Source
    source_encounter_id UUID REFERENCES encounters(encounter_id),
    recorded_by INTEGER NOT NULL REFERENCES users(id),

    -- Notes
    clinical_notes TEXT,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE  -- Soft delete
);

CREATE INDEX idx_problems_patient_status ON patient_problems(patient_id, status);
CREATE INDEX idx_problems_patient_icd10 ON patient_problems(patient_id, icd10_code);
CREATE INDEX idx_problems_active ON patient_problems(patient_id)
    WHERE status = 'active' AND deleted_at IS NULL;
```

**Problem List Service:**
```python
GET    /api/patients/{patient_id}/problems              # Active problem list
POST   /api/patients/{patient_id}/problems              # Add problem
PUT    /api/patients/{patient_id}/problems/{id}         # Update (status, notes)
DELETE /api/patients/{patient_id}/problems/{id}         # Soft delete
POST   /api/patients/{patient_id}/problems/from-encounter/{encounter_id}  # Promote encounter diagnosis to persistent problem
```

**Auto-populate from encounters:**
When an encounter is completed with diagnoses marked as `confirmed=true` and `type=principal`, offer to add to persistent problem list.

### 2. CDSS Auto-Population Endpoint

**New endpoint:** `GET /api/patients/{patient_id}/cdss/auto-populate/{calculator}`

**Location:** Add to `backend/app/modules/cardiology/cdss/router.py`

```python
@router.get("/patients/{patient_id}/cdss/auto-populate/{calculator}")
async def auto_populate_cdss(
    patient_id: int,
    calculator: str,  # grace, cha2ds2vasc, hasbled, prevent, euroscore
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Gather patient data and pre-fill CDSS calculator inputs.
    Returns partial input with confidence indicators.
    """
```

**Response Schema:**
```python
class AutoPopulateResponse(BaseModel):
    calculator: str
    patient_id: int
    populated_fields: dict[str, PopulatedField]
    missing_fields: list[str]  # Fields that couldn't be populated
    data_freshness: dict[str, DataFreshness]  # When each value was last recorded
    confidence: str  # high, medium, low (based on data completeness)
    warnings: list[str]  # e.g., "Creatinine is 6 months old"

class PopulatedField(BaseModel):
    value: Any
    source: str  # "latest_vitals", "latest_lab", "problem_list", "active_medications", "demographics"
    source_date: Optional[datetime]
    source_encounter_id: Optional[UUID]
    is_stale: bool  # > 6 months old for labs, > 1 month for vitals
    confidence: str  # high (direct measurement), medium (inferred), low (old data)
```

**Auto-Population Logic per Calculator:**

#### GRACE
```python
async def populate_grace(patient_id: int, db: AsyncSession) -> dict:
    patient = await get_patient(patient_id, db)  # age, sex from demographics
    vitals = await get_latest_vitals(patient_id, db)  # HR, SBP
    creatinine = await get_latest_lab(patient_id, "2160-0", db)  # LOINC for Creatinine
    troponin = await get_latest_lab(patient_id, "49563-0", db)  # hs-TnI

    return {
        "age": calculate_age(patient.date_of_birth),
        "heart_rate": vitals.heart_rate if vitals else None,
        "systolic_bp": vitals.systolic_bp if vitals else None,
        "creatinine_mg_dl": creatinine.value_numeric if creatinine else None,
        "elevated_cardiac_enzymes": (troponin.value_numeric > troponin.reference_range_high)
            if troponin else None,
        # Killip, cardiac_arrest, ST deviation → cannot auto-populate (clinical assessment)
    }
```

#### CHA2DS2-VASc
```python
async def populate_cha2ds2vasc(patient_id: int, db: AsyncSession) -> dict:
    patient = await get_patient(patient_id, db)
    problems = await get_active_problems(patient_id, db)
    vitals = await get_latest_vitals(patient_id, db)

    return {
        "age": calculate_age(patient.date_of_birth),
        "sex": patient.sex,
        "congestive_heart_failure": has_problem(problems, ["I50"]),  # ICD-10 prefix
        "hypertension": has_problem(problems, ["I10", "I11", "I12", "I13", "I15"])
            or (vitals and vitals.systolic_bp >= 140),
        "diabetes": has_problem(problems, ["E10", "E11", "E13", "E14"]),
        "stroke_tia_te": has_problem(problems, ["I63", "I64", "G45", "I74"]),
        "vascular_disease": has_problem(problems, ["I70", "I21", "I25", "I71"]),
    }
```

#### HAS-BLED
```python
async def populate_hasbled(patient_id: int, db: AsyncSession) -> dict:
    patient = await get_patient(patient_id, db)
    problems = await get_active_problems(patient_id, db)
    vitals = await get_latest_vitals(patient_id, db)
    egfr = await get_latest_lab(patient_id, "33914-3", db)
    creatinine = await get_latest_lab(patient_id, "2160-0", db)
    alt = await get_latest_lab(patient_id, "1742-6", db)
    ast = await get_latest_lab(patient_id, "1920-8", db)
    inr_history = await get_lab_trend(patient_id, "6301-6", limit=10, db=db)
    medications = await get_active_medications(patient_id, db)

    return {
        "uncontrolled_hypertension": vitals and vitals.systolic_bp > 160,
        "renal_dysfunction": (egfr and egfr.value_numeric < 60) or
                             (creatinine and creatinine.value_numeric > 2.3),
        "liver_dysfunction": (alt and alt.value_numeric > 120) or  # 3× ULN
                             (ast and ast.value_numeric > 120),
        "stroke_history": has_problem(problems, ["I63", "I64", "G45"]),
        "bleeding_history": has_problem(problems, ["K92.0", "K92.1", "K92.2", "R04"]),
        "labile_inr": calculate_ttr(inr_history) < 60 if len(inr_history) >= 3 else None,
        "age_over_65": calculate_age(patient.date_of_birth) > 65,
        "drugs": any(
            med.atc_code and (
                med.atc_code.startswith("B01AC") or  # Antiplatelets
                med.atc_code.startswith("M01A")      # NSAIDs
            ) for med in medications
        ),
        # alcohol → social history (not stored, remains manual)
    }
```

#### PREVENT
```python
async def populate_prevent(patient_id: int, db: AsyncSession) -> dict:
    patient = await get_patient(patient_id, db)
    vitals = await get_latest_vitals(patient_id, db)
    problems = await get_active_problems(patient_id, db)
    medications = await get_active_medications(patient_id, db)
    total_chol = await get_latest_lab(patient_id, "2093-3", db)
    hdl = await get_latest_lab(patient_id, "2085-9", db)
    egfr = await get_latest_lab(patient_id, "33914-3", db)
    hba1c = await get_latest_lab(patient_id, "4548-4", db)

    return {
        "age": calculate_age(patient.date_of_birth),
        "sex": patient.sex,
        "systolic_bp": vitals.systolic_bp if vitals else None,
        "total_cholesterol": total_chol.value_numeric if total_chol else None,
        "hdl_cholesterol": hdl.value_numeric if hdl else None,
        "egfr": egfr.value_numeric if egfr else None,
        "diabetes": has_problem(problems, ["E10", "E11", "E13", "E14"]),
        "on_bp_treatment": any(
            med.atc_code and med.atc_code[:3] in ["C02", "C03", "C07", "C08", "C09"]
            for med in medications
        ),
        "on_statin": any(
            med.atc_code and med.atc_code.startswith("C10AA")
            for med in medications
        ),
        "hba1c": hba1c.value_numeric if hba1c else None,
        # current_smoker → social history (manual)
        # uacr → not commonly stored (manual)
    }
```

### 3. CDSS Action Recommendations Engine

**New file:** `backend/app/modules/cardiology/cdss/actions.py`

```python
class CDSSActionEngine:
    """Generates actionable recommendations based on CDSS scores"""

    def get_actions(self, calculator: str, result: CDSSResult,
                    patient_context: PatientContext) -> list[SuggestedAction]:
        """
        Based on calculator type and score, generate specific actions.
        PatientContext includes: current meds, problems, labs, allergies.
        """

# Action Types
class SuggestedAction(BaseModel):
    action_type: str  # prescribe, order_lab, schedule_followup, flag, refer
    priority: str     # immediate, soon, routine
    description: str
    rationale: str    # Why this action is recommended

    # For prescriptions
    prescription_prefill: Optional[PrescriptionPrefill]

    # For lab orders
    lab_panel_code: Optional[str]
    lab_tests: Optional[list[str]]  # LOINC codes

    # For follow-up
    followup_days: Optional[int]
    followup_type: Optional[str]  # appointment type

    # For referrals
    referral_specialty: Optional[str]

class PrescriptionPrefill(BaseModel):
    drug_name: str
    atc_code: str
    strength: str
    frequency: str
    route: str
    duration_days: Optional[int]
    indication: str
    notes: Optional[str]
    alternatives: list[AlternativeDrug]  # Other options in same class
```

**Clinical Action Rules:**

```python
CDSS_ACTION_RULES = {
    "cha2ds2vasc": [
        ActionRule(
            condition=lambda score, sex: (sex == "male" and score >= 2) or (sex == "female" and score >= 3),
            actions=[
                SuggestedAction(
                    action_type="prescribe",
                    priority="soon",
                    description="Initiate oral anticoagulation",
                    rationale="CHA₂DS₂-VASc indicates high stroke risk requiring anticoagulation",
                    prescription_prefill=PrescriptionPrefill(
                        drug_name="Apixaban",
                        atc_code="B01AF02",
                        strength="5mg",
                        frequency="BD",
                        route="oral",
                        indication="Stroke prevention in non-valvular AF",
                        alternatives=[
                            AlternativeDrug("Rivaroxaban", "B01AF01", "20mg OD"),
                            AlternativeDrug("Edoxaban", "B01AF03", "60mg OD"),
                            AlternativeDrug("Dabigatran", "B01AE07", "150mg BD"),
                        ]
                    )
                ),
                SuggestedAction(
                    action_type="order_lab",
                    priority="routine",
                    description="Check renal function before initiating anticoagulation",
                    lab_panel_code="RENAL_FUNCTION"
                ),
            ]
        ),
        ActionRule(
            condition=lambda score, sex: (sex == "male" and score == 1) or (sex == "female" and score == 2),
            actions=[
                SuggestedAction(
                    action_type="flag",
                    priority="routine",
                    description="Consider anticoagulation - discuss risks/benefits with patient",
                    rationale="Intermediate stroke risk - clinical judgment required"
                ),
            ]
        ),
    ],

    "grace": [
        ActionRule(
            condition=lambda score, _: score > 140,
            actions=[
                SuggestedAction(
                    action_type="prescribe",
                    priority="immediate",
                    description="Dual antiplatelet therapy (DAPT)",
                    prescription_prefill=PrescriptionPrefill(
                        drug_name="Ticagrelor",
                        atc_code="B01AC24",
                        strength="90mg",
                        frequency="BD",
                        indication="ACS - high GRACE score",
                        notes="Loading dose: 180mg STAT"
                    )
                ),
                SuggestedAction(
                    action_type="order_lab",
                    priority="immediate",
                    description="Serial cardiac markers (Troponin at 0, 3, 6 hours)",
                    lab_tests=["49563-0"]  # hs-TnI
                ),
                SuggestedAction(
                    action_type="flag",
                    priority="immediate",
                    description="Consider urgent invasive strategy within 24 hours",
                    rationale="GRACE >140 indicates high-risk ACS requiring early catheterization"
                ),
                SuggestedAction(
                    action_type="schedule_followup",
                    priority="immediate",
                    description="Schedule cardiac catheterization",
                    followup_days=0,
                    followup_type="procedure"
                ),
            ]
        ),
        ActionRule(
            condition=lambda score, _: 109 <= score <= 140,
            actions=[
                SuggestedAction(
                    action_type="prescribe",
                    priority="soon",
                    description="Dual antiplatelet therapy (DAPT)",
                    prescription_prefill=PrescriptionPrefill(
                        drug_name="Clopidogrel",
                        atc_code="B01AC04",
                        strength="75mg",
                        frequency="OD",
                        indication="ACS - intermediate GRACE score",
                        notes="Loading dose: 300mg STAT"
                    )
                ),
                SuggestedAction(
                    action_type="order_lab",
                    priority="soon",
                    description="Repeat troponin in 3-6 hours",
                    lab_tests=["49563-0"]
                ),
                SuggestedAction(
                    action_type="schedule_followup",
                    priority="soon",
                    description="Consider invasive strategy within 72 hours",
                    followup_days=3,
                    followup_type="procedure"
                ),
            ]
        ),
    ],

    "prevent": [
        ActionRule(
            condition=lambda risk, _: risk.get("ascvd_10yr", 0) >= 20,
            actions=[
                SuggestedAction(
                    action_type="prescribe",
                    priority="soon",
                    description="High-intensity statin therapy",
                    prescription_prefill=PrescriptionPrefill(
                        drug_name="Atorvastatin",
                        atc_code="C10AA05",
                        strength="40mg",
                        frequency="OD",
                        route="oral",
                        indication="Primary ASCVD prevention - high 10-year risk",
                        alternatives=[
                            AlternativeDrug("Rosuvastatin", "C10AA07", "20mg OD"),
                        ]
                    )
                ),
                SuggestedAction(
                    action_type="order_lab",
                    priority="routine",
                    description="Baseline liver function before starting statin",
                    lab_panel_code="LIVER_FUNCTION"
                ),
                SuggestedAction(
                    action_type="schedule_followup",
                    priority="routine",
                    description="Follow-up lipid panel in 6-12 weeks",
                    followup_days=56,
                    followup_type="follow_up"
                ),
            ]
        ),
        ActionRule(
            condition=lambda risk, _: 7.5 <= risk.get("ascvd_10yr", 0) < 20,
            actions=[
                SuggestedAction(
                    action_type="prescribe",
                    priority="routine",
                    description="Moderate-intensity statin therapy",
                    prescription_prefill=PrescriptionPrefill(
                        drug_name="Atorvastatin",
                        atc_code="C10AA05",
                        strength="20mg",
                        frequency="OD",
                        indication="Primary ASCVD prevention - borderline-intermediate risk",
                    )
                ),
            ]
        ),
    ],

    "hasbled": [
        ActionRule(
            condition=lambda score, _: score >= 3,
            actions=[
                SuggestedAction(
                    action_type="flag",
                    priority="soon",
                    description="High bleeding risk - review anticoagulation dose and duration",
                    rationale="HAS-BLED ≥3 does NOT contraindicate anticoagulation but requires closer monitoring"
                ),
                SuggestedAction(
                    action_type="order_lab",
                    priority="routine",
                    description="Check CBC and coagulation panel",
                    lab_panel_code="CBC"
                ),
                SuggestedAction(
                    action_type="schedule_followup",
                    priority="routine",
                    description="Schedule 4-week medication review",
                    followup_days=28,
                    followup_type="follow_up"
                ),
            ]
        ),
    ],
}
```

### 4. Enhanced CDSS API Response

**Modify `CDSSResult` to include actions:**

```python
class CDSSResultWithActions(BaseModel):
    # Existing fields
    score: float
    risk_category: str
    interpretation: str
    recommendations: list[str]
    details: dict

    # New fields
    suggested_actions: list[SuggestedAction]
    auto_populated_from: dict[str, str]  # field → source description
    data_warnings: list[str]  # "Creatinine is 8 months old", "No recent BP"
```

**New endpoints:**
```python
# Calculate with auto-population AND actions
POST /api/cdss/{calculator}/with-actions
    Body: {patient_id: int, overrides: dict}  # Override auto-populated values

# Get actions only (if score already calculated)
GET /api/patients/{patient_id}/cdss/{calculator}/actions?score=...&risk_category=...
```

### 5. CDSS Audit Enhancement

**Extend CDSSAuditLog (migration addition):**
```sql
ALTER TABLE cdss_audit_log ADD COLUMN actions_suggested JSONB;
ALTER TABLE cdss_audit_log ADD COLUMN actions_taken JSONB;
ALTER TABLE cdss_audit_log ADD COLUMN actions_dismissed JSONB;
ALTER TABLE cdss_audit_log ADD COLUMN auto_populated_fields JSONB;
ALTER TABLE cdss_audit_log ADD COLUMN overridden_fields JSONB;
```

**Track what happened after calculation:**
```python
# When clinician acts on a suggestion:
POST /api/cdss/audit/{log_id}/action-taken
    Body: {action_index: int, action_type: str, details: dict}

# When clinician dismisses a suggestion:
POST /api/cdss/audit/{log_id}/action-dismissed
    Body: {action_index: int, reason: str}
```

### 6. Frontend: Integrated CDSS Workflow

#### Enhanced Calculator Pages

**Modify all 5 CDSS pages to add:**

1. **"Auto-fill from patient record" button** (top of form)
   - Requires patient selection (dropdown or URL param)
   - Calls auto-populate endpoint
   - Fills available fields with source indicators
   - Shows warnings for stale/missing data
   - Remaining fields highlighted for manual entry

2. **Action Cards** (below results, after calculation)
   - Each action displayed as a card with:
     - Action type icon (pill for prescribe, flask for lab, calendar for follow-up)
     - Priority badge (immediate=red, soon=amber, routine=blue)
     - Description and rationale
     - Action button:
       - "Prescribe" → opens PrescriptionForm pre-filled (Phase 1 component)
       - "Order Labs" → opens LabOrderForm pre-filled (Phase 4 component)
       - "Schedule" → opens appointment creation with pre-filled type/interval
       - "Acknowledge" → for flags, records acknowledgment
     - "Dismiss" button with required reason
   - Already-actioned items shown with checkmark

3. **Patient Context Panel** (sidebar)
   - Current medications relevant to calculation
   - Recent labs used in auto-population
   - Active problems relevant to score
   - Previous calculation history (trend of scores over time)

#### New Components

**`frontend/src/components/cdss/AutoPopulateButton.tsx`**
- Patient selector (if not already on patient page)
- Loading state while fetching data
- Shows: X of Y fields auto-filled
- Warnings for stale data
- "Override" option for each pre-filled field

**`frontend/src/components/cdss/ActionCard.tsx`**
- Action type icon + priority badge
- Description text
- Primary action button (Prescribe/Order/Schedule/Acknowledge)
- Dismiss button with reason modal
- Completed state (after action taken)

**`frontend/src/components/cdss/CDSSScoreHistory.tsx`**
- Mini chart showing score trend over time for this patient+calculator
- Annotations for when actions were taken
- Date and score for each historical calculation

**`frontend/src/components/cdss/PatientContextPanel.tsx`**
- Active medications list (compact)
- Recent lab values used in calculation
- Active problem list
- Data freshness indicators

#### Patient Dashboard Integration

**Modify `frontend/src/app/patients/[id]/page.tsx`:**
- Add "Risk Alerts" section
- Shows any recently calculated high-risk scores
- Quick-action buttons on each alert
- "Run Calculator" shortcut for each relevant calculator
- Auto-trigger risk calculation prompt when new labs arrive

### 7. Quality Metrics Dashboard

**New page:** `frontend/src/app/cdss/quality/page.tsx`

**Metrics:**
- % of AF patients with CHA2DS2-VASc calculated
- % of high CHA2DS2-VASc patients on anticoagulation
- % of high ASCVD risk patients on statin
- % of ACS patients with GRACE score calculated
- Average time from calculation to action
- Action dismissal rate and common reasons

**Backend endpoint:**
```python
GET /api/cdss/quality-metrics?from=&to=
```

---

## Cross-Cutting Gaps Identified

| Gap | Impact on Phase 5 | Addressed In |
|-----|-------------------|-------------|
| No patient social history | Can't auto-populate: smoking, alcohol | Enhancement (new module) |
| No allergy list | Can't check drug allergies when suggesting Rx | Enhancement (new module) |
| No ECG structured data | Can't auto-detect ST deviation for GRACE | Enhancement (ECG module) |
| No clinical assessment storage | Killip class not stored outside CDSS input | Enhancement |
| Encounter diagnoses not promoted | Problem list needs manual population | This phase (auto-promote) |
| No real-time notifications | Can't push alerts when labs trigger risk | Infrastructure |
| No PDF report generation | Can't generate CDSS report for patient file | Enhancement |
| TTR calculation needs INR history | Labile INR detection for HAS-BLED needs enough data | Phase 4 data |
| No drug allergy checking | Suggested prescriptions don't check allergies | Phase 1 enhancement |
| FHIR CDS Hooks not implemented | Can't integrate with external CDS services | Phase 6 |

---

## Testing

**`backend/tests/test_cdss_actions.py`:**
- Auto-population: with full data, partial data, no data
- Each calculator's action rules at various thresholds
- Action generation with patient on conflicting medications
- Audit logging of actions taken/dismissed
- Quality metrics calculation
- Stale data detection (>6 months for labs)
- Override handling (manual values replacing auto-populated)

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `backend/alembic/versions/0012_patient_problems.py` | CREATE | Problem list table |
| `backend/app/modules/patient/problem_list.py` | CREATE | Problem list service |
| `backend/app/modules/cardiology/cdss/auto_populate.py` | CREATE | Auto-population logic |
| `backend/app/modules/cardiology/cdss/actions.py` | CREATE | Action recommendation engine |
| `backend/app/modules/cardiology/cdss/router.py` | MODIFY | Add auto-populate + action endpoints |
| `backend/app/modules/cardiology/cdss/models.py` | MODIFY | Add action schemas |
| `backend/app/core/audit.py` | MODIFY | Extend CDSSAuditLog with action fields |
| `backend/app/modules/patient/service.py` | MODIFY | Add problem list to timeline |
| `frontend/src/app/cdss/grace/page.tsx` | MODIFY | Add auto-populate + actions |
| `frontend/src/app/cdss/cha2ds2vasc/page.tsx` | MODIFY | Same |
| `frontend/src/app/cdss/hasbled/page.tsx` | MODIFY | Same |
| `frontend/src/app/cdss/prevent/page.tsx` | MODIFY | Same |
| `frontend/src/app/cdss/euroscore/page.tsx` | MODIFY | Same |
| `frontend/src/components/cdss/AutoPopulateButton.tsx` | CREATE | Auto-fill UI |
| `frontend/src/components/cdss/ActionCard.tsx` | CREATE | Action suggestion card |
| `frontend/src/components/cdss/CDSSScoreHistory.tsx` | CREATE | Score trend chart |
| `frontend/src/components/cdss/PatientContextPanel.tsx` | CREATE | Context sidebar |
| `frontend/src/app/cdss/quality/page.tsx` | CREATE | Quality metrics dashboard |
| `frontend/src/app/patients/[id]/page.tsx` | MODIFY | Add risk alerts section |
| `frontend/src/lib/api/cdss.ts` | MODIFY | Add auto-populate + action APIs |
| `backend/tests/test_cdss_actions.py` | CREATE | Test suite |
