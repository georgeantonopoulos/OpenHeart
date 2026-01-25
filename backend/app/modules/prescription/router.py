"""FastAPI router for prescription endpoints."""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import Permission, require_permission
from app.core.security import TokenPayload
from app.db.session import get_db
from app.modules.prescription.cardiology_formulary import (
    CARDIOLOGY_FORMULARY,
    get_all_formulary_drugs,
    get_drug_by_atc,
    search_formulary,
)
from app.modules.prescription.schemas import (
    DrugTemplateResponse,
    FormularyResponse,
    InteractionCheckRequest,
    InteractionCheckResponse,
    MedicationHistoryResponse,
    PrescriptionCreate,
    PrescriptionDiscontinue,
    PrescriptionHold,
    PrescriptionListResponse,
    PrescriptionRenew,
    PrescriptionResponse,
    PrescriptionUpdate,
)
from app.modules.prescription.service import PrescriptionService

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])


def _build_response(prescription) -> PrescriptionResponse:
    """Build PrescriptionResponse from ORM model."""
    resp = PrescriptionResponse.model_validate(prescription)
    resp.can_renew = prescription.can_renew
    resp.days_remaining = prescription.days_remaining
    resp.interactions = [
        {
            "id": i.id,
            "interacting_drug_name": i.interacting_drug_name,
            "interacting_atc_code": i.interacting_atc_code,
            "severity": i.severity,
            "interaction_type": i.interaction_type,
            "description": i.description,
            "management_recommendation": i.management_recommendation,
            "acknowledged_at": i.acknowledged_at,
            "override_reason": i.override_reason,
        }
        for i in (prescription.interactions or [])
    ]
    return resp


# =============================================================================
# Patient Prescription Endpoints
# =============================================================================


@router.post(
    "/patients/{patient_id}",
    response_model=PrescriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_prescription(
    patient_id: int,
    data: PrescriptionCreate,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.PRESCRIPTION_WRITE))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PrescriptionResponse:
    """Create a new prescription for a patient."""
    if data.patient_id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="patient_id in body does not match URL",
        )

    service = PrescriptionService(db, user.clinic_id, user.sub)
    try:
        prescription = await service.create_prescription(data)
        await db.commit()
        return _build_response(prescription)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.get(
    "/patients/{patient_id}",
    response_model=PrescriptionListResponse,
)
async def list_patient_prescriptions(
    patient_id: int,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.PRESCRIPTION_READ))],
    db: Annotated[AsyncSession, Depends(get_db)],
    prescription_status: Optional[str] = Query(None, alias="status", description="Filter by status"),
    include_inactive: bool = Query(True, description="Include discontinued/expired"),
) -> PrescriptionListResponse:
    """List all prescriptions for a patient."""
    service = PrescriptionService(db, user.clinic_id, user.sub)
    prescriptions, total = await service.list_prescriptions(
        patient_id=patient_id,
        status=prescription_status,
        include_inactive=include_inactive,
    )
    return PrescriptionListResponse(
        items=[_build_response(rx) for rx in prescriptions],
        total=total,
    )


@router.get(
    "/patients/{patient_id}/active",
    response_model=list[PrescriptionResponse],
)
async def get_active_medications(
    patient_id: int,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.PRESCRIPTION_READ))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PrescriptionResponse]:
    """Get active medications only for a patient."""
    service = PrescriptionService(db, user.clinic_id, user.sub)
    prescriptions = await service.get_active_medications(patient_id)
    return [_build_response(rx) for rx in prescriptions]


@router.get(
    "/patients/{patient_id}/chronic",
    response_model=list[PrescriptionResponse],
)
async def get_chronic_medications(
    patient_id: int,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.PRESCRIPTION_READ))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PrescriptionResponse]:
    """Get chronic medications for a patient."""
    service = PrescriptionService(db, user.clinic_id, user.sub)
    prescriptions = await service.get_chronic_medications(patient_id)
    return [_build_response(rx) for rx in prescriptions]


# =============================================================================
# Individual Prescription Endpoints
# =============================================================================


@router.get(
    "/{prescription_id}",
    response_model=PrescriptionResponse,
)
async def get_prescription(
    prescription_id: UUID,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.PRESCRIPTION_READ))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PrescriptionResponse:
    """Get prescription details."""
    service = PrescriptionService(db, user.clinic_id, user.sub)
    prescription = await service.get_prescription(prescription_id)
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found",
        )
    return _build_response(prescription)


@router.put(
    "/{prescription_id}",
    response_model=PrescriptionResponse,
)
async def update_prescription(
    prescription_id: UUID,
    data: PrescriptionUpdate,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.PRESCRIPTION_WRITE))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PrescriptionResponse:
    """Update prescription details (dose change, notes)."""
    service = PrescriptionService(db, user.clinic_id, user.sub)
    try:
        prescription = await service.update_prescription(prescription_id, data)
        if not prescription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prescription not found",
            )
        await db.commit()
        return _build_response(prescription)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.post(
    "/{prescription_id}/discontinue",
    response_model=PrescriptionResponse,
)
async def discontinue_prescription(
    prescription_id: UUID,
    data: PrescriptionDiscontinue,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.PRESCRIPTION_WRITE))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PrescriptionResponse:
    """Discontinue a prescription with required reason."""
    service = PrescriptionService(db, user.clinic_id, user.sub)
    try:
        prescription = await service.discontinue(prescription_id, data)
        if not prescription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prescription not found",
            )
        await db.commit()
        return _build_response(prescription)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.post(
    "/{prescription_id}/renew",
    response_model=PrescriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def renew_prescription(
    prescription_id: UUID,
    data: PrescriptionRenew,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.PRESCRIPTION_WRITE))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PrescriptionResponse:
    """Renew a chronic prescription."""
    service = PrescriptionService(db, user.clinic_id, user.sub)
    try:
        new_rx = await service.renew_prescription(prescription_id, data)
        await db.commit()
        return _build_response(new_rx)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.post(
    "/{prescription_id}/hold",
    response_model=PrescriptionResponse,
)
async def hold_prescription(
    prescription_id: UUID,
    data: PrescriptionHold,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.PRESCRIPTION_WRITE))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PrescriptionResponse:
    """Put a prescription on hold."""
    service = PrescriptionService(db, user.clinic_id, user.sub)
    try:
        prescription = await service.hold_prescription(prescription_id, data)
        if not prescription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prescription not found",
            )
        await db.commit()
        return _build_response(prescription)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.post(
    "/{prescription_id}/resume",
    response_model=PrescriptionResponse,
)
async def resume_prescription(
    prescription_id: UUID,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.PRESCRIPTION_WRITE))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PrescriptionResponse:
    """Resume a prescription from hold."""
    service = PrescriptionService(db, user.clinic_id, user.sub)
    try:
        prescription = await service.resume_prescription(prescription_id)
        if not prescription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prescription not found",
            )
        await db.commit()
        return _build_response(prescription)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.get(
    "/{prescription_id}/history",
    response_model=list[MedicationHistoryResponse],
)
async def get_prescription_history(
    prescription_id: UUID,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.PRESCRIPTION_READ))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[MedicationHistoryResponse]:
    """Get medication change history for a prescription."""
    service = PrescriptionService(db, user.clinic_id, user.sub)
    history = await service.get_prescription_history(prescription_id)
    return [MedicationHistoryResponse.model_validate(h) for h in history]


# =============================================================================
# Interaction Checking
# =============================================================================


@router.post(
    "/interactions/check",
    response_model=InteractionCheckResponse,
)
async def check_interactions(
    data: InteractionCheckRequest,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.PRESCRIPTION_READ))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InteractionCheckResponse:
    """Check drug interactions before prescribing."""
    service = PrescriptionService(db, user.clinic_id, user.sub)
    return await service.check_interactions(data)


# =============================================================================
# Formulary Endpoints
# =============================================================================


@router.get(
    "/formulary/cardiology",
    response_model=FormularyResponse,
)
async def get_cardiology_formulary(
    user: Annotated[TokenPayload, Depends(require_permission(Permission.PRESCRIPTION_READ))],
) -> FormularyResponse:
    """Get the curated cardiology formulary grouped by category."""
    categories = {}
    total = 0
    for category_name, drugs in CARDIOLOGY_FORMULARY.items():
        categories[category_name] = [
            DrugTemplateResponse(
                generic_name=d.generic_name,
                atc_code=d.atc_code,
                category=d.category,
                default_strength=d.default_strength,
                default_form=d.default_form,
                default_frequency=d.default_frequency,
                default_route=d.default_route,
                is_chronic=d.is_chronic,
                available_strengths=d.available_strengths,
                common_indications=d.common_indications,
                loading_dose=d.loading_dose,
                renal_adjustment=d.renal_adjustment,
            )
            for d in drugs
        ]
        total += len(drugs)

    return FormularyResponse(categories=categories, total_drugs=total)


@router.get(
    "/formulary/search",
    response_model=list[DrugTemplateResponse],
)
async def search_formulary_endpoint(
    q: str = Query(..., min_length=2, description="Search query"),
    user: Annotated[TokenPayload, Depends(require_permission(Permission.PRESCRIPTION_READ))] = None,
) -> list[DrugTemplateResponse]:
    """Search the formulary by drug name, ATC code, or indication."""
    results = search_formulary(q)
    return [
        DrugTemplateResponse(
            generic_name=d.generic_name,
            atc_code=d.atc_code,
            category=d.category,
            default_strength=d.default_strength,
            default_form=d.default_form,
            default_frequency=d.default_frequency,
            default_route=d.default_route,
            is_chronic=d.is_chronic,
            available_strengths=d.available_strengths,
            common_indications=d.common_indications,
            loading_dose=d.loading_dose,
            renal_adjustment=d.renal_adjustment,
        )
        for d in results
    ]


@router.get(
    "/formulary/categories",
    response_model=list[str],
)
async def get_formulary_categories(
    user: Annotated[TokenPayload, Depends(require_permission(Permission.PRESCRIPTION_READ))],
) -> list[str]:
    """List available drug categories in the formulary."""
    return list(CARDIOLOGY_FORMULARY.keys())


@router.get(
    "/formulary/{atc_code}/defaults",
    response_model=DrugTemplateResponse,
)
async def get_drug_defaults(
    atc_code: str,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.PRESCRIPTION_READ))],
) -> DrugTemplateResponse:
    """Get default dosing for a drug by ATC code."""
    drug = get_drug_by_atc(atc_code)
    if not drug:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drug with ATC code '{atc_code}' not found in formulary",
        )
    return DrugTemplateResponse(
        generic_name=drug.generic_name,
        atc_code=drug.atc_code,
        category=drug.category,
        default_strength=drug.default_strength,
        default_form=drug.default_form,
        default_frequency=drug.default_frequency,
        default_route=drug.default_route,
        is_chronic=drug.is_chronic,
        available_strengths=drug.available_strengths,
        common_indications=drug.common_indications,
        loading_dose=drug.loading_dose,
        renal_adjustment=drug.renal_adjustment,
    )
