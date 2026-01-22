"""
Pydantic schemas for Encounter API.

Handles validation for clinical encounters and vitals.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EncounterType(str, Enum):
    """Types of clinical encounters."""

    OUTPATIENT = "outpatient"
    INPATIENT = "inpatient"
    EMERGENCY = "emergency"
    TELEHEALTH = "telehealth"
    HOME_VISIT = "home_visit"


class EncounterStatus(str, Enum):
    """Encounter status."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class BillingStatus(str, Enum):
    """Billing status for encounter."""

    PENDING = "pending"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class Diagnosis(BaseModel):
    """Diagnosis entry for an encounter."""

    code: str = Field(..., description="ICD-10 code")
    description: str = Field(..., max_length=500)
    diagnosis_type: str = Field(
        default="principal",
        description="principal, secondary, or admitting",
    )
    is_confirmed: bool = Field(default=True)


class DischargeSummary(BaseModel):
    """Structured discharge/visit summary."""

    assessment: Optional[str] = None
    plan: Optional[str] = None
    instructions: Optional[str] = None
    follow_up_instructions: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    prescriptions: Optional[list[dict]] = None
    referrals: Optional[list[dict]] = None


# ============================================================================
# Encounter Schemas
# ============================================================================


class EncounterCreate(BaseModel):
    """Schema for creating a new encounter."""

    patient_id: int = Field(..., gt=0)
    encounter_type: EncounterType = Field(default=EncounterType.OUTPATIENT)

    # Timing
    scheduled_start: Optional[datetime] = None

    # Reason for visit
    chief_complaint: Optional[str] = Field(None, max_length=500)
    visit_reason_code: Optional[str] = Field(None, max_length=20)

    # Location
    location: Optional[str] = Field(None, max_length=100)

    # Referral
    referral_source: Optional[str] = Field(None, max_length=255)
    is_follow_up: bool = False
    follow_up_to_encounter_id: Optional[int] = None
    gesy_referral_id: Optional[str] = Field(None, max_length=50)


class EncounterUpdate(BaseModel):
    """Schema for updating an encounter."""

    status: Optional[EncounterStatus] = None
    encounter_type: Optional[EncounterType] = None

    # Timing
    scheduled_start: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None

    # Clinical
    chief_complaint: Optional[str] = Field(None, max_length=500)
    visit_reason_code: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = Field(None, max_length=100)

    # Discharge
    discharge_summary: Optional[DischargeSummary] = None
    diagnoses: Optional[list[Diagnosis]] = None

    # Billing
    billing_status: Optional[BillingStatus] = None
    gesy_claim_id: Optional[str] = Field(None, max_length=50)


class EncounterStart(BaseModel):
    """Schema for starting an encounter."""

    chief_complaint: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=100)


class EncounterComplete(BaseModel):
    """Schema for completing an encounter."""

    discharge_summary: Optional[DischargeSummary] = None
    diagnoses: Optional[list[Diagnosis]] = None
    follow_up_date: Optional[datetime] = None
    follow_up_instructions: Optional[str] = None


class EncounterResponse(BaseModel):
    """Response schema for encounter data."""

    model_config = ConfigDict(from_attributes=True)

    encounter_id: int
    patient_id: int
    clinic_id: int
    encounter_type: str
    status: str

    # Timing
    scheduled_start: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    duration_minutes: Optional[int] = None

    # Clinical
    chief_complaint: Optional[str] = None
    visit_reason_code: Optional[str] = None
    location: Optional[str] = None

    # Provider
    attending_physician_id: int
    attending_physician_name: Optional[str] = None

    # Referral
    referral_source: Optional[str] = None
    is_follow_up: bool
    follow_up_to_encounter_id: Optional[int] = None
    gesy_referral_id: Optional[str] = None

    # Summary
    discharge_summary: Optional[dict] = None
    diagnoses: Optional[list] = None

    # Billing
    billing_status: str
    gesy_claim_id: Optional[str] = None

    # Patient info (joined)
    patient_name: Optional[str] = None
    patient_mrn: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime


class EncounterListResponse(BaseModel):
    """Paginated encounter list response."""

    items: list[EncounterResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class EncounterSearchQuery(BaseModel):
    """Search query parameters for encounters."""

    patient_id: Optional[int] = None
    status: Optional[EncounterStatus] = None
    encounter_type: Optional[EncounterType] = None
    attending_physician_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    billing_status: Optional[BillingStatus] = None


# ============================================================================
# Vitals Schemas
# ============================================================================


class VitalsCreate(BaseModel):
    """Schema for recording vitals."""

    # Cardiovascular
    heart_rate: Optional[int] = Field(None, ge=20, le=300, description="bpm")
    systolic_bp: Optional[int] = Field(None, ge=50, le=300, description="mmHg")
    diastolic_bp: Optional[int] = Field(None, ge=30, le=200, description="mmHg")
    respiratory_rate: Optional[int] = Field(None, ge=5, le=60, description="breaths/min")
    oxygen_saturation: Optional[int] = Field(None, ge=50, le=100, description="SpO2 %")

    # General
    temperature: Optional[float] = Field(None, ge=30.0, le=45.0, description="Celsius")
    weight: Optional[float] = Field(None, ge=1.0, le=500.0, description="kg")
    height: Optional[float] = Field(None, ge=30.0, le=300.0, description="cm")

    # Recording metadata
    position: Optional[str] = Field(
        None,
        description="Patient position: sitting, standing, supine",
    )

    @field_validator("position")
    @classmethod
    def validate_position(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_positions = ["sitting", "standing", "supine", "prone", "lateral"]
            if v.lower() not in valid_positions:
                raise ValueError(f"Position must be one of: {', '.join(valid_positions)}")
            return v.lower()
        return v


class VitalsResponse(BaseModel):
    """Response schema for vitals."""

    model_config = ConfigDict(from_attributes=True)

    vital_id: int
    encounter_id: int
    patient_id: int

    # Cardiovascular
    heart_rate: Optional[int] = None
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    respiratory_rate: Optional[int] = None
    oxygen_saturation: Optional[int] = None

    # General
    temperature: Optional[float] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    bmi: Optional[float] = None

    # Recording metadata
    recorded_at: datetime
    recorded_by: int
    recorded_by_name: Optional[str] = None
    position: Optional[str] = None


class VitalsTrend(BaseModel):
    """Vitals trend for a patient over time."""

    patient_id: int
    vital_type: str  # heart_rate, systolic_bp, etc.
    data_points: list[dict]  # [{date, value}]
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    avg_value: Optional[float] = None
