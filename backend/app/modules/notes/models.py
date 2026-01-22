"""
Doctor's Notes SQLAlchemy Models.

Implements clinical documentation with version control, attachments,
and comprehensive audit logging for GDPR compliance.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    BigInteger,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from typing import List


class NoteType(str, Enum):
    """Types of clinical notes."""

    FREE_TEXT = "free_text"
    SOAP = "soap"
    PROCEDURE = "procedure"
    CONSULTATION = "consultation"
    DISCHARGE = "discharge"
    PROGRESS = "progress"


class NoteAccessAction(str, Enum):
    """Actions tracked in note access log."""

    VIEW = "VIEW"
    EDIT = "EDIT"
    CREATE = "CREATE"
    DOWNLOAD_ATTACHMENT = "DOWNLOAD_ATTACHMENT"
    SEARCH = "SEARCH"
    EXPORT = "EXPORT"


class ClinicalNote(Base):
    """
    Clinical notes with version control.

    Each note tracks its current version and links to all historical versions.
    RLS policy ensures clinic isolation.
    """

    __tablename__ = "clinical_notes"

    note_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("patients.patient_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    encounter_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("encounters.encounter_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    clinic_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("clinics.clinic_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    note_type: Mapped[str] = mapped_column(
        String(50),
        default=NoteType.FREE_TEXT.value,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Metadata
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    locked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )
    locked_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Timestamps
    created_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    versions: Mapped["List[NoteVersion]"] = relationship(
        "NoteVersion",
        back_populates="note",
        cascade="all, delete-orphan",
        order_by="NoteVersion.version_number.desc()",
    )
    attachments: Mapped["List[NoteAttachment]"] = relationship(
        "NoteAttachment",
        back_populates="note",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_clinical_notes_patient_clinic", "patient_id", "clinic_id"),
        Index("idx_clinical_notes_created_at", "created_at"),
        {"comment": "Clinical notes with version control - RLS enabled"},
    )


class NoteVersion(Base):
    """
    Version history for clinical notes.

    Each edit creates a new version, preserving the complete history
    for audit and compliance purposes. Versions are immutable once created.
    """

    __tablename__ = "note_versions"

    version_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    note_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("clinical_notes.note_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Content
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    content_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Structured content for SOAP notes
    structured_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Diff tracking - stores JSON diff from previous version
    diff_from_previous: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Edit metadata
    edited_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=False,
    )
    edit_reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Required for edits after initial creation",
    )

    # Word/character counts for analytics
    word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    char_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationship
    note: Mapped["ClinicalNote"] = relationship("ClinicalNote", back_populates="versions")

    __table_args__ = (
        Index("idx_note_versions_note_version", "note_id", "version_number", unique=True),
        Index(
            "idx_note_versions_content_fts",
            text("to_tsvector('english', content_text)"),
            postgresql_using="gin",
        ),
        {"comment": "Immutable version history for clinical notes"},
    )


class NoteAttachment(Base):
    """
    File attachments for clinical notes.

    Supports PDF, DOCX, images with text extraction and optional
    vector embeddings for semantic search.
    """

    __tablename__ = "note_attachments"

    attachment_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    note_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("clinical_notes.note_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # File metadata
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    original_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="pdf, docx, image, txt",
    )
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Storage
    storage_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="S3/MinIO path",
    )
    storage_bucket: Mapped[str] = mapped_column(String(100), nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)

    # Extracted content
    extracted_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="OCR/parsed text for search",
    )
    extraction_status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        comment="pending, processing, completed, failed",
    )
    extraction_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Image-specific metadata
    image_width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    image_height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    page_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="For PDFs and multi-page documents",
    )

    # Audit
    uploaded_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=False,
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Soft delete for compliance
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationship
    note: Mapped["ClinicalNote"] = relationship("ClinicalNote", back_populates="attachments")

    __table_args__ = (
        Index(
            "idx_attachment_extracted_fts",
            text("to_tsvector('english', extracted_text)"),
            postgresql_using="gin",
            postgresql_where=text("extracted_text IS NOT NULL"),
        ),
        Index("idx_attachments_not_deleted", "note_id", postgresql_where=text("is_deleted = false")),
        {"comment": "File attachments with text extraction"},
    )


class NoteAccessLog(Base):
    """
    GDPR-compliant access logging for clinical notes.

    Partitioned by timestamp for efficient querying and 15-year retention.
    All views, edits, and downloads are logged.
    """

    __tablename__ = "note_access_log"

    log_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    note_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    attachment_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    # Action
    action: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="VIEW, EDIT, CREATE, DOWNLOAD_ATTACHMENT, SEARCH, EXPORT",
    )
    version_accessed: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Which version was viewed/compared",
    )

    # User context
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    user_email: Mapped[str] = mapped_column(String(255), nullable=False)
    user_role: Mapped[str] = mapped_column(String(50), nullable=False)
    clinic_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Request context
    ip_address: Mapped[str] = mapped_column(INET, nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Metadata
    request_path: Mapped[str] = mapped_column(String(500), nullable=False)
    request_method: Mapped[str] = mapped_column(String(10), nullable=False)
    response_status: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)

    # Additional context
    search_query: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="For SEARCH actions",
    )
    export_format: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="For EXPORT actions",
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("idx_note_access_user_time", "user_id", "timestamp"),
        Index("idx_note_access_note_time", "note_id", "timestamp"),
        {
            "comment": "GDPR audit log for note access - 15 year retention",
            "postgresql_partition_by": "RANGE (timestamp)",
        },
    )
