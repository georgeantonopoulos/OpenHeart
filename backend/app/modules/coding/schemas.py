"""Pydantic schemas for medical coding API responses."""

from pydantic import BaseModel
from typing import Optional


class ICD10CodeResponse(BaseModel):
    code: str
    description_en: str
    description_el: Optional[str] = None
    chapter: Optional[str] = None
    category: Optional[str] = None
    is_billable: bool = True

    model_config = {"from_attributes": True}


class ICPC2CodeResponse(BaseModel):
    code: str
    description_en: str
    description_el: Optional[str] = None
    component: Optional[str] = None
    chapter: Optional[str] = None

    model_config = {"from_attributes": True}


class LOINCCodeResponse(BaseModel):
    code: str
    long_name: str
    short_name: Optional[str] = None
    component: Optional[str] = None
    class_type: Optional[str] = None

    model_config = {"from_attributes": True}


class ATCCodeResponse(BaseModel):
    code: str
    name: str
    level: int
    parent_code: Optional[str] = None
    ddd: Optional[str] = None

    model_config = {"from_attributes": True}


class CPTCodeResponse(BaseModel):
    code: str
    description: str
    category: Optional[str] = None
    relative_value: Optional[float] = None

    model_config = {"from_attributes": True}


class HIOServiceCodeResponse(BaseModel):
    code: str
    description_en: str
    description_el: Optional[str] = None
    service_type: Optional[str] = None
    specialty_code: Optional[str] = None
    base_price_eur: Optional[float] = None

    model_config = {"from_attributes": True}


class GesyMedicationResponse(BaseModel):
    hio_product_id: str
    atc_code: str
    brand_name: str
    generic_name: Optional[str] = None
    strength: Optional[str] = None
    form: Optional[str] = None
    pack_size: Optional[int] = None
    manufacturer: Optional[str] = None
    price_eur: Optional[float] = None
    requires_pre_auth: bool = False

    model_config = {"from_attributes": True}
