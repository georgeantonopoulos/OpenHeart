"""
Pydantic schemas for Doctor's Notes API.

Provides request/response validation with strict typing.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NoteType(str, Enum):
    """Types of clinical notes."""

    FREE_TEXT = "free_text"
    SOAP = "soap"
    PROCEDURE = "procedure"
    CONSULTATION = "consultation"
    DISCHARGE = "discharge"
    PROGRESS = "progress"


class ExtractionStatus(str, Enum):
    """Status of text extraction from attachments."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# Note Schemas
# ============================================================================


class SOAPContent(BaseModel):
    """Structured SOAP note content."""

    subjective: str = Field(default="", description="Patient's chief complaint and history")
    objective: str = Field(default="", description="Physical exam, vitals, test results")
    assessment: str = Field(default="", description="Diagnosis and clinical impression")
    plan: str = Field(default="", description="Treatment plan and follow-up")


class NoteCreate(BaseModel):
    """Schema for creating a new clinical note."""

    patient_id: int = Field(..., gt=0, description="Patient ID")
    encounter_id: Optional[int] = Field(None, gt=0, description="Optional encounter ID")
    note_type: NoteType = Field(default=NoteType.FREE_TEXT)
    title: str = Field(..., min_length=1, max_length=255)
    content_text: str = Field(..., min_length=1, description="Note content (markdown/plain text)")
    content_html: Optional[str] = Field(None, description="Rendered HTML content")
    structured_data: Optional[SOAPContent] = Field(
        None, description="Structured SOAP content if note_type is SOAP"
    )

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        return v.strip()


class NoteUpdate(BaseModel):
    """Schema for editing a clinical note (creates new version)."""

    content_text: str = Field(..., min_length=1)
    content_html: Optional[str] = None
    structured_data: Optional[SOAPContent] = None
    edit_reason: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Required explanation for the edit",
    )

    @field_validator("edit_reason")
    @classmethod
    def validate_reason(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Edit reason must be at least 3 characters")
        return v


class NoteVersionResponse(BaseModel):
    """Response schema for a note version."""

    model_config = ConfigDict(from_attributes=True)

    version_id: int
    version_number: int
    content_text: str
    content_html: Optional[str] = None
    structured_data: Optional[dict[str, Any]] = None
    diff_from_previous: Optional[dict[str, Any]] = None
    edited_by: int
    edit_reason: Optional[str] = None
    word_count: int
    char_count: int
    created_at: datetime


class NoteAttachmentResponse(BaseModel):
    """Response schema for a note attachment."""

    model_config = ConfigDict(from_attributes=True)

    attachment_id: int
    file_name: str
    original_file_name: str
    file_type: str
    mime_type: str
    file_size_bytes: int
    extraction_status: str
    page_count: Optional[int] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    uploaded_by: int
    uploaded_at: datetime


class NoteResponse(BaseModel):
    """Response schema for a clinical note."""

    model_config = ConfigDict(from_attributes=True)

    note_id: int
    patient_id: int
    encounter_id: Optional[int] = None
    note_type: str
    title: str
    current_version: int
    is_locked: bool
    locked_at: Optional[datetime] = None
    locked_reason: Optional[str] = None
    created_by: int
    created_at: datetime
    updated_at: datetime

    # Current version content (latest)
    content_text: Optional[str] = None
    content_html: Optional[str] = None
    structured_data: Optional[dict[str, Any]] = None

    # Related data
    attachment_count: int = 0
    version_count: int = 0


class NoteListResponse(BaseModel):
    """Paginated list of notes."""

    items: list[NoteResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class NoteDetailResponse(NoteResponse):
    """Detailed note response with versions and attachments."""

    versions: list[NoteVersionResponse] = []
    attachments: list[NoteAttachmentResponse] = []


# ============================================================================
# Diff Schemas
# ============================================================================


class DiffHunk(BaseModel):
    """A single diff hunk showing changes."""

    line_start: int
    line_end: int
    old_content: str
    new_content: str
    change_type: str = Field(description="add, delete, or modify")


class VersionDiffResponse(BaseModel):
    """Response for comparing two versions."""

    note_id: int
    version_from: int
    version_to: int
    hunks: list[DiffHunk]
    summary: str = Field(description="Brief summary of changes")
    additions: int = Field(description="Number of lines added")
    deletions: int = Field(description="Number of lines deleted")


# ============================================================================
# Search Schemas
# ============================================================================


class NoteSearchQuery(BaseModel):
    """Query parameters for searching notes."""

    q: str = Field(..., min_length=2, max_length=500, description="Search query")
    patient_id: Optional[int] = Field(None, gt=0)
    note_type: Optional[NoteType] = None
    author_id: Optional[int] = Field(None, gt=0)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    include_attachments: bool = Field(
        default=True, description="Search within attachment text"
    )


class SearchHighlight(BaseModel):
    """Search result highlight."""

    field: str = Field(description="Field where match was found")
    text: str = Field(description="Highlighted text with <mark> tags")
    score: float = Field(description="Relevance score")


class NoteSearchResult(BaseModel):
    """A single search result."""

    note_id: int
    patient_id: int
    title: str
    note_type: str
    created_at: datetime
    author_name: str
    highlights: list[SearchHighlight]
    relevance_score: float


class NoteSearchResponse(BaseModel):
    """Search results response."""

    query: str
    results: list[NoteSearchResult]
    total: int
    page: int
    page_size: int
    search_time_ms: int


# ============================================================================
# Attachment Upload Schemas
# ============================================================================


class AttachmentUploadResponse(BaseModel):
    """Response after uploading an attachment."""

    attachment_id: int
    file_name: str
    file_type: str
    file_size_bytes: int
    extraction_status: str
    message: str = "Attachment uploaded successfully"


class AttachmentDownloadResponse(BaseModel):
    """Response for attachment download (presigned URL)."""

    attachment_id: int
    file_name: str
    download_url: str
    expires_in_seconds: int = 3600


# ============================================================================
# Access Log Schemas
# ============================================================================


class NoteAccessLogEntry(BaseModel):
    """A single access log entry."""

    model_config = ConfigDict(from_attributes=True)

    log_id: int
    note_id: int
    action: str
    version_accessed: Optional[int] = None
    user_id: int
    user_email: str
    user_role: str
    ip_address: str
    timestamp: datetime


class NoteAccessLogResponse(BaseModel):
    """Paginated access log response."""

    note_id: int
    entries: list[NoteAccessLogEntry]
    total: int
    page: int
    page_size: int
