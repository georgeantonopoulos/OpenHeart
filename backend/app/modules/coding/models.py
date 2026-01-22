"""SQLAlchemy models for medical coding tables."""

from sqlalchemy import Boolean, Column, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase

from app.db.base import Base


class ICD10Code(Base):
    __tablename__ = "icd10_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    description_en = Column(Text, nullable=False)
    description_el = Column(Text, nullable=True)
    chapter = Column(String(5), nullable=True)
    category = Column(String(100), nullable=True)
    is_billable = Column(Boolean, server_default="true")
    is_active = Column(Boolean, server_default="true")


class ICPC2Code(Base):
    __tablename__ = "icpc2_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    description_en = Column(Text, nullable=False)
    description_el = Column(Text, nullable=True)
    component = Column(String(100), nullable=True)
    chapter = Column(String(5), nullable=True)
    is_active = Column(Boolean, server_default="true")


class LOINCCode(Base):
    __tablename__ = "loinc_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    long_name = Column(Text, nullable=False)
    short_name = Column(String(255), nullable=True)
    component = Column(String(255), nullable=True)
    class_type = Column(String(50), nullable=True)
    is_active = Column(Boolean, server_default="true")


class ATCCode(Base):
    __tablename__ = "atc_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    level = Column(Integer, nullable=False)
    parent_code = Column(String(10), nullable=True)
    ddd = Column(String(50), nullable=True)
    is_active = Column(Boolean, server_default="true")


class CPTCode(Base):
    __tablename__ = "cpt_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    relative_value = Column(Float, nullable=True)
    is_active = Column(Boolean, server_default="true")


class HIOServiceCode(Base):
    __tablename__ = "hio_service_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    description_en = Column(Text, nullable=False)
    description_el = Column(Text, nullable=True)
    service_type = Column(String(50), nullable=True)
    specialty_code = Column(String(10), nullable=True)
    base_price_eur = Column(Float, nullable=True)
    is_active = Column(Boolean, server_default="true")


class GesyMedication(Base):
    __tablename__ = "gesy_medications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    hio_product_id = Column(String(50), unique=True, nullable=False)
    atc_code = Column(String(10), nullable=False, index=True)
    brand_name = Column(String(255), nullable=False)
    generic_name = Column(String(255), nullable=True)
    strength = Column(String(100), nullable=True)
    form = Column(String(100), nullable=True)
    pack_size = Column(Integer, nullable=True)
    manufacturer = Column(String(255), nullable=True)
    price_eur = Column(Float, nullable=True)
    requires_pre_auth = Column(Boolean, server_default="false")
    is_active = Column(Boolean, server_default="true")
