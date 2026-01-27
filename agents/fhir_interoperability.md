---
title: FHIR R4 Interoperability Guide
version: 1.0
status: planning
created: 2026-01-21
description: FHIR R4 implementation patterns for healthcare data exchange in OpenHeart Cyprus EMR.
---

# FHIR R4 Interoperability Guide

## 1. Overview

OpenHeart Cyprus implements FHIR R4 (v4.0.1) for standardized healthcare data exchange. It uses **Cyprus Core Profiles** (adapted from HL7 EU/International) to ensure national compatibility.

## 2. Core FHIR Resources

### Patient Resource

```json
{
  "resourceType": "Patient",
  "id": "patient-123",
  "identifier": [
    {
      "system": "urn:oid:2.16.196.1.113883.3.1.1",
      "value": "CY12345678",
      "type": {
        "coding": [{
          "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
          "code": "NI",
          "display": "National ID"
        }]
      }
    },
    {
      "system": "urn:oid:2.16.196.1.113883.3.1.2",
      "value": "ARC987654",
      "type": {
        "coding": [{
          "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
          "code": "PPN",
          "display": "Alien Registration Certificate"
        }]
      }
    }
  ],
  "name": [{
    "use": "official",
    "family": "Papadopoulos",
    "given": ["Nikos"]
  }],
  "telecom": [{
    "system": "phone",
    "value": "+357-22-123456",
    "use": "mobile"
  }],
  "gender": "male",
  "birthDate": "1965-03-15",
  "address": [{
    "use": "home",
    "city": "Nicosia",
    "country": "CY"
  }]
}
```

### Observation Resource (Vital Signs)

```json
{
  "resourceType": "Observation",
  "id": "bp-observation-456",
  "status": "final",
  "category": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/observation-category",
      "code": "vital-signs",
      "display": "Vital Signs"
    }]
  }],
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "85354-9",
      "display": "Blood pressure panel"
    }]
  },
  "subject": {
    "reference": "Patient/patient-123"
  },
  "effectiveDateTime": "2026-01-21T10:30:00+02:00",
  "component": [
    {
      "code": {
        "coding": [{
          "system": "http://loinc.org",
          "code": "8480-6",
          "display": "Systolic blood pressure"
        }]
      },
      "valueQuantity": {
        "value": 140,
        "unit": "mmHg",
        "system": "http://unitsofmeasure.org",
        "code": "mm[Hg]"
      }
    },
    {
      "code": {
        "coding": [{
          "system": "http://loinc.org",
          "code": "8462-4",
          "display": "Diastolic blood pressure"
        }]
      },
      "valueQuantity": {
        "value": 90,
        "unit": "mmHg",
        "system": "http://unitsofmeasure.org",
        "code": "mm[Hg]"
      }
    }
  ]
}
```

### Observation Resource (Cardiac: LVEF)

```json
{
  "resourceType": "Observation",
  "id": "lvef-789",
  "status": "final",
  "category": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/observation-category",
      "code": "imaging",
      "display": "Imaging"
    }]
  }],
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "10230-1",
      "display": "Left ventricular Ejection fraction"
    }]
  },
  "subject": {
    "reference": "Patient/patient-123"
  },
  "effectiveDateTime": "2026-01-20T14:00:00+02:00",
  "valueQuantity": {
    "value": 55,
    "unit": "%",
    "system": "http://unitsofmeasure.org",
    "code": "%"
  },
  "interpretation": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
      "code": "N",
      "display": "Normal"
    }]
  }],
  "derivedFrom": [{
    "reference": "DiagnosticReport/echo-report-101"
  }]
}
```

### DiagnosticReport Resource (Echo Report)

```json
{
  "resourceType": "DiagnosticReport",
  "id": "echo-report-101",
  "status": "final",
  "category": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
      "code": "CUS",
      "display": "Cardiac Ultrasound"
    }]
  }],
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "34552-0",
      "display": "Echocardiogram study"
    }]
  },
  "subject": {
    "reference": "Patient/patient-123"
  },
  "effectiveDateTime": "2026-01-20T14:00:00+02:00",
  "performer": [{
    "reference": "Practitioner/dr-costa-456"
  }],
  "result": [
    {"reference": "Observation/lvef-789"},
    {"reference": "Observation/wall-motion-790"},
    {"reference": "Observation/valve-status-791"}
  ],
  "conclusion": "Normal LV systolic function. No significant valvular disease.",
  "imagingStudy": [{
    "reference": "ImagingStudy/echo-study-202"
  }]
}
```

## 3. FastAPI FHIR Endpoints

### Router Structure

```python
# api/fhir/router.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List

fhir_router = APIRouter(prefix="/fhir/r4", tags=["FHIR"])

@fhir_router.get("/Patient/{patient_id}")
async def get_patient(patient_id: str) -> dict:
    """Retrieve patient resource by ID."""
    patient = await patient_service.get_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient.to_fhir()

@fhir_router.get("/Patient")
async def search_patients(
    identifier: str = None,
    name: str = None,
    birthdate: str = None,
    _count: int = 20
) -> dict:
    """Search patients with FHIR search parameters."""
    results = await patient_service.search(
        identifier=identifier,
        name=name,
        birthdate=birthdate,
        limit=_count
    )
    return create_bundle("searchset", results)

@fhir_router.get("/Observation")
async def search_observations(
    patient: str,
    category: str = None,
    code: str = None,
    date: str = None
) -> dict:
    """Search observations for a patient."""
    # Parse patient reference
    patient_id = patient.replace("Patient/", "")
    results = await observation_service.search(
        patient_id=patient_id,
        category=category,
        code=code,
        date=date
    )
    return create_bundle("searchset", results)

@fhir_router.post("/Patient")
async def create_patient(patient: dict) -> dict:
    """Create a new patient resource."""
    validated = validate_fhir_resource(patient, "Patient")
    created = await patient_service.create(validated)
    return created.to_fhir()
```

### FHIR Bundle Helper

```python
# fhir/bundle.py
def create_bundle(bundle_type: str, resources: List[dict]) -> dict:
    """Create a FHIR Bundle from a list of resources."""
    return {
        "resourceType": "Bundle",
        "type": bundle_type,
        "total": len(resources),
        "entry": [
            {
                "fullUrl": f"urn:uuid:{r.get('id')}",
                "resource": r
            }
            for r in resources
        ]
    }
```

## 4. Gesy Integration Codification

Cyprus Gesy requires specific code systems for different provider types:

| Provider Type | Diagnoses | Procedures | Services |
|---------------|-----------|------------|----------|
| Personal Doctors | ICPC-II | N/A | HIO Codification |
| Outpatient Specialists | ICD-10 / HIO | N/A | CPT |
| Laboratories | N/A | N/A | LOINC |
| Inpatient | ICD-10-CY V1.0 | CMP-CY V1.0 | DRG-CY |
| Pharmaceuticals | N/A | N/A | ATC + unique ID |

### Code System Mapping

```python
# fhir/codesystems.py
GESY_CODE_SYSTEMS = {
    "diagnosis": {
        "personal_doctor": "http://hl7.org/fhir/sid/icpc-2",
        "specialist": "http://hl7.org/fhir/sid/icd-10",
        "inpatient": "http://gesy.org.cy/fhir/CodeSystem/icd-10-cy"
    },
    "procedure": {
        "inpatient": "http://gesy.org.cy/fhir/CodeSystem/cmp-cy"
    },
    "service": {
        "laboratory": "http://loinc.org",
        "specialist": "http://www.ama-assn.org/go/cpt",
        "pharmacy": "http://www.whocc.no/atc"
    }
}
```

## 5. SMART on FHIR Authorization

### OAuth2 Configuration

```python
# auth/smart_fhir.py
from fastapi import Depends
from authlib.integrations.starlette_client import OAuth

SMART_SCOPES = [
    "openid",
    "fhirUser",
    "patient/*.read",
    "patient/*.write",
    "user/*.read",
    "launch/patient"
]

# SMART on FHIR metadata endpoint
@fhir_router.get("/.well-known/smart-configuration")
async def smart_configuration():
    return {
        "authorization_endpoint": f"{BASE_URL}/oauth/authorize",
        "token_endpoint": f"{BASE_URL}/oauth/token",
        "capabilities": [
            "launch-ehr",
            "client-public",
            "client-confidential-symmetric",
            "context-ehr-patient",
            "sso-openid-connect"
        ],
        "code_challenge_methods_supported": ["S256"],
        "scopes_supported": SMART_SCOPES
    }
```

## 6. Data Export for GDPR

### Patient Everything Operation

```python
@fhir_router.get("/Patient/{patient_id}/$everything")
async def patient_everything(
    patient_id: str,
    _since: str = None,
    _type: str = None
) -> dict:
    """
    FHIR $everything operation for GDPR data portability.
    Returns all data related to a patient.
    """
    resources = []

    # Get patient
    patient = await patient_service.get_by_id(patient_id)
    resources.append(patient.to_fhir())

    # Get all related resources
    observations = await observation_service.get_by_patient(patient_id)
    resources.extend([o.to_fhir() for o in observations])

    conditions = await condition_service.get_by_patient(patient_id)
    resources.extend([c.to_fhir() for c in conditions])

    procedures = await procedure_service.get_by_patient(patient_id)
    resources.extend([p.to_fhir() for p in procedures])

    # ... more resource types

    return create_bundle("searchset", resources)
```

## 7. Cardiology-Specific LOINC Codes

| Measurement | LOINC Code | Display |
|-------------|------------|---------|
| LVEF | 10230-1 | Left ventricular Ejection fraction |
| E/A Ratio | 59127-0 | E/A ratio |
| Heart Rate | 8867-4 | Heart rate |
| Systolic BP | 8480-6 | Systolic blood pressure |
| Diastolic BP | 8462-4 | Diastolic blood pressure |
| Troponin I | 10839-9 | Troponin I.cardiac |
| Troponin T | 6598-7 | Troponin T.cardiac |
| BNP | 30934-4 | BNP |
| NT-proBNP | 33762-6 | NT-proBNP |
| Creatinine | 2160-0 | Creatinine |
| eGFR | 33914-3 | eGFR |
| LDL Cholesterol | 13457-7 | LDL Cholesterol |
| HDL Cholesterol | 14646-4 | HDL Cholesterol |
| Total Cholesterol | 2093-3 | Cholesterol |
| Triglycerides | 2571-8 | Triglycerides |

## 8. Real-time Interoperability (FHIR Subscriptions)

To handle real-time alerts (e.g., critical lab results), use FHIR Subscriptions over WebSockets or Webhooks.

```python
# fhir/subscription.py
async def handle_critical_lab_alert(subscription_event: dict):
    """Notify clinic on critical lab result via FHIR Subscription."""
    resource = subscription_event.get("focus")
    if resource.get("interpretation") == "AA":  # Extra Abnormal
        await notify_clinician(
            clinician_id=resource.get("performer")[0],
            message=f"CRITICAL LAB: {resource.get('code').get('display')}"
        )
```

## 9. Testing FHIR Compliance

Use the official FHIR validator:

```bash
# Download FHIR validator
curl -L https://github.com/hapifhir/org.hl7.fhir.core/releases/latest/download/validator_cli.jar -o validator_cli.jar

# Validate a resource
java -jar validator_cli.jar patient.json -version 4.0.1
```

### pytest FHIR Tests

```python
# tests/test_fhir.py
import pytest
from fhir.resources.patient import Patient

def test_patient_resource_valid():
    """Test that our Patient resource is FHIR-compliant."""
    patient_data = {
        "resourceType": "Patient",
        "id": "test-123",
        "name": [{"family": "Test", "given": ["User"]}]
    }
    patient = Patient(**patient_data)
    assert patient.resource_type == "Patient"

def test_observation_has_required_fields():
    """Test Observation includes mandatory elements."""
    obs = create_observation(patient_id="123", code="8867-4", value=72)
    assert obs.get("status") is not None
    assert obs.get("code") is not None
    assert obs.get("subject") is not None
```
