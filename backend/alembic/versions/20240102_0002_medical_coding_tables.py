"""Medical coding tables for ICD-10, CPT, LOINC, ATC, HIO, and Gesy medications.

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-02 00:00:00.000000

This migration creates:
- PostgreSQL unaccent extension for Greek text search
- ICD-10 diagnosis codes
- ICPC-2 primary care codes
- LOINC lab/observation codes
- ATC medication classification codes
- CPT procedure codes
- HIO service codes (Cyprus-specific)
- Gesy medications (HIO product registry for e-Prescriptions)
- Full-text search indexes with unaccent for Greek accent normalization
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # Extensions for Greek text search
    # =========================================================================
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")

    # =========================================================================
    # ICD-10 Diagnosis Codes
    # =========================================================================
    op.create_table(
        "icd10_codes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(10), nullable=False, unique=True),
        sa.Column("description_en", sa.Text(), nullable=False),
        sa.Column("description_el", sa.Text(), nullable=True),
        sa.Column("chapter", sa.String(5), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("is_billable", sa.Boolean(), server_default="true"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.PrimaryKeyConstraint("id"),
        comment="ICD-10 diagnosis codes with Greek translations",
    )
    op.create_index("idx_icd10_code", "icd10_codes", ["code"])
    op.create_index("idx_icd10_chapter", "icd10_codes", ["chapter"])

    # =========================================================================
    # ICPC-2 Primary Care Codes
    # =========================================================================
    op.create_table(
        "icpc2_codes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(10), nullable=False, unique=True),
        sa.Column("description_en", sa.Text(), nullable=False),
        sa.Column("description_el", sa.Text(), nullable=True),
        sa.Column("component", sa.String(100), nullable=True),
        sa.Column("chapter", sa.String(5), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.PrimaryKeyConstraint("id"),
        comment="ICPC-2 primary care classification codes",
    )
    op.create_index("idx_icpc2_code", "icpc2_codes", ["code"])

    # =========================================================================
    # LOINC Codes
    # =========================================================================
    op.create_table(
        "loinc_codes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(20), nullable=False, unique=True),
        sa.Column("long_name", sa.Text(), nullable=False),
        sa.Column("short_name", sa.String(255), nullable=True),
        sa.Column("component", sa.String(255), nullable=True),
        sa.Column("class_type", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.PrimaryKeyConstraint("id"),
        comment="LOINC lab and observation codes",
    )
    op.create_index("idx_loinc_code", "loinc_codes", ["code"])
    op.create_index("idx_loinc_class", "loinc_codes", ["class_type"])

    # =========================================================================
    # ATC Medication Codes
    # =========================================================================
    op.create_table(
        "atc_codes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(10), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("parent_code", sa.String(10), nullable=True),
        sa.Column("ddd", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.PrimaryKeyConstraint("id"),
        comment="ATC anatomical therapeutic chemical classification",
    )
    op.create_index("idx_atc_code", "atc_codes", ["code"])
    op.create_index("idx_atc_parent", "atc_codes", ["parent_code"])
    op.create_index("idx_atc_level", "atc_codes", ["level"])

    # =========================================================================
    # CPT Procedure Codes
    # =========================================================================
    op.create_table(
        "cpt_codes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(10), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("relative_value", sa.Float(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.PrimaryKeyConstraint("id"),
        comment="CPT procedure codes for billing",
    )
    op.create_index("idx_cpt_code", "cpt_codes", ["code"])
    op.create_index("idx_cpt_category", "cpt_codes", ["category"])

    # =========================================================================
    # HIO Service Codes (Cyprus-specific)
    # =========================================================================
    op.create_table(
        "hio_service_codes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(20), nullable=False, unique=True),
        sa.Column("description_en", sa.Text(), nullable=False),
        sa.Column("description_el", sa.Text(), nullable=True),
        sa.Column("service_type", sa.String(50), nullable=True),
        sa.Column("specialty_code", sa.String(10), nullable=True),
        sa.Column("base_price_eur", sa.Float(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.PrimaryKeyConstraint("id"),
        comment="Cyprus HIO specific service codes for Gesy billing",
    )
    op.create_index("idx_hio_code", "hio_service_codes", ["code"])
    op.create_index("idx_hio_specialty", "hio_service_codes", ["specialty_code"])
    op.create_index("idx_hio_type", "hio_service_codes", ["service_type"])
    
    # Create immutable wrapper for unaccent to use in indexes
    op.execute("""
        CREATE OR REPLACE FUNCTION public.immutable_unaccent(text)
          RETURNS text AS
        $func$
        SELECT public.unaccent($1)
        $func$ LANGUAGE sql IMMUTABLE;
    """)

    # =========================================================================
    # Gesy Medications (HIO Product Registry)
    # =========================================================================
    op.create_table(
        "gesy_medications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("hio_product_id", sa.String(50), unique=True, nullable=False),
        sa.Column("atc_code", sa.String(10), nullable=False),
        sa.Column("brand_name", sa.String(255), nullable=False),
        sa.Column("generic_name", sa.String(255), nullable=True),
        sa.Column("strength", sa.String(100), nullable=True),
        sa.Column("form", sa.String(100), nullable=True),
        sa.Column("pack_size", sa.Integer(), nullable=True),
        sa.Column("manufacturer", sa.String(255), nullable=True),
        sa.Column("price_eur", sa.Float(), nullable=True),
        sa.Column("requires_pre_auth", sa.Boolean(), server_default="false"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.PrimaryKeyConstraint("id"),
        comment="HIO Gesy pharmaceutical products for e-Prescriptions",
    )
    op.create_index("idx_gesy_med_hio_id", "gesy_medications", ["hio_product_id"])
    op.create_index("idx_gesy_med_atc", "gesy_medications", ["atc_code"])
    op.create_index("idx_gesy_med_brand", "gesy_medications", ["brand_name"])

    # =========================================================================
    # Full-text search indexes with unaccent for Greek
    # =========================================================================
    op.execute("""
        CREATE INDEX idx_icd10_description_fts
        ON icd10_codes
        USING GIN (to_tsvector('simple', immutable_unaccent(description_en) || ' ' || coalesce(immutable_unaccent(description_el), '')))
    """)

    op.execute("""
        CREATE INDEX idx_cpt_description_fts
        ON cpt_codes
        USING GIN (to_tsvector('simple', immutable_unaccent(description)))
    """)

    op.execute("""
        CREATE INDEX idx_hio_description_fts
        ON hio_service_codes
        USING GIN (to_tsvector('simple', immutable_unaccent(description_en) || ' ' || coalesce(immutable_unaccent(description_el), '')))
    """)

    op.execute("""
        CREATE INDEX idx_gesy_med_name_fts
        ON gesy_medications
        USING GIN (to_tsvector('simple', immutable_unaccent(brand_name) || ' ' || coalesce(immutable_unaccent(generic_name), '')))
    """)


def downgrade() -> None:
    op.drop_table("gesy_medications")
    op.drop_table("hio_service_codes")
    op.drop_table("cpt_codes")
    op.drop_table("atc_codes")
    op.drop_table("loinc_codes")
    op.drop_table("icpc2_codes")
    op.drop_table("icd10_codes")
    op.execute("DROP EXTENSION IF EXISTS unaccent;")
