"""Initial schema with RLS policies.

Revision ID: 0001
Revises: None
Create Date: 2024-01-01 00:00:00.000000

This migration creates the complete OpenHeart Cyprus schema including:
- Multi-tenant clinic structure
- User authentication with MFA
- Patient demographics with encrypted PII
- Clinical encounters and vitals
- Clinical notes with version control
- GDPR audit logging

Row-Level Security (RLS) policies ensure data isolation between clinics.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # Extensions
    # =========================================================================
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")  # For fuzzy search

    # =========================================================================
    # Clinics Table
    # =========================================================================
    op.create_table(
        "clinics",
        sa.Column("clinic_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("website", sa.String(255), nullable=True),
        sa.Column("gesy_provider_id", sa.String(50), nullable=True),
        sa.Column("operating_hours", postgresql.JSONB(), nullable=True),
        sa.Column("settings", postgresql.JSONB(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("clinic_id"),
        sa.UniqueConstraint("code"),
        sa.UniqueConstraint("gesy_provider_id"),
        comment="Healthcare clinics for multi-tenant isolation",
    )
    op.create_index("idx_clinics_gesy", "clinics", ["gesy_provider_id"])

    # =========================================================================
    # Users Table
    # =========================================================================
    op.create_table(
        "users",
        sa.Column("user_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("title", sa.String(50), nullable=True),
        sa.Column("specialty", sa.String(100), nullable=True),
        sa.Column("license_number", sa.String(50), nullable=True),
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("mfa_secret", sa.String(32), nullable=True),
        sa.Column("mfa_backup_codes", postgresql.JSONB(), nullable=True),
        sa.Column("webauthn_credentials", postgresql.JSONB(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("must_change_password", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("email"),
        comment="User accounts with MFA support",
    )
    op.create_index("idx_users_email", "users", ["email"])

    # =========================================================================
    # User-Clinic Roles Table
    # =========================================================================
    op.create_table(
        "user_clinic_roles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("clinic_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("additional_permissions", postgresql.JSONB(), nullable=True),
        sa.Column("is_primary_clinic", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.clinic_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "clinic_id", name="uq_user_clinic"),
        comment="User-clinic role assignments",
    )
    op.create_index("idx_user_clinic_roles_user", "user_clinic_roles", ["user_id"])
    op.create_index("idx_user_clinic_roles_clinic", "user_clinic_roles", ["clinic_id"])

    # =========================================================================
    # Patients Table (with RLS)
    # =========================================================================
    op.create_table(
        "patients",
        sa.Column("patient_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("clinic_id", sa.Integer(), nullable=False),
        sa.Column("mrn", sa.String(50), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column("gender", sa.String(20), nullable=False, server_default="unknown"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("gesy_beneficiary_id", sa.String(50), nullable=True),
        sa.Column("referring_physician", sa.String(255), nullable=True),
        sa.Column("primary_physician_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("patient_id"),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.clinic_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["primary_physician_id"], ["users.user_id"], ondelete="SET NULL"),
        comment="Patient demographics - RLS enabled by clinic_id",
    )
    op.create_index("idx_patients_clinic_id", "patients", ["clinic_id"])
    op.create_index("idx_patients_clinic_mrn", "patients", ["clinic_id", "mrn"], unique=True)
    op.create_index("idx_patients_clinic_active", "patients", ["clinic_id", "status"])
    op.create_index("idx_patients_gesy", "patients", ["gesy_beneficiary_id"])

    # Enable RLS on patients
    op.execute("ALTER TABLE patients ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY patient_clinic_isolation ON patients
        FOR ALL
        USING (clinic_id = current_setting('app.clinic_id', true)::int)
    """)

    # =========================================================================
    # Patient PII Table (encrypted)
    # =========================================================================
    op.create_table(
        "patient_pii",
        sa.Column("pii_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("first_name_encrypted", sa.Text(), nullable=False),
        sa.Column("last_name_encrypted", sa.Text(), nullable=False),
        sa.Column("middle_name_encrypted", sa.Text(), nullable=True),
        sa.Column("cyprus_id_encrypted", sa.Text(), nullable=True),
        sa.Column("arc_number_encrypted", sa.Text(), nullable=True),
        sa.Column("phone_encrypted", sa.Text(), nullable=True),
        sa.Column("email_encrypted", sa.Text(), nullable=True),
        sa.Column("address_encrypted", sa.Text(), nullable=True),
        sa.Column("emergency_contact_encrypted", sa.Text(), nullable=True),
        sa.Column("encryption_key_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("pii_id"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.patient_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("patient_id"),
        comment="Encrypted PII - separate access control",
    )

    # =========================================================================
    # Encounters Table (with RLS)
    # =========================================================================
    op.create_table(
        "encounters",
        sa.Column("encounter_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("clinic_id", sa.Integer(), nullable=False),
        sa.Column("encounter_type", sa.String(50), nullable=False, server_default="outpatient"),
        sa.Column("status", sa.String(50), nullable=False, server_default="planned"),
        sa.Column("scheduled_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("chief_complaint", sa.String(500), nullable=True),
        sa.Column("visit_reason_code", sa.String(20), nullable=True),
        sa.Column("attending_physician_id", sa.Integer(), nullable=False),
        sa.Column("location", sa.String(100), nullable=True),
        sa.Column("referral_source", sa.String(255), nullable=True),
        sa.Column("is_follow_up", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("follow_up_to_encounter_id", sa.Integer(), nullable=True),
        sa.Column("gesy_referral_id", sa.String(50), nullable=True),
        sa.Column("discharge_summary", postgresql.JSONB(), nullable=True),
        sa.Column("diagnoses", postgresql.JSONB(), nullable=True),
        sa.Column("billing_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("gesy_claim_id", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("encounter_id"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.patient_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.clinic_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["attending_physician_id"], ["users.user_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["follow_up_to_encounter_id"], ["encounters.encounter_id"], ondelete="SET NULL"),
        comment="Clinical encounters - RLS enabled by clinic_id",
    )
    op.create_index("idx_encounters_patient_id", "encounters", ["patient_id"])
    op.create_index("idx_encounters_clinic_id", "encounters", ["clinic_id"])
    op.create_index("idx_encounters_patient_date", "encounters", ["patient_id", "scheduled_start"])
    op.create_index("idx_encounters_physician_date", "encounters", ["attending_physician_id", "scheduled_start"])
    op.create_index("idx_encounters_clinic_status", "encounters", ["clinic_id", "status"])
    op.create_index("idx_encounters_gesy_referral", "encounters", ["gesy_referral_id"])

    # Enable RLS on encounters
    op.execute("ALTER TABLE encounters ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY encounter_clinic_isolation ON encounters
        FOR ALL
        USING (clinic_id = current_setting('app.clinic_id', true)::int)
    """)

    # =========================================================================
    # Vitals Table
    # =========================================================================
    op.create_table(
        "vitals",
        sa.Column("vital_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("encounter_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("heart_rate", sa.Integer(), nullable=True),
        sa.Column("systolic_bp", sa.Integer(), nullable=True),
        sa.Column("diastolic_bp", sa.Integer(), nullable=True),
        sa.Column("respiratory_rate", sa.Integer(), nullable=True),
        sa.Column("oxygen_saturation", sa.Integer(), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("weight", sa.Float(), nullable=True),
        sa.Column("height", sa.Float(), nullable=True),
        sa.Column("bmi", sa.Float(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("recorded_by", sa.Integer(), nullable=False),
        sa.Column("position", sa.String(20), nullable=True),
        sa.PrimaryKeyConstraint("vital_id"),
        sa.ForeignKeyConstraint(["encounter_id"], ["encounters.encounter_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.patient_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recorded_by"], ["users.user_id"], ondelete="SET NULL"),
        comment="Vital signs measurements",
    )
    op.create_index("idx_vitals_encounter_id", "vitals", ["encounter_id"])
    op.create_index("idx_vitals_patient_id", "vitals", ["patient_id"])
    op.create_index("idx_vitals_patient_time", "vitals", ["patient_id", "recorded_at"])

    # =========================================================================
    # Clinical Notes Table (with RLS)
    # =========================================================================
    op.create_table(
        "clinical_notes",
        sa.Column("note_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("encounter_id", sa.Integer(), nullable=True),
        sa.Column("clinic_id", sa.Integer(), nullable=False),
        sa.Column("note_type", sa.String(50), nullable=False, server_default="free_text"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("current_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_by", sa.Integer(), nullable=True),
        sa.Column("locked_reason", sa.String(255), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("note_id"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.patient_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["encounter_id"], ["encounters.encounter_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.clinic_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["locked_by"], ["users.user_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.user_id"], ondelete="SET NULL"),
        comment="Clinical notes with version control - RLS enabled",
    )
    op.create_index("idx_clinical_notes_patient_id", "clinical_notes", ["patient_id"])
    op.create_index("idx_clinical_notes_clinic_id", "clinical_notes", ["clinic_id"])
    op.create_index("idx_clinical_notes_patient_clinic", "clinical_notes", ["patient_id", "clinic_id"])
    op.create_index("idx_clinical_notes_created_at", "clinical_notes", ["created_at"])

    # Enable RLS on clinical_notes
    op.execute("ALTER TABLE clinical_notes ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY note_clinic_isolation ON clinical_notes
        FOR ALL
        USING (clinic_id = current_setting('app.clinic_id', true)::int)
    """)

    # =========================================================================
    # Note Versions Table
    # =========================================================================
    op.create_table(
        "note_versions",
        sa.Column("version_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("note_id", sa.BigInteger(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("content_html", sa.Text(), nullable=True),
        sa.Column("structured_data", postgresql.JSONB(), nullable=True),
        sa.Column("diff_from_previous", postgresql.JSONB(), nullable=True),
        sa.Column("edited_by", sa.Integer(), nullable=False),
        sa.Column("edit_reason", sa.String(255), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("char_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("version_id"),
        sa.ForeignKeyConstraint(["note_id"], ["clinical_notes.note_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["edited_by"], ["users.user_id"], ondelete="SET NULL"),
        comment="Immutable version history for clinical notes",
    )
    op.create_index("idx_note_versions_note_id", "note_versions", ["note_id"])
    op.create_index("idx_note_versions_note_version", "note_versions", ["note_id", "version_number"], unique=True)

    # Full-text search index on content
    op.execute("""
        CREATE INDEX idx_note_versions_content_fts
        ON note_versions
        USING GIN (to_tsvector('english', content_text))
    """)

    # =========================================================================
    # Note Attachments Table
    # =========================================================================
    op.create_table(
        "note_attachments",
        sa.Column("attachment_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("note_id", sa.BigInteger(), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("original_file_name", sa.String(255), nullable=False),
        sa.Column("file_type", sa.String(50), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("storage_path", sa.String(500), nullable=False),
        sa.Column("storage_bucket", sa.String(100), nullable=False),
        sa.Column("checksum_sha256", sa.String(64), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("extraction_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("extraction_error", sa.Text(), nullable=True),
        sa.Column("image_width", sa.Integer(), nullable=True),
        sa.Column("image_height", sa.Integer(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("uploaded_by", sa.Integer(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("attachment_id"),
        sa.ForeignKeyConstraint(["note_id"], ["clinical_notes.note_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.user_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["deleted_by"], ["users.user_id"], ondelete="SET NULL"),
        comment="File attachments with text extraction",
    )
    op.create_index("idx_note_attachments_note_id", "note_attachments", ["note_id"])

    # Full-text search index on extracted text
    op.execute("""
        CREATE INDEX idx_attachment_extracted_fts
        ON note_attachments
        USING GIN (to_tsvector('english', extracted_text))
        WHERE extracted_text IS NOT NULL
    """)

    # =========================================================================
    # Note Access Log Table (Partitioned)
    # =========================================================================
    op.execute("""
        CREATE TABLE note_access_log (
            log_id BIGSERIAL,
            note_id BIGINT NOT NULL,
            attachment_id BIGINT,
            action VARCHAR(30) NOT NULL,
            version_accessed INT,
            user_id INT NOT NULL,
            user_email VARCHAR(255) NOT NULL,
            user_role VARCHAR(50) NOT NULL,
            clinic_id INT NOT NULL,
            ip_address INET NOT NULL,
            user_agent VARCHAR(500),
            session_id VARCHAR(100),
            request_path VARCHAR(500) NOT NULL,
            request_method VARCHAR(10) NOT NULL,
            response_status INT NOT NULL,
            duration_ms INT NOT NULL,
            search_query VARCHAR(500),
            export_format VARCHAR(20),
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (log_id, timestamp)
        ) PARTITION BY RANGE (timestamp)
    """)

    op.create_index("idx_note_access_user_time", "note_access_log", ["user_id", "timestamp"])
    op.create_index("idx_note_access_note_time", "note_access_log", ["note_id", "timestamp"])

    # Create initial partitions (current year + next year)
    op.execute("""
        CREATE TABLE note_access_log_2024 PARTITION OF note_access_log
        FOR VALUES FROM ('2024-01-01') TO ('2025-01-01')
    """)
    op.execute("""
        CREATE TABLE note_access_log_2025 PARTITION OF note_access_log
        FOR VALUES FROM ('2025-01-01') TO ('2026-01-01')
    """)
    op.execute("""
        CREATE TABLE note_access_log_2026 PARTITION OF note_access_log
        FOR VALUES FROM ('2026-01-01') TO ('2027-01-01')
    """)

    # =========================================================================
    # Security Audit Log Table (Partitioned) - GDPR 15 year retention
    # =========================================================================
    op.execute("""
        CREATE TABLE security_audit (
            audit_id BIGSERIAL,
            user_id INT,
            user_email VARCHAR(255),
            user_role VARCHAR(50),
            clinic_id INT,
            ip_address INET NOT NULL,
            user_agent VARCHAR(500),
            session_id VARCHAR(100),
            action VARCHAR(50) NOT NULL,
            resource_type VARCHAR(50),
            resource_id VARCHAR(100),
            request_path VARCHAR(500) NOT NULL,
            request_method VARCHAR(10) NOT NULL,
            request_body_hash VARCHAR(64),
            response_status INT NOT NULL,
            response_time_ms INT NOT NULL,
            error_message TEXT,
            additional_data JSONB,
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (audit_id, timestamp)
        ) PARTITION BY RANGE (timestamp)
    """)

    op.create_index("idx_security_audit_user", "security_audit", ["user_id", "timestamp"])
    op.create_index("idx_security_audit_clinic", "security_audit", ["clinic_id", "timestamp"])
    op.create_index("idx_security_audit_action", "security_audit", ["action", "timestamp"])

    # Create partitions for security audit (15 year retention required by Cyprus law)
    for year in range(2024, 2040):
        op.execute(f"""
            CREATE TABLE security_audit_{year} PARTITION OF security_audit
            FOR VALUES FROM ('{year}-01-01') TO ('{year + 1}-01-01')
        """)


def downgrade() -> None:
    # Drop partitioned tables
    op.execute("DROP TABLE IF EXISTS security_audit CASCADE")
    op.execute("DROP TABLE IF EXISTS note_access_log CASCADE")

    # Drop tables in reverse order
    op.drop_table("note_attachments")
    op.drop_table("note_versions")
    op.drop_table("clinical_notes")
    op.drop_table("vitals")
    op.drop_table("encounters")
    op.drop_table("patient_pii")
    op.drop_table("patients")
    op.drop_table("user_clinic_roles")
    op.drop_table("users")
    op.drop_table("clinics")

    # Drop extensions
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
