"""
Encounter API Router.

REST endpoints for clinical encounters and vitals.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_permission
from app.core.permissions import Permission
from app.db.session import get_session
from app.modules.encounter.schemas import (
    EncounterComplete,
    EncounterCreate,
    EncounterListResponse,
    EncounterResponse,
    EncounterStart,
    EncounterStatus,
    EncounterType,
    EncounterUpdate,
    BillingStatus,
    VitalsCreate,
    VitalsResponse,
    VitalsTrend,
)
from app.modules.encounter.service import EncounterService

router = APIRouter(prefix="/encounters", tags=["Encounters"])


# ============================================================================
# Helper Functions
# ============================================================================


def get_encounter_service(
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> EncounterService:
    """Get encounter service with current user context."""
    return EncounterService(
        session=session,
        clinic_id=current_user["clinic_id"],
        user_id=current_user["user_id"],
    )


# ============================================================================
# Encounter Endpoints
# ============================================================================


@router.get("", response_model=EncounterListResponse)
@require_permission(Permission.VIEW_PATIENTS)
async def list_encounters(
    patient_id: Optional[int] = Query(None, description="Filter by patient"),
    status: Optional[EncounterStatus] = Query(None, description="Filter by status"),
    encounter_type: Optional[EncounterType] = Query(None, description="Filter by type"),
    attending_physician_id: Optional[int] = Query(None, description="Filter by physician"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    billing_status: Optional[BillingStatus] = Query(None, description="Filter by billing status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: EncounterService = Depends(get_encounter_service),
) -> EncounterListResponse:
    """
    List encounters with filtering and pagination.

    Filters:
    - patient_id: Filter by specific patient
    - status: planned, in_progress, completed, cancelled, no_show
    - encounter_type: outpatient, inpatient, emergency, telehealth, home_visit
    - attending_physician_id: Filter by physician
    - date_from/date_to: Date range filter
    - billing_status: pending, submitted, approved, rejected, paid
    """
    encounters, total = await service.get_encounters(
        patient_id=patient_id,
        status=status.value if status else None,
        encounter_type=encounter_type.value if encounter_type else None,
        attending_physician_id=attending_physician_id,
        date_from=date_from,
        date_to=date_to,
        billing_status=billing_status.value if billing_status else None,
        page=page,
        page_size=page_size,
    )

    items = [await service.build_encounter_response(e) for e in encounters]
    total_pages = (total + page_size - 1) // page_size

    return EncounterListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/today", response_model=list[EncounterResponse])
@require_permission(Permission.VIEW_PATIENTS)
async def get_today_encounters(
    service: EncounterService = Depends(get_encounter_service),
) -> list[EncounterResponse]:
    """Get today's encounters for the current physician."""
    encounters = await service.get_today_encounters()
    return [await service.build_encounter_response(e) for e in encounters]


@router.post("", response_model=EncounterResponse, status_code=status.HTTP_201_CREATED)
@require_permission(Permission.EDIT_PATIENTS)
async def create_encounter(
    data: EncounterCreate,
    service: EncounterService = Depends(get_encounter_service),
) -> EncounterResponse:
    """
    Create a new encounter.

    The current user will be set as the attending physician.
    """
    try:
        encounter = await service.create_encounter(data)
        return await service.build_encounter_response(encounter)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{encounter_id}", response_model=EncounterResponse)
@require_permission(Permission.VIEW_PATIENTS)
async def get_encounter(
    encounter_id: int,
    service: EncounterService = Depends(get_encounter_service),
) -> EncounterResponse:
    """Get encounter by ID."""
    encounter = await service.get_encounter(encounter_id)
    if not encounter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encounter not found",
        )
    return await service.build_encounter_response(encounter)


@router.put("/{encounter_id}", response_model=EncounterResponse)
@require_permission(Permission.EDIT_PATIENTS)
async def update_encounter(
    encounter_id: int,
    data: EncounterUpdate,
    service: EncounterService = Depends(get_encounter_service),
) -> EncounterResponse:
    """Update an encounter."""
    encounter = await service.update_encounter(encounter_id, data)
    if not encounter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encounter not found",
        )
    return await service.build_encounter_response(encounter)


@router.post("/{encounter_id}/start", response_model=EncounterResponse)
@require_permission(Permission.EDIT_PATIENTS)
async def start_encounter(
    encounter_id: int,
    data: EncounterStart = EncounterStart(),
    service: EncounterService = Depends(get_encounter_service),
) -> EncounterResponse:
    """
    Start an encounter (set status to in_progress).

    Records the actual start time.
    """
    encounter = await service.start_encounter(encounter_id, data)
    if not encounter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encounter not found",
        )
    return await service.build_encounter_response(encounter)


@router.post("/{encounter_id}/complete", response_model=EncounterResponse)
@require_permission(Permission.EDIT_PATIENTS)
async def complete_encounter(
    encounter_id: int,
    data: EncounterComplete = EncounterComplete(),
    service: EncounterService = Depends(get_encounter_service),
) -> EncounterResponse:
    """
    Complete an encounter.

    Records the actual end time and optional discharge summary/diagnoses.
    """
    encounter = await service.complete_encounter(encounter_id, data)
    if not encounter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encounter not found",
        )
    return await service.build_encounter_response(encounter)


@router.post("/{encounter_id}/cancel", response_model=EncounterResponse)
@require_permission(Permission.EDIT_PATIENTS)
async def cancel_encounter(
    encounter_id: int,
    reason: Optional[str] = Query(None, max_length=500),
    service: EncounterService = Depends(get_encounter_service),
) -> EncounterResponse:
    """Cancel an encounter with optional reason."""
    encounter = await service.cancel_encounter(encounter_id, reason)
    if not encounter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encounter not found",
        )
    return await service.build_encounter_response(encounter)


@router.post("/{encounter_id}/no-show", response_model=EncounterResponse)
@require_permission(Permission.EDIT_PATIENTS)
async def mark_no_show(
    encounter_id: int,
    service: EncounterService = Depends(get_encounter_service),
) -> EncounterResponse:
    """Mark an encounter as no-show."""
    encounter = await service.mark_no_show(encounter_id)
    if not encounter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encounter not found",
        )
    return await service.build_encounter_response(encounter)


# ============================================================================
# Vitals Endpoints
# ============================================================================


@router.post("/{encounter_id}/vitals", response_model=VitalsResponse, status_code=status.HTTP_201_CREATED)
@require_permission(Permission.EDIT_PATIENTS)
async def record_vitals(
    encounter_id: int,
    data: VitalsCreate,
    service: EncounterService = Depends(get_encounter_service),
) -> VitalsResponse:
    """
    Record vitals for an encounter.

    BMI is calculated automatically if height and weight are provided.
    """
    vitals = await service.record_vitals(encounter_id, data)
    if not vitals:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encounter not found",
        )
    return await service.build_vitals_response(vitals)


@router.get("/{encounter_id}/vitals", response_model=list[VitalsResponse])
@require_permission(Permission.VIEW_PATIENTS)
async def get_encounter_vitals(
    encounter_id: int,
    service: EncounterService = Depends(get_encounter_service),
) -> list[VitalsResponse]:
    """Get all vitals recorded during an encounter."""
    vitals_list = await service.get_encounter_vitals(encounter_id)
    return [await service.build_vitals_response(v) for v in vitals_list]


# ============================================================================
# Patient Vitals Endpoints (moved from patient router for convenience)
# ============================================================================


@router.get("/patients/{patient_id}/vitals/latest", response_model=Optional[VitalsResponse])
@require_permission(Permission.VIEW_PATIENTS)
async def get_patient_latest_vitals(
    patient_id: int,
    service: EncounterService = Depends(get_encounter_service),
) -> Optional[VitalsResponse]:
    """Get the most recent vitals for a patient."""
    vitals = await service.get_latest_vitals(patient_id)
    if vitals:
        return await service.build_vitals_response(vitals)
    return None


@router.get("/patients/{patient_id}/vitals/trend", response_model=list[VitalsResponse])
@require_permission(Permission.VIEW_PATIENTS)
async def get_patient_vitals_trend(
    patient_id: int,
    limit: int = Query(20, ge=1, le=100),
    service: EncounterService = Depends(get_encounter_service),
) -> list[VitalsResponse]:
    """Get vitals history for a patient (most recent first)."""
    vitals_list = await service.get_patient_vitals_trend(patient_id, "all", limit)
    return [await service.build_vitals_response(v) for v in vitals_list]
