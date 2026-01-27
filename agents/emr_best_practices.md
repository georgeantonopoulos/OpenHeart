---
title: Open Source EMR Best Practices
version: 1.0
status: planning
created: 2026-01-21
description: Lessons learned and best practices from established open source EMR platforms.
---

# Open Source EMR Best Practices

## 1. Platform Comparison Summary

| Platform | Architecture | Best For | Key Strength |
|----------|--------------|----------|--------------|
| **OpenEMR** | Standalone monolith | Feature-complete clinics | ONC/Meaningful Use certified |
| **OpenMRS** | Platform + modules | Customizable deployments | Extensible architecture |
| **Bahmni** | OpenMRS + OpenELIS + Odoo | Integrated clinical + lab + billing | Complete out-of-box solution |
| **LibreHealth** | OpenMRS fork | Independent development | Toolkit approach |

## 2. Architecture Patterns

### Module-Based Architecture (OpenMRS Pattern)

```
┌─────────────────────────────────────────────────────┐
│                    Core Platform                     │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────┐ │
│  │ Patient │  │  Visit  │  │   Obs   │  │ Order  │ │
│  └─────────┘  └─────────┘  └─────────┘  └────────┘ │
└───────────────────────┬─────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│   Cardiology  │ │  Laboratory   │ │   Pharmacy    │
│    Module     │ │    Module     │ │    Module     │
└───────────────┘ └───────────────┘ └───────────────┘
```

### OpenHeart Cyprus Adaptation

```
OpenHeart Core
├── modules/
│   ├── patient/          # Demographics, Cyprus ID/ARC
│   ├── encounter/        # Visit management
│   ├── cardiology/       # Echo, Cath, ECG, CDSS, Device Checks
│   ├── imaging/          # DICOM/PACS integration
│   ├── laboratory/       # Lab results (LOINC, HL7 v2)
│   ├── pharmacy/         # Prescriptions (ATC codes, e-Prescription)
│   ├── billing/          # Gesy claims
│   └── reporting/        # Trend Analytics, audit
```

## 3. Data Model Principles

### Observation Pattern (from OpenMRS)

All clinical data as Observations allows flexibility:

```sql
CREATE TABLE observations (
    observation_id SERIAL PRIMARY KEY,
    patient_id INT NOT NULL,
    encounter_id INT,
    concept_id INT NOT NULL,  -- What was measured (LOINC, SNOMED)
    value_numeric DECIMAL(15, 5),
    value_text TEXT,
    value_coded INT,  -- Reference to concept for coded values
    value_datetime TIMESTAMP,
    observation_datetime TIMESTAMP NOT NULL,
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Example: Blood Pressure
-- concept_id = 123 (Systolic BP, LOINC 8480-6)
-- value_numeric = 140

-- Example: NYHA Class
-- concept_id = 456 (NYHA Classification)
-- value_coded = 789 (concept for "Class II")
```

### Concept Dictionary

```sql
CREATE TABLE concepts (
    concept_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    short_name VARCHAR(100),
    description TEXT,
    data_type VARCHAR(50),  -- numeric, text, coded, date, boolean
    concept_class VARCHAR(50),  -- diagnosis, procedure, finding, drug
    is_set BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE concept_mappings (
    mapping_id SERIAL PRIMARY KEY,
    concept_id INT REFERENCES concepts(concept_id),
    source VARCHAR(50),  -- LOINC, ICD-10, SNOMED, CPT
    source_code VARCHAR(50),
    UNIQUE(concept_id, source)
);
```

## 4. Security Best Practices

### Role-Based Access Control (RBAC)

From OpenEMR/OpenMRS patterns:

```sql
CREATE TABLE roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE permissions (
    permission_id SERIAL PRIMARY KEY,
    permission_name VARCHAR(100) UNIQUE NOT NULL,
    resource VARCHAR(100),  -- patients, encounters, reports
    action VARCHAR(50)  -- read, write, delete, export
);

CREATE TABLE role_permissions (
    role_id INT REFERENCES roles(role_id),
    permission_id INT REFERENCES permissions(permission_id),
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE user_roles (
    user_id INT REFERENCES users(user_id),
    role_id INT REFERENCES roles(role_id),
    clinic_id INT REFERENCES clinics(clinic_id),  -- Scoped to clinic
    PRIMARY KEY (user_id, role_id, clinic_id)
);
```

### Predefined Cardiology Roles

| Role | Typical Permissions |
|------|---------------------|
| Cardiologist | Full patient access, CDSS, DICOM, prescriptions |
| Cardiac Nurse | Vitals, ECG, triage notes, appointments |
| Echo Technician | DICOM upload/view, echo measurements |
| Cath Lab Tech | Angio studies, cath reports |
| Receptionist | Demographics, scheduling only |
| Billing Staff | Claims, invoices, no clinical data |
| Administrator | User management, clinic settings |

## 5. Audit Trail Implementation

### Comprehensive Logging (HIPAA/GDPR compliant)

```sql
CREATE TABLE audit_log (
    audit_id BIGSERIAL PRIMARY KEY,
    event_time TIMESTAMPTZ DEFAULT NOW(),

    -- Who
    user_id INT,
    user_email VARCHAR(255),
    user_role VARCHAR(100),
    clinic_id INT,

    -- Where
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255),

    -- What
    event_type VARCHAR(50),  -- login, view, create, update, delete, export, print
    resource_type VARCHAR(100),
    resource_id VARCHAR(100),

    -- Details
    old_values JSONB,
    new_values JSONB,
    query_params JSONB,

    -- Context
    request_id VARCHAR(255),  -- Correlation ID
    duration_ms INT
);

-- Indexes for common audit queries
CREATE INDEX idx_audit_user ON audit_log(user_id, event_time DESC);
CREATE INDEX idx_audit_patient ON audit_log(resource_type, resource_id) WHERE resource_type = 'patient';
CREATE INDEX idx_audit_time ON audit_log(event_time DESC);
```

### Audit Triggers (PostgreSQL)

```sql
-- Automatic audit on patient table changes
CREATE OR REPLACE FUNCTION audit_patient_changes()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (
        event_type,
        resource_type,
        resource_id,
        old_values,
        new_values,
        user_id
    ) VALUES (
        TG_OP,
        'patient',
        COALESCE(NEW.patient_id, OLD.patient_id)::VARCHAR,
        CASE WHEN TG_OP IN ('UPDATE', 'DELETE') THEN to_jsonb(OLD) END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN to_jsonb(NEW) END,
        current_setting('app.user_id', true)::INT
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER patient_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON patients
FOR EACH ROW EXECUTE FUNCTION audit_patient_changes();
```

## 6. Internationalization (i18n)

### Database Schema for Multi-Language

```sql
CREATE TABLE translations (
    translation_id SERIAL PRIMARY KEY,
    locale VARCHAR(10) NOT NULL,  -- 'en', 'el' (Greek)
    namespace VARCHAR(100),  -- 'common', 'cardiology', 'errors'
    key VARCHAR(255) NOT NULL,
    value TEXT NOT NULL,
    UNIQUE(locale, namespace, key)
);

-- Seed Greek cardiology terms
INSERT INTO translations (locale, namespace, key, value) VALUES
('el', 'cardiology', 'lvef', 'Κλάσμα Εξώθησης Αριστεράς Κοιλίας'),
('el', 'cardiology', 'nyha_class', 'Κατηγορία NYHA'),
('el', 'cardiology', 'echocardiogram', 'Υπερηχοκαρδιογράφημα'),
('en', 'cardiology', 'lvef', 'Left Ventricular Ejection Fraction'),
('en', 'cardiology', 'nyha_class', 'NYHA Class'),
('en', 'cardiology', 'echocardiogram', 'Echocardiogram');
```

### Next.js i18n Setup

```typescript
// next.config.js
module.exports = {
  i18n: {
    locales: ['en', 'el'],  // English, Greek
    defaultLocale: 'en',
    localeDetection: true,
  },
};

// hooks/useTranslation.ts
import { useRouter } from 'next/router';
import translations from '@/locales';

export function useTranslation(namespace = 'common') {
  const { locale } = useRouter();

  const t = (key: string) => {
    return translations[locale]?.[namespace]?.[key] || key;
  };

  return { t, locale };
}
```

## 7. Offline Capability (Bahmni Pattern)

For mobile/tablet use in clinics with poor connectivity:

### Service Worker Strategy

```typescript
// sw.ts
const CACHE_NAME = 'openheart-v1';
const OFFLINE_URLS = [
  '/',
  '/patients',
  '/appointments',
  '/offline.html',
];

self.addEventListener('fetch', (event) => {
  // Cache-first for static assets
  // Network-first for API calls with offline fallback
});
```

### IndexedDB for Local Data

```typescript
// db/offline-store.ts
import { openDB } from 'idb';

const db = await openDB('openheart-offline', 1, {
  upgrade(db) {
    db.createObjectStore('pending-observations', { keyPath: 'localId', autoIncrement: true });
    db.createObjectStore('cached-patients', { keyPath: 'patientId' });
  },
});

export async function savePendingObservation(observation: Observation) {
  await db.add('pending-observations', {
    ...observation,
    syncStatus: 'pending',
    createdOffline: new Date().toISOString(),
  });
}

export async function syncPendingObservations() {
  const pending = await db.getAll('pending-observations');
  for (const obs of pending) {
    try {
      await api.post('/observations', obs);
      await db.delete('pending-observations', obs.localId);
    } catch (e) {
      console.error('Sync failed, will retry', e);
    }
  }
}
```

## 8. Clinical UX & Visualization Best Practices

### The "Cardiologist Dashboard"

Cardiology is data-heavy. The dashboard must prioritize:

1. **Critical Vitals Trend**: BP, HR, Weight (for heart failure) over the last 12 months.
2. **Latest Imaging**: Direct link to the last Echo/Cath.
3. **Medication Adherence**: Visual timeline of statins, anticoagulants, etc.
4. **Recent Labs**: Troponin, BNP, LDL trends.

### Minimizing Clinical Load

- **One-Click Notes**: Use templates that auto-populate from the last encounter.
- **Smart Search**: Cmd+K (Mac) or Ctrl+K (Windows) to jump to any patient from anywhere.
- **Context-Aware Sidebar**: Show relevant CDSS scores (GRACE, HAS-BLED) while the doctor is typing a note.

### Data Visualization (Trend Analysis)

Use Sparklines for laboratory data and detailed interactive charts (Recharts/D3) for:

- LVEF % over years.
- SBP/DBP trends.
- Device (Pacemaker) battery life and lead impedance.

## 9. Legacy Integration (HL7 v2)

While FHIR is the goal, most Cyprus labs still use HL7 v2.5.1 messages over MLLP.

### HL7 v2 Parser Pattern

```python
# services/legacy_lab.py
from hl7apy import core

def parse_oru_r01(message_str: str):
    """Parse HL7 v2 Observation Result message."""
    msg = core.Message(message_str)
    # Extract Patient ID from PID segment
    # Extract Results from OBX segments
    # Convert to FHIR Observation for internal storage
    pass
```

## 10. Performance Considerations

### Database Optimization

```sql
-- Partition large tables by date (for observations, audit logs)
CREATE TABLE observations (
    observation_id BIGSERIAL,
    patient_id INT NOT NULL,
    observation_date DATE NOT NULL,
    -- ... other columns
) PARTITION BY RANGE (observation_date);

CREATE TABLE observations_2026 PARTITION OF observations
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

-- Materialized view for patient summary (dashboard)
CREATE MATERIALIZED VIEW patient_cardio_summary AS
SELECT
    p.patient_id,
    p.patient_name,
    MAX(CASE WHEN c.name = 'LVEF' THEN o.value_numeric END) as latest_lvef,
    MAX(CASE WHEN c.name = 'SystolicBP' THEN o.value_numeric END) as latest_sbp,
    COUNT(DISTINCT e.encounter_id) as total_visits,
    MAX(e.encounter_date) as last_visit
FROM patients p
LEFT JOIN encounters e ON p.patient_id = e.patient_id
LEFT JOIN observations o ON e.encounter_id = o.encounter_id
LEFT JOIN concepts c ON o.concept_id = c.concept_id
GROUP BY p.patient_id, p.patient_name;

-- Refresh daily or on-demand
REFRESH MATERIALIZED VIEW patient_cardio_summary;
```

## 9. Testing Patterns

### Clinical Data Fixtures

```python
# tests/fixtures/cardiology.py
import pytest
from models import Patient, Observation

@pytest.fixture
def high_risk_acs_patient():
    """Patient with high GRACE score inputs."""
    return Patient(
        patient_id=1,
        age=75,
        observations=[
            Observation(concept="heart_rate", value_numeric=110),
            Observation(concept="systolic_bp", value_numeric=90),
            Observation(concept="creatinine", value_numeric=2.5),
            Observation(concept="killip_class", value_coded="IV"),
            Observation(concept="cardiac_arrest", value_boolean=True),
            Observation(concept="st_deviation", value_boolean=True),
            Observation(concept="elevated_enzymes", value_boolean=True),
        ]
    )

@pytest.fixture
def normal_echo_findings():
    """Normal echocardiogram results."""
    return {
        "lvef": 60,
        "wall_motion": "normal",
        "lv_dimensions": {"lvidd": 45, "lvids": 28},
        "valves": {
            "mitral": "no regurgitation",
            "aortic": "no stenosis",
            "tricuspid": "trace regurgitation"
        }
    }
```

### CDSS Unit Tests

```python
# tests/test_cdss.py
def test_grace_score_high_risk(high_risk_acs_patient):
    """Test GRACE score calculation for high-risk patient."""
    result = calculate_grace_score(high_risk_acs_patient)

    assert result["risk_category"] == "High"
    assert int(result["score"]) > 140
    assert "urgent" in result["recommendation"].lower()

def test_grace_score_boundary_values():
    """Test GRACE score at category boundaries."""
    # Score exactly at 109 should be Low
    patient_108 = create_patient_with_grace_score(108)
    assert calculate_grace_score(patient_108)["risk_category"] == "Low"

    # Score at 109 should be Intermediate
    patient_109 = create_patient_with_grace_score(109)
    assert calculate_grace_score(patient_109)["risk_category"] == "Intermediate"
```

## 10. Deployment Considerations

### Health Check Endpoint

```python
@app.get("/health")
async def health_check():
    """Kubernetes-friendly health check."""
    checks = {
        "database": await check_db_connection(),
        "orthanc": await check_orthanc_connection(),
        "redis": await check_redis_connection(),
    }
    all_healthy = all(checks.values())
    return {
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks,
        "version": os.environ.get("APP_VERSION", "dev")
    }
```

### Configuration Management

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str
    database_pool_size: int = 10

    # Security
    secret_key: str
    jwt_expiry_minutes: int = 15
    pii_encryption_key: str

    # Orthanc
    orthanc_url: str = "http://orthanc:8042"
    orthanc_username: str = "admin"
    orthanc_password: str

    # Gesy
    gesy_api_url: str = ""
    gesy_api_key: str = ""
    gesy_provider_id: str = ""

    # Feature flags
    enable_offline_mode: bool = False
    enable_fhir_api: bool = True

    class Config:
        env_file = ".env"
```
