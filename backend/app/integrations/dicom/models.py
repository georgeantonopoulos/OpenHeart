"""
DICOM Integration SQLAlchemy Models.

Includes study-to-patient linking for the imaging subsystem.
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PatientStudyLink(Base):
    """
    Links a DICOM study to an OpenHeart patient record.

    Studies can be linked either:
    - Automatically via matching DICOM Patient ID to Cyprus ID
    - Manually by a clinician from the patient profile

    The unique constraint on (study_instance_uid, patient_id) prevents
    duplicate links for the same study-patient pair.
    """

    __tablename__ = "patient_study_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    study_instance_uid: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        comment="DICOM Study Instance UID",
    )
    patient_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("patients.patient_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    encounter_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("encounters.encounter_id", ondelete="SET NULL"),
        nullable=True,
    )
    clinic_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("clinics.clinic_id", ondelete="CASCADE"),
        nullable=False,
    )
    linked_by_user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=False,
    )

    # Study metadata (cached from Orthanc at link time)
    link_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Reason for manual linking",
    )
    study_date: Mapped[datetime | None] = mapped_column(
        Date,
        nullable=True,
    )
    study_description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    modality: Mapped[str | None] = mapped_column(
        String(16),
        nullable=True,
        comment="Primary modality (CT, MR, US, etc.)",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    # Relationships
    patient = relationship("Patient", foreign_keys=[patient_id])
    encounter = relationship("Encounter", foreign_keys=[encounter_id])

    __table_args__ = (
        UniqueConstraint(
            "study_instance_uid", "patient_id",
            name="uq_study_patient",
        ),
        {"comment": "Links DICOM studies to OpenHeart patient records"},
    )
