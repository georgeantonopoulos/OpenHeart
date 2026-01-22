"""
Modality Worklist (MWL) Models for OpenHeart Cyprus.

Defines database models for scheduled procedures that populate
the DICOM Modality Worklist, allowing imaging equipment to query
patient/procedure information before exams.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProcedureStatus(str, Enum):
    """Status of a scheduled procedure."""

    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ImagingModality(str, Enum):
    """Modality types for cardiology imaging."""

    US = "US"  # Ultrasound (Echo)
    XA = "XA"  # X-Ray Angiography (Cath)
    CT = "CT"  # Computed Tomography (CTA)
    MR = "MR"  # Magnetic Resonance (CMR)
    NM = "NM"  # Nuclear Medicine (SPECT/PET)


class ScheduledProcedure(Base):
    """
    Scheduled imaging procedure for Modality Worklist.

    When a procedure is scheduled, a record is created here.
    The imaging equipment (Echo/Cath) queries this table via
    DICOM MWL C-FIND to get patient demographics and procedure info.

    This eliminates manual data entry on imaging equipment,
    reducing errors and improving workflow efficiency.
    """

    __tablename__ = "scheduled_procedures"

    id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Patient reference (OpenHeart patient)
    patient_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("patients.patient_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Clinic for RLS
    clinic_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("clinics.clinic_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Accession number (unique identifier for the exam)
    accession_number: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        unique=True,
        comment="Unique exam identifier (DICOM 0008,0050)",
    )

    # Equipment routing (which machine should perform the exam)
    scheduled_station_ae_title: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        comment="Target AE Title: ECHO1, ECHO2, CATH1, etc.",
    )
    scheduled_station_name: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="Friendly name: Echo Room 1, Cath Lab, etc.",
    )

    # Procedure details
    modality: Mapped[ImagingModality] = mapped_column(
        SQLEnum(ImagingModality, native_enum=False),
        nullable=False,
        comment="DICOM Modality code",
    )
    procedure_code: Mapped[Optional[str]] = mapped_column(
        String(16),
        nullable=True,
        comment="Procedure code for billing/coding",
    )
    procedure_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Scheduled Procedure Step Description (DICOM 0040,0007)",
    )

    # Scheduling
    scheduled_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Scheduled start date/time",
    )
    expected_duration_minutes: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Expected duration in minutes",
    )

    # Performing physician
    performing_physician_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )

    # Referring physician
    referring_physician_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )
    referring_physician_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="External referring physician name",
    )

    # DICOM identifiers (populated after exam starts)
    study_instance_uid: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="Assigned Study Instance UID",
    )
    scheduled_procedure_step_id: Mapped[Optional[str]] = mapped_column(
        String(16),
        nullable=True,
        comment="SPS ID (DICOM 0040,0009)",
    )

    # Status tracking
    status: Mapped[ProcedureStatus] = mapped_column(
        SQLEnum(ProcedureStatus, native_enum=False),
        default=ProcedureStatus.SCHEDULED,
        nullable=False,
        index=True,
    )

    # Actual timing (updated during exam)
    actual_start_datetime: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    actual_end_datetime: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Clinical context
    reason_for_exam: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Clinical indication",
    )
    priority: Mapped[str] = mapped_column(
        String(8),
        default="ROUTINE",
        nullable=False,
        comment="STAT, ROUTINE, URGENT",
    )

    # Linked encounter
    encounter_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("encounters.encounter_id", ondelete="SET NULL"),
        nullable=True,
    )

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(),
        onupdate=lambda: datetime.now(),
        nullable=False,
    )
    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    cancellation_reason: Mapped[Optional[str]] = mapped_column(
        String(256),
        nullable=True,
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Internal scheduling notes",
    )

    # Relationships
    patient = relationship("Patient", back_populates="scheduled_procedures")
    clinic = relationship("Clinic")
    performing_physician = relationship(
        "User",
        foreign_keys=[performing_physician_id],
    )
    created_by = relationship(
        "User",
        foreign_keys=[created_by_user_id],
    )


class WorklistStation(Base):
    """
    Configuration for imaging equipment AE Titles.

    Defines the equipment that can query the Modality Worklist.
    """

    __tablename__ = "worklist_stations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Clinic association
    clinic_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("clinics.clinic_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Station identification
    ae_title: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        unique=True,
        comment="DICOM Application Entity Title",
    )
    station_name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="Friendly display name",
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="Physical location (room number, etc.)",
    )

    # Equipment type
    modality: Mapped[ImagingModality] = mapped_column(
        SQLEnum(ImagingModality, native_enum=False),
        nullable=False,
    )
    manufacturer: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="Equipment manufacturer (GE, Philips, Siemens)",
    )
    model: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="Equipment model",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    last_query_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last MWL query timestamp",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(),
        onupdate=lambda: datetime.now(),
        nullable=False,
    )

    # Relationship
    clinic = relationship("Clinic")
