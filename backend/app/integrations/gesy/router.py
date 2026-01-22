"""
Gesy Integration API Router.

Exposes endpoints for Cyprus General Healthcare System (GHS) integration:
- Beneficiary verification
- Referral management
- Claims submission and tracking
- Reference data (specialties, code validation)
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.permissions import Permission, require_permission
from app.integrations.gesy.interface import GesyApiError
from app.integrations.gesy.schemas import (
    BeneficiaryStatus,
    GesyClaim,
    GesyClaimCreate,
    GesyClaimStatus,
    GesyReferral,
    GesyReferralCreate,
    GesyReferralStatus,
    GesySpecialty,
)
from app.integrations.gesy.service import GesyService, get_gesy_service

router = APIRouter(prefix="/gesy", tags=["Gesy"])


def _get_provider_id(request: Request) -> str:
    """Extract the clinic's Gesy provider ID from request context."""
    return getattr(request.state, "gesy_provider_id", "CARD001")


# =============================================================================
# Beneficiary Endpoints
# =============================================================================


@router.get(
    "/beneficiary/{beneficiary_id}",
    response_model=BeneficiaryStatus,
    dependencies=[Depends(require_permission(Permission.GESY_BENEFICIARY_READ))],
    summary="Verify Gesy beneficiary status",
)
async def verify_beneficiary(
    beneficiary_id: str,
    service: GesyService = Depends(get_gesy_service),
) -> BeneficiaryStatus:
    """Verify a patient's Gesy beneficiary status by Gesy ID."""
    result = await service.verify_beneficiary(beneficiary_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Beneficiary not found or inactive",
        )
    return result


@router.get(
    "/beneficiary/lookup/{cyprus_id}",
    response_model=BeneficiaryStatus,
    dependencies=[Depends(require_permission(Permission.GESY_BENEFICIARY_READ))],
    summary="Lookup beneficiary by Cyprus ID card",
)
async def lookup_beneficiary_by_id_card(
    cyprus_id: str,
    service: GesyService = Depends(get_gesy_service),
) -> BeneficiaryStatus:
    """Look up beneficiary by Cyprus ID card number."""
    result = await service.verify_beneficiary_by_id_card(cyprus_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No beneficiary found for this ID card",
        )
    return result


# =============================================================================
# Referral Endpoints
# =============================================================================


@router.post(
    "/referrals",
    response_model=GesyReferral,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.GESY_REFERRAL_WRITE))],
    summary="Create a Gesy referral",
)
async def create_referral(
    data: GesyReferralCreate,
    service: GesyService = Depends(get_gesy_service),
) -> GesyReferral:
    """Create a new Gesy specialist referral voucher."""
    try:
        return await service.create_referral(data)
    except GesyApiError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/referrals/{referral_id}",
    response_model=GesyReferral,
    dependencies=[Depends(require_permission(Permission.GESY_REFERRAL_READ))],
    summary="Get referral details",
)
async def get_referral(
    referral_id: str,
    service: GesyService = Depends(get_gesy_service),
) -> GesyReferral:
    """Get referral details by voucher ID."""
    result = await service.get_referral(referral_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referral not found",
        )
    return result


@router.put(
    "/referrals/{referral_id}/close",
    response_model=GesyReferral,
    dependencies=[Depends(require_permission(Permission.GESY_REFERRAL_WRITE))],
    summary="Close a referral with summary",
)
async def close_referral(
    referral_id: str,
    summary_notes: Optional[str] = Query(None, max_length=1000),
    service: GesyService = Depends(get_gesy_service),
) -> GesyReferral:
    """Close a referral with summary notes after completing specialist service."""
    try:
        return await service.close_referral(referral_id, summary_notes)
    except GesyApiError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/referrals",
    response_model=list[GesyReferral],
    dependencies=[Depends(require_permission(Permission.GESY_REFERRAL_READ))],
    summary="List patient referrals",
)
async def list_referrals(
    beneficiary_id: str = Query(..., description="Patient's Gesy beneficiary ID"),
    referral_status: Optional[GesyReferralStatus] = Query(
        None, alias="status", description="Filter by referral status"
    ),
    from_date: Optional[date] = Query(None, description="Filter from date"),
    to_date: Optional[date] = Query(None, description="Filter to date"),
    service: GesyService = Depends(get_gesy_service),
) -> list[GesyReferral]:
    """List referrals for a patient with optional filters."""
    return await service.list_patient_referrals(
        beneficiary_id, referral_status, from_date, to_date
    )


# =============================================================================
# Claims Endpoints
# =============================================================================


@router.post(
    "/claims",
    response_model=GesyClaim,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.GESY_CLAIM_WRITE))],
    summary="Submit a claim",
)
async def submit_claim(
    data: GesyClaimCreate,
    service: GesyService = Depends(get_gesy_service),
) -> GesyClaim:
    """Submit a claim for Gesy reimbursement."""
    try:
        return await service.submit_claim(data)
    except GesyApiError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/claims/{claim_id}",
    response_model=GesyClaim,
    dependencies=[Depends(require_permission(Permission.GESY_CLAIM_READ))],
    summary="Get claim details",
)
async def get_claim(
    claim_id: str,
    service: GesyService = Depends(get_gesy_service),
) -> GesyClaim:
    """Get claim details and current status."""
    result = await service.get_claim(claim_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found",
        )
    return result


@router.get(
    "/claims",
    response_model=list[GesyClaim],
    dependencies=[Depends(require_permission(Permission.GESY_CLAIM_READ))],
    summary="List provider claims",
)
async def list_claims(
    request: Request,
    claim_status: Optional[GesyClaimStatus] = Query(
        None, alias="status", description="Filter by claim status"
    ),
    from_date: Optional[date] = Query(None, description="Filter from date"),
    to_date: Optional[date] = Query(None, description="Filter to date"),
    service: GesyService = Depends(get_gesy_service),
) -> list[GesyClaim]:
    """List claims for the current provider/clinic."""
    provider_id = _get_provider_id(request)
    return await service.list_provider_claims(
        provider_id, claim_status, from_date, to_date
    )


# =============================================================================
# Reference Data Endpoints
# =============================================================================


@router.get(
    "/specialties",
    response_model=list[GesySpecialty],
    summary="List Gesy specialties",
)
async def list_specialties(
    service: GesyService = Depends(get_gesy_service),
) -> list[GesySpecialty]:
    """Get list of all Gesy medical specialties."""
    return await service.list_specialties()


@router.get(
    "/validate/diagnosis/{code}",
    summary="Validate ICD-10 code",
)
async def validate_diagnosis_code(
    code: str,
    service: GesyService = Depends(get_gesy_service),
) -> dict:
    """Validate an ICD-10 diagnosis code against Gesy standards."""
    valid = await service.validate_diagnosis_code(code)
    return {"code": code, "valid": valid}


@router.get(
    "/validate/procedure/{code}",
    summary="Validate CPT code",
)
async def validate_procedure_code(
    code: str,
    service: GesyService = Depends(get_gesy_service),
) -> dict:
    """Validate a CPT procedure code against Gesy standards."""
    valid = await service.validate_procedure_code(code)
    return {"code": code, "valid": valid}
