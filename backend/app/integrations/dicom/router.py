"""
DICOM API Router for OpenHeart Cyprus.

Provides REST endpoints for DICOM imaging operations including
study search, retrieval, and OHIF viewer integration.
"""

from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.encryption import decrypt_pii
from app.core.permissions import Permission, require_permission
from app.core.security import TokenPayload, get_current_user
from app.db.session import get_db
from app.integrations.dicom.models import PatientStudyLink
from app.integrations.dicom.schemas import (
    DicomStudy,
    DicomStudyList,
    EchoMeasurements,
    Modality,
    StudySearchRequest,
    ViewerUrlResponse,
)
from app.integrations.dicom.service import DicomService
from app.modules.patient.models import Patient

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
        Depends(require_permission(Permission.DICOM_DELETE)),
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
        Depends(require_permission(Permission.PATIENT_WRITE)),
    ],
    dicom: Annotated[DicomService, Depends(get_dicom_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
    encounter_id: Optional[int] = None,
    link_reason: Optional[str] = None,
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
        link_reason: Optional reason for linking
    """
    # Verify study exists in Orthanc
    study = await dicom.get_study(study_uid)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found",
        )

    # Check for existing link (prevent duplicates)
    existing = await db.execute(
        select(PatientStudyLink).where(
            PatientStudyLink.study_instance_uid == study_uid,
            PatientStudyLink.patient_id == patient_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Study is already linked to this patient",
        )

    # Create link with cached study metadata
    link = PatientStudyLink(
        study_instance_uid=study_uid,
        patient_id=patient_id,
        encounter_id=encounter_id,
        clinic_id=user.clinic_id,
        linked_by_user_id=user.sub,
        link_reason=link_reason,
        study_date=study.study_date if study else None,
        study_description=study.study_description if study else None,
        modality=study.modalities[0].value if study and study.modalities else None,
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)

    return {
        "id": link.id,
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
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """
    Get all DICOM studies linked to a patient.

    This queries both:
    1. Studies matching the patient's DICOM Patient ID (Cyprus ID)
    2. Studies explicitly linked in OpenHeart's database

    Returns studies ordered by date (most recent first), deduplicated.
    """
    studies_by_uid: dict[str, DicomStudy] = {}

    # 1. Get patient's Cyprus ID from encrypted PII for Orthanc lookup
    result = await db.execute(
        select(Patient)
        .options(selectinload(Patient.pii))
        .where(Patient.patient_id == patient_id)
    )
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    # Query Orthanc using the patient's Cyprus ID as DICOM Patient ID
    if patient.pii and patient.pii.cyprus_id_encrypted:
        try:
            cyprus_id = decrypt_pii(patient.pii.cyprus_id_encrypted)
            if cyprus_id:
                search_request = StudySearchRequest(
                    patient_id=cyprus_id,
                    page=1,
                    per_page=100,  # Get all matching studies
                )
                orthanc_results = await dicom.search_studies(search_request)
                for study in orthanc_results.studies:
                    study.linked_patient_id = patient_id
                    studies_by_uid[study.study_instance_uid] = study
        except Exception:
            # Orthanc may be unavailable; continue with DB links only
            pass

    # 2. Query manually linked studies from database
    db_result = await db.execute(
        select(PatientStudyLink)
        .where(PatientStudyLink.patient_id == patient_id)
        .order_by(PatientStudyLink.study_date.desc().nulls_last())
    )
    db_links = db_result.scalars().all()

    # For DB-linked studies not already found via Orthanc, create entries
    for link in db_links:
        if link.study_instance_uid not in studies_by_uid:
            studies_by_uid[link.study_instance_uid] = DicomStudy(
                study_instance_uid=link.study_instance_uid,
                study_date=link.study_date,
                study_description=link.study_description,
                linked_patient_id=patient_id,
                linked_encounter_id=link.encounter_id,
            )
        else:
            # Update existing entry with link metadata
            studies_by_uid[link.study_instance_uid].linked_encounter_id = link.encounter_id

    # Sort by study date (most recent first), nulls last
    all_studies = sorted(
        studies_by_uid.values(),
        key=lambda s: s.study_date or date.min,
        reverse=True,
    )

    # Paginate
    total = len(all_studies)
    start = (page - 1) * per_page
    end = start + per_page
    paginated = all_studies[start:end]

    return DicomStudyList(
        studies=paginated,
        total=total,
        page=page,
        per_page=per_page,
    )
