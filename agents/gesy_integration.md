---
title: Gesy (General Healthcare System) Integration Guide
version: 1.0
status: planning
created: 2026-01-21
description: Integration patterns for Cyprus Gesy (GHS) healthcare system compatibility.
---

# Gesy (General Healthcare System) Integration Guide

## 1. Overview

Gesy (General Healthcare System of Cyprus) is managed by the Health Insurance Organization (HIO). OpenHeart Cyprus must be compatible with Gesy's IT systems for claims, referrals, and data exchange.

**Important**: Gesy does not publish public API documentation. Integration requires HIO provider enrollment and direct consultation for technical specifications.

## 2. Codification Standards (Mandatory)

Gesy mandates specific code systems for communication, claims, and data exchange:

### Diagnosis Codes

| Provider Type | Code System | Notes |
|---------------|-------------|-------|
| Personal Doctors | ICPC-II | International Classification of Primary Care |
| Outpatient Specialists | ICD-10 / HIO | ICD-10 with HIO extensions |
| Inpatient | ICD-10-CY V1.0 | Cyprus-specific ICD-10 adaptation |

### Procedure Codes

| Provider Type | Code System |
|---------------|-------------|
| Inpatient | CMP-CY V1.0 (Cyprus Medical Procedures) |

### Service/Reimbursement Codes

| Provider Type | Code System |
|---------------|-------------|
| Personal Doctors | HIO Codification |
| Outpatient Specialists | CPT (Current Procedural Terminology) |
| Laboratories | LOINC |
| Inpatient | DRG-CY (Diagnosis Related Groups - Cyprus) |
| Pharmaceuticals | ATC + unique HIO ID |
| Medical Devices | HIO Codification |

## 3. Adapter Pattern Implementation

Since Gesy API specs are not publicly available, implement an adapter pattern for testing with mock data and future real API integration.

### Interface Definition

```python
# interfaces/gesy_provider.py
from abc import ABC, abstractmethod
from typing import Optional
from datetime import date
from pydantic import BaseModel

class BeneficiaryStatus(BaseModel):
    """Gesy beneficiary verification result."""
    beneficiary_id: str
    is_active: bool
    personal_doctor_id: Optional[str]
    coverage_start_date: date
    coverage_end_date: Optional[date]

class Referral(BaseModel):
    """Gesy referral for specialist visit."""
    referral_id: str
    patient_id: str
    from_doctor_id: str
    to_specialty: str
    diagnosis_code: str  # ICPC-II
    valid_until: date
    status: str  # pending, approved, used, expired

class Claim(BaseModel):
    """Gesy reimbursement claim."""
    claim_id: str
    patient_id: str
    provider_id: str
    service_date: date
    diagnosis_codes: list[str]
    procedure_codes: list[str]
    total_amount: float
    status: str  # submitted, processing, approved, rejected

class IGesyProvider(ABC):
    """Interface for Gesy integration."""

    @abstractmethod
    async def verify_beneficiary(self, patient_id: str) -> BeneficiaryStatus:
        """Verify patient is an active Gesy beneficiary."""
        pass

    @abstractmethod
    async def get_referral(self, referral_id: str) -> Optional[Referral]:
        """Retrieve a referral by ID."""
        pass

    @abstractmethod
    async def create_referral(self, referral: Referral) -> Referral:
        """Create a new referral (for personal doctors)."""
        pass

    @abstractmethod
    async def submit_claim(self, claim: Claim) -> Claim:
        """Submit a reimbursement claim."""
        pass

    @abstractmethod
    async def get_claim_status(self, claim_id: str) -> Claim:
        """Check status of a submitted claim."""
        pass

    @abstractmethod
    async def create_prescription(self, prescription: dict) -> dict:
        """Submit an e-Prescription to Gesy."""
        pass

    @abstractmethod
    async def close_referral(self, referral_id: str, summary_report: str) -> bool:
        """Close a referral by submitting a clinical summary report."""
        pass
```

### Mock Implementation (for Development/Testing)

```python
# adapters/mock_gesy_provider.py
from interfaces.gesy_provider import IGesyProvider, BeneficiaryStatus, Referral, Claim
from datetime import date, timedelta
import uuid

class MockGesyProvider(IGesyProvider):
    """Mock Gesy provider for development and testing."""

    def __init__(self):
        self._referrals: dict[str, Referral] = {}
        self._claims: dict[str, Claim] = {}

    async def verify_beneficiary(self, patient_id: str) -> BeneficiaryStatus:
        """Always returns active status for testing."""
        return BeneficiaryStatus(
            beneficiary_id=patient_id,
            is_active=True,
            personal_doctor_id="DR-001",
            coverage_start_date=date(2019, 6, 1),  # Gesy launch date
            coverage_end_date=None
        )

    async def get_referral(self, referral_id: str) -> Optional[Referral]:
        return self._referrals.get(referral_id)

    async def create_referral(self, referral: Referral) -> Referral:
        referral.referral_id = f"REF-{uuid.uuid4().hex[:8].upper()}"
        referral.status = "approved"
        referral.valid_until = date.today() + timedelta(days=30)
        self._referrals[referral.referral_id] = referral
        return referral

    async def submit_claim(self, claim: Claim) -> Claim:
        claim.claim_id = f"CLM-{uuid.uuid4().hex[:8].upper()}"
        claim.status = "submitted"
        self._claims[claim.claim_id] = claim
        return claim

    async def get_claim_status(self, claim_id: str) -> Claim:
        claim = self._claims.get(claim_id)
        if claim:
            # Simulate processing
            claim.status = "processing"
        return claim
```

### Real Gesy Provider (Placeholder)

```python
# adapters/real_gesy_provider.py
from interfaces.gesy_provider import IGesyProvider, BeneficiaryStatus, Referral, Claim
import httpx

class RealGesyProvider(IGesyProvider):
    """
    Real Gesy API integration.

    Prerequisites:
    1. Provider enrollment with HIO
    2. API credentials from HIO
    3. Gesy API documentation (available to enrolled providers)
    """

    def __init__(self, api_url: str, api_key: str, provider_id: str):
        self.api_url = api_url
        self.api_key = api_key
        self.provider_id = provider_id
        self.client = httpx.AsyncClient(
            base_url=api_url,
            headers={"Authorization": f"Bearer {api_key}"}
        )

    async def verify_beneficiary(self, patient_id: str) -> BeneficiaryStatus:
        """
        Verify beneficiary status via Gesy API.

        TODO: Implement when API documentation is available.
        """
        raise NotImplementedError("Awaiting Gesy API documentation")

    async def get_referral(self, referral_id: str) -> Optional[Referral]:
        raise NotImplementedError("Awaiting Gesy API documentation")

    async def create_referral(self, referral: Referral) -> Referral:
        raise NotImplementedError("Awaiting Gesy API documentation")

    async def submit_claim(self, claim: Claim) -> Claim:
        raise NotImplementedError("Awaiting Gesy API documentation")

    async def get_claim_status(self, claim_id: str) -> Claim:
        raise NotImplementedError("Awaiting Gesy API documentation")
```

### Dependency Injection

```python
# dependencies.py
from functools import lru_cache
from adapters.mock_gesy_provider import MockGesyProvider
from adapters.real_gesy_provider import RealGesyProvider
from interfaces.gesy_provider import IGesyProvider
import os

@lru_cache
def get_gesy_provider() -> IGesyProvider:
    """Return appropriate Gesy provider based on environment."""
    if os.environ.get("GESY_API_KEY"):
        return RealGesyProvider(
            api_url=os.environ["GESY_API_URL"],
            api_key=os.environ["GESY_API_KEY"],
            provider_id=os.environ["GESY_PROVIDER_ID"]
        )
    return MockGesyProvider()
```

## 4. Gatekeeping (Referral System)

Gesy uses a gatekeeping model where patients must get referrals from their personal doctor to see specialists.

### Referral Workflow

```
Patient → Personal Doctor → Referral → Specialist (Cardiologist)
```

### FastAPI Endpoints

```python
# api/gesy/router.py
from fastapi import APIRouter, Depends, HTTPException
from interfaces.gesy_provider import IGesyProvider, Referral
from dependencies import get_gesy_provider

gesy_router = APIRouter(prefix="/api/gesy", tags=["Gesy"])

@gesy_router.get("/beneficiary/{patient_id}")
async def verify_beneficiary(
    patient_id: str,
    gesy: IGesyProvider = Depends(get_gesy_provider)
):
    """Verify patient is active Gesy beneficiary."""
    return await gesy.verify_beneficiary(patient_id)

@gesy_router.get("/referral/{referral_id}")
async def get_referral(
    referral_id: str,
    gesy: IGesyProvider = Depends(get_gesy_provider)
):
    """Get referral details."""
    referral = await gesy.get_referral(referral_id)
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")
    return referral

@gesy_router.post("/referral")
async def create_referral(
    referral: Referral,
    gesy: IGesyProvider = Depends(get_gesy_provider)
):
    """Create new referral (personal doctors only)."""
    return await gesy.create_referral(referral)

@gesy_router.post("/claim")
async def submit_claim(
    claim: Claim,
    gesy: IGesyProvider = Depends(get_gesy_provider)
):
    """Submit reimbursement claim to Gesy."""
    return await gesy.submit_claim(claim)

@gesy_router.post("/prescription")
async def create_prescription(
    prescription: dict,
    gesy: IGesyProvider = Depends(get_gesy_provider)
):
    """Submit e-Prescription."""
    return await gesy.create_prescription(prescription)

@gesy_router.post("/referral/{referral_id}/close")
async def close_referral(
    referral_id: str,
    summary: dict,
    gesy: IGesyProvider = Depends(get_gesy_provider)
):
    """Close referral with summary report."""
    return await gesy.close_referral(referral_id, summary.get("report"))
```

## 5. Code System Database Tables

```sql
-- ICD-10-CY Diagnosis Codes
CREATE TABLE icd10_cy_codes (
    code VARCHAR(10) PRIMARY KEY,
    description_en TEXT NOT NULL,
    description_el TEXT,  -- Greek
    category VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE
);

-- ICPC-II Codes (for personal doctors)
CREATE TABLE icpc2_codes (
    code VARCHAR(10) PRIMARY KEY,
    description_en TEXT NOT NULL,
    description_el TEXT,
    chapter VARCHAR(50)
);

-- CPT Procedure Codes
CREATE TABLE cpt_codes (
    code VARCHAR(10) PRIMARY KEY,
    description_en TEXT NOT NULL,
    category VARCHAR(50),
    relative_value DECIMAL(10, 2)
);

-- HIO Service Codes
CREATE TABLE hio_service_codes (
    code VARCHAR(20) PRIMARY KEY,
    description_en TEXT NOT NULL,
    description_el TEXT,
    provider_type VARCHAR(50),  -- personal_doctor, specialist, lab, etc.
    reimbursement_rate DECIMAL(10, 2)
);

-- LOINC Laboratory Codes
CREATE TABLE loinc_codes (
    code VARCHAR(20) PRIMARY KEY,
    long_name TEXT NOT NULL,
    short_name VARCHAR(100),
    component VARCHAR(100),
    property VARCHAR(50),
    time_aspect VARCHAR(50),
    system VARCHAR(100),
    scale VARCHAR(20),
    method VARCHAR(100)
);
```

## 6. Clinical Guidelines

Gesy publishes clinical guidelines (CGs) and clinical protocols (CPs) adapted from NICE guidelines for Cyprus. Relevant cardiology guidelines:

- Acute Coronary Syndrome management
- Atrial fibrillation anticoagulation
- Heart failure diagnosis and treatment
- Hypertension management
- Lipid management

### Guidelines Integration

```python
# services/clinical_guidelines.py
from typing import Optional

async def get_guideline_recommendations(
    diagnosis_code: str,
    patient_context: dict
) -> list[str]:
    """
    Get Gesy-approved clinical recommendations based on diagnosis.

    Future: Integrate with HIO's clinical guidelines API/database.
    """
    # Placeholder - implement with actual guideline database
    guidelines = {
        "I21": [  # Acute MI
            "Urgent cardiology referral required",
            "Follow GRACE score for risk stratification",
            "Dual antiplatelet therapy per ESC guidelines"
        ],
        "I48": [  # Atrial fibrillation
            "Calculate CHA2DS2-VASc score",
            "Calculate HAS-BLED score",
            "Consider anticoagulation if CHA2DS2-VASc ≥2"
        ]
    }

    # Get first 3 characters of ICD-10 code
    code_prefix = diagnosis_code[:3]
    return guidelines.get(code_prefix, [])
```

## 7. Resources

- **HIO Official Website**: <https://www.gesy.org.cy>
- **HIO Codification**: <https://www.gesy.org.cy/en-us/hiocodificationproviders>
- **Clinical Guidelines**: <https://www.gesy.org.cy/en-us/hioclinicalguidelinesproviders>
- **Provider Enrollment**: Contact HIO directly for API access and documentation

## 8. Implementation Checklist

- [ ] Enroll as provider with HIO
- [ ] Obtain Gesy API credentials
- [ ] Import ICD-10-CY code database
- [ ] Import ICPC-II code database
- [ ] Import LOINC code database
- [ ] Import CPT code database
- [ ] Implement real Gesy API adapter
- [ ] Test beneficiary verification flow
- [ ] Test referral workflow
- [ ] Test claims submission
- [ ] Integrate clinical guidelines
