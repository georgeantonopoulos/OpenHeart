# Phase 1: Prescription Module (e-Prescribing)

## Priority: CRITICAL | Dependencies: None | Can Start Immediately

---

## Executive Summary

Anticoagulation and antiplatelet management is ~50% of a cardiologist's prescribing workload. Without prescriptions, OpenHeart cannot action CDSS recommendations (e.g., CHA2DS2-VASc >= 2 recommends anticoagulation, but there's no way to prescribe it). This phase bridges the gap between risk calculation and clinical action.

---

## Existing Infrastructure (What We Already Have)

### Database Layer
| Asset | Location | Status |
|-------|----------|--------|
| ATC Codes table | `backend/alembic/versions/20240102_0002_medical_coding_tables.py` | Complete - hierarchical drug classification |
| Gesy Medications table | Same migration | Complete - 50+ cardiac drugs with HIO product IDs |
| Full-text search index | On brand_name + generic_name | Complete - with Greek unaccent support |

### Backend Services
| Asset | Location | Status |
|-------|----------|--------|
| ATCCode model | `backend/app/modules/coding/models.py` | Complete |
| GesyMedication model | `backend/app/modules/coding/models.py` | Complete |
| Medication search API | `backend/app/modules/coding/router.py` | Complete - `GET /api/codes/medications/search` |
| ATC search API | `backend/app/modules/coding/router.py` | Complete - `GET /api/codes/atc/search` |
| CodingService | `backend/app/modules/coding/service.py` | Complete - search with Greek accent normalization |
| Permissions defined | `backend/app/core/permissions.py:53-54` | Complete - `PRESCRIPTION_READ`, `PRESCRIPTION_WRITE` |
| Permission assignments | `backend/app/core/permissions.py:108-109` | Complete - Cardiologist has both |

### Frontend Components
| Asset | Location | Status |
|-------|----------|--------|
| MedicationPicker modal | `frontend/src/components/coding/MedicationPicker.tsx` | Complete - search + select Gesy drugs |
| Medication API client | `frontend/src/lib/api/coding.ts` | Complete - `searchMedications()` function |

### Partial/Placeholder References
| Asset | Location | Status |
|-------|----------|--------|
| DischargeSummary.prescriptions | `backend/app/modules/encounter/schemas.py:64` | Defined as `Optional[list[dict]]` but unused |
| Patient profile medications | `frontend/src/app/patients/[id]/page.tsx` | Comment: "Placeholder for medications" |
| CDSS medication inputs | `backend/app/modules/cardiology/cdss/models.py` | `on_statin`, `on_bp_treatment`, `antiplatelet_or_nsaid` - read-only booleans |

---

## What's Missing (Implementation Required)

### 1. Database Migration: `0009_prescriptions.py`

**Location:** `backend/alembic/versions/20240109_0009_prescriptions.py`

#### Table: `prescriptions`
```sql
CREATE TABLE prescriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    encounter_id UUID REFERENCES encounters(encounter_id),
    prescriber_id INTEGER NOT NULL REFERENCES users(id),
    clinic_id INTEGER NOT NULL REFERENCES clinics(id),

    -- Drug identification (links to gesy_medications OR free-text)
    gesy_medication_id INTEGER REFERENCES gesy_medications(id),
    drug_name VARCHAR(200) NOT NULL,
    atc_code VARCHAR(10),
    generic_name VARCHAR(200),

    -- Prescription details
    form VARCHAR(50),          -- tablet, capsule, injection, etc.
    strength VARCHAR(50),       -- e.g., "5mg", "10mg/5ml"
    dosage VARCHAR(100),        -- e.g., "1 tablet", "5ml"
    quantity INTEGER,           -- total units dispensed

    -- Frequency & schedule
    frequency VARCHAR(20) NOT NULL DEFAULT 'OD',
        -- OD, BD, TDS, QDS, PRN, STAT, nocte, mane, custom
    frequency_custom VARCHAR(100), -- e.g., "Mon/Wed/Fri" or "Every 8 hours"
    frequency_display VARCHAR(200), -- human-readable: "Once daily", "Twice daily"

    -- Route
    route VARCHAR(30) NOT NULL DEFAULT 'oral',
        -- oral, sublingual, IV, IM, SC, topical, inhaled, transdermal, rectal, nasal

    -- Duration
    duration_days INTEGER,       -- NULL for chronic/indefinite
    start_date DATE NOT NULL DEFAULT CURRENT_DATE,
    end_date DATE,               -- auto-calculated from start_date + duration_days if set

    -- Refills
    refills_allowed INTEGER NOT NULL DEFAULT 0,
    refills_used INTEGER NOT NULL DEFAULT 0,

    -- Status lifecycle
    status VARCHAR(20) NOT NULL DEFAULT 'active',
        -- active, completed, discontinued, cancelled, on_hold, expired
    is_chronic BOOLEAN NOT NULL DEFAULT FALSE,

    -- Clinical linkage
    linked_diagnosis_icd10 VARCHAR(10), -- e.g., "I48.0" for AF
    linked_diagnosis_description VARCHAR(200),
    indication VARCHAR(500),     -- free-text clinical reason

    -- Discontinuation
    discontinued_at TIMESTAMP WITH TIME ZONE,
    discontinued_by INTEGER REFERENCES users(id),
    discontinuation_reason TEXT,

    -- Chain tracking (for renewals)
    original_prescription_id UUID REFERENCES prescriptions(id),
    renewal_count INTEGER NOT NULL DEFAULT 0,

    -- Gesy billing linkage
    gesy_claim_id VARCHAR(50),
    requires_prior_auth BOOLEAN NOT NULL DEFAULT FALSE,
    prior_auth_status VARCHAR(20), -- pending, approved, denied

    -- Notes
    prescriber_notes TEXT,
    pharmacist_notes TEXT,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE, -- soft delete

    -- RLS
    CONSTRAINT fk_clinic FOREIGN KEY (clinic_id) REFERENCES clinics(id)
);

-- Indexes
CREATE INDEX idx_prescriptions_patient_status ON prescriptions(patient_id, status);
CREATE INDEX idx_prescriptions_patient_atc ON prescriptions(patient_id, atc_code);
CREATE INDEX idx_prescriptions_prescriber ON prescriptions(prescriber_id, created_at);
CREATE INDEX idx_prescriptions_clinic ON prescriptions(clinic_id);
CREATE INDEX idx_prescriptions_status ON prescriptions(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_prescriptions_chronic ON prescriptions(patient_id) WHERE is_chronic = TRUE AND status = 'active';
```

#### Table: `prescription_interactions`
```sql
CREATE TABLE prescription_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prescription_id UUID NOT NULL REFERENCES prescriptions(id),
    interacting_prescription_id UUID REFERENCES prescriptions(id), -- NULL if checking against new Rx
    interacting_drug_name VARCHAR(200) NOT NULL,
    interacting_atc_code VARCHAR(10),

    severity VARCHAR(20) NOT NULL, -- minor, moderate, major, contraindicated
    interaction_type VARCHAR(50),   -- pharmacodynamic, pharmacokinetic, therapeutic_duplication
    description TEXT NOT NULL,
    clinical_significance TEXT,
    management_recommendation TEXT,
    source VARCHAR(100) NOT NULL DEFAULT 'openheart_cardiology_rules',

    -- Resolution
    acknowledged_by INTEGER REFERENCES users(id),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    override_reason TEXT,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_interactions_prescription ON prescription_interactions(prescription_id);
CREATE INDEX idx_interactions_severity ON prescription_interactions(severity);
```

#### Table: `medication_history`
```sql
CREATE TABLE medication_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prescription_id UUID NOT NULL REFERENCES prescriptions(id),
    previous_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    changed_by INTEGER NOT NULL REFERENCES users(id),
    changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    reason TEXT,
    change_type VARCHAR(30) NOT NULL, -- created, status_change, renewed, dose_change, discontinued
    details JSONB -- additional context (e.g., old dose, new dose)
);

CREATE INDEX idx_med_history_prescription ON medication_history(prescription_id, changed_at);
CREATE INDEX idx_med_history_patient ON medication_history(changed_at);
```

### 2. Backend Module: `backend/app/modules/prescription/`

#### File Structure
```
backend/app/modules/prescription/
    __init__.py
    models.py              - SQLAlchemy ORM models
    schemas.py             - Pydantic request/response schemas
    service.py             - Business logic
    router.py              - FastAPI endpoints
    interactions.py        - Drug-drug interaction checking engine
    cardiology_formulary.py - Curated drug list with defaults
```

#### `models.py` - Key Models
```python
class Prescription(Base):
    __tablename__ = "prescriptions"
    # All columns from migration above
    # Relationships:
    patient = relationship("Patient")
    prescriber = relationship("User", foreign_keys=[prescriber_id])
    encounter = relationship("Encounter")
    gesy_medication = relationship("GesyMedication")
    interactions = relationship("PrescriptionInteraction", back_populates="prescription")
    history = relationship("MedicationHistory", order_by="MedicationHistory.changed_at")
    original_prescription = relationship("Prescription", remote_side=[id])

class PrescriptionInteraction(Base):
    __tablename__ = "prescription_interactions"
    prescription = relationship("Prescription", back_populates="interactions")

class MedicationHistory(Base):
    __tablename__ = "medication_history"
    prescription = relationship("Prescription", back_populates="history")
```

#### `schemas.py` - Key Schemas
```python
class PrescriptionCreate(BaseModel):
    patient_id: int
    encounter_id: Optional[UUID] = None
    gesy_medication_id: Optional[int] = None
    drug_name: str
    atc_code: Optional[str] = None
    generic_name: Optional[str] = None
    form: Optional[str] = None
    strength: Optional[str] = None
    dosage: Optional[str] = None
    quantity: Optional[int] = None
    frequency: str = "OD"
    frequency_custom: Optional[str] = None
    route: str = "oral"
    duration_days: Optional[int] = None
    start_date: date = date.today()
    refills_allowed: int = 0
    is_chronic: bool = False
    linked_diagnosis_icd10: Optional[str] = None
    linked_diagnosis_description: Optional[str] = None
    indication: Optional[str] = None
    prescriber_notes: Optional[str] = None
    acknowledge_interactions: list[UUID] = []  # Pre-acknowledged interaction IDs

class PrescriptionResponse(BaseModel):
    id: UUID
    # ... all fields ...
    patient_name: Optional[str]  # Decrypted
    prescriber_name: Optional[str]
    interactions: list[InteractionResponse]
    can_renew: bool  # Computed: is_chronic and status == 'active'
    days_remaining: Optional[int]  # Computed from end_date

class PrescriptionRenew(BaseModel):
    duration_days: Optional[int] = None  # Override original duration
    quantity: Optional[int] = None
    notes: Optional[str] = None

class PrescriptionDiscontinue(BaseModel):
    reason: str  # Required
    effective_date: Optional[date] = None  # Default: today

class InteractionCheckRequest(BaseModel):
    patient_id: int
    drug_name: str
    atc_code: Optional[str] = None
    exclude_prescription_id: Optional[UUID] = None  # For updates

class InteractionCheckResponse(BaseModel):
    has_interactions: bool
    interactions: list[InteractionDetail]
    can_proceed: bool  # False if any contraindicated

class InteractionDetail(BaseModel):
    interacting_drug: str
    interacting_atc: Optional[str]
    severity: str
    interaction_type: str
    description: str
    management: Optional[str]
```

#### `service.py` - Business Logic

**Key Methods:**
```python
class PrescriptionService:
    async def create_prescription(self, data: PrescriptionCreate, user: User) -> PrescriptionResponse:
        """
        1. Validate patient exists and user has access
        2. Run interaction check against patient's active medications
        3. If major/contraindicated interactions found and not pre-acknowledged, raise
        4. Create prescription record
        5. Log to medication_history (change_type='created')
        6. Calculate end_date if duration_days provided
        7. Generate frequency_display from frequency code
        8. Return with interactions attached
        """

    async def get_active_medications(self, patient_id: int) -> list[PrescriptionResponse]:
        """Get all active prescriptions for a patient (status='active', not expired)"""

    async def get_medication_history(self, patient_id: int, include_inactive: bool = True) -> list:
        """Full medication history including discontinued"""

    async def discontinue(self, prescription_id: UUID, data: PrescriptionDiscontinue, user: User):
        """
        1. Validate prescription is active
        2. Update status to 'discontinued'
        3. Set discontinued_at, discontinued_by, discontinuation_reason
        4. Log to medication_history
        """

    async def renew_prescription(self, prescription_id: UUID, data: PrescriptionRenew, user: User):
        """
        1. Validate original is active and is_chronic
        2. Create new prescription copying original details
        3. Set original_prescription_id linkage
        4. Increment renewal_count
        5. Re-run interaction check (medications may have changed)
        6. Log to medication_history (change_type='renewed')
        """

    async def hold_prescription(self, prescription_id: UUID, reason: str, user: User):
        """Temporarily hold (e.g., pre-surgery). Status -> 'on_hold'"""

    async def resume_prescription(self, prescription_id: UUID, user: User):
        """Resume from hold. Status -> 'active'"""

    async def check_interactions(self, request: InteractionCheckRequest) -> InteractionCheckResponse:
        """
        1. Get patient's active medications
        2. Run interaction engine against proposed drug
        3. Return severity-sorted interactions
        """

    async def expire_completed_prescriptions(self):
        """Background task: Mark prescriptions past end_date as 'expired'"""
```

#### `interactions.py` - Drug Interaction Engine

**Architecture:**
```python
# Cardiology-specific interaction rules
CARDIOLOGY_INTERACTIONS = [
    # Anticoagulant + Antiplatelet = Bleeding Risk
    InteractionRule(
        drug_a_atc_prefix="B01AF",  # DOACs (Apixaban, Rivaroxaban, etc.)
        drug_b_atc_prefix="B01AC",  # Antiplatelets (Aspirin, Clopidogrel, etc.)
        severity="major",
        interaction_type="pharmacodynamic",
        description="Combined anticoagulant and antiplatelet therapy significantly increases bleeding risk",
        management="Consider if dual therapy is clinically necessary. Monitor for bleeding signs. Consider PPI co-prescription."
    ),
    # Digoxin + Amiodarone = Toxicity
    InteractionRule(
        drug_a_atc="C01AA05",  # Digoxin
        drug_b_atc="C01BD01",  # Amiodarone
        severity="major",
        interaction_type="pharmacokinetic",
        description="Amiodarone increases digoxin levels by 70-100%, risking toxicity",
        management="Reduce digoxin dose by 50% when initiating amiodarone. Monitor levels."
    ),
    # ACE-I + K-sparing diuretic = Hyperkalemia
    InteractionRule(
        drug_a_atc_prefix="C09A",   # ACE inhibitors
        drug_b_atc_prefix="C03DA",  # K-sparing diuretics (Spironolactone, Eplerenone)
        severity="major",
        interaction_type="pharmacodynamic",
        description="Risk of life-threatening hyperkalemia",
        management="Monitor potassium closely. Start K-sparing diuretic at low dose. Check K+ within 1 week."
    ),
    # Statin + Fibrate = Rhabdomyolysis
    InteractionRule(
        drug_a_atc_prefix="C10AA",  # Statins
        drug_b_atc_prefix="C10AB",  # Fibrates
        severity="major",
        interaction_type="pharmacokinetic",
        description="Increased risk of myopathy and rhabdomyolysis",
        management="Prefer fenofibrate over gemfibrozil. Monitor CK levels. Educate patient on myalgia symptoms."
    ),
    # Beta-blocker + Non-dihydropyridine CCB = Heart Block
    InteractionRule(
        drug_a_atc_prefix="C07",    # Beta-blockers
        drug_b_atc_codes=["C08DA01", "C08DB01"],  # Verapamil, Diltiazem
        severity="contraindicated",
        interaction_type="pharmacodynamic",
        description="Combined negative chronotropic/dromotropic effects risk severe bradycardia or heart block",
        management="AVOID combination. Use dihydropyridine CCB (Amlodipine) instead if CCB needed."
    ),
    # Warfarin + Amiodarone = INR elevation
    InteractionRule(
        drug_a_atc="B01AA03",  # Warfarin
        drug_b_atc="C01BD01",  # Amiodarone
        severity="major",
        interaction_type="pharmacokinetic",
        description="Amiodarone inhibits warfarin metabolism, increasing INR by 30-50%",
        management="Reduce warfarin dose by 30-50%. Check INR weekly for 4-6 weeks."
    ),
    # DOAC + Strong CYP3A4/P-gp inhibitors
    InteractionRule(
        drug_a_atc_prefix="B01AF",  # DOACs
        drug_b_atc_codes=["J02AC01", "J02AC02"],  # Ketoconazole, Itraconazole
        severity="contraindicated",
        interaction_type="pharmacokinetic",
        description="Strong CYP3A4/P-gp inhibition markedly increases DOAC levels",
        management="AVOID combination. Consider alternative antifungal or switch to warfarin with INR monitoring."
    ),
    # Therapeutic duplication: Two anticoagulants
    InteractionRule(
        drug_a_atc_prefix="B01A",
        drug_b_atc_prefix="B01A",
        severity="major",
        interaction_type="therapeutic_duplication",
        description="Duplicate anticoagulant therapy - extreme bleeding risk",
        management="Review if intentional bridging therapy. Ensure single anticoagulant for maintenance."
    ),
    # Nitrate + PDE5 inhibitor = Severe hypotension
    InteractionRule(
        drug_a_atc_prefix="C01DA",  # Nitrates
        drug_b_atc_prefix="G04BE",  # PDE5 inhibitors (Sildenafil, Tadalafil)
        severity="contraindicated",
        interaction_type="pharmacodynamic",
        description="Synergistic vasodilation causing potentially fatal hypotension",
        management="ABSOLUTE contraindication. Wait 24-48h after PDE5i before nitrate use."
    ),
    # Metformin + Contrast (relevant for cath lab)
    InteractionRule(
        drug_a_atc="A10BA02",  # Metformin
        drug_b_category="contrast_media",
        severity="moderate",
        interaction_type="pharmacodynamic",
        description="Risk of lactic acidosis with iodinated contrast in renal impairment",
        management="Hold metformin 48h before and after contrast. Check eGFR before resuming."
    ),
]

class InteractionEngine:
    def check_interactions(self, new_drug_atc: str, active_medications: list[Prescription]) -> list[InteractionDetail]:
        """
        1. Check new drug against each active medication
        2. Match by exact ATC code or prefix (therapeutic class)
        3. Check both directions (A interacts with B = B interacts with A)
        4. Check therapeutic duplication (same ATC level 4 prefix)
        5. Return sorted by severity (contraindicated > major > moderate > minor)
        """

    def check_therapeutic_duplication(self, new_atc: str, active_atcs: list[str]) -> Optional[InteractionDetail]:
        """Flag if same therapeutic subgroup (ATC level 4) already prescribed"""

    def check_renal_adjustment(self, drug_atc: str, egfr: Optional[float]) -> Optional[str]:
        """Flag drugs needing dose adjustment in CKD (DOACs, metformin, digoxin)"""
```

#### `cardiology_formulary.py` - Curated Drug Defaults

**Structure:**
```python
CARDIOLOGY_FORMULARY = {
    "antiplatelets": [
        DrugTemplate(
            generic_name="Aspirin",
            atc_code="B01AC06",
            default_strength="75mg",
            default_form="tablet",
            default_frequency="OD",
            default_route="oral",
            is_chronic=True,
            common_indications=["Post-ACS", "Secondary prevention", "Post-PCI"],
            available_strengths=["75mg", "100mg", "300mg"],
        ),
        DrugTemplate(
            generic_name="Clopidogrel",
            atc_code="B01AC04",
            default_strength="75mg",
            ...
            loading_dose="300mg STAT",
        ),
        DrugTemplate(
            generic_name="Ticagrelor",
            atc_code="B01AC24",
            default_strength="90mg",
            default_frequency="BD",
            loading_dose="180mg STAT",
            ...
        ),
        # ... Prasugrel
    ],
    "anticoagulants": [
        DrugTemplate(
            generic_name="Apixaban",
            atc_code="B01AF02",
            default_strength="5mg",
            default_frequency="BD",
            renal_adjustment={"egfr_threshold": 25, "adjusted_dose": "2.5mg BD"},
            ...
        ),
        # Rivaroxaban, Edoxaban, Dabigatran, Warfarin, Enoxaparin
    ],
    "statins": [...],       # Atorvastatin, Rosuvastatin, Simvastatin, Pravastatin
    "beta_blockers": [...],  # Bisoprolol, Metoprolol, Carvedilol, Nebivolol, Atenolol
    "ace_inhibitors": [...], # Ramipril, Perindopril, Enalapril, Lisinopril
    "arbs": [...],           # Valsartan, Candesartan, Irbesartan, Losartan, Telmisartan
    "ccbs": [...],           # Amlodipine, Nifedipine, Diltiazem, Verapamil
    "diuretics": [...],      # Furosemide, Bumetanide, Spironolactone, Eplerenone, HCTZ, Indapamide
    "antiarrhythmics": [...], # Amiodarone, Flecainide, Dronedarone, Sotalol
    "nitrates": [...],       # GTN, ISDN, ISMN
    "heart_failure": [...],  # Sacubitril/Valsartan, Ivabradine, Dapagliflozin, Empagliflozin
    "other": [...],          # Doxazosin, Moxonidine, Ranolazine
}
```

#### `router.py` - API Endpoints

```python
# Patient Prescriptions
POST   /api/patients/{patient_id}/prescriptions          # Create new prescription
GET    /api/patients/{patient_id}/prescriptions          # List all (with status filter)
GET    /api/patients/{patient_id}/prescriptions/active   # Active medications only
GET    /api/patients/{patient_id}/prescriptions/chronic  # Chronic medications

# Individual Prescription Operations
GET    /api/prescriptions/{id}                           # Get prescription detail
PUT    /api/prescriptions/{id}                           # Update (dose change, notes)
POST   /api/prescriptions/{id}/discontinue               # Discontinue with reason
POST   /api/prescriptions/{id}/renew                     # Renew chronic prescription
POST   /api/prescriptions/{id}/hold                      # Put on hold
POST   /api/prescriptions/{id}/resume                    # Resume from hold
GET    /api/prescriptions/{id}/history                   # Medication change history

# Interaction Checking
POST   /api/prescriptions/interactions/check             # Check before prescribing
GET    /api/prescriptions/{id}/interactions              # View existing interactions

# Formulary
GET    /api/formulary/cardiology                         # Curated cardiology drugs
GET    /api/formulary/search                             # Search all formulary
GET    /api/formulary/categories                         # List drug categories
GET    /api/formulary/{atc_code}/defaults                # Get default dosing for drug
```

### 3. Frontend Implementation

#### Pages to Create

**`frontend/src/app/patients/[id]/prescriptions/page.tsx`** - Medication List
- Active medications tab (default)
- History tab (all prescriptions including discontinued)
- Each medication card shows: drug name, strength, frequency, route, start date, status badge
- Quick actions: Renew, Hold, Discontinue
- "New Prescription" button
- Filter by category (Anticoagulants, Antiplatelets, etc.)

**`frontend/src/app/patients/[id]/prescriptions/new/page.tsx`** - New Prescription
- Step 1: Drug selection (search formulary or free-text)
- Step 2: Dosage configuration (pre-filled from formulary defaults)
- Step 3: Interaction check result + acknowledge if needed
- Step 4: Review and confirm
- Pre-fill from CDSS recommendation if navigated from calculator

**`frontend/src/app/patients/[id]/prescriptions/[rxId]/page.tsx`** - Prescription Detail
- Full prescription information
- Medication timeline (all status changes)
- Interaction alerts (if any)
- Renewal chain (links to previous/next prescriptions)
- Actions: Renew, Hold, Discontinue, Print

#### Components to Create

**`frontend/src/components/prescription/DrugSearch.tsx`**
- Unified search across formulary + Gesy medications
- Results grouped by therapeutic category
- Shows: drug name, strength, form, ATC code, Gesy coverage badge
- "Quick pick" buttons for common cardiology drugs
- Recent prescriptions for this patient highlighted

**`frontend/src/components/prescription/PrescriptionForm.tsx`**
- Drug name (from DrugSearch or manual entry)
- Strength selector (from available strengths)
- Dosage input
- Frequency picker (OD/BD/TDS/QDS/PRN/custom)
- Route selector
- Duration: chronic toggle vs. finite days
- Start date, refills
- Indication/diagnosis linkage (ICD-10 search)
- Notes field

**`frontend/src/components/prescription/InteractionAlert.tsx`**
- Modal for major/contraindicated interactions (must acknowledge or cancel)
- Inline warning for moderate interactions
- Info badge for minor interactions
- Shows: severity badge, interacting drug, description, management recommendation
- "Acknowledge & Proceed" with required reason text for major/contraindicated
- "Cancel Prescription" button

**`frontend/src/components/prescription/MedicationList.tsx`**
- Compact list of active medications for patient header/sidebar
- Status badges: active (green), on_hold (amber), chronic (blue ring)
- Drug name, strength, frequency on each line
- Used in patient profile sidebar

**`frontend/src/components/prescription/MedicationTimeline.tsx`**
- Chronological view of all medication events
- Color-coded: started (green), discontinued (red), renewed (blue), held (amber)
- Shows reason for each change
- Links to prescription detail

**`frontend/src/components/prescription/PrescriptionPrint.tsx`**
- Cyprus prescription pad format
- Clinic letterhead, prescriber details, registration number
- Patient demographics
- Drug details: name, strength, dosage, frequency, quantity, refills
- Prescriber signature line
- Date in DD/MM/YYYY format
- Print/PDF export

#### API Client

**`frontend/src/lib/api/prescriptions.ts`**
```typescript
// CRUD
createPrescription(token, patientId, data)
listPrescriptions(token, patientId, filters?)
getActiveMedications(token, patientId)
getPrescription(token, prescriptionId)

// Actions
discontinuePrescription(token, prescriptionId, reason)
renewPrescription(token, prescriptionId, data?)
holdPrescription(token, prescriptionId, reason)
resumePrescription(token, prescriptionId)

// Interactions
checkInteractions(token, patientId, drugName, atcCode?)
acknowledgeInteraction(token, interactionId, reason)

// Formulary
searchFormulary(token, query)
getCardiologyFormulary(token)
getDrugDefaults(token, atcCode)

// History
getPrescriptionHistory(token, prescriptionId)
```

### 4. Integration Points

#### Wire into Main App
- `backend/app/main.py`: Add `app.include_router(prescription_router, prefix="/api", tags=["Prescriptions"])`
- `frontend/src/app/patients/[id]/page.tsx`: Add medications section with MedicationList component
- Patient timeline: Add prescription events to timeline aggregation

#### Wire into Encounter
- `backend/app/modules/encounter/service.py`: When completing encounter, optionally link prescriptions created during the encounter
- `DischargeSummary.prescriptions`: Populate from prescriptions created in that encounter

#### Wire into CDSS (Phase 5 prerequisite)
- CDSS forms: Add "Prescribe" action button on results page
- Auto-fill prescription from CDSS recommendation
- Pre-populate `indication` from calculator context

### 5. Seed Data Updates

**`backend/app/core/seed.py` additions:**
- 3-5 sample prescriptions per test patient
- Mix of active, discontinued, and chronic medications
- At least one interaction scenario for testing

### 6. Testing

**`backend/tests/test_prescriptions.py`:**
- Create prescription: valid, invalid patient, missing required fields
- Interaction detection: each major cardiology interaction pair
- Therapeutic duplication detection
- Discontinue: valid, already discontinued, permission denied
- Renew: chronic only, non-chronic rejection
- Hold/Resume cycle
- Expired prescription detection
- Formulary search: by name, by ATC, by category
- Permission enforcement: Nurse cannot prescribe, Receptionist cannot view

---

## Cross-Cutting Gaps Identified (Not Prescription-Specific)

These gaps affect Phase 1 but belong to other phases:

| Gap | Impact on Phase 1 | Addressed In |
|-----|-------------------|-------------|
| No patient problem list model | Can't auto-link diagnoses to prescriptions | Phase 5 |
| No lab results storage | Can't check renal function for dose adjustments | Phase 4 |
| Vitals panel is placeholder | Can't show BP context when prescribing antihypertensives | Phase 4 |
| No notification system | Can't alert on prescription expiry or renewal due | Phase 2 |
| User management endpoints missing | Can't manage prescriber credentials | Pre-existing gap |
| No background task scheduler | Can't auto-expire prescriptions | Infrastructure |
| Encounter billing_status not wired | Can't link prescriptions to billing claims | Phase 3 |
| FHIR MedicationRequest not implemented | Can't export prescriptions in standard format | Phase 6 |

---

## Files to Create/Modify Summary

| File | Action | Purpose |
|------|--------|---------|
| `backend/alembic/versions/20240109_0009_prescriptions.py` | CREATE | Database migration |
| `backend/app/modules/prescription/__init__.py` | CREATE | Module init |
| `backend/app/modules/prescription/models.py` | CREATE | SQLAlchemy models |
| `backend/app/modules/prescription/schemas.py` | CREATE | Pydantic schemas |
| `backend/app/modules/prescription/service.py` | CREATE | Business logic |
| `backend/app/modules/prescription/router.py` | CREATE | API endpoints |
| `backend/app/modules/prescription/interactions.py` | CREATE | Interaction engine |
| `backend/app/modules/prescription/cardiology_formulary.py` | CREATE | Drug defaults |
| `backend/app/main.py` | MODIFY | Register router |
| `backend/app/core/seed.py` | MODIFY | Add sample prescriptions |
| `backend/tests/test_prescriptions.py` | CREATE | Test suite |
| `frontend/src/app/patients/[id]/prescriptions/page.tsx` | CREATE | Medication list |
| `frontend/src/app/patients/[id]/prescriptions/new/page.tsx` | CREATE | New Rx form |
| `frontend/src/app/patients/[id]/prescriptions/[rxId]/page.tsx` | CREATE | Rx detail |
| `frontend/src/components/prescription/DrugSearch.tsx` | CREATE | Drug autocomplete |
| `frontend/src/components/prescription/PrescriptionForm.tsx` | CREATE | Rx form |
| `frontend/src/components/prescription/InteractionAlert.tsx` | CREATE | Interaction UI |
| `frontend/src/components/prescription/MedicationList.tsx` | CREATE | Compact med list |
| `frontend/src/components/prescription/MedicationTimeline.tsx` | CREATE | Rx history |
| `frontend/src/components/prescription/PrescriptionPrint.tsx` | CREATE | Print format |
| `frontend/src/lib/api/prescriptions.ts` | CREATE | API client |
| `frontend/src/app/patients/[id]/page.tsx` | MODIFY | Add medications section |
| `backend/app/modules/patient/service.py` | MODIFY | Add Rx events to timeline |
