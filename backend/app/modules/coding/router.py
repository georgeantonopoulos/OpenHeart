"""Medical coding API router.

Provides search endpoints for ICD-10, CPT, LOINC, ATC, HIO,
and Gesy medication codes with Greek accent normalization.
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.coding.schemas import (
    ATCCodeResponse,
    CPTCodeResponse,
    GesyMedicationResponse,
    HIOServiceCodeResponse,
    ICD10CodeResponse,
    ICPC2CodeResponse,
    LOINCCodeResponse,
)
from app.modules.coding.service import CodingService

router = APIRouter(prefix="/codes", tags=["Medical Coding"])


def get_coding_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CodingService:
    return CodingService(db)


# =============================================================================
# ICD-10 Endpoints
# =============================================================================


@router.get("/icd10/search", response_model=list[ICD10CodeResponse])
async def search_icd10(
    q: str = Query(..., min_length=2, description="Search term"),
    limit: int = Query(20, ge=1, le=100),
    service: CodingService = Depends(get_coding_service),
) -> list[ICD10CodeResponse]:
    """Search ICD-10 diagnosis codes by description or code prefix."""
    results = await service.search_icd10(q, limit)
    return [ICD10CodeResponse.model_validate(r) for r in results]


@router.get("/icd10/{code}", response_model=ICD10CodeResponse)
async def get_icd10(
    code: str,
    service: CodingService = Depends(get_coding_service),
) -> ICD10CodeResponse:
    """Get a specific ICD-10 code."""
    result = await service.get_icd10(code)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ICD-10 code '{code}' not found",
        )
    return ICD10CodeResponse.model_validate(result)


# =============================================================================
# ICPC-2 Endpoints
# =============================================================================


@router.get("/icpc2/search", response_model=list[ICPC2CodeResponse])
async def search_icpc2(
    q: str = Query(..., min_length=2, description="Search term"),
    limit: int = Query(20, ge=1, le=100),
    service: CodingService = Depends(get_coding_service),
) -> list[ICPC2CodeResponse]:
    """Search ICPC-2 primary care codes."""
    results = await service.search_icpc2(q, limit)
    return [ICPC2CodeResponse.model_validate(r) for r in results]


# =============================================================================
# CPT Endpoints
# =============================================================================


@router.get("/cpt/search", response_model=list[CPTCodeResponse])
async def search_cpt(
    q: str = Query(..., min_length=2, description="Search term"),
    limit: int = Query(20, ge=1, le=100),
    service: CodingService = Depends(get_coding_service),
) -> list[CPTCodeResponse]:
    """Search CPT procedure codes."""
    results = await service.search_cpt(q, limit)
    return [CPTCodeResponse.model_validate(r) for r in results]


@router.get("/cpt/{code}", response_model=CPTCodeResponse)
async def get_cpt(
    code: str,
    service: CodingService = Depends(get_coding_service),
) -> CPTCodeResponse:
    """Get a specific CPT code."""
    result = await service.get_cpt(code)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CPT code '{code}' not found",
        )
    return CPTCodeResponse.model_validate(result)


# =============================================================================
# HIO Service Codes
# =============================================================================


@router.get("/hio/search", response_model=list[HIOServiceCodeResponse])
async def search_hio(
    q: str = Query(..., min_length=2, description="Search term"),
    specialty: Optional[str] = Query(None, description="Filter by specialty code"),
    limit: int = Query(20, ge=1, le=100),
    service: CodingService = Depends(get_coding_service),
) -> list[HIOServiceCodeResponse]:
    """Search HIO service codes with optional specialty filter."""
    results = await service.search_hio(q, specialty, limit)
    return [HIOServiceCodeResponse.model_validate(r) for r in results]


# =============================================================================
# LOINC Endpoints
# =============================================================================


@router.get("/loinc/search", response_model=list[LOINCCodeResponse])
async def search_loinc(
    q: str = Query(..., min_length=2, description="Search term"),
    limit: int = Query(20, ge=1, le=100),
    service: CodingService = Depends(get_coding_service),
) -> list[LOINCCodeResponse]:
    """Search LOINC lab and observation codes."""
    results = await service.search_loinc(q, limit)
    return [LOINCCodeResponse.model_validate(r) for r in results]


# =============================================================================
# ATC Endpoints
# =============================================================================


@router.get("/atc/search", response_model=list[ATCCodeResponse])
async def search_atc(
    q: str = Query(..., min_length=2, description="Search term"),
    limit: int = Query(20, ge=1, le=100),
    service: CodingService = Depends(get_coding_service),
) -> list[ATCCodeResponse]:
    """Search ATC medication classification codes."""
    results = await service.search_atc(q, limit)
    return [ATCCodeResponse.model_validate(r) for r in results]


# =============================================================================
# Gesy Medications
# =============================================================================


@router.get("/medications/search", response_model=list[GesyMedicationResponse])
async def search_medications(
    q: str = Query(..., min_length=2, description="Brand name, generic name, or ATC code"),
    limit: int = Query(20, ge=1, le=100),
    service: CodingService = Depends(get_coding_service),
) -> list[GesyMedicationResponse]:
    """Search Gesy medications by brand name, generic name, or ATC code."""
    results = await service.search_medications(q, limit)
    return [GesyMedicationResponse.model_validate(r) for r in results]


@router.get("/medications/{hio_product_id}", response_model=GesyMedicationResponse)
async def get_medication(
    hio_product_id: str,
    service: CodingService = Depends(get_coding_service),
) -> GesyMedicationResponse:
    """Get a specific medication by HIO product ID."""
    result = await service.get_medication(hio_product_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medication '{hio_product_id}' not found",
        )
    return GesyMedicationResponse.model_validate(result)
