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

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import Permission, require_permission
from app.core.security import TokenPayload
from app.db.session import get_db
from app.modules.patient.models import PatientStatus
from app.modules.patient.schemas import (
    ErasureRequestCancelBody,
    ErasureRequestCreate,
    ErasureRequestEvaluate,
    ErasureRequestListResponse,
    ErasureRequestResponse,
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



# ============================================================================
# Patient CRUD Endpoints
# ============================================================================


@router.post(
    "/",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_patient(
    data: PatientCreate,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.PATIENT_WRITE))],
    service: PatientService = Depends(get_patient_service),
) -> PatientResponse:
    """
    Create a new patient.

    Creates a patient record with encrypted PII. At least one Cyprus
    identifier (Cyprus ID or ARC) should be provided.

    Returns the created patient with decrypted PII for display.
    """
    patient = await service.create_patient(
        data=data,
        user_id=user.sub,
        clinic_id=user.clinic_id,
    )

    return service.build_patient_response(patient, include_pii=True)


@router.get(
    "/",
    response_model=PatientListResponse,
)
async def list_patients(
    user: Annotated[TokenPayload, Depends(require_permission(Permission.PATIENT_READ))],
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
    patients, total = await service.get_patients(
        clinic_id=user.clinic_id,
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
)
async def search_patients(
    user: Annotated[TokenPayload, Depends(require_permission(Permission.PATIENT_READ))],
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
    query = PatientSearchQuery(
        q=q,
        birth_date=birth_date,
        gender=gender,
        status=status,
        gesy_only=gesy_only,
    )

    patients, total = await service.search_patients(
        query=query,
        clinic_id=user.clinic_id,
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
)
async def get_patient(
    patient_id: int,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.PATIENT_READ))],
    service: PatientService = Depends(get_patient_service),
) -> PatientResponse:
    """
    Get a patient by ID.

    Returns full patient details including decrypted PII.
    Access is logged for GDPR compliance.
    """
    patient = await service.get_patient(
        patient_id=patient_id,
        clinic_id=user.clinic_id,
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
)
async def update_patient(
    patient_id: int,
    data: PatientUpdate,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.PATIENT_WRITE))],
    service: PatientService = Depends(get_patient_service),
) -> PatientResponse:
    """
    Update a patient's information.

    Updates both demographic data and encrypted PII.
    """
    patient = await service.update_patient(
        patient_id=patient_id,
        data=data,
        user_id=user.sub,
        clinic_id=user.clinic_id,
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
)
async def delete_patient(
    patient_id: int,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.PATIENT_DELETE))],
    reason: Optional[str] = Query(
        None, max_length=255, description="Reason for deactivation"
    ),
    service: PatientService = Depends(get_patient_service),
) -> None:
    """
    Tier 1: Deactivate a patient (administrative soft-delete).

    The patient is marked as inactive but PII remains encrypted and recoverable.
    This is reversible via the reactivate endpoint.
    For GDPR erasure (PII anonymization), use the erasure-requests endpoints.
    """
    success = await service.delete_patient(
        patient_id=patient_id,
        user_id=user.sub,
        clinic_id=user.clinic_id,
        reason=reason,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )


@router.post(
    "/{patient_id}/reactivate",
    response_model=PatientResponse,
)
async def reactivate_patient(
    patient_id: int,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.PATIENT_DELETE))],
    service: PatientService = Depends(get_patient_service),
) -> PatientResponse:
    """
    Reverse a Tier 1 deactivation.

    Cannot reactivate patients whose PII has been anonymized (Tier 2 erasure).
    """
    patient = await service.reactivate_patient(
        patient_id=patient_id,
        user_id=user.sub,
        clinic_id=user.clinic_id,
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found or not eligible for reactivation",
        )

    return service.build_patient_response(patient, include_pii=True)


# ============================================================================
# Patient Timeline
# ============================================================================


@router.get(
    "/{patient_id}/timeline",
)
async def get_patient_timeline(
    patient_id: int,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.PATIENT_READ))],
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
    timeline = await service.get_patient_timeline(
        patient_id=patient_id,
        clinic_id=user.clinic_id,
        page=page,
        page_size=page_size,
    )

    if not timeline.get("events") and timeline.get("total") == 0:
        # Check if patient exists
        patient = await service.get_patient(patient_id, user.clinic_id)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found",
            )

    return timeline


# ============================================================================
# GDPR Erasure Requests (Article 17)
# ============================================================================


@router.post(
    "/{patient_id}/erasure-requests",
    response_model=ErasureRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_erasure_request(
    patient_id: int,
    data: ErasureRequestCreate,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.ERASURE_REQUEST))],
    service: PatientService = Depends(get_patient_service),
) -> ErasureRequestResponse:
    """
    Submit a GDPR Article 17 erasure request on behalf of a patient.

    The request enters PENDING status and must be evaluated by a System Admin
    before any data is anonymized.
    """
    result = await service.create_erasure_request(
        patient_id=patient_id,
        data=data,
        user_id=user.sub,
        clinic_id=user.clinic_id,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Patient not found or an active erasure request already exists",
        )

    return service.build_erasure_response(result)


@router.get(
    "/{patient_id}/erasure-requests",
    response_model=ErasureRequestListResponse,
)
async def list_erasure_requests(
    patient_id: int,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.ERASURE_VIEW))],
    service: PatientService = Depends(get_patient_service),
) -> ErasureRequestListResponse:
    """
    List all GDPR erasure requests for a patient.

    Includes historical requests (denied, cancelled, executed).
    """
    requests = await service.get_erasure_requests(
        patient_id=patient_id,
        clinic_id=user.clinic_id,
    )

    return ErasureRequestListResponse(
        items=[service.build_erasure_response(r) for r in requests],
        total=len(requests),
    )


@router.patch(
    "/{patient_id}/erasure-requests/{request_id}",
    response_model=ErasureRequestResponse,
)
async def evaluate_erasure_request(
    patient_id: int,
    request_id: int,
    data: ErasureRequestEvaluate,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.ERASURE_EVALUATE))],
    service: PatientService = Depends(get_patient_service),
) -> ErasureRequestResponse:
    """
    Evaluate (approve or deny) a pending erasure request.

    If approved, a 72-hour cooling-off period begins. The request can be
    cancelled during this window. After cooling-off, execution is allowed.

    If denied, the Article 17(3) exception must be documented.
    """
    result = await service.evaluate_erasure_request(
        request_id=request_id,
        data=data,
        user_id=user.sub,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Erasure request not found or not in pending status",
        )

    return service.build_erasure_response(result)


@router.post(
    "/{patient_id}/erasure-requests/{request_id}/cancel",
    response_model=ErasureRequestResponse,
)
async def cancel_erasure_request(
    patient_id: int,
    request_id: int,
    data: ErasureRequestCancelBody,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.ERASURE_EVALUATE))],
    service: PatientService = Depends(get_patient_service),
) -> ErasureRequestResponse:
    """
    Cancel an approved erasure request during the 72-hour cooling-off.

    Only valid while the cooling-off period has not expired.
    After expiry, the request must be executed or a new evaluation initiated.
    """
    result = await service.cancel_approved_erasure(
        request_id=request_id,
        user_id=user.sub,
        reason=data.reason,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Request not found, not approved, or cooling-off period has expired",
        )

    return service.build_erasure_response(result)


@router.post(
    "/{patient_id}/erasure-requests/{request_id}/execute",
    response_model=dict,
)
async def execute_erasure(
    patient_id: int,
    request_id: int,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.ERASURE_EXECUTE))],
    service: PatientService = Depends(get_patient_service),
) -> dict:
    """
    Execute PII anonymization after the 72-hour cooling-off.

    This is IRREVERSIBLE. Overwrites all PII fields with anonymized values.
    Clinical notes are preserved under Article 17(3)(c) healthcare exemption.

    Requires SYSTEM_ADMIN role.
    """
    result = await service.execute_anonymization(
        request_id=request_id,
        user_id=user.sub,
        clinic_id=user.clinic_id,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Request not eligible for execution (not approved, cooling-off not elapsed, or patient not found)",
        )

    return result
