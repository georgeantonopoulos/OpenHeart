"""
Pydantic schemas for Gesy (GHS) integration.

Defines data structures for beneficiary verification, referrals, and claims.
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class BeneficiaryType(str, Enum):
    """Types of Gesy beneficiaries."""

    CITIZEN = "citizen"
    EU_NATIONAL = "eu_national"
    THIRD_COUNTRY = "third_country"
    DEPENDENT = "dependent"


class BeneficiaryStatus(BaseModel):
    """Status of a Gesy beneficiary."""

    beneficiary_id: str = Field(..., description="Gesy beneficiary ID")
    is_active: bool = Field(..., description="Whether beneficiary is currently active")
    beneficiary_type: BeneficiaryType
    registration_date: date
    expiry_date: Optional[date] = None

    # Coverage details
    primary_doctor_id: Optional[str] = Field(None, description="Assigned personal doctor")
    coverage_category: str = Field(default="A", description="Coverage category (A, B, etc.)")

    # Verification
    verified_at: datetime
    verification_source: str = Field(default="gesy_api")


class GesyReferralStatus(str, Enum):
    """Status of a Gesy referral."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    USED = "used"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class GesyReferralCreate(BaseModel):
    """Request to create a Gesy referral."""

    beneficiary_id: str
    referring_doctor_id: str
    specialty_code: str = Field(..., description="Specialist specialty code")
    diagnosis_code: str = Field(..., description="ICD-10 diagnosis code")
    diagnosis_description: str
    urgency: str = Field(default="routine", description="routine, urgent, emergency")
    clinical_notes: Optional[str] = None
    requested_procedures: Optional[list[str]] = Field(
        None, description="List of CPT codes"
    )


class GesyReferral(BaseModel):
    """A Gesy referral voucher."""

    referral_id: str = Field(..., description="Unique referral voucher ID")
    beneficiary_id: str
    referring_doctor_id: str
    specialist_id: Optional[str] = Field(None, description="Assigned specialist")
    specialty_code: str
    diagnosis_code: str
    diagnosis_description: str

    status: GesyReferralStatus = GesyReferralStatus.PENDING
    urgency: str

    # Validity
    issued_date: date
    valid_from: date
    valid_until: date

    # Usage tracking
    used_date: Optional[date] = None
    used_by_provider_id: Optional[str] = None

    # Additional info
    clinical_notes: Optional[str] = None
    requested_procedures: Optional[list[str]] = None
    approved_procedures: Optional[list[str]] = None


class GesyClaimStatus(str, Enum):
    """Status of a Gesy claim."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    PARTIALLY_APPROVED = "partially_approved"
    REJECTED = "rejected"
    PAID = "paid"


class GesyClaimLineItem(BaseModel):
    """A line item in a Gesy claim."""

    line_number: int
    procedure_code: str = Field(..., description="CPT code")
    procedure_description: str
    quantity: int = Field(default=1)
    unit_price: float = Field(..., description="Price in EUR")
    total_price: float

    # Diagnosis linkage
    diagnosis_codes: list[str] = Field(..., description="ICD-10 codes")

    # Approval status
    approved: Optional[bool] = None
    approved_amount: Optional[float] = None
    rejection_reason: Optional[str] = None


class GesyClaimCreate(BaseModel):
    """Request to create a Gesy claim."""

    referral_id: str = Field(..., description="Associated referral voucher ID")
    provider_id: str = Field(..., description="Healthcare provider Gesy ID")
    beneficiary_id: str
    service_date: date

    # Encounter details
    encounter_type: str = Field(default="outpatient")
    diagnosis_codes: list[str] = Field(..., description="ICD-10 diagnosis codes")
    primary_diagnosis_code: str

    # Line items
    line_items: list[GesyClaimLineItem]

    # Additional documentation
    clinical_notes: Optional[str] = None
    supporting_documents: Optional[list[str]] = Field(
        None, description="Document reference IDs"
    )


class GesyClaim(BaseModel):
    """A Gesy claim for reimbursement."""

    claim_id: str = Field(..., description="Unique claim ID")
    referral_id: str
    provider_id: str
    beneficiary_id: str
    service_date: date

    encounter_type: str
    diagnosis_codes: list[str]
    primary_diagnosis_code: str

    # Line items
    line_items: list[GesyClaimLineItem]

    # Financials
    total_claimed: float
    total_approved: Optional[float] = None
    total_paid: Optional[float] = None

    # Status
    status: GesyClaimStatus = GesyClaimStatus.DRAFT
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None

    # Review details
    reviewer_notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class GesyProviderInfo(BaseModel):
    """Information about a Gesy healthcare provider."""

    provider_id: str
    name: str
    provider_type: str = Field(..., description="specialist, personal_doctor, hospital")
    specialty_codes: list[str]
    address: str
    phone: str
    email: Optional[str] = None
    is_active: bool = True


class GesySpecialty(BaseModel):
    """A Gesy specialty category."""

    code: str
    name_en: str
    name_el: str
    category: str = Field(..., description="medical, surgical, diagnostic")
    requires_referral: bool = True
