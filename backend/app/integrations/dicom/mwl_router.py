"""
Modality Worklist (MWL) API Router for OpenHeart Cyprus.

Provides REST endpoints for scheduling imaging procedures,
querying the worklist, and managing equipment stations.
"""

from datetime import date, datetime
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import Permission, require_permission
from app.core.security import TokenPayload, get_current_user
from app.db.session import get_db
from app.integrations.dicom.mwl_models import ImagingModality, ProcedureStatus
from app.integrations.dicom.mwl_service import MWLService

router = APIRouter(prefix="/procedures", tags=["Modality Worklist"])


# =============================================================================
# Request/Response Models
# =============================================================================


class ScheduleProcedureRequest(BaseModel):
    """Request to schedule a new imaging procedure."""

    patient_id: int
    modality: ImagingModality
    scheduled_datetime: datetime
    station_ae_title: str
    procedure_description: Optional[str] = None
    procedure_code: Optional[str] = None
    performing_physician_id: Optional[int] = None
    referring_physician_name: Optional[str] = None
    reason_for_exam: Optional[str] = None
    priority: str = Field(default="ROUTINE", pattern="^(STAT|URGENT|ROUTINE)$")
    encounter_id: Optional[int] = None
    expected_duration_minutes: Optional[int] = Field(None, ge=5, le=480)
    notes: Optional[str] = None


class ScheduledProcedureResponse(BaseModel):
    """Response for a scheduled procedure."""

    id: str
    patient_id: int
    clinic_id: int
    accession_number: str
    station_ae_title: str
    station_name: Optional[str]
    modality: str
    procedure_description: Optional[str]
    scheduled_datetime: datetime
    status: str
    priority: str
    reason_for_exam: Optional[str]
    performing_physician_id: Optional[int]
    study_instance_uid: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class WorklistItemResponse(BaseModel):
    """DICOM-formatted worklist item."""

    PatientID: str
    PatientName: str
    PatientBirthDate: str
    PatientSex: str
    AccessionNumber: str
    Modality: str
    ScheduledProcedureStepStartDate: str
    ScheduledProcedureStepStartTime: str
    ScheduledStationAETitle: str
    ScheduledProcedureStepDescription: str
    ScheduledProcedureStepStatus: str
    ScheduledPerformingPhysicianName: str
    StudyInstanceUID: str


class WorklistStationResponse(BaseModel):
    """Configured worklist station."""

    id: int
    ae_title: str
    station_name: str
    modality: str
    location: Optional[str]
    manufacturer: Optional[str]
    model: Optional[str]
    is_active: bool
    last_query_at: Optional[datetime]

    class Config:
        from_attributes = True


class CreateStationRequest(BaseModel):
    """Request to create a worklist station."""

    ae_title: str = Field(..., max_length=16, pattern="^[A-Z0-9_]+$")
    station_name: str = Field(..., max_length=64)
    modality: ImagingModality
    location: Optional[str] = Field(None, max_length=64)
    manufacturer: Optional[str] = Field(None, max_length=64)
    model: Optional[str] = Field(None, max_length=64)


class UpdateStatusRequest(BaseModel):
    """Request to update procedure status."""

    status: ProcedureStatus
    actual_start_datetime: Optional[datetime] = None
    actual_end_datetime: Optional[datetime] = None
    study_instance_uid: Optional[str] = None


class CancelProcedureRequest(BaseModel):
    """Request to cancel a procedure."""

    cancellation_reason: str = Field(..., min_length=3, max_length=256)


# =============================================================================
# Dependencies
# =============================================================================


async def get_mwl_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MWLService:
    """Get MWL service instance."""
    return MWLService(db)


# =============================================================================
# Procedure Scheduling Endpoints
# =============================================================================


@router.post("/schedule", response_model=ScheduledProcedureResponse)
async def schedule_procedure(
    request: ScheduleProcedureRequest,
    user: Annotated[
        TokenPayload,
        Depends(require_permission(Permission.CLINICAL_WRITE)),
    ],
    mwl: Annotated[MWLService, Depends(get_mwl_service)],
):
    """
    Schedule a new imaging procedure.

    Creates a record that will appear in the Modality Worklist
    for the specified imaging equipment.

    Requires CLINICAL_WRITE permission.
    """
    try:
        procedure = await mwl.schedule_procedure(
            patient_id=request.patient_id,
            clinic_id=user.clinic_id,
            modality=request.modality,
            scheduled_datetime=request.scheduled_datetime,
            station_ae_title=request.station_ae_title,
            procedure_description=request.procedure_description,
            procedure_code=request.procedure_code,
            performing_physician_id=request.performing_physician_id,
            referring_physician_name=request.referring_physician_name,
            reason_for_exam=request.reason_for_exam,
            priority=request.priority,
            encounter_id=request.encounter_id,
            expected_duration_minutes=request.expected_duration_minutes,
            notes=request.notes,
            created_by_user_id=user.sub,
        )

        return ScheduledProcedureResponse(
            id=str(procedure.id),
            patient_id=procedure.patient_id,
            clinic_id=procedure.clinic_id,
            accession_number=procedure.accession_number,
            station_ae_title=procedure.scheduled_station_ae_title,
            station_name=procedure.scheduled_station_name,
            modality=procedure.modality.value,
            procedure_description=procedure.procedure_description,
            scheduled_datetime=procedure.scheduled_datetime,
            status=procedure.status.value,
            priority=procedure.priority,
            reason_for_exam=procedure.reason_for_exam,
            performing_physician_id=procedure.performing_physician_id,
            study_instance_uid=procedure.study_instance_uid,
            created_at=procedure.created_at,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/scheduled", response_model=list[ScheduledProcedureResponse])
async def list_scheduled_procedures(
    user: Annotated[TokenPayload, Depends(get_current_user)],
    mwl: Annotated[MWLService, Depends(get_mwl_service)],
    scheduled_date: Optional[date] = Query(None, description="Filter by date"),
    station_ae_title: Optional[str] = Query(None, description="Filter by station"),
    modality: Optional[ImagingModality] = Query(None, description="Filter by modality"),
    patient_id: Optional[int] = Query(None, description="Filter by patient"),
    include_completed: bool = Query(False, description="Include completed procedures"),
):
    """
    List scheduled procedures (worklist view).

    Returns procedures scheduled for the user's clinic.
    Default shows only SCHEDULED and IN_PROGRESS status.
    """
    worklist = await mwl.get_worklist(
        station_ae_title=station_ae_title,
        modality=modality,
        scheduled_date=scheduled_date or date.today(),
        clinic_id=user.clinic_id,
        include_completed=include_completed,
    )

    # Convert worklist format to response format
    procedures = []
    for item in worklist:
        procedures.append(
            ScheduledProcedureResponse(
                id=item.get("_openheart_procedure_id", ""),
                patient_id=item.get("_openheart_patient_id", 0),
                clinic_id=user.clinic_id,
                accession_number=item["AccessionNumber"],
                station_ae_title=item["ScheduledStationAETitle"],
                station_name=item.get("ScheduledStationName"),
                modality=item["Modality"],
                procedure_description=item.get("ScheduledProcedureStepDescription"),
                scheduled_datetime=datetime.strptime(
                    f"{item['ScheduledProcedureStepStartDate']}{item['ScheduledProcedureStepStartTime']}",
                    "%Y%m%d%H%M%S",
                ),
                status=item["ScheduledProcedureStepStatus"],
                priority=item.get("RequestedProcedurePriority", "ROUTINE"),
                reason_for_exam=item.get("ReasonForTheRequestedProcedure"),
                performing_physician_id=None,
                study_instance_uid=item.get("StudyInstanceUID"),
                created_at=datetime.now(),  # Not available in worklist format
            )
        )

    return procedures


@router.get("/worklist", response_model=list[WorklistItemResponse])
async def get_worklist(
    user: Annotated[TokenPayload, Depends(get_current_user)],
    mwl: Annotated[MWLService, Depends(get_mwl_service)],
    station_ae_title: Optional[str] = Query(None),
    modality: Optional[ImagingModality] = Query(None),
    scheduled_date: Optional[date] = Query(None),
):
    """
    Get worklist in DICOM-compatible format.

    This endpoint returns data formatted for DICOM MWL C-FIND responses.
    Used by DICOM bridge services that translate HTTP to DICOM protocol.
    """
    worklist = await mwl.get_worklist(
        station_ae_title=station_ae_title,
        modality=modality,
        scheduled_date=scheduled_date,
        clinic_id=user.clinic_id,
    )

    # Filter to DICOM-standard fields only
    return [
        WorklistItemResponse(
            PatientID=item["PatientID"],
            PatientName=item["PatientName"],
            PatientBirthDate=item["PatientBirthDate"],
            PatientSex=item["PatientSex"],
            AccessionNumber=item["AccessionNumber"],
            Modality=item["Modality"],
            ScheduledProcedureStepStartDate=item["ScheduledProcedureStepStartDate"],
            ScheduledProcedureStepStartTime=item["ScheduledProcedureStepStartTime"],
            ScheduledStationAETitle=item["ScheduledStationAETitle"],
            ScheduledProcedureStepDescription=item["ScheduledProcedureStepDescription"],
            ScheduledProcedureStepStatus=item["ScheduledProcedureStepStatus"],
            ScheduledPerformingPhysicianName=item["ScheduledPerformingPhysicianName"],
            StudyInstanceUID=item["StudyInstanceUID"],
        )
        for item in worklist
    ]


@router.get("/{procedure_id}", response_model=ScheduledProcedureResponse)
async def get_procedure(
    procedure_id: str,
    user: Annotated[TokenPayload, Depends(get_current_user)],
    mwl: Annotated[MWLService, Depends(get_mwl_service)],
):
    """Get a specific procedure by ID."""
    procedure = await mwl.get_procedure(procedure_id)

    if not procedure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procedure not found",
        )

    # Verify clinic access
    if procedure.clinic_id != user.clinic_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return ScheduledProcedureResponse(
        id=str(procedure.id),
        patient_id=procedure.patient_id,
        clinic_id=procedure.clinic_id,
        accession_number=procedure.accession_number,
        station_ae_title=procedure.scheduled_station_ae_title,
        station_name=procedure.scheduled_station_name,
        modality=procedure.modality.value,
        procedure_description=procedure.procedure_description,
        scheduled_datetime=procedure.scheduled_datetime,
        status=procedure.status.value,
        priority=procedure.priority,
        reason_for_exam=procedure.reason_for_exam,
        performing_physician_id=procedure.performing_physician_id,
        study_instance_uid=procedure.study_instance_uid,
        created_at=procedure.created_at,
    )


@router.put("/{procedure_id}/status")
async def update_procedure_status(
    procedure_id: str,
    request: UpdateStatusRequest,
    user: Annotated[
        TokenPayload,
        Depends(require_permission(Permission.CLINICAL_WRITE)),
    ],
    mwl: Annotated[MWLService, Depends(get_mwl_service)],
):
    """
    Update procedure status (MPPS integration).

    Called when imaging equipment reports procedure progress.
    """
    procedure = await mwl.update_procedure_status(
        procedure_id=procedure_id,
        status=request.status,
        actual_start_datetime=request.actual_start_datetime,
        actual_end_datetime=request.actual_end_datetime,
        study_instance_uid=request.study_instance_uid,
    )

    if not procedure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procedure not found",
        )

    return {"status": "updated", "new_status": procedure.status.value}


@router.post("/{procedure_id}/cancel")
async def cancel_procedure(
    procedure_id: str,
    request: CancelProcedureRequest,
    user: Annotated[
        TokenPayload,
        Depends(require_permission(Permission.CLINICAL_WRITE)),
    ],
    mwl: Annotated[MWLService, Depends(get_mwl_service)],
):
    """Cancel a scheduled procedure."""
    procedure = await mwl.cancel_procedure(
        procedure_id=procedure_id,
        cancellation_reason=request.cancellation_reason,
        cancelled_by_user_id=user.sub,
    )

    if not procedure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procedure not found or already in progress",
        )

    return {"status": "cancelled", "accession_number": procedure.accession_number}


# =============================================================================
# Patient Procedures
# =============================================================================


@router.get("/patient/{patient_id}", response_model=list[ScheduledProcedureResponse])
async def get_patient_procedures(
    patient_id: int,
    user: Annotated[TokenPayload, Depends(get_current_user)],
    mwl: Annotated[MWLService, Depends(get_mwl_service)],
    include_cancelled: bool = Query(False),
):
    """Get all scheduled procedures for a patient."""
    procedures = await mwl.get_patient_procedures(
        patient_id=patient_id,
        include_cancelled=include_cancelled,
    )

    return [
        ScheduledProcedureResponse(
            id=str(proc.id),
            patient_id=proc.patient_id,
            clinic_id=proc.clinic_id,
            accession_number=proc.accession_number,
            station_ae_title=proc.scheduled_station_ae_title,
            station_name=proc.scheduled_station_name,
            modality=proc.modality.value,
            procedure_description=proc.procedure_description,
            scheduled_datetime=proc.scheduled_datetime,
            status=proc.status.value,
            priority=proc.priority,
            reason_for_exam=proc.reason_for_exam,
            performing_physician_id=proc.performing_physician_id,
            study_instance_uid=proc.study_instance_uid,
            created_at=proc.created_at,
        )
        for proc in procedures
    ]


# =============================================================================
# Station Management
# =============================================================================


@router.get("/stations", response_model=list[WorklistStationResponse])
async def list_stations(
    user: Annotated[TokenPayload, Depends(get_current_user)],
    mwl: Annotated[MWLService, Depends(get_mwl_service)],
):
    """List configured worklist stations for the clinic."""
    stations = await mwl.get_stations(user.clinic_id)

    return [
        WorklistStationResponse(
            id=station.id,
            ae_title=station.ae_title,
            station_name=station.station_name,
            modality=station.modality.value,
            location=station.location,
            manufacturer=station.manufacturer,
            model=station.model,
            is_active=station.is_active,
            last_query_at=station.last_query_at,
        )
        for station in stations
    ]


@router.post("/stations", response_model=WorklistStationResponse)
async def create_station(
    request: CreateStationRequest,
    user: Annotated[
        TokenPayload,
        Depends(require_permission(Permission.CLINIC_ADMIN)),
    ],
    mwl: Annotated[MWLService, Depends(get_mwl_service)],
):
    """
    Create or update a worklist station configuration.

    Requires CLINIC_ADMIN permission.
    """
    station = await mwl.create_station(
        clinic_id=user.clinic_id,
        ae_title=request.ae_title,
        station_name=request.station_name,
        modality=request.modality,
        location=request.location,
        manufacturer=request.manufacturer,
        model=request.model,
    )

    return WorklistStationResponse(
        id=station.id,
        ae_title=station.ae_title,
        station_name=station.station_name,
        modality=station.modality.value,
        location=station.location,
        manufacturer=station.manufacturer,
        model=station.model,
        is_active=station.is_active,
        last_query_at=station.last_query_at,
    )
