"""Appointment API Router.

REST endpoints for appointment scheduling, conflict detection,
check-in, and encounter handover.
"""

from datetime import date, datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import Permission, require_permission
from app.core.security import TokenPayload, get_current_user
from app.db.session import get_db
from app.modules.appointment.models import AppointmentStatus
from app.modules.appointment.schemas import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentUpdate,
    check_duration_warning,
)
from app.modules.appointment.service import AppointmentService

router = APIRouter(prefix="/appointments", tags=["Appointments"])


def _build_response(appointment) -> AppointmentResponse:
    """Build response with optional duration warning."""
    response = AppointmentResponse.model_validate(appointment)
    response.duration_warning = check_duration_warning(
        appointment.appointment_type, appointment.duration_minutes
    )
    return response


# =============================================================================
# CRUD Endpoints
# =============================================================================


@router.post(
    "",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_appointment(
    data: AppointmentCreate,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.APPOINTMENT_WRITE))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppointmentResponse:
    """Create a new appointment with conflict check."""
    service = AppointmentService(db, user.clinic_id, user.sub)
    try:
        appointment = await service.create_appointment(data)
        await db.commit()
        return _build_response(appointment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get("", response_model=list[AppointmentResponse])
async def list_appointments(
    user: Annotated[TokenPayload, Depends(require_permission(Permission.APPOINTMENT_READ))],
    db: Annotated[AsyncSession, Depends(get_db)],
    from_date: Optional[date] = Query(None, description="Start date filter"),
    to_date: Optional[date] = Query(None, description="End date filter"),
    provider_id: Optional[int] = Query(None, description="Filter by provider"),
    patient_id: Optional[int] = Query(None, description="Filter by patient"),
    appointment_status: Optional[str] = Query(None, alias="status", description="Filter by status"),
) -> list[AppointmentResponse]:
    """List appointments with optional filters."""
    service = AppointmentService(db, user.clinic_id, user.sub)
    appointments = await service.list_appointments(
        from_date=from_date,
        to_date=to_date,
        provider_id=provider_id,
        patient_id=patient_id,
        status=appointment_status,
    )
    # Batch-resolve patient names (encrypted PII)
    patient_ids = list({a.patient_id for a in appointments})
    name_map = await service.resolve_patient_names(patient_ids)
    responses = []
    for a in appointments:
        resp = _build_response(a)
        resp.patient_name = name_map.get(a.patient_id)
        responses.append(resp)
    return responses


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: int,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.APPOINTMENT_READ))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppointmentResponse:
    """Get appointment details."""
    service = AppointmentService(db, user.clinic_id, user.sub)
    appointment = await service.get_appointment(appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )
    resp = _build_response(appointment)
    name_map = await service.resolve_patient_names([appointment.patient_id])
    resp.patient_name = name_map.get(appointment.patient_id)
    return resp


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: int,
    data: AppointmentUpdate,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.APPOINTMENT_WRITE))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppointmentResponse:
    """Update or reschedule an appointment."""
    service = AppointmentService(db, user.clinic_id, user.sub)
    try:
        appointment = await service.update_appointment(appointment_id, data)
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found",
            )
        await db.commit()
        return _build_response(appointment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.delete("/{appointment_id}", response_model=AppointmentResponse)
async def cancel_appointment(
    appointment_id: int,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.APPOINTMENT_DELETE))],
    db: Annotated[AsyncSession, Depends(get_db)],
    reason: Optional[str] = Query(None, max_length=500),
) -> AppointmentResponse:
    """Cancel an appointment."""
    service = AppointmentService(db, user.clinic_id, user.sub)
    try:
        appointment = await service.cancel_appointment(appointment_id, reason)
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found",
            )
        await db.commit()
        return _build_response(appointment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =============================================================================
# Workflow Endpoints
# =============================================================================


@router.post("/{appointment_id}/check-in", response_model=AppointmentResponse)
async def check_in_appointment(
    appointment_id: int,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.APPOINTMENT_WRITE))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppointmentResponse:
    """Check in a patient for their appointment."""
    service = AppointmentService(db, user.clinic_id, user.sub)
    try:
        appointment = await service.check_in(appointment_id)
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found",
            )
        await db.commit()
        return _build_response(appointment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{appointment_id}/start-encounter")
async def start_encounter_from_appointment(
    appointment_id: int,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.ENCOUNTER_WRITE))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Create an encounter from an appointment and link them.

    This is the appointment-to-encounter handover:
    - Creates a new encounter with appointment data pre-populated
    - Links appointment to the new encounter
    - Updates appointment status to IN_PROGRESS
    """
    service = AppointmentService(db, user.clinic_id, user.sub)
    try:
        encounter = await service.start_encounter_from_appointment(appointment_id)
        await db.commit()
        return {
            "encounter_id": encounter.encounter_id,
            "appointment_id": appointment_id,
            "status": "in_progress",
            "message": "Encounter created and linked to appointment",
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =============================================================================
# Scheduling Helpers
# =============================================================================


@router.get("/slots/available")
async def get_available_slots(
    provider_id: int,
    target_date: date,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.APPOINTMENT_READ))],
    db: Annotated[AsyncSession, Depends(get_db)],
    duration_minutes: int = Query(30, ge=5, le=480),
) -> list[dict]:
    """Get available time slots for a provider on a date."""
    service = AppointmentService(db, user.clinic_id, user.sub)
    return await service.get_available_slots(
        provider_id=provider_id,
        target_date=target_date,
        duration_minutes=duration_minutes,
    )


@router.get("/conflicts/check")
async def check_conflicts(
    provider_id: int,
    start_time: datetime,
    end_time: datetime,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.APPOINTMENT_READ))],
    db: Annotated[AsyncSession, Depends(get_db)],
    exclude_id: Optional[int] = Query(None),
) -> list[dict]:
    """Check for scheduling conflicts for a provider in a time range."""
    service = AppointmentService(db, user.clinic_id, user.sub)
    conflicts = await service.check_conflicts(
        provider_id=provider_id,
        start_time=start_time,
        end_time=end_time,
        exclude_id=exclude_id,
    )
    return [c.model_dump() for c in conflicts]
