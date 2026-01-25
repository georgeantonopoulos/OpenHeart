# Phase 6: Interoperability & External Integrations

## Priority: MEDIUM-HIGH | Dependencies: Phase 3 (Billing for Gesy), Phase 4 (Labs for HL7) | Long-term Viability

---

## Executive Summary

OpenHeart has excellent internal infrastructure but limited external data exchange. The FHIR library is installed but unused, HL7 v2 library is installed but has no implementation, and the Gesy adapter uses a mock provider. This phase implements real interoperability: HL7 v2 lab import, FHIR R4 resource exposure, real Gesy API connection, and data export capabilities. This ensures OpenHeart can participate in the broader healthcare ecosystem rather than operating as an island.

---

## Existing Infrastructure (What We Already Have)

### Dependencies Installed (Ready to Use)
| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| `fhir.resources` | >=7.1.0 | FHIR R4 Python models | Installed, unused |
| `hl7apy` | >=1.3.4 | HL7 v2 message parsing | Installed, unused |
| `pydicom` | >=2.4.0 | DICOM file parsing | Used extensively |
| `httpx` | >=0.26.0 | Async HTTP client | Used for Orthanc/Gesy |
| `boto3` | >=1.34.0 | MinIO/S3 operations | Used for file storage |

### DICOM Integration (Complete - Reference Architecture)
| Feature | Location | Status |
|---------|----------|--------|
| DICOMweb (QIDO-RS, WADO-RS, STOW-RS) | `backend/app/integrations/dicom/service.py` | Complete |
| Modality Worklist (MWL) | `backend/app/integrations/dicom/mwl_*` | Complete |
| Study-Patient linking | `dicom/models.py` | PatientStudyLink with dedup |
| SR parsing (40+ codes) | `dicom/sr_parser.py` | LOINC/SNOMED/DCM mappings |
| Orthanc health check | `dicom/service.py` | In /health probe |
| OHIF Viewer integration | Frontend | Viewer URL generation |

### Medical Coding Standards (Complete)
| Standard | Records | Location |
|----------|---------|----------|
| ICD-10 | 86 codes | `backend/scripts/seed_codes.py` |
| LOINC | 27 codes | Same |
| CPT | 60+ codes | Same |
| ATC | 40+ codes | Same |
| SNOMED-CT | 20+ codes | `dicom/sr_parser.py` concept map |
| HIO (Cyprus) | 20+ codes | `seed_codes.py` |
| ICPC-2 | Table ready | Not seeded |

### Gesy Adapter Pattern (Mock Complete)
| Feature | Location | Status |
|---------|----------|--------|
| IGesyProvider interface | `gesy/interface.py` | 10 abstract methods |
| MockGesyProvider | `gesy/mock_provider.py` | Full mock implementation |
| Gesy router | `gesy/router.py` | 11 endpoints |
| Gesy schemas | `gesy/schemas.py` | Complete data structures |
| Beneficiary, Referral, Claim | All | Full lifecycle |

### FHIR Stub
| Feature | Location | Status |
|---------|----------|--------|
| Router import | `backend/app/main.py:216-217` | Commented out |
| FHIR R4 dependency | `pyproject.toml:65` | Installed |
| Planned prefix | `/fhir/r4` | In comment |

### Security & Audit (GDPR-Compliant)
| Feature | Location | Status |
|---------|----------|--------|
| Audit middleware | `core/audit.py` | All API access logged |
| PII encryption | `core/encryption.py` | Fernet at-rest encryption |
| GDPR erasure | Migration 0008 | Complete erasure lifecycle |
| Row-level security | All modules | Clinic-level isolation |

### Docker Infrastructure
| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL 16 | 5432 | Primary database |
| Redis 7 | 6379 | Sessions/cache |
| MinIO | 9000/9001 | File storage (S3-compatible) |
| Orthanc | 4242/8042 | DICOM server |
| OHIF Viewer | 3001 | DICOM viewing |
| Backend | 8000 | FastAPI |
| Frontend | 3000 | Next.js |

---

## What's Missing (Implementation Required)

### 1. HL7 v2 Lab Interface

**Purpose:** Receive lab results automatically from external laboratory systems.

#### Architecture
```
External Lab System
        │
        │ MLLP (TCP/IP on port 2575)
        │
        ▼
┌─────────────────────┐
│  HL7 Listener       │ (New Docker service or backend async task)
│  (MLLP Server)      │
│                     │
│  1. Receive ORU^R01 │ (Observation Result)
│  2. Parse message   │ (hl7apy)
│  3. Map fields      │ (Lab-specific config)
│  4. Store results   │ (lab_results table from Phase 4)
│  5. Send ACK        │ (Application Accept)
└─────────────────────┘
        │
        ▼
   lab_results table (Phase 4)
```

#### Implementation: `backend/app/integrations/hl7/`

```
backend/app/integrations/hl7/
    __init__.py
    listener.py         - MLLP server (asyncio TCP)
    parser.py           - HL7 v2 message parsing
    mapper.py           - OBX → lab_results field mapping
    ack_builder.py      - ACK/NAK message generation
    config.py           - Per-lab configuration profiles
    router.py           - Admin endpoints for HL7 config
    models.py           - HL7MessageLog ORM model
```

#### `parser.py` - HL7 v2 Message Parser

```python
from hl7apy.parser import parse_message
from hl7apy.core import Message

class HL7LabParser:
    """Parse HL7 v2 ORU^R01 messages into lab results"""

    def parse_oru(self, raw_message: str) -> ParsedLabResult:
        """
        Parse ORU^R01 (Observation Result) message.

        Segments used:
        - MSH: Message header (sender, receiver, timestamp, message type)
        - PID: Patient demographics (ID, name, DOB)
        - PV1: Patient visit (encounter context)
        - OBR: Observation request (order info, placer/filler numbers)
        - OBX: Observation result (test code, value, units, reference range, abnormal flag)
        - NTE: Notes (free-text comments)
        """

    def extract_patient_id(self, pid_segment) -> str:
        """Extract Cyprus ID from PID-3 (Patient Identifier List)"""

    def extract_results(self, obx_segments: list) -> list[LabResultFromHL7]:
        """
        Map OBX segments to lab_results fields:
        - OBX-3: Test identifier (map to LOINC code)
        - OBX-5: Result value
        - OBX-6: Units
        - OBX-7: Reference range
        - OBX-8: Abnormal flags (N, L, H, LL, HH, A)
        - OBX-11: Result status (F=Final, P=Preliminary, C=Corrected)
        - OBX-14: Date/Time of observation
        """

    def map_abnormal_flag(self, hl7_flag: str) -> str:
        """
        Map HL7 abnormal flags to our enum:
        N → normal, L → low, H → high,
        LL → critical_low, HH → critical_high,
        A → abnormal
        """
```

#### `mapper.py` - Lab-Specific Code Mapping

```python
class LabMapper:
    """Maps lab-specific test codes to LOINC codes"""

    def __init__(self, lab_profile: LabProfile):
        self.profile = lab_profile

    def map_test_code(self, lab_code: str) -> Optional[str]:
        """
        Convert lab-internal test code to LOINC.
        E.g., Bioanalytica "TROP_I" → LOINC "49563-0"
        """

    def map_units(self, lab_unit: str, loinc_code: str) -> tuple[str, float]:
        """
        Normalize units. E.g.:
        - "umol/L" creatinine → convert to "mg/dL" (÷ 88.4)
        - "mmol/L" cholesterol → convert to "mg/dL" (× 38.67)
        Returns: (normalized_unit, conversion_factor)
        """

# Lab profiles (configurable per lab)
BIOANALYTICA_PROFILE = LabProfile(
    lab_code="BIO",
    lab_name="Bioanalytica",
    mapping={
        "CREAT": "2160-0",
        "TROP_I": "49563-0",
        "CHOL_T": "2093-3",
        "HDL": "2085-9",
        "LDL": "13457-7",
        "TG": "2571-8",
        "INR": "6301-6",
        "K": "2823-3",
        "NA": "2951-2",
        # ... more mappings
    },
    unit_system="SI",  # or "conventional"
)
```

#### `listener.py` - MLLP Server

```python
import asyncio
from hl7apy.mllp import MLLPServer  # or custom asyncio implementation

class HL7Listener:
    """Asynchronous HL7 v2 MLLP listener"""

    def __init__(self, host: str = "0.0.0.0", port: int = 2575):
        self.host = host
        self.port = port

    async def start(self):
        """Start listening for HL7 messages"""
        server = await asyncio.start_server(
            self.handle_connection, self.host, self.port
        )
        async with server:
            await server.serve_forever()

    async def handle_connection(self, reader, writer):
        """
        1. Read MLLP-framed message (0x0B start, 0x1C0x0D end)
        2. Parse HL7 message
        3. Process based on message type:
           - ORU^R01: Lab result → store in lab_results
           - ADT^A01: Patient admission (future)
           - ORM^O01: Order acknowledgment (future)
        4. Send ACK or NAK
        5. Log message to hl7_message_log
        """

    async def process_oru(self, message: Message) -> ProcessingResult:
        """
        1. Parse patient identifier from PID
        2. Match to OpenHeart patient (by Cyprus ID)
        3. For each OBX segment:
           a. Map test code to LOINC
           b. Convert units if needed
           c. Create lab_result record
           d. Check for critical values
        4. If matched: link to existing lab_order (by filler_order_number)
        5. Return processing summary
        """
```

#### Database: `hl7_message_log`
```sql
CREATE TABLE hl7_message_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_control_id VARCHAR(50),     -- MSH-10
    message_type VARCHAR(20),           -- e.g., "ORU^R01"
    sending_facility VARCHAR(200),      -- MSH-4
    receiving_facility VARCHAR(200),    -- MSH-6
    message_datetime TIMESTAMP WITH TIME ZONE, -- MSH-7
    patient_id INTEGER REFERENCES patients(id), -- Matched patient (NULL if no match)
    processing_status VARCHAR(20) NOT NULL, -- received, processed, failed, unmatched
    error_message TEXT,
    raw_message TEXT NOT NULL,           -- Full HL7 message (for debugging)
    results_created INTEGER DEFAULT 0,   -- Number of lab_results created
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_hl7_log_status ON hl7_message_log(processing_status);
CREATE INDEX idx_hl7_log_patient ON hl7_message_log(patient_id);
CREATE INDEX idx_hl7_log_date ON hl7_message_log(created_at DESC);
```

#### Docker Addition (Optional Separate Service)
```yaml
# docker-compose.yml addition:
hl7-listener:
    build:
      context: ./backend
      dockerfile: Dockerfile.hl7  # Lightweight image for listener
    ports:
      - "2575:2575"  # MLLP port
    environment:
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      - postgres
    restart: unless-stopped
```

### 2. FHIR R4 Resource API

**Purpose:** Expose patient data in FHIR R4 format for data exchange with other systems.

#### Implementation: `backend/app/integrations/fhir/`

```
backend/app/integrations/fhir/
    __init__.py
    router.py           - FHIR REST endpoints
    resources/
        __init__.py
        patient.py      - Patient ↔ FHIR Patient mapping
        observation.py  - Vitals/Labs ↔ FHIR Observation mapping
        medication_request.py - Prescriptions ↔ FHIR MedicationRequest
        condition.py    - Problems ↔ FHIR Condition mapping
        encounter.py    - Encounters ↔ FHIR Encounter mapping
        appointment.py  - Appointments ↔ FHIR Appointment mapping
        diagnostic_report.py - Lab panels ↔ FHIR DiagnosticReport
        document_reference.py - Notes ↔ FHIR DocumentReference
        imaging_study.py - DICOM ↔ FHIR ImagingStudy
        bundle.py       - Patient summary bundle
    service.py          - FHIR resource generation service
    search.py           - FHIR search parameter handling
    capability.py       - CapabilityStatement generation
```

#### Priority FHIR Resources

**1. Patient** (`/fhir/r4/Patient`)
```python
from fhir.resources.patient import Patient as FHIRPatient

def to_fhir_patient(patient: Patient) -> FHIRPatient:
    """
    Map OpenHeart Patient → FHIR Patient:
    - id → FHIR id
    - first_name, last_name → HumanName
    - date_of_birth → birthDate
    - sex → gender (male/female/other/unknown)
    - cyprus_id → identifier (type: NATIONAL, system: urn:oid:2.16.196.x)
    - phone → telecom (system: phone)
    - email → telecom (system: email)
    - address → address (country: CY)
    """
```

**2. Observation** (`/fhir/r4/Observation`)
```python
from fhir.resources.observation import Observation as FHIRObservation

def vitals_to_fhir(vitals: Vitals) -> list[FHIRObservation]:
    """
    Each vital sign becomes a separate FHIR Observation:
    - category: vital-signs
    - code: LOINC code (8480-6 for SBP, 8462-4 for DBP, 8867-4 for HR, etc.)
    - valueQuantity: {value, unit, system: UCUM}
    - effectiveDateTime: recorded_at
    - subject: Patient reference
    """

def lab_to_fhir(lab_result: LabResult) -> FHIRObservation:
    """
    - category: laboratory
    - code: LOINC code from lab_result.loinc_code
    - valueQuantity: {value_numeric, unit}
    - referenceRange: [{low, high, text}]
    - interpretation: abnormal_flag mapping
    - effectiveDateTime: result_datetime
    """
```

**3. MedicationRequest** (`/fhir/r4/MedicationRequest`)
```python
def prescription_to_fhir(rx: Prescription) -> FHIRMedicationRequest:
    """
    - status: active/completed/cancelled/stopped/on-hold
    - intent: order
    - medicationCodeableConcept: {coding: [{system: ATC, code: atc_code}]}
    - subject: Patient reference
    - authoredOn: created_at
    - requester: Prescriber reference
    - dosageInstruction: [{timing, route, doseAndRate}]
    - dispenseRequest: {quantity, numberOfRepeatsAllowed}
    """
```

**4. Condition** (`/fhir/r4/Condition`)
```python
def problem_to_fhir(problem: PatientProblem) -> FHIRCondition:
    """
    - clinicalStatus: active/recurrence/relapse/inactive/remission/resolved
    - code: {coding: [{system: ICD-10, code: icd10_code}]}
    - subject: Patient reference
    - onsetDateTime: onset_date
    - abatementDateTime: resolved_date (if resolved)
    - recordedDate: recorded_date
    """
```

**5. Bundle** (`/fhir/r4/Patient/{id}/$everything`)
```python
def patient_summary_bundle(patient_id: int) -> FHIRBundle:
    """
    Complete patient summary as FHIR Bundle (type: searchset):
    - Patient resource
    - Active Conditions
    - Active MedicationRequests
    - Recent Observations (vitals + labs, last 6 months)
    - Recent Encounters (last 6 months)
    - Active Appointments
    - DiagnosticReports
    - ImagingStudy references
    """
```

#### FHIR REST Endpoints

```python
# Read operations
GET    /fhir/r4/Patient/{id}                    # Get patient as FHIR
GET    /fhir/r4/Patient/{id}/$everything        # Patient summary bundle
GET    /fhir/r4/Observation?patient={id}        # Patient observations
GET    /fhir/r4/MedicationRequest?patient={id}  # Patient prescriptions
GET    /fhir/r4/Condition?patient={id}          # Patient problems
GET    /fhir/r4/Encounter?patient={id}          # Patient encounters
GET    /fhir/r4/Appointment?patient={id}        # Patient appointments

# Search operations
GET    /fhir/r4/Patient?identifier={cyprus_id}  # Search by Cyprus ID
GET    /fhir/r4/Observation?code={loinc}&patient={id}&date={range}

# Capability
GET    /fhir/r4/metadata                        # CapabilityStatement

# Write operations (Phase 6b - import from external)
POST   /fhir/r4/Patient                         # Create patient from FHIR
POST   /fhir/r4/Bundle                          # Import patient bundle
```

### 3. Real Gesy API Integration

**Purpose:** Replace MockGesyProvider with real HIO API calls.

#### Implementation: `backend/app/integrations/gesy/real_provider.py`

```python
class RealGesyProvider(IGesyProvider):
    """
    Real implementation of IGesyProvider connecting to HIO (Gesy) APIs.
    Replaces MockGesyProvider in production.
    """

    def __init__(self, config: GesyConfig):
        self.base_url = config.gesy_api_url
        self.client_id = config.gesy_client_id
        self.client_secret = config.gesy_client_secret
        self.provider_id = config.gesy_provider_id
        self._token: Optional[str] = None
        self._token_expires: Optional[datetime] = None
        self._http_client = httpx.AsyncClient(timeout=30.0)

    async def _authenticate(self) -> str:
        """
        OAuth2 client_credentials flow with HIO:
        POST {base_url}/oauth/token
        Body: grant_type=client_credentials&client_id=...&client_secret=...
        Returns: access_token, expires_in
        Cache token until expiry.
        """

    async def verify_beneficiary(self, beneficiary_id: str) -> Optional[BeneficiaryStatus]:
        """
        GET {base_url}/beneficiaries/{beneficiary_id}
        Headers: Authorization: Bearer {token}
        Map HIO response to BeneficiaryStatus schema.
        """

    async def submit_claim(self, claim: GesyClaimCreate) -> GesyClaim:
        """
        POST {base_url}/claims
        Body: HIO-formatted claim JSON
        - Map OpenHeart claim structure to HIO format
        - Include referral_id, provider_id, beneficiary_id
        - Line items with procedure codes and amounts
        Returns: claim_id, initial status
        """

    async def get_claim_status(self, claim_id: str) -> Optional[GesyClaim]:
        """
        GET {base_url}/claims/{claim_id}
        Returns current status including:
        - Approval/rejection per line item
        - Total approved amount
        - Payment date (if paid)
        """
```

#### Configuration

```python
class GesyConfig(BaseModel):
    gesy_api_url: str = "https://api.gesy.org.cy/v1"  # Production URL
    gesy_client_id: str
    gesy_client_secret: str
    gesy_provider_id: str       # OpenHeart clinic's Gesy provider ID
    gesy_environment: str = "sandbox"  # sandbox | production
    gesy_timeout: int = 30      # seconds

# Environment variable loading
GESY_CONFIG = GesyConfig(
    gesy_api_url=os.environ.get("GESY_API_URL", "https://sandbox.gesy.org.cy/v1"),
    gesy_client_id=os.environ["GESY_CLIENT_ID"],
    gesy_client_secret=os.environ["GESY_CLIENT_SECRET"],
    gesy_provider_id=os.environ["GESY_PROVIDER_ID"],
)
```

#### Provider Selection (Environment-Based)

```python
# In dependency injection:
def get_gesy_provider() -> IGesyProvider:
    if settings.ENVIRONMENT == "development":
        return MockGesyProvider()
    else:
        return RealGesyProvider(GESY_CONFIG)
```

### 4. Data Export Capabilities

**Purpose:** Allow clinics to export patient data in standard formats.

#### Endpoints

```python
# Patient data export
GET /api/patients/{id}/export/fhir           # FHIR Bundle (JSON)
GET /api/patients/{id}/export/pdf            # Clinical summary PDF
GET /api/patients/{id}/export/csv            # Tabular data (labs, vitals)

# Bulk export (clinic-level, admin only)
POST /api/export/bulk                        # Trigger bulk export job
GET  /api/export/bulk/{job_id}               # Check export status
GET  /api/export/bulk/{job_id}/download      # Download export file

# Audit export (compliance)
GET /api/audit/export?from=&to=&format=csv   # Audit log export
```

#### PDF Report Generation

```python
# Using reportlab or weasyprint
class ClinicalSummaryPDF:
    def generate(self, patient_id: int) -> bytes:
        """
        Generate clinical summary PDF:
        - Patient demographics (header)
        - Active problem list
        - Current medications
        - Recent vitals with trends
        - Latest lab results
        - CDSS risk scores
        - Recent encounters
        - Imaging studies list
        """
```

### 5. Cyprus Lab-Specific Import Profiles

**Purpose:** Configure import profiles for common Cyprus laboratories.

```python
# Admin-configurable lab profiles
LAB_PROFILES = {
    "bioanalytica": LabProfile(
        name="Bioanalytica",
        code="BIO",
        interface_type="csv",  # csv, hl7, api
        csv_config=CSVConfig(
            delimiter=",",
            date_format="%d/%m/%Y",
            encoding="utf-8",
            test_name_column="Test",
            value_column="Result",
            unit_column="Units",
            reference_column="Reference Range",
        ),
        code_mappings={...},  # Test name → LOINC
    ),
    "yiannoukas": LabProfile(
        name="Yiannoukas Medical Labs",
        code="YML",
        interface_type="csv",
        csv_config=CSVConfig(...),
        code_mappings={...},
    ),
    "nipd_genetics": LabProfile(
        name="NIPD Genetics",
        code="NIPD",
        interface_type="csv",
        csv_config=CSVConfig(...),
        code_mappings={...},
    ),
}
```

**Admin UI for Lab Profiles:**
- `frontend/src/app/settings/labs/page.tsx` - Manage lab profiles
- Add/edit/delete lab configurations
- Test import with sample file
- View import history

### 6. Event/Webhook System (Foundation)

**Purpose:** Enable event-driven integrations for future connections.

```python
# Event types
class ClinicalEvent(BaseModel):
    event_type: str  # lab_result_critical, appointment_created, prescription_created
    patient_id: int
    data: dict
    timestamp: datetime

# Redis pub/sub for internal events
class EventBus:
    async def publish(self, event: ClinicalEvent):
        """Publish event to Redis channel"""
        await redis.publish(f"clinical_events:{event.event_type}", event.json())

    async def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to event type with handler"""

# Webhook configuration (future)
class WebhookConfig(Base):
    __tablename__ = "webhook_configs"
    id = Column(UUID, primary_key=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"))
    url = Column(String, nullable=False)
    event_types = Column(JSONB)  # Which events to send
    secret = Column(String)      # HMAC signing key
    is_active = Column(Boolean, default=True)
```

---

## Cross-Cutting Gaps Identified

| Gap | Impact on Phase 6 | Addressed In |
|-----|-------------------|-------------|
| No API versioning | FHIR endpoints may break clients | This phase (use /fhir/r4 prefix) |
| No rate limiting | External integrations could overwhelm system | Infrastructure |
| No API key management | External systems need auth tokens | Enhancement |
| No background job queue | Bulk exports need async processing | Infrastructure (Celery/ARQ) |
| No PDF generation library | Clinical summary export needs it | Add: weasyprint or reportlab |
| Gesy API documentation | Real API format not publicly documented | Requires HIO partnership |
| Lab system diversity | Each Cyprus lab has different format | Configurable profiles |
| No data validation on import | HL7/CSV imports could inject bad data | Validation layer |
| No conflict resolution | FHIR import could conflict with existing data | Merge strategy |
| No audit for external access | FHIR/HL7 access should be logged | Extend audit middleware |
| No SMART on FHIR | Can't host third-party FHIR apps | Future (OAuth2 scopes) |

---

## Implementation Order

1. **FHIR R4 Read-Only** (Patient, Observation, Condition) - Lowest risk, highest value
2. **Real Gesy Provider** (replace mock in production) - Business-critical
3. **Data Export** (PDF + CSV) - Clinical workflow need
4. **Lab Import Profiles** (CSV for Cyprus labs) - Most common integration
5. **HL7 v2 Listener** (for labs that support it) - Technical complexity
6. **FHIR Write/Import** (Bundle import) - Patient transfer use case
7. **Event/Webhook System** - Foundation for future integrations
8. **SMART on FHIR** (Future) - Third-party app hosting

---

## Testing

**`backend/tests/test_fhir.py`:**
- Patient → FHIR Patient mapping (all fields)
- Vitals → FHIR Observation (correct LOINC codes, UCUM units)
- Lab → FHIR Observation (with interpretation, reference range)
- Prescription → FHIR MedicationRequest (dosage instruction formatting)
- Problem → FHIR Condition (status mapping)
- Bundle generation (completeness, references)
- FHIR search parameters (patient, code, date range)
- CapabilityStatement accuracy

**`backend/tests/test_hl7.py`:**
- ORU^R01 parsing (valid message, all segments)
- Patient matching (by Cyprus ID, by name+DOB)
- OBX → lab_result mapping (values, units, flags)
- Unit conversion (SI → conventional and vice versa)
- ACK generation (accept, reject with error)
- Unmatched patient handling
- Malformed message handling
- MLLP framing (start/end characters)

**`backend/tests/test_gesy_real.py`:**
- OAuth2 token acquisition (mock HIO endpoint)
- Token caching and refresh
- Beneficiary verification (valid, invalid, expired)
- Claim submission (success, validation error)
- Claim status polling
- Network error handling with retry

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/integrations/fhir/__init__.py` | CREATE | Module init |
| `backend/app/integrations/fhir/router.py` | CREATE | FHIR REST endpoints |
| `backend/app/integrations/fhir/service.py` | CREATE | Resource generation |
| `backend/app/integrations/fhir/resources/patient.py` | CREATE | Patient mapping |
| `backend/app/integrations/fhir/resources/observation.py` | CREATE | Vitals/Labs mapping |
| `backend/app/integrations/fhir/resources/medication_request.py` | CREATE | Rx mapping |
| `backend/app/integrations/fhir/resources/condition.py` | CREATE | Problem mapping |
| `backend/app/integrations/fhir/resources/encounter.py` | CREATE | Encounter mapping |
| `backend/app/integrations/fhir/resources/bundle.py` | CREATE | Summary bundle |
| `backend/app/integrations/fhir/capability.py` | CREATE | CapabilityStatement |
| `backend/app/integrations/hl7/__init__.py` | CREATE | Module init |
| `backend/app/integrations/hl7/listener.py` | CREATE | MLLP server |
| `backend/app/integrations/hl7/parser.py` | CREATE | Message parsing |
| `backend/app/integrations/hl7/mapper.py` | CREATE | Code mapping |
| `backend/app/integrations/hl7/ack_builder.py` | CREATE | ACK generation |
| `backend/app/integrations/hl7/config.py` | CREATE | Lab profiles |
| `backend/app/integrations/hl7/models.py` | CREATE | HL7MessageLog |
| `backend/app/integrations/gesy/real_provider.py` | CREATE | Real Gesy API |
| `backend/app/integrations/gesy/config.py` | CREATE | Gesy configuration |
| `backend/app/main.py` | MODIFY | Uncomment FHIR router |
| `backend/app/core/events.py` | CREATE | Event bus |
| `frontend/src/app/settings/labs/page.tsx` | CREATE | Lab profile config |
| `docker-compose.yml` | MODIFY | Add HL7 listener service (optional) |
| `backend/alembic/versions/0013_hl7_interop.py` | CREATE | HL7 log + webhook tables |
| `backend/tests/test_fhir.py` | CREATE | FHIR test suite |
| `backend/tests/test_hl7.py` | CREATE | HL7 test suite |
| `backend/tests/test_gesy_real.py` | CREATE | Real Gesy tests |
