"""Pydantic schemas for the prescription module."""

from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# =============================================================================
# Enums
# =============================================================================


class PrescriptionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    DISCONTINUED = "discontinued"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"
    EXPIRED = "expired"


class Frequency(str, Enum):
    OD = "OD"       # Once daily
    BD = "BD"       # Twice daily
    TDS = "TDS"     # Three times daily
    QDS = "QDS"     # Four times daily
    PRN = "PRN"     # As needed
    STAT = "STAT"   # Immediately
    NOCTE = "nocte"  # At night
    MANE = "mane"   # In the morning
    CUSTOM = "custom"


class Route(str, Enum):
    ORAL = "oral"
    SUBLINGUAL = "sublingual"
    IV = "IV"
    IM = "IM"
    SC = "SC"
    TOPICAL = "topical"
    INHALED = "inhaled"
    TRANSDERMAL = "transdermal"
    RECTAL = "rectal"
    NASAL = "nasal"


class InteractionSeverity(str, Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CONTRAINDICATED = "contraindicated"


FREQUENCY_DISPLAY_MAP: dict[str, str] = {
    "OD": "Once daily",
    "BD": "Twice daily",
    "TDS": "Three times daily",
    "QDS": "Four times daily",
    "PRN": "As needed",
    "STAT": "Immediately (once)",
    "nocte": "At night",
    "mane": "In the morning",
}


# =============================================================================
# Prescription Schemas
# =============================================================================


class PrescriptionCreate(BaseModel):
    """Schema for creating a new prescription."""

    patient_id: int = Field(..., gt=0)
    encounter_id: Optional[int] = Field(None, gt=0)
    gesy_medication_id: Optional[int] = Field(None, gt=0)
    drug_name: str = Field(..., min_length=1, max_length=200)
    atc_code: Optional[str] = Field(None, max_length=10)
    generic_name: Optional[str] = Field(None, max_length=200)
    form: Optional[str] = Field(None, max_length=50)
    strength: Optional[str] = Field(None, max_length=50)
    dosage: Optional[str] = Field(None, max_length=100)
    quantity: Optional[int] = Field(None, gt=0)
    frequency: str = Field(default="OD", max_length=20)
    frequency_custom: Optional[str] = Field(None, max_length=100)
    route: str = Field(default="oral", max_length=30)
    duration_days: Optional[int] = Field(None, gt=0)
    start_date: date = Field(default_factory=date.today)
    refills_allowed: int = Field(default=0, ge=0)
    is_chronic: bool = Field(default=False)
    linked_diagnosis_icd10: Optional[str] = Field(None, max_length=10)
    linked_diagnosis_description: Optional[str] = Field(None, max_length=200)
    indication: Optional[str] = Field(None, max_length=500)
    prescriber_notes: Optional[str] = None
    acknowledge_interactions: list[UUID] = Field(default_factory=list)

    @field_validator("drug_name")
    @classmethod
    def strip_drug_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v: str) -> str:
        valid = {"OD", "BD", "TDS", "QDS", "PRN", "STAT", "nocte", "mane", "custom"}
        if v not in valid:
            raise ValueError(f"Invalid frequency: {v}. Must be one of: {valid}")
        return v

    @field_validator("route")
    @classmethod
    def validate_route(cls, v: str) -> str:
        valid = {"oral", "sublingual", "IV", "IM", "SC", "topical", "inhaled", "transdermal", "rectal", "nasal"}
        if v not in valid:
            raise ValueError(f"Invalid route: {v}. Must be one of: {valid}")
        return v


class PrescriptionUpdate(BaseModel):
    """Schema for updating a prescription (dose change, notes)."""

    dosage: Optional[str] = Field(None, max_length=100)
    strength: Optional[str] = Field(None, max_length=50)
    frequency: Optional[str] = Field(None, max_length=20)
    frequency_custom: Optional[str] = Field(None, max_length=100)
    quantity: Optional[int] = Field(None, gt=0)
    prescriber_notes: Optional[str] = None
    indication: Optional[str] = Field(None, max_length=500)


class PrescriptionDiscontinue(BaseModel):
    """Schema for discontinuing a prescription."""

    reason: str = Field(..., min_length=3, max_length=500, description="Required discontinuation reason")
    effective_date: Optional[date] = None

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Discontinuation reason must be at least 3 characters")
        return v


class PrescriptionRenew(BaseModel):
    """Schema for renewing a chronic prescription."""

    duration_days: Optional[int] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, gt=0)
    notes: Optional[str] = None


class PrescriptionHold(BaseModel):
    """Schema for placing a prescription on hold."""

    reason: str = Field(..., min_length=3, max_length=500)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, v: str) -> str:
        return v.strip()


# =============================================================================
# Interaction Schemas
# =============================================================================


class InteractionCheckRequest(BaseModel):
    """Schema for checking drug interactions before prescribing."""

    patient_id: int = Field(..., gt=0)
    drug_name: str = Field(..., min_length=1)
    atc_code: Optional[str] = None
    exclude_prescription_id: Optional[UUID] = None


class InteractionDetail(BaseModel):
    """Detail of a single drug interaction."""

    interacting_drug: str
    interacting_atc: Optional[str] = None
    interacting_prescription_id: Optional[UUID] = None
    severity: str
    interaction_type: str
    description: str
    management: Optional[str] = None


class InteractionCheckResponse(BaseModel):
    """Response from interaction check."""

    has_interactions: bool
    interactions: list[InteractionDetail]
    can_proceed: bool  # False if any contraindicated


# =============================================================================
# Response Schemas
# =============================================================================


class InteractionResponse(BaseModel):
    """Interaction record in prescription response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    interacting_drug_name: str
    interacting_atc_code: Optional[str] = None
    severity: str
    interaction_type: Optional[str] = None
    description: str
    management_recommendation: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    override_reason: Optional[str] = None


class MedicationHistoryResponse(BaseModel):
    """History entry in prescription response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    previous_status: Optional[str] = None
    new_status: str
    changed_by: int
    changed_at: datetime
    reason: Optional[str] = None
    change_type: str
    details: Optional[dict] = None


class PrescriptionResponse(BaseModel):
    """Full prescription response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    patient_id: int
    encounter_id: Optional[int] = None
    prescriber_id: int
    clinic_id: int

    # Drug info
    gesy_medication_id: Optional[int] = None
    drug_name: str
    atc_code: Optional[str] = None
    generic_name: Optional[str] = None

    # Details
    form: Optional[str] = None
    strength: Optional[str] = None
    dosage: Optional[str] = None
    quantity: Optional[int] = None
    frequency: str
    frequency_custom: Optional[str] = None
    frequency_display: Optional[str] = None
    route: str

    # Duration
    duration_days: Optional[int] = None
    start_date: date
    end_date: Optional[date] = None

    # Refills
    refills_allowed: int = 0
    refills_used: int = 0

    # Status
    status: str
    is_chronic: bool = False

    # Clinical
    linked_diagnosis_icd10: Optional[str] = None
    linked_diagnosis_description: Optional[str] = None
    indication: Optional[str] = None

    # Discontinuation
    discontinued_at: Optional[datetime] = None
    discontinuation_reason: Optional[str] = None

    # Chain
    original_prescription_id: Optional[UUID] = None
    renewal_count: int = 0

    # Gesy
    requires_prior_auth: bool = False
    prior_auth_status: Optional[str] = None

    # Notes
    prescriber_notes: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Computed fields (set by service)
    can_renew: bool = False
    days_remaining: Optional[int] = None
    prescriber_name: Optional[str] = None

    # Related
    interactions: list[InteractionResponse] = []


class PrescriptionListResponse(BaseModel):
    """Paginated list of prescriptions."""

    items: list[PrescriptionResponse]
    total: int


# =============================================================================
# Formulary Schemas
# =============================================================================


class DrugTemplateResponse(BaseModel):
    """Drug template from the cardiology formulary."""

    generic_name: str
    atc_code: str
    category: str
    default_strength: str
    default_form: str
    default_frequency: str
    default_route: str
    is_chronic: bool
    available_strengths: list[str]
    common_indications: list[str]
    loading_dose: Optional[str] = None
    renal_adjustment: Optional[dict] = None


class FormularyResponse(BaseModel):
    """Full formulary response grouped by category."""

    categories: dict[str, list[DrugTemplateResponse]]
    total_drugs: int
