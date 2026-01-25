"""SQLAlchemy models for the prescription module."""

import uuid
from datetime import date, datetime
from typing import List, Optional

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
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Prescription(Base):
    """Core prescription record with drug info, dosage, and status lifecycle."""

    __tablename__ = "prescriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # References
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
    )
    prescriber_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
    )
    clinic_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("clinics.clinic_id", ondelete="CASCADE"),
        nullable=False,
    )

    # Drug identification
    gesy_medication_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("gesy_medications.id", ondelete="SET NULL"),
        nullable=True,
    )
    drug_name: Mapped[str] = mapped_column(String(200), nullable=False)
    atc_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    generic_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Prescription details
    form: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    strength: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    dosage: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Frequency & schedule
    frequency: Mapped[str] = mapped_column(String(20), nullable=False, server_default="OD")
    frequency_custom: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    frequency_display: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Route
    route: Mapped[str] = mapped_column(String(30), nullable=False, server_default="oral")

    # Duration
    duration_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False, server_default=text("CURRENT_DATE"))
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Refills
    refills_allowed: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    refills_used: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    # Status lifecycle
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="active")
    is_chronic: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    # Clinical linkage
    linked_diagnosis_icd10: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    linked_diagnosis_description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    indication: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Discontinuation
    discontinued_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    discontinued_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )
    discontinuation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Chain tracking (renewals)
    original_prescription_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prescriptions.id", ondelete="SET NULL"),
        nullable=True,
    )
    renewal_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    # Gesy billing linkage
    gesy_claim_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    requires_prior_auth: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    prior_auth_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Notes
    prescriber_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pharmacist_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    interactions: Mapped[List["PrescriptionInteraction"]] = relationship(
        "PrescriptionInteraction",
        back_populates="prescription",
        cascade="all, delete-orphan",
        foreign_keys="PrescriptionInteraction.prescription_id",
    )
    history: Mapped[List["MedicationHistory"]] = relationship(
        "MedicationHistory",
        back_populates="prescription",
        cascade="all, delete-orphan",
        order_by="MedicationHistory.changed_at",
    )
    original_prescription: Mapped[Optional["Prescription"]] = relationship(
        "Prescription",
        remote_side=[id],
        foreign_keys=[original_prescription_id],
    )

    __table_args__ = (
        Index("idx_prescriptions_patient_status", "patient_id", "status"),
        Index("idx_prescriptions_patient_atc", "patient_id", "atc_code"),
        Index("idx_prescriptions_prescriber", "prescriber_id", "created_at"),
        Index("idx_prescriptions_clinic", "clinic_id"),
        {"comment": "Prescription records with drug identification, dosage, and status lifecycle"},
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def can_renew(self) -> bool:
        return self.is_chronic and self.status == "active"

    @property
    def days_remaining(self) -> Optional[int]:
        if self.end_date:
            delta = self.end_date - date.today()
            return max(0, delta.days)
        return None


class PrescriptionInteraction(Base):
    """Drug-drug interaction alert linked to a prescription."""

    __tablename__ = "prescription_interactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    prescription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prescriptions.id", ondelete="CASCADE"),
        nullable=False,
    )
    interacting_prescription_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prescriptions.id", ondelete="SET NULL"),
        nullable=True,
    )
    interacting_drug_name: Mapped[str] = mapped_column(String(200), nullable=False)
    interacting_atc_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    interaction_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    clinical_significance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    management_recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(
        String(100), nullable=False, server_default="openheart_cardiology_rules"
    )

    # Resolution
    acknowledged_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    override_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    prescription: Mapped["Prescription"] = relationship(
        "Prescription",
        back_populates="interactions",
        foreign_keys=[prescription_id],
    )

    __table_args__ = (
        Index("idx_interactions_prescription", "prescription_id"),
        Index("idx_interactions_severity", "severity"),
        {"comment": "Drug-drug interaction alerts linked to prescriptions"},
    )


class MedicationHistory(Base):
    """Audit trail of prescription status changes."""

    __tablename__ = "medication_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    prescription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prescriptions.id", ondelete="CASCADE"),
        nullable=False,
    )
    previous_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    new_status: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=False
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    change_type: Mapped[str] = mapped_column(String(30), nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    prescription: Mapped["Prescription"] = relationship(
        "Prescription", back_populates="history"
    )

    __table_args__ = (
        Index("idx_med_history_prescription", "prescription_id", "changed_at"),
        {"comment": "Full audit trail of prescription status changes"},
    )
