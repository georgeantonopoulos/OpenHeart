# Phase 4: Lab Interface & Longitudinal Vitals Trending

## Priority: HIGH | Dependencies: Patient module (exists) | Prerequisite for Phase 5

---

## Executive Summary

Cardiology is data-heavy. A cardiologist tracks Troponin, CK-MB, BNP, Lipid Panels, INR, and eGFR over time. Currently, OpenHeart stores vital signs per encounter but has **no lab results storage**, **no trending visualization**, and the **VitalsPanel is a placeholder**. The CDSS calculators require manual data entry for values that should come from the patient record. This phase adds lab result management, vitals trending charts, and the data foundation Phase 5 needs for auto-population.

---

## Existing Infrastructure (What We Already Have)

### Backend - Vitals System (Complete but Limited to Encounters)
| Feature | Location | Status |
|---------|----------|--------|
| Vitals model | `backend/app/modules/encounter/models.py` | HR, BP(sys/dia), RR, SpO2, temp, weight, height, BMI |
| Vitals recording | `encounter/router.py` | `POST /encounters/{id}/vitals` |
| Per-encounter vitals | `encounter/router.py` | `GET /encounters/{id}/vitals` |
| Latest vitals | `encounter/router.py` | `GET /encounters/patients/{id}/vitals/latest` |
| Vitals trend | `encounter/router.py` | `GET /encounters/patients/{id}/vitals/trend` (last 20 readings) |
| BMI auto-calculation | `encounter/service.py` | From height + weight |
| Position tracking | `encounter/models.py` | sitting/standing/supine/prone/lateral |
| Patient+time index | `encounter/models.py` | `idx_vitals_patient_time` |

### Backend - LOINC Codes (Seeded Reference Data)
| Feature | Location | Status |
|---------|----------|--------|
| LOINC code model | `backend/app/modules/coding/models.py` | LOINCCode with component, property, system, scale |
| 27 cardiac lab codes | `backend/scripts/seed_codes.py` | Troponin, BNP, Lipids, Renal, Coag, Metabolic |
| LOINC search API | `backend/app/modules/coding/router.py` | `GET /api/codes/loinc/search` |

### Backend - DICOM SR Parsing (Echo Measurements)
| Feature | Location | Status |
|---------|----------|--------|
| SR parser | `backend/app/integrations/dicom/sr_parser.py` | 40+ concept codes mapped |
| EchoMeasurements schema | `backend/app/integrations/dicom/schemas.py` | LVEF, dimensions, diastolic, valves, hemodynamics |
| CathLabReport schema | Same | Access, contrast, coronary anatomy, stents, hemodynamics |
| Concept code map | `sr_parser.py:37-117` | LOINC, SNOMED-CT, DCM code mappings |

### Backend - CDSS Inputs (Lab Values Referenced)
| Calculator | Lab Values Used | Currently |
|-----------|----------------|-----------|
| GRACE | Creatinine (mg/dL) | Manual input |
| PREVENT | Total cholesterol, HDL, eGFR, HbA1c, UACR | Manual input |
| HAS-BLED | INR (labile check), renal dysfunction, liver dysfunction | Boolean manual input |
| EuroSCORE II | Creatinine/dialysis, pulmonary HTN | Manual input |

### Frontend - Visualization Infrastructure
| Feature | Location | Status |
|---------|----------|--------|
| Recharts library | `frontend/package.json` | Installed (`^2.15.4`) but UNUSED |
| VitalsPanel component | `frontend/src/app/patients/[id]/components/VitalsPanel.tsx` | PLACEHOLDER - shows "--" for all values |
| Patient timeline | `frontend/src/app/patients/[id]/components/Timeline.tsx` | Shows "observation" events but no detail |

### Backend - Patient Timeline (Aggregates Vitals)
| Feature | Location | Status |
|---------|----------|--------|
| Timeline aggregation | `backend/app/modules/patient/service.py` | Includes vitals as timeline events |
| Permission-filtered | Same | Requires Permission.OBSERVATION_READ |

---

## What's Missing (Implementation Required)

### 1. Database Migration: `0011_lab_results.py`

**Location:** `backend/alembic/versions/20240111_0011_lab_results.py`

#### Table: `lab_orders`
```sql
CREATE TABLE lab_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    encounter_id UUID REFERENCES encounters(encounter_id),
    clinic_id INTEGER NOT NULL REFERENCES clinics(id),
    ordering_provider_id INTEGER NOT NULL REFERENCES users(id),

    -- Order identification
    order_number VARCHAR(50) UNIQUE, -- Internal order number
    placer_order_number VARCHAR(50), -- HL7 OBR-2 equivalent
    filler_order_number VARCHAR(50), -- HL7 OBR-3 equivalent (from lab)

    -- Order details
    panel_code VARCHAR(20),      -- Reference to lab_panels
    panel_name VARCHAR(200),
    order_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    priority VARCHAR(10) NOT NULL DEFAULT 'routine', -- routine, urgent, stat
    clinical_notes TEXT,         -- Reason for ordering

    -- Lab facility
    lab_facility VARCHAR(200),   -- External lab name
    lab_facility_code VARCHAR(50), -- Lab identifier

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'ordered',
        -- ordered, collected, processing, resulted, partially_resulted, cancelled
    collected_at TIMESTAMP WITH TIME ZONE,
    resulted_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    cancellation_reason TEXT,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_lab_orders_patient ON lab_orders(patient_id, order_date DESC);
CREATE INDEX idx_lab_orders_status ON lab_orders(status);
CREATE INDEX idx_lab_orders_clinic ON lab_orders(clinic_id, order_date DESC);
CREATE INDEX idx_lab_orders_filler ON lab_orders(filler_order_number);
```

#### Table: `lab_results`
```sql
CREATE TABLE lab_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lab_order_id UUID REFERENCES lab_orders(id),  -- NULL if manually entered
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    clinic_id INTEGER NOT NULL REFERENCES clinics(id),

    -- Test identification
    loinc_code VARCHAR(20),      -- LOINC code (e.g., "2160-0" for Creatinine)
    test_code VARCHAR(50),       -- Lab-specific test code
    test_name VARCHAR(200) NOT NULL, -- Human-readable name

    -- Result value
    value_text VARCHAR(200),     -- Raw result as text (handles qualitative: "Positive")
    value_numeric FLOAT,         -- Parsed numeric value (for trending)
    unit VARCHAR(50),            -- Unit of measurement (mg/dL, ng/mL, etc.)

    -- Reference ranges
    reference_range_low FLOAT,
    reference_range_high FLOAT,
    reference_range_text VARCHAR(100), -- Display: "<0.04 ng/mL" or "3.5-5.0 mmol/L"

    -- Interpretation
    abnormal_flag VARCHAR(20) NOT NULL DEFAULT 'normal',
        -- normal, low, high, critical_low, critical_high, abnormal, indeterminate
    critical_value BOOLEAN NOT NULL DEFAULT FALSE, -- Requires immediate notification

    -- Result metadata
    result_status VARCHAR(20) NOT NULL DEFAULT 'final',
        -- preliminary, final, corrected, cancelled
    result_datetime TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    performing_lab VARCHAR(200),
    performing_lab_code VARCHAR(50),

    -- Source
    entry_method VARCHAR(20) NOT NULL DEFAULT 'manual',
        -- manual, csv_import, pdf_import, hl7, dicom_sr
    source_document_id VARCHAR(200), -- Reference to uploaded file if imported

    -- Notes
    comments TEXT,               -- Lab comments
    clinical_notes TEXT,         -- Clinician notes on result

    -- Audit
    entered_by INTEGER REFERENCES users(id),
    verified_by INTEGER REFERENCES users(id),
    verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_lab_results_patient_loinc ON lab_results(patient_id, loinc_code, result_datetime DESC);
CREATE INDEX idx_lab_results_patient_date ON lab_results(patient_id, result_datetime DESC);
CREATE INDEX idx_lab_results_order ON lab_results(lab_order_id);
CREATE INDEX idx_lab_results_abnormal ON lab_results(patient_id, abnormal_flag)
    WHERE abnormal_flag != 'normal';
CREATE INDEX idx_lab_results_critical ON lab_results(critical_value, created_at)
    WHERE critical_value = TRUE;
CREATE INDEX idx_lab_results_loinc ON lab_results(loinc_code, result_datetime DESC);
```

#### Table: `lab_panels`
```sql
CREATE TABLE lab_panels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    loinc_codes JSONB NOT NULL DEFAULT '[]', -- Array of LOINC codes in panel
    category VARCHAR(50),        -- cardiac_markers, lipid, coagulation, renal, etc.
    is_cardiology_default BOOLEAN NOT NULL DEFAULT FALSE,
    display_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

### 2. Cardiology Lab Panels (Seed Data)

```python
CARDIOLOGY_PANELS = [
    LabPanel(
        code="CARDIAC_MARKERS",
        name="Cardiac Markers",
        category="cardiac_markers",
        is_cardiology_default=True,
        loinc_codes=[
            {"code": "49563-0", "name": "hs-Troponin I", "unit": "ng/L", "ref_low": 0, "ref_high": 14},
            {"code": "67151-1", "name": "hs-Troponin T", "unit": "ng/L", "ref_low": 0, "ref_high": 14},
            {"code": "13969-1", "name": "CK-MB", "unit": "ng/mL", "ref_low": 0, "ref_high": 5},
            {"code": "30934-4", "name": "BNP", "unit": "pg/mL", "ref_low": 0, "ref_high": 100},
            {"code": "33762-6", "name": "NT-proBNP", "unit": "pg/mL", "ref_low": 0, "ref_high": 125},
        ]
    ),
    LabPanel(
        code="LIPID_PANEL",
        name="Lipid Panel",
        category="lipid",
        is_cardiology_default=True,
        loinc_codes=[
            {"code": "2093-3", "name": "Total Cholesterol", "unit": "mg/dL", "ref_low": 0, "ref_high": 200},
            {"code": "13457-7", "name": "LDL Cholesterol", "unit": "mg/dL", "ref_low": 0, "ref_high": 100},
            {"code": "2085-9", "name": "HDL Cholesterol", "unit": "mg/dL", "ref_low": 40, "ref_high": 999},
            {"code": "2571-8", "name": "Triglycerides", "unit": "mg/dL", "ref_low": 0, "ref_high": 150},
            {"code": "43396-1", "name": "Non-HDL Cholesterol", "unit": "mg/dL", "ref_low": 0, "ref_high": 130},
        ]
    ),
    LabPanel(
        code="COAGULATION",
        name="Coagulation Panel",
        category="coagulation",
        is_cardiology_default=True,
        loinc_codes=[
            {"code": "6301-6", "name": "INR", "unit": "", "ref_low": 0.8, "ref_high": 1.2},
            {"code": "5902-2", "name": "PT", "unit": "seconds", "ref_low": 11, "ref_high": 13.5},
            {"code": "3173-2", "name": "aPTT", "unit": "seconds", "ref_low": 25, "ref_high": 35},
            {"code": "48065-7", "name": "D-dimer", "unit": "ng/mL", "ref_low": 0, "ref_high": 500},
        ]
    ),
    LabPanel(
        code="RENAL_FUNCTION",
        name="Renal Function",
        category="renal",
        is_cardiology_default=True,
        loinc_codes=[
            {"code": "2160-0", "name": "Creatinine", "unit": "mg/dL", "ref_low": 0.6, "ref_high": 1.2},
            {"code": "33914-3", "name": "eGFR (CKD-EPI)", "unit": "mL/min/1.73m²", "ref_low": 90, "ref_high": 999},
            {"code": "3094-0", "name": "BUN", "unit": "mg/dL", "ref_low": 7, "ref_high": 20},
            {"code": "2823-3", "name": "Potassium", "unit": "mmol/L", "ref_low": 3.5, "ref_high": 5.0},
            {"code": "2951-2", "name": "Sodium", "unit": "mmol/L", "ref_low": 136, "ref_high": 145},
        ]
    ),
    LabPanel(
        code="THYROID",
        name="Thyroid Function",
        category="thyroid",
        is_cardiology_default=True,  # Amiodarone monitoring, AF workup
        loinc_codes=[
            {"code": "3016-3", "name": "TSH", "unit": "mIU/L", "ref_low": 0.4, "ref_high": 4.0},
            {"code": "3024-7", "name": "Free T4", "unit": "ng/dL", "ref_low": 0.8, "ref_high": 1.8},
        ]
    ),
    LabPanel(
        code="LIVER_FUNCTION",
        name="Liver Function",
        category="liver",
        is_cardiology_default=True,  # Statin monitoring
        loinc_codes=[
            {"code": "1742-6", "name": "ALT", "unit": "U/L", "ref_low": 0, "ref_high": 40},
            {"code": "1920-8", "name": "AST", "unit": "U/L", "ref_low": 0, "ref_high": 40},
            {"code": "6768-6", "name": "ALP", "unit": "U/L", "ref_low": 40, "ref_high": 130},
            {"code": "1975-2", "name": "Total Bilirubin", "unit": "mg/dL", "ref_low": 0.1, "ref_high": 1.2},
        ]
    ),
    LabPanel(
        code="HBA1C",
        name="HbA1c",
        category="metabolic",
        is_cardiology_default=True,  # CV risk factor
        loinc_codes=[
            {"code": "4548-4", "name": "HbA1c", "unit": "%", "ref_low": 4.0, "ref_high": 5.6},
        ]
    ),
    LabPanel(
        code="CBC",
        name="Complete Blood Count",
        category="hematology",
        is_cardiology_default=True,  # Bleeding risk, pre-procedure
        loinc_codes=[
            {"code": "718-7", "name": "Hemoglobin", "unit": "g/dL", "ref_low": 12, "ref_high": 17},
            {"code": "6690-2", "name": "WBC", "unit": "×10³/µL", "ref_low": 4.0, "ref_high": 11.0},
            {"code": "777-3", "name": "Platelet Count", "unit": "×10³/µL", "ref_low": 150, "ref_high": 400},
        ]
    ),
    LabPanel(
        code="INFLAMMATORY",
        name="Inflammatory Markers",
        category="inflammatory",
        is_cardiology_default=False,
        loinc_codes=[
            {"code": "30522-7", "name": "hs-CRP", "unit": "mg/L", "ref_low": 0, "ref_high": 3.0},
            {"code": "1988-5", "name": "CRP", "unit": "mg/L", "ref_low": 0, "ref_high": 5.0},
        ]
    ),
]
```

### 3. Backend Module: `backend/app/modules/labs/`

#### File Structure
```
backend/app/modules/labs/
    __init__.py
    models.py           - LabOrder, LabResult, LabPanel ORM models
    schemas.py          - Pydantic schemas for all operations
    service.py          - Business logic (CRUD, trending, import)
    router.py           - API endpoints
    import_csv.py       - CSV lab import parser
    import_pdf.py       - PDF lab report parser (future)
    panels.py           - Panel definitions and seed data
    alerts.py           - Critical value detection and alerting
```

#### `service.py` - Key Methods

```python
class LabService:
    async def create_lab_order(self, data: LabOrderCreate, user: User) -> LabOrderResponse:
        """Create lab order with panel expansion to individual test codes"""

    async def record_results(self, order_id: UUID, results: list[LabResultCreate], user: User):
        """
        1. Validate results against order's expected tests
        2. Parse numeric values from text
        3. Calculate abnormal flags from reference ranges
        4. Detect critical values → generate alert
        5. Mark order as 'resulted' or 'partially_resulted'
        """

    async def record_manual_result(self, data: ManualLabResultCreate, user: User):
        """Direct result entry without order (e.g., external lab report)"""

    async def get_patient_labs(self, patient_id: int, loinc_code: Optional[str],
                               from_date: Optional[date], to_date: Optional[date]) -> list:
        """Get lab results with optional LOINC/date filtering"""

    async def get_lab_trend(self, patient_id: int, loinc_code: str,
                            limit: int = 20) -> LabTrendResponse:
        """
        Returns time-series data for a specific lab test:
        - data_points: [{datetime, value, abnormal_flag}]
        - min_value, max_value, avg_value
        - reference_range_low, reference_range_high
        - trend_direction: improving/worsening/stable
        """

    async def get_latest_labs(self, patient_id: int) -> dict[str, LabResultResponse]:
        """Latest value for each LOINC code (for CDSS auto-population)"""

    async def get_patient_lab_summary(self, patient_id: int) -> LabSummary:
        """
        Aggregated view:
        - Latest result per category (cardiac, lipid, renal, coag)
        - Abnormal count
        - Last lab date
        - Pending orders
        """

    async def import_csv(self, patient_id: int, file_content: bytes, mapping: CSVMapping, user: User):
        """
        1. Parse CSV rows
        2. Map columns to LOINC codes using provided mapping
        3. Validate values and units
        4. Create lab_results records
        5. Return import summary (success/error counts)
        """

    async def detect_critical_values(self, results: list[LabResult]) -> list[CriticalAlert]:
        """
        Check results against critical thresholds:
        - Troponin > 5× ULN → Critical
        - K+ < 2.5 or > 6.0 → Critical
        - INR > 5.0 → Critical
        - eGFR < 15 → Critical
        - Platelets < 50 → Critical
        """

    async def calculate_derived_values(self, patient_id: int, results: list[LabResult]):
        """
        Auto-calculate:
        - Non-HDL = Total Chol - HDL (if both present)
        - eGFR from creatinine + age + sex (CKD-EPI)
        - LDL (Friedewald) if not directly measured
        - BMI from latest vitals weight + height
        """
```

#### `router.py` - API Endpoints

```python
# Lab Orders
POST   /api/patients/{patient_id}/lab-orders           # Create lab order
GET    /api/patients/{patient_id}/lab-orders            # List orders (with status filter)
GET    /api/lab-orders/{order_id}                       # Order detail with results
PUT    /api/lab-orders/{order_id}/cancel                # Cancel order

# Lab Results
POST   /api/lab-orders/{order_id}/results              # Record results for order
POST   /api/patients/{patient_id}/lab-results          # Manual result entry (no order)
GET    /api/patients/{patient_id}/lab-results           # All results (with filters)
GET    /api/patients/{patient_id}/lab-results/latest    # Latest per LOINC code
GET    /api/patients/{patient_id}/lab-results/summary   # Categorized summary

# Trending
GET    /api/patients/{patient_id}/labs/trend/{loinc_code}  # Time-series for specific test
GET    /api/patients/{patient_id}/labs/trends               # Multiple test trends (batch)

# Panels
GET    /api/lab-panels                                  # List available panels
GET    /api/lab-panels/cardiology                       # Cardiology-default panels

# Import
POST   /api/patients/{patient_id}/lab-results/import-csv   # CSV upload
POST   /api/patients/{patient_id}/lab-results/import-pdf   # PDF upload (future)

# Vitals Trending (enhance existing)
GET    /api/patients/{patient_id}/vitals/trends         # Multi-vital trends (batch)
```

### 4. Frontend Implementation

#### Replace VitalsPanel Placeholder

**`frontend/src/app/patients/[id]/components/VitalsPanel.tsx`** - Complete Rewrite
```typescript
// Replace placeholder with:
// 1. Fetch latest vitals from /encounters/patients/{id}/vitals/latest
// 2. Display current values with trend arrows (↑↓→)
// 3. Color-code: normal (green), borderline (amber), abnormal (red)
// 4. Click on any vital → opens trend chart modal
// 5. Show "Last recorded: X days ago" with staleness warning
```

#### New Components

**`frontend/src/components/labs/LabResultsPanel.tsx`**
- Categorized display of latest lab results
- Categories: Cardiac Markers | Lipids | Renal | Coagulation | Thyroid | Liver | Other
- Each result shows: test name, value, unit, reference range, abnormal flag badge
- Sparkline mini-chart for each value (last 5 readings)
- Click on result → opens full trend view
- "Order Labs" button
- "Enter Results" button
- Staleness indicator per category

**`frontend/src/components/labs/LabTrendChart.tsx`**
- Full-width Recharts LineChart for selected lab test
- X-axis: Date/time
- Y-axis: Value with unit
- Reference range shown as colored band (green zone)
- Data points colored by abnormal status
- Annotations: medication changes overlay (if Phase 1 complete)
- Time range selector: 3m, 6m, 1y, 2y, all
- Multiple tests on same chart (e.g., Total Chol + LDL + HDL together)

**`frontend/src/components/labs/VitalsTrendChart.tsx`**
- Recharts for vitals trending (BP, HR, Weight)
- BP shows systolic + diastolic as range band
- HR with resting vs. during-exercise context
- Weight with BMI overlay
- Time range: 3m, 6m, 1y, all

**`frontend/src/components/labs/LabEntryForm.tsx`**
- Panel-based entry: select panel → shows all tests in panel
- Each test: value input, unit (pre-filled), datetime
- Auto-flags abnormal values as user types (red border + warning)
- "Normal" button to skip tests with normal results
- Batch save all results at once
- Lab facility name input
- Option to link to existing order or create ad-hoc

**`frontend/src/components/labs/LabOrderForm.tsx`**
- Select from cardiology panels (checkboxes)
- Or search individual LOINC codes
- Priority selector (routine/urgent/stat)
- Clinical notes / reason for ordering
- Lab facility (saved from previous orders)
- Date/time for collection

**`frontend/src/components/labs/CriticalValueAlert.tsx`**
- Modal alert for critical values
- Shows: test name, value, reference range, clinical significance
- Actions: Acknowledge, Contact Patient, Order Follow-up
- Audit: who acknowledged and when

**`frontend/src/components/labs/CSVImportModal.tsx`**
- File upload (CSV/TSV)
- Column mapping interface: map file columns to LOINC codes
- Preview parsed results in table
- Validate before import
- Show import results (success/errors)

**`frontend/src/components/labs/ClinicalDashboard.tsx`**
- Patient-level dashboard combining:
  - Latest vitals with mini-trends
  - Latest labs by category
  - Active medications (Phase 1)
  - Recent CDSS scores
  - Pending lab orders
  - Critical alerts

#### New Pages

**`frontend/src/app/patients/[id]/labs/page.tsx`** - Lab Results Hub
- Tab: Results (all results, filterable by category/date)
- Tab: Orders (pending/completed orders)
- Tab: Trends (multi-test trend charts)
- Tab: Import (CSV/PDF upload)
- "Order Labs" and "Enter Results" action buttons

#### API Client

**`frontend/src/lib/api/labs.ts`**
```typescript
// Orders
createLabOrder(token, patientId, data)
listLabOrders(token, patientId, filters?)
getLabOrder(token, orderId)
cancelLabOrder(token, orderId)

// Results
recordResults(token, orderId, results)
recordManualResults(token, patientId, results)
getPatientLabResults(token, patientId, filters?)
getLatestLabs(token, patientId)
getLabSummary(token, patientId)

// Trending
getLabTrend(token, patientId, loincCode, options?)
getLabTrends(token, patientId, loincCodes[])

// Panels
getLabPanels(token)
getCardiologyPanels(token)

// Import
importCSV(token, patientId, file, mapping)

// Vitals (enhanced)
getVitalsTrends(token, patientId, metrics[])
```

### 5. Enhanced Vitals Endpoints

**Modify existing `encounter/service.py` and `encounter/router.py`:**

```python
# New endpoint: Multi-vital trends
GET /api/encounters/patients/{patient_id}/vitals/trends
    ?metrics=systolic_bp,diastolic_bp,heart_rate
    &from=2024-01-01
    &to=2024-12-31
    &limit=100

# Response:
{
    "patient_id": "...",
    "trends": {
        "systolic_bp": {
            "data_points": [{"date": "...", "value": 135, "position": "sitting"}],
            "min": 118, "max": 162, "avg": 132,
            "trend": "improving"  # based on recent direction
        },
        "diastolic_bp": {...},
        "heart_rate": {...}
    }
}
```

### 6. Integration: DICOM SR → Lab Results

**Connect echo measurements to lab-like trending:**

When echo SR is parsed (existing `sr_parser.py`), store key measurements as lab_results with entry_method='dicom_sr':
- LVEF → LOINC 18043-0
- LV dimensions → appropriate LOINC codes
- E/A ratio, E/e' ratio → LOINC codes

This enables trending of echo measurements alongside lab results.

### 7. CSV Import Format

**Standard format for Cyprus labs (Bioanalytica, Yiannoukas):**
```csv
Test Name,Result,Unit,Reference Range,Date
Creatinine,1.1,mg/dL,0.6-1.2,15/01/2024
eGFR,78,mL/min/1.73m²,>90,15/01/2024
Potassium,4.2,mmol/L,3.5-5.0,15/01/2024
...
```

**Mapping configuration:**
```python
class CSVMapping(BaseModel):
    test_name_column: str
    value_column: str
    unit_column: Optional[str]
    reference_range_column: Optional[str]
    date_column: str
    date_format: str = "%d/%m/%Y"  # Cyprus DD/MM/YYYY
    delimiter: str = ","
    skip_header: bool = True
    test_name_to_loinc: dict[str, str]  # Lab-specific name → LOINC mapping
```

---

## Cross-Cutting Gaps Identified

| Gap | Impact on Phase 4 | Addressed In |
|-----|-------------------|-------------|
| No prescription module | Can't overlay medication changes on lab/vitals charts | Phase 1 |
| No notification system | Can't alert on critical values in real-time | Infrastructure |
| No background job scheduler | Can't schedule lab value checks or overdue alerts | Infrastructure |
| No patient problem list | Can't correlate lab values with diagnoses | Phase 5 |
| No file upload service | CSV/PDF import needs file handling | Infrastructure (MinIO exists) |
| VitalsPanel is placeholder | Immediate visual gap for users | This phase fixes it |
| CDSS manual input only | Phase 5 needs lab data to auto-populate | Phase 5 (depends on this) |
| No inter-lab normalization | Different labs use different units | Enhancement |
| No FHIR Observation resource | Can't export labs in standard format | Phase 6 |
| No HL7 ORU parser | Can't receive automated lab results | Phase 6 |
| Echo measurements not stored as observations | Can't trend LVEF alongside labs | This phase adds integration |

---

## Testing

**`backend/tests/test_labs.py`:**
- Lab order creation (from panel, individual tests)
- Result recording (valid, invalid values, out-of-range)
- Abnormal flag auto-detection
- Critical value detection
- Trend calculation (with sparse data)
- Derived value calculation (Non-HDL, eGFR from creatinine)
- CSV import (valid file, bad mapping, malformed data)
- Latest labs retrieval
- Lab summary by category
- Permission enforcement
- Multiple results per LOINC code (trending correctness)

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `backend/alembic/versions/20240111_0011_lab_results.py` | CREATE | Lab tables migration |
| `backend/app/modules/labs/__init__.py` | CREATE | Module init |
| `backend/app/modules/labs/models.py` | CREATE | LabOrder, LabResult, LabPanel |
| `backend/app/modules/labs/schemas.py` | CREATE | Pydantic schemas |
| `backend/app/modules/labs/service.py` | CREATE | Business logic |
| `backend/app/modules/labs/router.py` | CREATE | API endpoints |
| `backend/app/modules/labs/import_csv.py` | CREATE | CSV parser |
| `backend/app/modules/labs/panels.py` | CREATE | Panel definitions |
| `backend/app/modules/labs/alerts.py` | CREATE | Critical value logic |
| `backend/app/main.py` | MODIFY | Register labs_router |
| `backend/app/core/seed.py` | MODIFY | Add lab panels + sample results |
| `backend/app/modules/encounter/service.py` | MODIFY | Enhanced vitals trending |
| `backend/app/modules/encounter/router.py` | MODIFY | Multi-vital trends endpoint |
| `backend/app/modules/patient/service.py` | MODIFY | Add lab events to timeline |
| `frontend/src/app/patients/[id]/components/VitalsPanel.tsx` | REWRITE | Replace placeholder |
| `frontend/src/app/patients/[id]/labs/page.tsx` | CREATE | Lab results hub |
| `frontend/src/components/labs/LabResultsPanel.tsx` | CREATE | Categorized results |
| `frontend/src/components/labs/LabTrendChart.tsx` | CREATE | Recharts trend |
| `frontend/src/components/labs/VitalsTrendChart.tsx` | CREATE | Vitals charts |
| `frontend/src/components/labs/LabEntryForm.tsx` | CREATE | Panel-based entry |
| `frontend/src/components/labs/LabOrderForm.tsx` | CREATE | Order creation |
| `frontend/src/components/labs/CriticalValueAlert.tsx` | CREATE | Critical alerts |
| `frontend/src/components/labs/CSVImportModal.tsx` | CREATE | Import UI |
| `frontend/src/components/labs/ClinicalDashboard.tsx` | CREATE | Patient summary |
| `frontend/src/lib/api/labs.ts` | CREATE | API client |
| `backend/tests/test_labs.py` | CREATE | Test suite |
