"""
Doctor's Notes API Router.

Provides RESTful endpoints for clinical note management with:
- Full CRUD operations
- Version history and comparison
- Attachment upload/download
- Full-text search
- GDPR-compliant access logging
"""

import logging
import time
from typing import Annotated, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import Permission, require_permission
from app.core.security import TokenPayload
from app.db.session import get_db
from app.modules.notes.extraction import extraction_service
from app.modules.notes.models import NoteAccessAction
from app.modules.notes.schemas import (
    AttachmentDownloadResponse,
    AttachmentUploadResponse,
    NoteAccessLogResponse,
    NoteCreate,
    NoteDetailResponse,
    NoteListResponse,
    NoteResponse,
    NoteSearchQuery,
    NoteSearchResponse,
    NoteUpdate,
    NoteVersionResponse,
    VersionDiffResponse,
)
from app.modules.notes.service import NoteService

router = APIRouter(prefix="/notes", tags=["Clinical Notes"])
logger = logging.getLogger(__name__)


# ============================================================================
# Dependencies
# ============================================================================


async def get_note_service(db: AsyncSession = Depends(get_db)) -> NoteService:
    """Dependency for NoteService."""
    return NoteService(db)




# ============================================================================
# Note CRUD Endpoints
# ============================================================================


@router.post(
    "/",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_note(
    data: NoteCreate,
    request: Request,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.NOTE_WRITE))],
    service: NoteService = Depends(get_note_service),
) -> NoteResponse:
    """
    Create a new clinical note.

    Creates the note with an initial version. The note is associated with
    the patient and optionally an encounter.
    """
    start_time = time.time()

    note = await service.create_note(
        data=data,
        user_id=user.sub,
        clinic_id=user.clinic_id,
    )

    # Log access (non-fatal: note is already persisted)
    duration_ms = int((time.time() - start_time) * 1000)
    try:
        await service.log_access(
            note_id=note.note_id,
            action=NoteAccessAction.CREATE,
            user_id=user.sub,
            user_email=user.email,
            user_role=user.role,
            clinic_id=user.clinic_id,
            ip_address=request.client.host if request.client else "0.0.0.0",
            request_path=str(request.url.path),
            request_method=request.method,
            response_status=201,
            duration_ms=duration_ms,
        )
    except Exception:
        logger.warning("Failed to log note creation access", exc_info=True)

    # Get current version content
    versions = await service.get_all_versions(note.note_id, user.clinic_id)
    current_version = versions[0] if versions else None

    return NoteResponse(
        note_id=note.note_id,
        patient_id=note.patient_id,
        encounter_id=note.encounter_id,
        note_type=note.note_type,
        title=note.title,
        current_version=note.current_version,
        is_locked=note.is_locked,
        locked_at=note.locked_at,
        locked_reason=note.locked_reason,
        created_by=note.created_by,
        created_at=note.created_at,
        updated_at=note.updated_at,
        content_text=current_version.content_text if current_version else None,
        content_html=current_version.content_html if current_version else None,
        structured_data=current_version.structured_data if current_version else None,
        version_count=1,
        attachment_count=0,
    )


@router.get(
    "/patient/{patient_id}",
    response_model=NoteListResponse,
)
async def list_patient_notes(
    patient_id: int,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.NOTE_READ))],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    note_type: Optional[str] = Query(None),
    service: NoteService = Depends(get_note_service),
) -> NoteListResponse:
    """
    List clinical notes for a patient.

    Returns paginated notes with basic metadata. Use GET /notes/{id} for full details.
    """
    notes, total = await service.get_patient_notes(
        patient_id=patient_id,
        clinic_id=user.clinic_id,
        page=page,
        page_size=page_size,
        note_type=note_type,
    )

    total_pages = (total + page_size - 1) // page_size

    items = []
    for note in notes:
        current_version = note.versions[0] if note.versions else None
        items.append(
            NoteResponse(
                note_id=note.note_id,
                patient_id=note.patient_id,
                encounter_id=note.encounter_id,
                note_type=note.note_type,
                title=note.title,
                current_version=note.current_version,
                is_locked=note.is_locked,
                locked_at=note.locked_at,
                locked_reason=note.locked_reason,
                created_by=note.created_by,
                created_at=note.created_at,
                updated_at=note.updated_at,
                content_text=current_version.content_text if current_version else None,
                version_count=len(note.versions),
                attachment_count=len(note.attachments) if note.attachments else 0,
            )
        )

    return NoteListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{note_id}",
    response_model=NoteDetailResponse,
)
async def get_note(
    note_id: int,
    request: Request,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.NOTE_READ))],
    service: NoteService = Depends(get_note_service),
) -> NoteDetailResponse:
    """
    Get a clinical note with all versions and attachments.

    Returns complete note details including version history and attachments.
    Access is logged for GDPR compliance.
    """
    start_time = time.time()

    note = await service.get_note(
        note_id=note_id,
        clinic_id=user.clinic_id,
        include_versions=True,
        include_attachments=True,
    )

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )

    # Log access
    duration_ms = int((time.time() - start_time) * 1000)
    await service.log_access(
        note_id=note_id,
        action=NoteAccessAction.VIEW,
        user_id=user.sub,
        user_email=user.email,
        user_role=user.role,
        clinic_id=user.clinic_id,
        ip_address=request.client.host if request.client else "0.0.0.0",
        request_path=str(request.url.path),
        request_method=request.method,
        response_status=200,
        duration_ms=duration_ms,
        version_accessed=note.current_version,
    )

    current_version = note.versions[0] if note.versions else None
    active_attachments = [a for a in note.attachments if not a.is_deleted]

    return NoteDetailResponse(
        note_id=note.note_id,
        patient_id=note.patient_id,
        encounter_id=note.encounter_id,
        note_type=note.note_type,
        title=note.title,
        current_version=note.current_version,
        is_locked=note.is_locked,
        locked_at=note.locked_at,
        locked_reason=note.locked_reason,
        created_by=note.created_by,
        created_at=note.created_at,
        updated_at=note.updated_at,
        content_text=current_version.content_text if current_version else None,
        content_html=current_version.content_html if current_version else None,
        structured_data=current_version.structured_data if current_version else None,
        version_count=len(note.versions),
        attachment_count=len(active_attachments),
        versions=[
            NoteVersionResponse(
                version_id=v.version_id,
                version_number=v.version_number,
                content_text=v.content_text,
                content_html=v.content_html,
                structured_data=v.structured_data,
                diff_from_previous=v.diff_from_previous,
                edited_by=v.edited_by,
                edit_reason=v.edit_reason,
                word_count=v.word_count,
                char_count=v.char_count,
                created_at=v.created_at,
            )
            for v in note.versions
        ],
        attachments=[
            {
                "attachment_id": a.attachment_id,
                "file_name": a.file_name,
                "original_file_name": a.original_file_name,
                "file_type": a.file_type,
                "mime_type": a.mime_type,
                "file_size_bytes": a.file_size_bytes,
                "extraction_status": a.extraction_status,
                "page_count": a.page_count,
                "image_width": a.image_width,
                "image_height": a.image_height,
                "uploaded_by": a.uploaded_by,
                "uploaded_at": a.uploaded_at,
            }
            for a in active_attachments
        ],
    )


@router.put(
    "/{note_id}",
    response_model=NoteResponse,
)
async def update_note(
    note_id: int,
    data: NoteUpdate,
    request: Request,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.NOTE_WRITE))],
    service: NoteService = Depends(get_note_service),
) -> NoteResponse:
    """
    Update a clinical note by creating a new version.

    Requires an edit_reason explaining the change. The previous version
    is preserved for audit purposes.
    """
    start_time = time.time()

    try:
        note = await service.update_note(
            note_id=note_id,
            data=data,
            user_id=user.sub,
            clinic_id=user.clinic_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )

    # Log access
    duration_ms = int((time.time() - start_time) * 1000)
    await service.log_access(
        note_id=note_id,
        action=NoteAccessAction.EDIT,
        user_id=user.sub,
        user_email=user.email,
        user_role=user.role,
        clinic_id=user.clinic_id,
        ip_address=request.client.host if request.client else "0.0.0.0",
        request_path=str(request.url.path),
        request_method=request.method,
        response_status=200,
        duration_ms=duration_ms,
        version_accessed=note.current_version,
    )

    return NoteResponse(
        note_id=note.note_id,
        patient_id=note.patient_id,
        encounter_id=note.encounter_id,
        note_type=note.note_type,
        title=note.title,
        current_version=note.current_version,
        is_locked=note.is_locked,
        created_by=note.created_by,
        created_at=note.created_at,
        updated_at=note.updated_at,
        content_text=data.content_text,
        content_html=data.content_html,
    )


@router.post(
    "/{note_id}/lock",
    response_model=NoteResponse,
)
async def lock_note(
    note_id: int,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.NOTE_WRITE))],
    reason: str = Query(..., min_length=3, max_length=255),
    service: NoteService = Depends(get_note_service),
) -> NoteResponse:
    """Lock a note to prevent further edits."""
    note = await service.lock_note(
        note_id=note_id,
        user_id=user.sub,
        clinic_id=user.clinic_id,
        reason=reason,
    )

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )

    return NoteResponse(
        note_id=note.note_id,
        patient_id=note.patient_id,
        encounter_id=note.encounter_id,
        note_type=note.note_type,
        title=note.title,
        current_version=note.current_version,
        is_locked=note.is_locked,
        locked_at=note.locked_at,
        locked_reason=note.locked_reason,
        created_by=note.created_by,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


# ============================================================================
# Version Endpoints
# ============================================================================


@router.get(
    "/{note_id}/versions",
    response_model=list[NoteVersionResponse],
)
async def list_versions(
    note_id: int,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.NOTE_READ))],
    service: NoteService = Depends(get_note_service),
) -> list[NoteVersionResponse]:
    """Get all versions of a note."""
    versions = await service.get_all_versions(note_id, user.clinic_id)

    if not versions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found or no versions",
        )

    return [
        NoteVersionResponse(
            version_id=v.version_id,
            version_number=v.version_number,
            content_text=v.content_text,
            content_html=v.content_html,
            structured_data=v.structured_data,
            diff_from_previous=v.diff_from_previous,
            edited_by=v.edited_by,
            edit_reason=v.edit_reason,
            word_count=v.word_count,
            char_count=v.char_count,
            created_at=v.created_at,
        )
        for v in versions
    ]


@router.get(
    "/{note_id}/versions/{version_number}",
    response_model=NoteVersionResponse,
)
async def get_version(
    note_id: int,
    version_number: int,
    request: Request,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.NOTE_READ))],
    service: NoteService = Depends(get_note_service),
) -> NoteVersionResponse:
    """Get a specific version of a note."""
    start_time = time.time()

    version = await service.get_version(note_id, version_number, user.clinic_id)

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found",
        )

    # Log access
    duration_ms = int((time.time() - start_time) * 1000)
    await service.log_access(
        note_id=note_id,
        action=NoteAccessAction.VIEW,
        user_id=user.sub,
        user_email=user.email,
        user_role=user.role,
        clinic_id=user.clinic_id,
        ip_address=request.client.host if request.client else "0.0.0.0",
        request_path=str(request.url.path),
        request_method=request.method,
        response_status=200,
        duration_ms=duration_ms,
        version_accessed=version_number,
    )

    return NoteVersionResponse(
        version_id=version.version_id,
        version_number=version.version_number,
        content_text=version.content_text,
        content_html=version.content_html,
        structured_data=version.structured_data,
        diff_from_previous=version.diff_from_previous,
        edited_by=version.edited_by,
        edit_reason=version.edit_reason,
        word_count=version.word_count,
        char_count=version.char_count,
        created_at=version.created_at,
    )


@router.get(
    "/{note_id}/diff/{version_from}/{version_to}",
    response_model=VersionDiffResponse,
)
async def compare_versions(
    note_id: int,
    version_from: int,
    version_to: int,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.NOTE_READ))],
    service: NoteService = Depends(get_note_service),
) -> VersionDiffResponse:
    """Compare two versions of a note."""
    diff = await service.compare_versions(
        note_id=note_id,
        version_from=version_from,
        version_to=version_to,
        clinic_id=user.clinic_id,
    )

    if not diff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both versions not found",
        )

    return diff


# ============================================================================
# Attachment Endpoints
# ============================================================================


@router.post(
    "/{note_id}/attachments",
    response_model=AttachmentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_attachment(
    note_id: int,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.NOTE_WRITE))],
    file: UploadFile = File(...),
    service: NoteService = Depends(get_note_service),
) -> AttachmentUploadResponse:
    """
    Upload an attachment to a note.

    Supports PDF, DOCX, images (JPG, PNG), and text files.
    Text is automatically extracted for search indexing.
    """

    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename required",
        )

    content = await file.read()

    # Detect MIME type
    mime_type = file.content_type or extraction_service.detect_mime_type(
        content, file.filename
    )

    if not mime_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to determine file type",
        )

    if not extraction_service.is_supported(mime_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {mime_type}. Supported: PDF, DOCX, JPG, PNG, TXT",
        )

    try:
        attachment = await service.add_attachment(
            note_id=note_id,
            file_content=content,
            original_filename=file.filename,
            mime_type=mime_type,
            user_id=user.sub,
            clinic_id=user.clinic_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )

    return AttachmentUploadResponse(
        attachment_id=attachment.attachment_id,
        file_name=attachment.original_file_name,
        file_type=attachment.file_type,
        file_size_bytes=attachment.file_size_bytes,
        extraction_status=attachment.extraction_status,
    )


@router.get(
    "/{note_id}/attachments/{attachment_id}/download",
    response_model=AttachmentDownloadResponse,
)
async def download_attachment(
    note_id: int,
    attachment_id: int,
    request: Request,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.NOTE_READ))],
    service: NoteService = Depends(get_note_service),
) -> AttachmentDownloadResponse:
    """
    Get a presigned download URL for an attachment.

    Downloads are logged for GDPR compliance.
    """
    start_time = time.time()

    attachment = await service.get_attachment(attachment_id, user.clinic_id)

    if not attachment or attachment.note_id != note_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found",
        )

    # Log download access
    duration_ms = int((time.time() - start_time) * 1000)
    await service.log_access(
        note_id=note_id,
        action=NoteAccessAction.DOWNLOAD_ATTACHMENT,
        user_id=user.sub,
        user_email=user.email,
        user_role=user.role,
        clinic_id=user.clinic_id,
        ip_address=request.client.host if request.client else "0.0.0.0",
        request_path=str(request.url.path),
        request_method=request.method,
        response_status=200,
        duration_ms=duration_ms,
        attachment_id=attachment_id,
    )

    # Generate presigned S3/MinIO download URL
    from app.integrations.storage import get_storage_client

    expires_in = 3600
    storage = get_storage_client()
    download_url = storage.generate_presigned_url(
        bucket=attachment.storage_bucket,
        key=attachment.storage_path,
        expires_in=expires_in,
        filename=attachment.original_file_name,
    )

    return AttachmentDownloadResponse(
        attachment_id=attachment.attachment_id,
        file_name=attachment.original_file_name,
        download_url=download_url,
        expires_in_seconds=expires_in,
    )


@router.delete(
    "/{note_id}/attachments/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_attachment(
    note_id: int,
    attachment_id: int,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.NOTE_WRITE))],
    service: NoteService = Depends(get_note_service),
) -> None:
    """
    Soft-delete an attachment.

    The attachment is marked as deleted but retained for compliance.
    """
    success = await service.delete_attachment(
        attachment_id=attachment_id,
        user_id=user.sub,
        clinic_id=user.clinic_id,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found",
        )


# ============================================================================
# Search Endpoint
# ============================================================================


@router.get(
    "/search",
    response_model=NoteSearchResponse,
)
async def search_notes(
    request: Request,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.NOTE_READ))],
    q: str = Query(..., min_length=2, max_length=500),
    patient_id: Optional[int] = Query(None),
    note_type: Optional[str] = Query(None),
    author_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: NoteService = Depends(get_note_service),
) -> NoteSearchResponse:
    """
    Full-text search across clinical notes.

    Searches note content and extracted attachment text.
    Results are ranked by relevance.
    """
    start_time = time.time()

    query = NoteSearchQuery(
        q=q,
        patient_id=patient_id,
        note_type=note_type,
        author_id=author_id,
    )

    results, total, search_time_ms = await service.search_notes(
        query=query,
        clinic_id=user.clinic_id,
        page=page,
        page_size=page_size,
    )

    # Log search action (no specific note, just the search)
    await service.log_access(
        note_id=0,  # No specific note for search
        action=NoteAccessAction.SEARCH,
        user_id=user.sub,
        user_email=user.email,
        user_role=user.role,
        clinic_id=user.clinic_id,
        ip_address=request.client.host if request.client else "0.0.0.0",
        request_path=str(request.url.path),
        request_method=request.method,
        response_status=200,
        duration_ms=int((time.time() - start_time) * 1000),
        search_query=q,
    )

    return NoteSearchResponse(
        query=q,
        results=results,
        total=total,
        page=page,
        page_size=page_size,
        search_time_ms=search_time_ms,
    )


# ============================================================================
# Audit Log Endpoint
# ============================================================================


@router.get(
    "/{note_id}/access-log",
    response_model=NoteAccessLogResponse,
)
async def get_access_log(
    note_id: int,
    user: Annotated[TokenPayload, Depends(require_permission(Permission.AUDIT_READ))],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: NoteService = Depends(get_note_service),
) -> NoteAccessLogResponse:
    """
    Get access log for a note.

    Requires AUDIT_READ permission. Returns all access events
    for GDPR compliance auditing.
    """
    entries, total = await service.get_access_log(
        note_id=note_id,
        clinic_id=user.clinic_id,
        page=page,
        page_size=page_size,
    )

    return NoteAccessLogResponse(
        note_id=note_id,
        entries=[
            {
                "log_id": e.log_id,
                "note_id": e.note_id,
                "action": e.action,
                "version_accessed": e.version_accessed,
                "user_id": e.user_id,
                "user_email": e.user_email,
                "user_role": e.user_role,
                "ip_address": str(e.ip_address),
                "timestamp": e.timestamp,
            }
            for e in entries
        ],
        total=total,
        page=page,
        page_size=page_size,
    )
