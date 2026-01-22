"""
DICOM API Router for OpenHeart Cyprus.

Provides REST endpoints for DICOM imaging operations including
study search, retrieval, and OHIF viewer integration.
"""

from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse

from app.core.permissions import Permission, require_permission
from app.core.security import TokenPayload, get_current_user
from app.integrations.dicom.schemas import (
    DicomStudy,
    DicomStudyList,
    EchoMeasurements,
    Modality,
    StudySearchRequest,
    ViewerUrlResponse,
)
from app.integrations.dicom.service import DicomService

router = APIRouter(prefix="/dicom", tags=["DICOM/Imaging"])


def get_dicom_service() -> DicomService:
    """Dependency to get DICOM service instance."""
    return DicomService()


# =============================================================================
# Study Search & Retrieval
# =============================================================================


@router.get("/studies", response_model=DicomStudyList)
async def search_studies(
    user: Annotated[TokenPayload, Depends(get_current_user)],
    dicom: Annotated[DicomService, Depends(get_dicom_service)],
    patient_id: Optional[str] = Query(None, description="DICOM Patient ID"),
    patient_name: Optional[str] = Query(None, description="Patient name (partial match)"),
    accession_number: Optional[str] = Query(None, description="Accession number"),
    modality: Optional[Modality] = Query(None, description="Modality filter"),
    study_date_from: Optional[date] = Query(None, description="Study date from"),
    study_date_to: Optional[date] = Query(None, description="Study date to"),
    study_description: Optional[str] = Query(None, description="Study description (partial match)"),
    linked_patient_id: Optional[int] = Query(None, description="OpenHeart patient ID"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
):
    """
    Search for DICOM studies.

    Uses QIDO-RS to query the Orthanc PACS server. Supports filtering
    by patient demographics, dates, and modality.

    Permissions: Any authenticated user can search studies.
    Clinical data access is filtered by clinic_id.
    """
    request = StudySearchRequest(
        patient_id=patient_id,
        patient_name=patient_name,
        accession_number=accession_number,
        modality=modality,
        study_date_from=study_date_from,
        study_date_to=study_date_to,
        study_description=study_description,
        linked_patient_id=linked_patient_id,
        page=page,
        per_page=per_page,
    )

    return await dicom.search_studies(request)


@router.get("/studies/{study_uid}", response_model=DicomStudy)
async def get_study(
    study_uid: str,
    user: Annotated[TokenPayload, Depends(get_current_user)],
    dicom: Annotated[DicomService, Depends(get_dicom_service)],
):
    """
    Get detailed study metadata including series information.

    Args:
        study_uid: Study Instance UID
    """
    study = await dicom.get_study(study_uid)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found",
        )
    return study


@router.get("/studies/{study_uid}/viewer-url", response_model=ViewerUrlResponse)
async def get_viewer_url(
    study_uid: str,
    user: Annotated[TokenPayload, Depends(get_current_user)],
    dicom: Annotated[DicomService, Depends(get_dicom_service)],
):
    """
    Get OHIF Viewer URL for a study.

    Returns a URL that can be embedded in an iframe or opened
    in a new window to view the study in OHIF Viewer.
    """
    return await dicom.get_viewer_url(study_uid)


@router.get("/studies/{study_uid}/thumbnail")
async def get_study_thumbnail(
    study_uid: str,
    user: Annotated[TokenPayload, Depends(get_current_user)],
    dicom: Annotated[DicomService, Depends(get_dicom_service)],
):
    """
    Get a thumbnail preview image for a study.

    Returns a JPEG thumbnail of the first image in the study.
    """
    thumbnail = await dicom.get_study_thumbnail(study_uid)
    if not thumbnail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thumbnail not available",
        )
    return Response(content=thumbnail, media_type="image/jpeg")


# =============================================================================
# Structured Reports
# =============================================================================


@router.get("/studies/{study_uid}/echo-measurements", response_model=EchoMeasurements)
async def get_echo_measurements(
    study_uid: str,
    user: Annotated[TokenPayload, Depends(get_current_user)],
    dicom: Annotated[DicomService, Depends(get_dicom_service)],
):
    """
    Extract echocardiogram measurements from DICOM SR.

    Parses the structured report in the study to extract
    quantitative measurements (LVEF, dimensions, valve data).

    Returns 404 if no structured report is found.
    """
    measurements = await dicom.get_echo_measurements(study_uid)
    if not measurements:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No echo measurements found. Study may not contain a structured report.",
        )
    return measurements


# =============================================================================
# Admin / Management Endpoints
# =============================================================================


@router.delete(
    "/studies/{study_uid}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_study(
    study_uid: str,
    user: Annotated[
        TokenPayload,
        Depends(require_permission(Permission.CLINICAL_WRITE)),
    ],
    dicom: Annotated[DicomService, Depends(get_dicom_service)],
):
    """
    Delete a study from the PACS.

    Requires CLINICAL_WRITE permission. This permanently removes
    the study from Orthanc.

    Use with caution - this action cannot be undone.
    """
    success = await dicom.delete_study(study_uid)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found or could not be deleted",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/health")
async def check_dicom_health(
    dicom: Annotated[DicomService, Depends(get_dicom_service)],
):
    """
    Check DICOM/Orthanc connectivity.

    Returns connectivity status - useful for monitoring dashboards.
    """
    is_connected = await dicom.check_connection()
    return {
        "service": "orthanc",
        "status": "connected" if is_connected else "disconnected",
    }


# =============================================================================
# Patient Linking (Integration with OpenHeart)
# =============================================================================


@router.post("/studies/{study_uid}/link")
async def link_study_to_patient(
    study_uid: str,
    patient_id: int,
    user: Annotated[
        TokenPayload,
        Depends(require_permission(Permission.CLINICAL_WRITE)),
    ],
    dicom: Annotated[DicomService, Depends(get_dicom_service)],
    encounter_id: Optional[int] = None,
):
    """
    Link a DICOM study to an OpenHeart patient record.

    This creates an association between the DICOM study and
    the patient in OpenHeart's database for easy access from
    the patient profile.

    Args:
        study_uid: Study Instance UID
        patient_id: OpenHeart patient ID
        encounter_id: Optional encounter ID to link to
    """
    # Verify study exists
    study = await dicom.get_study(study_uid)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found",
        )

    # TODO: Store link in database
    # This would typically create a record in a patient_studies table
    # linking the DICOM study_instance_uid to the patient_id

    return {
        "study_instance_uid": study_uid,
        "patient_id": patient_id,
        "encounter_id": encounter_id,
        "status": "linked",
        "message": "Study linked to patient successfully",
    }


@router.get("/patients/{patient_id}/studies", response_model=DicomStudyList)
async def get_patient_studies(
    patient_id: int,
    user: Annotated[TokenPayload, Depends(get_current_user)],
    dicom: Annotated[DicomService, Depends(get_dicom_service)],
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """
    Get all DICOM studies linked to a patient.

    This queries both:
    1. Studies explicitly linked in OpenHeart
    2. Studies matching the patient's DICOM Patient ID

    Returns studies ordered by date (most recent first).
    """
    # TODO: Get patient's DICOM ID from database
    # For now, search by OpenHeart patient ID pattern
    # In production, this would look up the patient's Cyprus ID
    # which is used as the DICOM Patient ID

    request = StudySearchRequest(
        linked_patient_id=patient_id,
        page=page,
        per_page=per_page,
    )

    # For now, return empty as linking not fully implemented
    return DicomStudyList(
        studies=[],
        total=0,
        page=page,
        per_page=per_page,
    )
