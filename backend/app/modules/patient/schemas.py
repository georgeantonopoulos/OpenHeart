"""
Pydantic schemas for Patient API.

Handles validation for Cyprus-specific identifiers and contact formats.
"""

import re
from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Gender(str, Enum):
    """Patient gender options."""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


class PatientStatus(str, Enum):
    """Patient status in the system."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DECEASED = "deceased"


class Address(BaseModel):
    """Cyprus address structure."""

    street: str = Field(..., max_length=255)
    city: str = Field(..., max_length=100)
    postal_code: str = Field(..., max_length=10)
    district: Optional[str] = Field(None, max_length=50)
    country: str = Field(default="Cyprus", max_length=50)


class EmergencyContact(BaseModel):
    """Emergency contact information."""

    name: str = Field(..., max_length=255)
    relationship: str = Field(..., max_length=50)
    phone: str = Field(..., max_length=20)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        # Cyprus phone format: +357 XX XXXXXX
        cleaned = re.sub(r"[\s\-\(\)]", "", v)
        if not re.match(r"^\+357\d{8}$", cleaned):
            raise ValueError("Phone must be in Cyprus format: +357 XX XXXXXX")
        return cleaned


class PatientCreate(BaseModel):
    """Schema for creating a new patient."""

    # Required fields
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    birth_date: date = Field(...)
    gender: Gender = Field(default=Gender.UNKNOWN)

    # Optional fields
    middle_name: Optional[str] = Field(None, max_length=100)

    # Cyprus identifiers (at least one required)
    cyprus_id: Optional[str] = Field(
        None,
        description="Cyprus ID Card number",
    )
    arc_number: Optional[str] = Field(
        None,
        description="Alien Registration Certificate number",
    )

    # Contact
    phone: Optional[str] = Field(None, description="Phone in +357 XX XXXXXX format")
    email: Optional[str] = Field(None)

    # Address
    address: Optional[Address] = None

    # Emergency contact
    emergency_contact: Optional[EmergencyContact] = None

    # Gesy
    gesy_beneficiary_id: Optional[str] = Field(None)

    # Referral
    referring_physician: Optional[str] = Field(None, max_length=255)

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_names(cls, v: str) -> str:
        return v.strip()

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, v: date) -> date:
        today = date.today()
        if v > today:
            raise ValueError("Birth date cannot be in the future")
        age = (
            today.year
            - v.year
            - ((today.month, today.day) < (v.month, v.day))
        )
        if age > 120:
            raise ValueError("Birth date results in age over 120 years")
        return v

    @field_validator("cyprus_id")
    @classmethod
    def validate_cyprus_id(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip()
        # Cyprus ID: typically 7-8 digits or alphanumeric
        if not re.match(r"^[A-Z0-9]{6,10}$", cleaned.upper()):
            raise ValueError("Invalid Cyprus ID format")
        return cleaned.upper()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = re.sub(r"[\s\-\(\)]", "", v)
        if not re.match(r"^\+357\d{8}$", cleaned):
            raise ValueError("Phone must be in Cyprus format: +357 XX XXXXXX")
        return cleaned

    @model_validator(mode="after")
    def check_identifier(self) -> "PatientCreate":
        """At least one identifier (Cyprus ID or ARC) should be provided."""
        if not self.cyprus_id and not self.arc_number:
            # Warning but not error - some patients may not have ID yet
            pass
        return self


class PatientUpdate(BaseModel):
    """Schema for updating a patient."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[Gender] = None
    status: Optional[PatientStatus] = None

    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[Address] = None
    emergency_contact: Optional[EmergencyContact] = None

    gesy_beneficiary_id: Optional[str] = None
    referring_physician: Optional[str] = Field(None, max_length=255)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = re.sub(r"[\s\-\(\)]", "", v)
        if not re.match(r"^\+357\d{8}$", cleaned):
            raise ValueError("Phone must be in Cyprus format: +357 XX XXXXXX")
        return cleaned


class PatientResponse(BaseModel):
    """Response schema for patient data."""

    model_config = ConfigDict(from_attributes=True)

    patient_id: int
    mrn: str
    birth_date: date
    gender: str
    status: str
    age: int

    # PII (only if user has permission)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[Address] = None

    # Identifiers (masked for display)
    cyprus_id_masked: Optional[str] = Field(
        None, description="Last 4 digits visible: ***1234"
    )
    has_arc: bool = False

    # Gesy
    gesy_beneficiary_id: Optional[str] = None
    is_gesy_beneficiary: bool = False

    # Metadata
    referring_physician: Optional[str] = None
    primary_physician_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class PatientListResponse(BaseModel):
    """Paginated patient list response."""

    items: list[PatientResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PatientSearchQuery(BaseModel):
    """Search query parameters for patients."""

    q: Optional[str] = Field(None, min_length=2, max_length=100, description="Name or MRN search")
    birth_date: Optional[date] = None
    gender: Optional[Gender] = None
    status: Optional[PatientStatus] = Field(default=PatientStatus.ACTIVE)
    gesy_only: bool = Field(default=False, description="Filter to Gesy beneficiaries only")
