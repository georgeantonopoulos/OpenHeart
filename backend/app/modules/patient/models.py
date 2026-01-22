"""
Patient SQLAlchemy Models.

Implements patient demographics with Cyprus-specific identifiers
and encrypted PII for GDPR compliance.
"""

from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from typing import List


class Gender(str, Enum):
    """Patient gender options."""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


class PatientStatus(str, Enum):
    """Patient status in the system."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DECEASED = "deceased"


class Patient(Base):
    """
    Core patient record.

    Contains non-sensitive demographics. Sensitive PII is stored
    separately in PatientPII with encryption.

    RLS Policy: patients are isolated by clinic_id
    """

    __tablename__ = "patients"

    patient_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    clinic_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("clinics.clinic_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Medical Record Number (clinic-specific)
    mrn: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Non-sensitive demographics
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(20), default=Gender.UNKNOWN.value, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=PatientStatus.ACTIVE.value, nullable=False)

    # Gesy integration
    gesy_beneficiary_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Gesy GHS beneficiary ID",
    )

    # Referring physician (if external referral)
    referring_physician: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Primary cardiologist assignment
    primary_physician_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
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

    # Soft delete for GDPR "right to erasure" (actually anonymization)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    pii: Mapped["PatientPII"] = relationship(
        "PatientPII",
        back_populates="patient",
        uselist=False,
        cascade="all, delete-orphan",
    )
    scheduled_procedures: Mapped[list["ScheduledProcedure"]] = relationship(
        "ScheduledProcedure",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    scheduled_procedures: Mapped[list["ScheduledProcedure"]] = relationship(
        "ScheduledProcedure",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_patients_clinic_mrn", "clinic_id", "mrn", unique=True),
        Index("idx_patients_clinic_active", "clinic_id", "status"),
        Index("idx_patients_gesy", "gesy_beneficiary_id"),
        {"comment": "Patient demographics - RLS enabled by clinic_id"},
    )

    @property
    def age(self) -> int:
        """Calculate patient age in years."""
        today = date.today()
        return (
            today.year
            - self.birth_date.year
            - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        )


class PatientPII(Base):
    """
    Personally Identifiable Information (encrypted).

    Stored separately from Patient for:
    1. Column-level encryption
    2. Access control (separate permissions)
    3. GDPR data minimization

    All fields are encrypted using Fernet at the application level.
    """

    __tablename__ = "patient_pii"

    pii_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("patients.patient_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Name (encrypted)
    first_name_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    last_name_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    middle_name_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Cyprus Identifiers (encrypted)
    # Cyprus ID Card: 1234567 (7 digits) or older format
    cyprus_id_encrypted: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Cyprus ID Card number (encrypted)",
    )
    # Alien Registration Certificate for non-citizens
    arc_number_encrypted: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="ARC number for non-citizens (encrypted)",
    )

    # Contact information (encrypted)
    phone_encrypted: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="+357 format phone number (encrypted)",
    )
    email_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Address (encrypted as JSON)
    address_encrypted: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Full address as encrypted JSON",
    )

    # Emergency contact (encrypted as JSON)
    emergency_contact_encrypted: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Emergency contact as encrypted JSON",
    )

    # Encryption metadata
    encryption_key_version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Key version for rotation support",
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

    # Relationship
    patient: Mapped["Patient"] = relationship("Patient", back_populates="pii")

    __table_args__ = (
        {"comment": "Encrypted PII - separate access control"},
    )
