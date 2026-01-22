"""Appointment SQLAlchemy Model.

Implements appointment scheduling with conflict detection,
status tracking, and encounter handover support.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AppointmentType(str, Enum):
    """Types of cardiology appointments."""

    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"
    ECHO = "echo"
    STRESS_TEST = "stress_test"
    HOLTER = "holter"
    PROCEDURE = "procedure"
    ECG = "ecg"
    PRE_OP = "pre_op"


class AppointmentStatus(str, Enum):
    """Appointment lifecycle status."""

    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


# Default expected durations by appointment type (minutes)
EXPECTED_DURATIONS: dict[str, int] = {
    AppointmentType.CONSULTATION: 20,
    AppointmentType.FOLLOW_UP: 15,
    AppointmentType.ECHO: 30,
    AppointmentType.STRESS_TEST: 45,
    AppointmentType.HOLTER: 15,
    AppointmentType.PROCEDURE: 60,
    AppointmentType.ECG: 10,
    AppointmentType.PRE_OP: 30,
}


class Appointment(Base):
    """
    Patient appointment with scheduling and encounter linking.

    Supports:
    - Conflict detection via provider + time range index
    - Duration warnings when scheduled < expected
    - Encounter handover via encounter_id link
    - RLS clinic isolation
    """

    __tablename__ = "appointments"

    appointment_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    clinic_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clinics.clinic_id"), nullable=False
    )
    patient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("patients.patient_id"), nullable=False
    )
    provider_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False
    )

    # Scheduling
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_duration_minutes: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )

    # Type and status
    appointment_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=AppointmentStatus.SCHEDULED.value
    )

    # Details
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Gesy referral link
    gesy_referral_id: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )

    # Encounter link (set when "Start Encounter" is triggered)
    encounter_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("encounters.encounter_id"), nullable=True
    )

    # Cancellation
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=True
    )
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Audit
    created_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
