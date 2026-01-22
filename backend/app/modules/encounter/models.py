"""
Encounter SQLAlchemy Models.

Implements clinical encounters (visits) with support for
outpatient, inpatient, and emergency visit types.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    pass


class EncounterType(str, Enum):
    """Types of clinical encounters."""

    OUTPATIENT = "outpatient"
    INPATIENT = "inpatient"
    EMERGENCY = "emergency"
    TELEHEALTH = "telehealth"
    HOME_VISIT = "home_visit"


class EncounterStatus(str, Enum):
    """Encounter status."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class Encounter(Base):
    """
    Clinical encounter (visit) record.

    Represents a single patient visit with the cardiologist,
    containing timing, type, and clinical context.
    """

    __tablename__ = "encounters"

    encounter_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("patients.patient_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    clinic_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("clinics.clinic_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Encounter type and status
    encounter_type: Mapped[str] = mapped_column(
        String(50),
        default=EncounterType.OUTPATIENT.value,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default=EncounterStatus.PLANNED.value,
        nullable=False,
    )

    # Timing
    scheduled_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Scheduled appointment time",
    )
    actual_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When encounter actually started",
    )
    actual_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When encounter ended",
    )

    # Reason for visit
    chief_complaint: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Primary reason for visit",
    )
    visit_reason_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="ICD-10 or ICPC-II code for visit reason",
    )

    # Provider
    attending_physician_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=False,
    )

    # Location (for inpatient or specific clinic rooms)
    location: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Room or location identifier",
    )

    # Referral tracking
    referral_source: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Referring physician or facility",
    )
    is_follow_up: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="Whether this is a follow-up visit",
    )
    follow_up_to_encounter_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("encounters.encounter_id", ondelete="SET NULL"),
        nullable=True,
    )

    # Gesy referral (if applicable)
    gesy_referral_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Gesy referral voucher ID",
    )

    # Clinical summary (JSONB for flexibility)
    discharge_summary: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Structured discharge/visit summary",
    )

    # ICD-10 diagnoses (array of codes)
    diagnoses: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Array of diagnosis objects with code, description, type",
    )

    # Billing
    billing_status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
    )
    gesy_claim_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Gesy claim ID if submitted",
    )

    # Timestamps
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

    __table_args__ = (
        Index("idx_encounters_patient_date", "patient_id", "scheduled_start"),
        Index("idx_encounters_physician_date", "attending_physician_id", "scheduled_start"),
        Index("idx_encounters_clinic_status", "clinic_id", "status"),
        Index("idx_encounters_gesy_referral", "gesy_referral_id"),
        {"comment": "Clinical encounters - RLS enabled by clinic_id"},
    )

    @property
    def duration_minutes(self) -> Optional[int]:
        """Calculate encounter duration in minutes."""
        if self.actual_start and self.actual_end:
            delta = self.actual_end - self.actual_start
            return int(delta.total_seconds() / 60)
        return None


class Vitals(Base):
    """
    Vital signs recorded during an encounter.

    Linked to encounter with timestamps for trending.
    """

    __tablename__ = "vitals"

    vital_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    encounter_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("encounters.encounter_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    patient_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("patients.patient_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Cardiovascular vitals
    heart_rate: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="bpm"
    )
    systolic_bp: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="mmHg"
    )
    diastolic_bp: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="mmHg"
    )
    respiratory_rate: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="breaths/min"
    )
    oxygen_saturation: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="SpO2 %"
    )

    # General vitals
    temperature: Mapped[Optional[float]] = mapped_column(
        nullable=True, comment="Celsius"
    )
    weight: Mapped[Optional[float]] = mapped_column(
        nullable=True, comment="kg"
    )
    height: Mapped[Optional[float]] = mapped_column(
        nullable=True, comment="cm"
    )

    # Calculated
    bmi: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Recording metadata
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    recorded_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=False,
    )
    position: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Patient position: sitting, standing, supine",
    )

    __table_args__ = (
        Index("idx_vitals_patient_time", "patient_id", "recorded_at"),
        {"comment": "Vital signs measurements"},
    )
