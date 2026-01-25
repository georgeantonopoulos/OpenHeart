"""Prescription module tables for e-Prescribing.

Revision ID: 0009
Revises: 0008
Create Date: 2024-01-09 00:00:00.000000

Creates:
- prescriptions: Core prescription records with drug info, dosage, status lifecycle
- prescription_interactions: Drug-drug interaction alerts linked to prescriptions
- medication_history: Full audit trail of prescription status changes
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # prescriptions - Core prescription records
    # =========================================================================
    op.create_table(
        "prescriptions",
        # Primary key
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),

        # References
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False),
        sa.Column("encounter_id", sa.Integer(), sa.ForeignKey("encounters.encounter_id", ondelete="SET NULL"), nullable=True),
        sa.Column("prescriber_id", sa.Integer(), sa.ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("clinics.clinic_id", ondelete="CASCADE"), nullable=False),

        # Drug identification
        sa.Column("gesy_medication_id", sa.Integer(), sa.ForeignKey("gesy_medications.id", ondelete="SET NULL"), nullable=True),
        sa.Column("drug_name", sa.String(200), nullable=False),
        sa.Column("atc_code", sa.String(10), nullable=True),
        sa.Column("generic_name", sa.String(200), nullable=True),

        # Prescription details
        sa.Column("form", sa.String(50), nullable=True),
        sa.Column("strength", sa.String(50), nullable=True),
        sa.Column("dosage", sa.String(100), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=True),

        # Frequency & schedule
        sa.Column("frequency", sa.String(20), nullable=False, server_default="OD"),
        sa.Column("frequency_custom", sa.String(100), nullable=True),
        sa.Column("frequency_display", sa.String(200), nullable=True),

        # Route
        sa.Column("route", sa.String(30), nullable=False, server_default="oral"),

        # Duration
        sa.Column("duration_days", sa.Integer(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False, server_default=sa.text("CURRENT_DATE")),
        sa.Column("end_date", sa.Date(), nullable=True),

        # Refills
        sa.Column("refills_allowed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("refills_used", sa.Integer(), nullable=False, server_default="0"),

        # Status lifecycle
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("is_chronic", sa.Boolean(), nullable=False, server_default="false"),

        # Clinical linkage
        sa.Column("linked_diagnosis_icd10", sa.String(10), nullable=True),
        sa.Column("linked_diagnosis_description", sa.String(200), nullable=True),
        sa.Column("indication", sa.String(500), nullable=True),

        # Discontinuation
        sa.Column("discontinued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("discontinued_by", sa.Integer(), sa.ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True),
        sa.Column("discontinuation_reason", sa.Text(), nullable=True),

        # Chain tracking (renewals)
        sa.Column("original_prescription_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("prescriptions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("renewal_count", sa.Integer(), nullable=False, server_default="0"),

        # Gesy billing linkage
        sa.Column("gesy_claim_id", sa.String(50), nullable=True),
        sa.Column("requires_prior_auth", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("prior_auth_status", sa.String(20), nullable=True),

        # Notes
        sa.Column("prescriber_notes", sa.Text(), nullable=True),
        sa.Column("pharmacist_notes", sa.Text(), nullable=True),

        # Audit timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint("id"),
        comment="Prescription records with drug identification, dosage, and status lifecycle",
    )

    # Prescription indexes
    op.create_index("idx_prescriptions_patient_status", "prescriptions", ["patient_id", "status"])
    op.create_index("idx_prescriptions_patient_atc", "prescriptions", ["patient_id", "atc_code"])
    op.create_index("idx_prescriptions_prescriber", "prescriptions", ["prescriber_id", "created_at"])
    op.create_index("idx_prescriptions_clinic", "prescriptions", ["clinic_id"])
    op.create_index(
        "idx_prescriptions_active",
        "prescriptions",
        ["status"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_prescriptions_chronic",
        "prescriptions",
        ["patient_id"],
        postgresql_where=sa.text("is_chronic = true AND status = 'active'"),
    )

    # =========================================================================
    # prescription_interactions - Drug-drug interaction records
    # =========================================================================
    op.create_table(
        "prescription_interactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("prescription_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("prescriptions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("interacting_prescription_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("prescriptions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("interacting_drug_name", sa.String(200), nullable=False),
        sa.Column("interacting_atc_code", sa.String(10), nullable=True),

        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("interaction_type", sa.String(50), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("clinical_significance", sa.Text(), nullable=True),
        sa.Column("management_recommendation", sa.Text(), nullable=True),
        sa.Column("source", sa.String(100), nullable=False, server_default="openheart_cardiology_rules"),

        # Resolution
        sa.Column("acknowledged_by", sa.Integer(), sa.ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("override_reason", sa.Text(), nullable=True),

        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),

        sa.PrimaryKeyConstraint("id"),
        comment="Drug-drug interaction alerts linked to prescriptions",
    )

    op.create_index("idx_interactions_prescription", "prescription_interactions", ["prescription_id"])
    op.create_index("idx_interactions_severity", "prescription_interactions", ["severity"])

    # =========================================================================
    # medication_history - Audit trail of prescription changes
    # =========================================================================
    op.create_table(
        "medication_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("prescription_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("prescriptions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("previous_status", sa.String(20), nullable=True),
        sa.Column("new_status", sa.String(20), nullable=False),
        sa.Column("changed_by", sa.Integer(), sa.ForeignKey("users.user_id", ondelete="SET NULL"), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("change_type", sa.String(30), nullable=False),
        sa.Column("details", postgresql.JSONB(), nullable=True),

        sa.PrimaryKeyConstraint("id"),
        comment="Full audit trail of prescription status changes",
    )

    op.create_index("idx_med_history_prescription", "medication_history", ["prescription_id", "changed_at"])


def downgrade() -> None:
    op.drop_table("medication_history")
    op.drop_table("prescription_interactions")
    op.drop_table("prescriptions")
