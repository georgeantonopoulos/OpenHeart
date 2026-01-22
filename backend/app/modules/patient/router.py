"""
Patient API Router.

Provides RESTful endpoints for patient management with:
- CRUD operations with encrypted PII
- Search with Greek/Latin name support
- Cyprus-specific identifier handling
- GDPR-compliant data access logging
"""

from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import Permission, require_permission
from app.db.session import get_db
from app.modules.patient.models import PatientStatus
from app.modules.patient.schemas import (
    Gender,
    PatientCreate,
    PatientListResponse,
    PatientResponse,
    PatientSearchQuery,
    PatientUpdate,
)
from app.modules.patient.service import PatientService

router = APIRouter(prefix="/patients", tags=["Patients"])


# ============================================================================
# Dependencies
# ============================================================================


async def get_patient_service(db: AsyncSession = Depends(get_db)) -> PatientService:
    """Dependency for PatientService."""
    return PatientService(db)


def get_current_user_context(request: Request) -> dict:
    """
    Extract current user context from request.

    In production, this comes from JWT token validation.
    """
    return {
        "user_id": getattr(request.state, "user_id", 1),
        "user_email": getattr(request.state, "user_email", "doctor@openheart.cy"),
        "user_role": getattr(request.state, "user_role", "cardiologist"),
        "clinic_id": getattr(request.state, "clinic_id", 1),
    }


# ============================================================================
# Patient CRUD Endpoints
# ============================================================================


@router.post(
    "/",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.PATIENT_WRITE))],
)
async def create_patient(
    data: PatientCreate,
    request: Request,
    service: PatientService = Depends(get_patient_service),
) -> PatientResponse:
    """
    Create a new patient.

    Creates a patient record with encrypted PII. At least one Cyprus
    identifier (Cyprus ID or ARC) should be provided.

    Returns the created patient with decrypted PII for display.
    """
    user_ctx = get_current_user_context(request)

    patient = await service.create_patient(
        data=data,
        user_id=user_ctx["user_id"],
        clinic_id=user_ctx["clinic_id"],
    )

    return service.build_patient_response(patient, include_pii=True)


@router.get(
    "/",
    response_model=PatientListResponse,
    dependencies=[Depends(require_permission(Permission.PATIENT_READ))],
)
async def list_patients(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[PatientStatus] = Query(
        PatientStatus.ACTIVE, description="Filter by status"
    ),
    service: PatientService = Depends(get_patient_service),
) -> PatientListResponse:
    """
    List patients with pagination.

    Returns patients for the current clinic, sorted by last updated.
    """
    user_ctx = get_current_user_context(request)

    patients, total = await service.get_patients(
        clinic_id=user_ctx["clinic_id"],
        page=page,
        page_size=page_size,
        status=status,
    )

    total_pages = (total + page_size - 1) // page_size

    return PatientListResponse(
        items=[service.build_patient_response(p) for p in patients],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/search",
    response_model=PatientListResponse,
    dependencies=[Depends(require_permission(Permission.PATIENT_READ))],
)
async def search_patients(
    request: Request,
    q: Optional[str] = Query(
        None, min_length=2, max_length=100, description="Search name or MRN"
    ),
    birth_date: Optional[date] = Query(None, description="Filter by birth date"),
    gender: Optional[Gender] = Query(None, description="Filter by gender"),
    status: Optional[PatientStatus] = Query(
        PatientStatus.ACTIVE, description="Filter by status"
    ),
    gesy_only: bool = Query(False, description="Only Gesy beneficiaries"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: PatientService = Depends(get_patient_service),
) -> PatientListResponse:
    """
    Search patients by name, MRN, or filters.

    Supports searching by:
    - Patient name (first or last, Greek or Latin characters)
    - MRN (partial match)
    - Birth date (exact)
    - Gender
    - Gesy beneficiary status
    """
    user_ctx = get_current_user_context(request)

    query = PatientSearchQuery(
        q=q,
        birth_date=birth_date,
        gender=gender,
        status=status,
        gesy_only=gesy_only,
    )

    patients, total = await service.search_patients(
        query=query,
        clinic_id=user_ctx["clinic_id"],
        page=page,
        page_size=page_size,
    )

    total_pages = (total + page_size - 1) // page_size

    return PatientListResponse(
        items=[service.build_patient_response(p) for p in patients],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
    dependencies=[Depends(require_permission(Permission.PATIENT_READ))],
)
async def get_patient(
    patient_id: int,
    request: Request,
    service: PatientService = Depends(get_patient_service),
) -> PatientResponse:
    """
    Get a patient by ID.

    Returns full patient details including decrypted PII.
    Access is logged for GDPR compliance.
    """
    user_ctx = get_current_user_context(request)

    patient = await service.get_patient(
        patient_id=patient_id,
        clinic_id=user_ctx["clinic_id"],
        include_pii=True,
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    return service.build_patient_response(patient, include_pii=True)


@router.put(
    "/{patient_id}",
    response_model=PatientResponse,
    dependencies=[Depends(require_permission(Permission.PATIENT_WRITE))],
)
async def update_patient(
    patient_id: int,
    data: PatientUpdate,
    request: Request,
    service: PatientService = Depends(get_patient_service),
) -> PatientResponse:
    """
    Update a patient's information.

    Updates both demographic data and encrypted PII.
    """
    user_ctx = get_current_user_context(request)

    patient = await service.update_patient(
        patient_id=patient_id,
        data=data,
        user_id=user_ctx["user_id"],
        clinic_id=user_ctx["clinic_id"],
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    return service.build_patient_response(patient, include_pii=True)


@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(Permission.PATIENT_DELETE))],
)
async def delete_patient(
    patient_id: int,
    request: Request,
    service: PatientService = Depends(get_patient_service),
) -> None:
    """
    Soft-delete a patient.

    The patient is marked as deleted but retained for medical record keeping
    as required by Cyprus law (15-year retention). PII can be anonymized
    upon GDPR erasure request.
    """
    user_ctx = get_current_user_context(request)

    success = await service.delete_patient(
        patient_id=patient_id,
        user_id=user_ctx["user_id"],
        clinic_id=user_ctx["clinic_id"],
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )


# ============================================================================
# Patient Timeline
# ============================================================================


@router.get(
    "/{patient_id}/timeline",
    dependencies=[Depends(require_permission(Permission.PATIENT_READ))],
)
async def get_patient_timeline(
    patient_id: int,
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: PatientService = Depends(get_patient_service),
) -> dict:
    """
    Get patient activity timeline.

    Returns a chronological list of:
    - Encounters
    - Clinical notes
    - Observations/vitals
    - CDSS calculations
    - DICOM studies

    Ordered by date, newest first.
    """
    user_ctx = get_current_user_context(request)

    timeline = await service.get_patient_timeline(
        patient_id=patient_id,
        clinic_id=user_ctx["clinic_id"],
        page=page,
        page_size=page_size,
    )

    if not timeline.get("events") and timeline.get("total") == 0:
        # Check if patient exists
        patient = await service.get_patient(patient_id, user_ctx["clinic_id"])
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found",
            )

    return timeline
