"""
Doctor's Notes Service Layer.

Handles business logic for clinical note management including:
- CRUD operations with version control
- Attachment management with text extraction
- Full-text search across notes and attachments
- Version diffing and comparison
- GDPR-compliant access logging
"""

import difflib
import logging
import re
import uuid
from datetime import datetime
from typing import Any, Optional, Sequence

from sqlalchemy import and_, desc, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.notes.extraction import ExtractionResult, extraction_service
from app.modules.notes.models import (
    ClinicalNote,
    NoteAccessAction,
    NoteAccessLog,
    NoteAttachment,
    NoteVersion,
)
from app.modules.notes.schemas import (
    DiffHunk,
    NoteCreate,
    NoteSearchQuery,
    NoteSearchResult,
    NoteUpdate,
    SearchHighlight,
    VersionDiffResponse,
)

logger = logging.getLogger(__name__)


class NoteService:
    """Service for managing clinical notes."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ========================================================================
    # Note CRUD Operations
    # ========================================================================

    async def create_note(
        self,
        data: NoteCreate,
        user_id: int,
        clinic_id: int,
    ) -> ClinicalNote:
        """
        Create a new clinical note with initial version.

        Args:
            data: Note creation data
            user_id: Creating user's ID
            clinic_id: Clinic ID for RLS

        Returns:
            Created ClinicalNote with first version
        """
        # Create the note
        note = ClinicalNote(
            patient_id=data.patient_id,
            encounter_id=data.encounter_id,
            clinic_id=clinic_id,
            note_type=data.note_type.value,
            title=data.title,
            current_version=1,
            created_by=user_id,
        )
        self.db.add(note)
        await self.db.flush()  # Get note_id

        # Create initial version
        word_count = len(data.content_text.split())
        version = NoteVersion(
            note_id=note.note_id,
            version_number=1,
            content_text=data.content_text,
            content_html=data.content_html,
            structured_data=data.structured_data.model_dump() if data.structured_data else None,
            edited_by=user_id,
            word_count=word_count,
            char_count=len(data.content_text),
        )
        self.db.add(version)
        await self.db.commit()
        await self.db.refresh(note)

        return note

    async def get_note(
        self,
        note_id: int,
        clinic_id: int,
        include_versions: bool = False,
        include_attachments: bool = False,
    ) -> Optional[ClinicalNote]:
        """
        Get a clinical note by ID.

        Args:
            note_id: Note ID
            clinic_id: Clinic ID for RLS verification
            include_versions: Load all versions
            include_attachments: Load attachments

        Returns:
            ClinicalNote or None if not found/not authorized
        """
        query = select(ClinicalNote).where(
            and_(
                ClinicalNote.note_id == note_id,
                ClinicalNote.clinic_id == clinic_id,
            )
        )

        if include_versions:
            query = query.options(selectinload(ClinicalNote.versions))
        if include_attachments:
            query = query.options(selectinload(ClinicalNote.attachments))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_patient_notes(
        self,
        patient_id: int,
        clinic_id: int,
        page: int = 1,
        page_size: int = 20,
        note_type: Optional[str] = None,
    ) -> tuple[Sequence[ClinicalNote], int]:
        """
        Get paginated notes for a patient.

        Args:
            patient_id: Patient ID
            clinic_id: Clinic ID for RLS
            page: Page number (1-indexed)
            page_size: Items per page
            note_type: Optional filter by note type

        Returns:
            Tuple of (notes list, total count)
        """
        # Base query
        base_query = select(ClinicalNote).where(
            and_(
                ClinicalNote.patient_id == patient_id,
                ClinicalNote.clinic_id == clinic_id,
            )
        )

        if note_type:
            base_query = base_query.where(ClinicalNote.note_type == note_type)

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Fetch page
        offset = (page - 1) * page_size
        query = (
            base_query.options(
                selectinload(ClinicalNote.versions),
                selectinload(ClinicalNote.attachments),
            )
            .order_by(desc(ClinicalNote.updated_at))
            .offset(offset)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        notes = result.scalars().all()

        return notes, total

    async def update_note(
        self,
        note_id: int,
        data: NoteUpdate,
        user_id: int,
        clinic_id: int,
    ) -> Optional[ClinicalNote]:
        """
        Update a note by creating a new version.

        Args:
            note_id: Note ID
            data: Update data with edit_reason
            user_id: Editing user's ID
            clinic_id: Clinic ID for RLS

        Returns:
            Updated note or None if not found/locked
        """
        note = await self.get_note(note_id, clinic_id, include_versions=True)
        if not note:
            return None

        if note.is_locked:
            raise ValueError(f"Note is locked: {note.locked_reason}")

        # Get previous version for diff
        prev_version = note.versions[0] if note.versions else None
        prev_text = prev_version.content_text if prev_version else ""

        # Compute diff
        diff_data = self._compute_diff(prev_text, data.content_text)

        # Create new version
        new_version_num = note.current_version + 1
        word_count = len(data.content_text.split())

        version = NoteVersion(
            note_id=note_id,
            version_number=new_version_num,
            content_text=data.content_text,
            content_html=data.content_html,
            structured_data=data.structured_data.model_dump() if data.structured_data else None,
            diff_from_previous=diff_data,
            edited_by=user_id,
            edit_reason=data.edit_reason,
            word_count=word_count,
            char_count=len(data.content_text),
        )
        self.db.add(version)

        # Update note
        note.current_version = new_version_num
        note.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(note)

        return note

    async def lock_note(
        self,
        note_id: int,
        user_id: int,
        clinic_id: int,
        reason: str,
    ) -> Optional[ClinicalNote]:
        """Lock a note to prevent further edits."""
        note = await self.get_note(note_id, clinic_id)
        if not note:
            return None

        note.is_locked = True
        note.locked_at = datetime.utcnow()
        note.locked_by = user_id
        note.locked_reason = reason

        await self.db.commit()
        await self.db.refresh(note)
        return note

    # ========================================================================
    # Version Management
    # ========================================================================

    async def get_version(
        self,
        note_id: int,
        version_number: int,
        clinic_id: int,
    ) -> Optional[NoteVersion]:
        """Get a specific version of a note."""
        # Verify note access
        note = await self.get_note(note_id, clinic_id)
        if not note:
            return None

        query = select(NoteVersion).where(
            and_(
                NoteVersion.note_id == note_id,
                NoteVersion.version_number == version_number,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_versions(
        self,
        note_id: int,
        clinic_id: int,
    ) -> Sequence[NoteVersion]:
        """Get all versions of a note, newest first."""
        note = await self.get_note(note_id, clinic_id)
        if not note:
            return []

        query = (
            select(NoteVersion)
            .where(NoteVersion.note_id == note_id)
            .order_by(desc(NoteVersion.version_number))
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def compare_versions(
        self,
        note_id: int,
        version_from: int,
        version_to: int,
        clinic_id: int,
    ) -> Optional[VersionDiffResponse]:
        """
        Compare two versions of a note.

        Args:
            note_id: Note ID
            version_from: Earlier version number
            version_to: Later version number
            clinic_id: Clinic ID for RLS

        Returns:
            VersionDiffResponse with diff hunks
        """
        v1 = await self.get_version(note_id, version_from, clinic_id)
        v2 = await self.get_version(note_id, version_to, clinic_id)

        if not v1 or not v2:
            return None

        hunks, additions, deletions = self._compute_diff_hunks(
            v1.content_text, v2.content_text
        )

        return VersionDiffResponse(
            note_id=note_id,
            version_from=version_from,
            version_to=version_to,
            hunks=hunks,
            summary=f"{additions} additions, {deletions} deletions",
            additions=additions,
            deletions=deletions,
        )

    def _compute_diff(self, old_text: str, new_text: str) -> dict[str, Any]:
        """Compute a JSON-serializable diff between two texts."""
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)

        differ = difflib.unified_diff(old_lines, new_lines, lineterm="")
        diff_lines = list(differ)

        return {
            "unified_diff": "".join(diff_lines),
            "old_word_count": len(old_text.split()),
            "new_word_count": len(new_text.split()),
        }

    def _compute_diff_hunks(
        self, old_text: str, new_text: str
    ) -> tuple[list[DiffHunk], int, int]:
        """Compute detailed diff hunks for UI display."""
        old_lines = old_text.splitlines()
        new_lines = new_text.splitlines()

        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        hunks = []
        additions = 0
        deletions = 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue

            old_content = "\n".join(old_lines[i1:i2])
            new_content = "\n".join(new_lines[j1:j2])

            if tag == "delete":
                deletions += i2 - i1
                change_type = "delete"
            elif tag == "insert":
                additions += j2 - j1
                change_type = "add"
            else:  # replace
                deletions += i2 - i1
                additions += j2 - j1
                change_type = "modify"

            hunks.append(
                DiffHunk(
                    line_start=i1 + 1,
                    line_end=i2,
                    old_content=old_content,
                    new_content=new_content,
                    change_type=change_type,
                )
            )

        return hunks, additions, deletions

    # ========================================================================
    # Attachment Management
    # ========================================================================

    async def add_attachment(
        self,
        note_id: int,
        file_content: bytes,
        original_filename: str,
        mime_type: str,
        user_id: int,
        clinic_id: int,
        storage_bucket: str = "note-attachments",
    ) -> Optional[NoteAttachment]:
        """
        Add an attachment to a note with text extraction.

        Args:
            note_id: Note ID
            file_content: Raw file bytes
            original_filename: Original upload filename
            mime_type: MIME type
            user_id: Uploading user ID
            clinic_id: Clinic ID for RLS
            storage_bucket: S3/MinIO bucket name

        Returns:
            Created NoteAttachment or None if note not found
        """
        note = await self.get_note(note_id, clinic_id)
        if not note:
            return None

        # Validate file
        if not extraction_service.is_supported(mime_type):
            raise ValueError(f"Unsupported file type: {mime_type}")

        size_error = extraction_service.validate_size(file_content, mime_type)
        if size_error:
            raise ValueError(size_error)

        # Generate storage path
        file_type = extraction_service.get_file_type(mime_type)
        checksum = extraction_service.compute_checksum(file_content)
        ext = original_filename.rsplit(".", 1)[-1] if "." in original_filename else ""
        storage_filename = f"{uuid.uuid4()}.{ext}" if ext else str(uuid.uuid4())
        storage_path = f"clinic_{clinic_id}/notes/{note_id}/{storage_filename}"

        # Create attachment record
        attachment = NoteAttachment(
            note_id=note_id,
            file_name=storage_filename,
            original_file_name=original_filename,
            file_type=file_type or "unknown",
            mime_type=mime_type,
            file_size_bytes=len(file_content),
            storage_path=storage_path,
            storage_bucket=storage_bucket,
            checksum_sha256=checksum,
            extraction_status="pending",
            uploaded_by=user_id,
        )
        self.db.add(attachment)
        await self.db.flush()

        # Perform text extraction
        try:
            attachment.extraction_status = "processing"
            await self.db.flush()

            result = await extraction_service.extract(
                file_content, original_filename, mime_type
            )

            if result.success:
                attachment.extracted_text = result.text
                attachment.extraction_status = "completed"
                attachment.page_count = result.page_count
                attachment.image_width = result.image_width
                attachment.image_height = result.image_height
            else:
                attachment.extraction_status = "failed"
                attachment.extraction_error = result.error

        except Exception as e:
            logger.exception(f"Text extraction failed for attachment {attachment.attachment_id}")
            attachment.extraction_status = "failed"
            attachment.extraction_error = str(e)

        await self.db.commit()
        await self.db.refresh(attachment)

        return attachment

    async def get_attachment(
        self,
        attachment_id: int,
        clinic_id: int,
    ) -> Optional[NoteAttachment]:
        """Get an attachment by ID with clinic verification."""
        query = (
            select(NoteAttachment)
            .join(ClinicalNote)
            .where(
                and_(
                    NoteAttachment.attachment_id == attachment_id,
                    ClinicalNote.clinic_id == clinic_id,
                    NoteAttachment.is_deleted == False,  # noqa: E712
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def delete_attachment(
        self,
        attachment_id: int,
        user_id: int,
        clinic_id: int,
    ) -> bool:
        """Soft-delete an attachment."""
        attachment = await self.get_attachment(attachment_id, clinic_id)
        if not attachment:
            return False

        attachment.is_deleted = True
        attachment.deleted_at = datetime.utcnow()
        attachment.deleted_by = user_id

        await self.db.commit()
        return True

    # ========================================================================
    # Search
    # ========================================================================

    async def search_notes(
        self,
        query: NoteSearchQuery,
        clinic_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[NoteSearchResult], int, int]:
        """
        Full-text search across notes and attachments.

        Args:
            query: Search parameters
            clinic_id: Clinic ID for RLS
            page: Page number
            page_size: Items per page

        Returns:
            Tuple of (results, total count, search time ms)
        """
        import time

        start_time = time.time()

        # Build search query
        search_term = query.q.replace("'", "''")  # Escape single quotes

        # Search in note versions
        version_subquery = (
            select(
                NoteVersion.note_id,
                func.ts_rank(
                    func.to_tsvector("english", NoteVersion.content_text),
                    func.plainto_tsquery("english", search_term),
                ).label("rank"),
                func.ts_headline(
                    "english",
                    NoteVersion.content_text,
                    func.plainto_tsquery("english", search_term),
                    "MaxWords=50, MinWords=20, StartSel=<mark>, StopSel=</mark>",
                ).label("headline"),
            )
            .where(
                func.to_tsvector("english", NoteVersion.content_text).match(search_term)
            )
            .subquery()
        )

        # Main query joining with notes
        main_query = (
            select(
                ClinicalNote.note_id,
                ClinicalNote.patient_id,
                ClinicalNote.title,
                ClinicalNote.note_type,
                ClinicalNote.created_at,
                ClinicalNote.created_by,
                version_subquery.c.rank,
                version_subquery.c.headline,
            )
            .join(version_subquery, ClinicalNote.note_id == version_subquery.c.note_id)
            .where(ClinicalNote.clinic_id == clinic_id)
        )

        # Apply filters
        if query.patient_id:
            main_query = main_query.where(ClinicalNote.patient_id == query.patient_id)
        if query.note_type:
            main_query = main_query.where(ClinicalNote.note_type == query.note_type.value)
        if query.author_id:
            main_query = main_query.where(ClinicalNote.created_by == query.author_id)
        if query.date_from:
            main_query = main_query.where(ClinicalNote.created_at >= query.date_from)
        if query.date_to:
            main_query = main_query.where(ClinicalNote.created_at <= query.date_to)

        # Count total
        count_query = select(func.count()).select_from(main_query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Fetch page with ordering
        offset = (page - 1) * page_size
        main_query = (
            main_query.order_by(desc(version_subquery.c.rank))
            .offset(offset)
            .limit(page_size)
        )

        result = await self.db.execute(main_query)
        rows = result.all()

        # Build results
        results = []
        for row in rows:
            results.append(
                NoteSearchResult(
                    note_id=row.note_id,
                    patient_id=row.patient_id,
                    title=row.title,
                    note_type=row.note_type,
                    created_at=row.created_at,
                    author_name=str(row.created_by),  # Would join with users table
                    highlights=[
                        SearchHighlight(
                            field="content",
                            text=row.headline or "",
                            score=float(row.rank or 0),
                        )
                    ],
                    relevance_score=float(row.rank or 0),
                )
            )

        search_time_ms = int((time.time() - start_time) * 1000)
        return results, total, search_time_ms

    # ========================================================================
    # Access Logging
    # ========================================================================

    async def log_access(
        self,
        note_id: int,
        action: NoteAccessAction,
        user_id: int,
        user_email: str,
        user_role: str,
        clinic_id: int,
        ip_address: str,
        request_path: str,
        request_method: str,
        response_status: int,
        duration_ms: int,
        version_accessed: Optional[int] = None,
        attachment_id: Optional[int] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        search_query: Optional[str] = None,
        export_format: Optional[str] = None,
    ) -> None:
        """Log access to a clinical note for GDPR compliance."""
        log_entry = NoteAccessLog(
            note_id=note_id,
            attachment_id=attachment_id,
            action=action.value,
            version_accessed=version_accessed,
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            clinic_id=clinic_id,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            request_path=request_path,
            request_method=request_method,
            response_status=response_status,
            duration_ms=duration_ms,
            search_query=search_query,
            export_format=export_format,
        )
        self.db.add(log_entry)
        await self.db.commit()

    async def get_access_log(
        self,
        note_id: int,
        clinic_id: int,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[Sequence[NoteAccessLog], int]:
        """Get access log for a note (for auditors)."""
        # Verify note exists in clinic
        note = await self.get_note(note_id, clinic_id)
        if not note:
            return [], 0

        base_query = select(NoteAccessLog).where(NoteAccessLog.note_id == note_id)

        # Count
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Fetch page
        offset = (page - 1) * page_size
        query = (
            base_query.order_by(desc(NoteAccessLog.timestamp))
            .offset(offset)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        entries = result.scalars().all()

        return entries, total
