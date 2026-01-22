"""Medical coding search service with Greek accent normalization.

Uses PostgreSQL unaccent extension to handle Greek tonos:
- "Καρδιά" (with accent) matches "καρδια" (without accent)
- All searches are accent-insensitive via func.unaccent()
"""

from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.coding.models import (
    ATCCode,
    CPTCode,
    GesyMedication,
    HIOServiceCode,
    ICD10Code,
    ICPC2Code,
    LOINCCode,
)


class CodingService:
    """Service for searching medical coding tables."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def search_icd10(
        self, query: str, limit: int = 20
    ) -> list[ICD10Code]:
        """Search ICD-10 with Greek accent normalization."""
        stmt = (
            select(ICD10Code)
            .where(
                ICD10Code.is_active.is_(True),
                or_(
                    func.unaccent(ICD10Code.description_en).ilike(
                        func.unaccent(f"%{query}%")
                    ),
                    func.unaccent(ICD10Code.description_el).ilike(
                        func.unaccent(f"%{query}%")
                    ),
                    ICD10Code.code.ilike(f"{query}%"),
                ),
            )
            .order_by(ICD10Code.code)
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_icd10(self, code: str) -> Optional[ICD10Code]:
        """Get a specific ICD-10 code."""
        stmt = select(ICD10Code).where(ICD10Code.code == code)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def search_icpc2(
        self, query: str, limit: int = 20
    ) -> list[ICPC2Code]:
        """Search ICPC-2 codes."""
        stmt = (
            select(ICPC2Code)
            .where(
                ICPC2Code.is_active.is_(True),
                or_(
                    func.unaccent(ICPC2Code.description_en).ilike(
                        func.unaccent(f"%{query}%")
                    ),
                    func.unaccent(ICPC2Code.description_el).ilike(
                        func.unaccent(f"%{query}%")
                    ),
                    ICPC2Code.code.ilike(f"{query}%"),
                ),
            )
            .order_by(ICPC2Code.code)
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def search_cpt(
        self, query: str, limit: int = 20
    ) -> list[CPTCode]:
        """Search CPT procedure codes."""
        stmt = (
            select(CPTCode)
            .where(
                CPTCode.is_active.is_(True),
                or_(
                    func.unaccent(CPTCode.description).ilike(
                        func.unaccent(f"%{query}%")
                    ),
                    CPTCode.code.ilike(f"{query}%"),
                ),
            )
            .order_by(CPTCode.code)
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_cpt(self, code: str) -> Optional[CPTCode]:
        """Get a specific CPT code."""
        stmt = select(CPTCode).where(CPTCode.code == code)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def search_hio(
        self,
        query: str,
        specialty: Optional[str] = None,
        limit: int = 20,
    ) -> list[HIOServiceCode]:
        """Search HIO service codes with optional specialty filter."""
        conditions = [
            HIOServiceCode.is_active.is_(True),
            or_(
                func.unaccent(HIOServiceCode.description_en).ilike(
                    func.unaccent(f"%{query}%")
                ),
                func.unaccent(HIOServiceCode.description_el).ilike(
                    func.unaccent(f"%{query}%")
                ),
                HIOServiceCode.code.ilike(f"{query}%"),
            ),
        ]
        if specialty:
            conditions.append(HIOServiceCode.specialty_code == specialty)

        stmt = (
            select(HIOServiceCode)
            .where(*conditions)
            .order_by(HIOServiceCode.code)
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def search_loinc(
        self, query: str, limit: int = 20
    ) -> list[LOINCCode]:
        """Search LOINC codes."""
        stmt = (
            select(LOINCCode)
            .where(
                LOINCCode.is_active.is_(True),
                or_(
                    LOINCCode.long_name.ilike(f"%{query}%"),
                    LOINCCode.short_name.ilike(f"%{query}%"),
                    LOINCCode.code.ilike(f"{query}%"),
                ),
            )
            .order_by(LOINCCode.code)
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def search_atc(
        self, query: str, limit: int = 20
    ) -> list[ATCCode]:
        """Search ATC medication classification codes."""
        stmt = (
            select(ATCCode)
            .where(
                ATCCode.is_active.is_(True),
                or_(
                    ATCCode.name.ilike(f"%{query}%"),
                    ATCCode.code.ilike(f"{query}%"),
                ),
            )
            .order_by(ATCCode.code)
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def search_medications(
        self, query: str, limit: int = 20
    ) -> list[GesyMedication]:
        """Search Gesy medications by brand name, generic name, or ATC code."""
        stmt = (
            select(GesyMedication)
            .where(
                GesyMedication.is_active.is_(True),
                or_(
                    func.unaccent(GesyMedication.brand_name).ilike(
                        func.unaccent(f"%{query}%")
                    ),
                    func.unaccent(GesyMedication.generic_name).ilike(
                        func.unaccent(f"%{query}%")
                    ),
                    GesyMedication.atc_code.ilike(f"{query}%"),
                    GesyMedication.hio_product_id.ilike(f"{query}%"),
                ),
            )
            .order_by(GesyMedication.brand_name)
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_medication(
        self, hio_product_id: str
    ) -> Optional[GesyMedication]:
        """Get a specific medication by HIO product ID."""
        stmt = select(GesyMedication).where(
            GesyMedication.hio_product_id == hio_product_id
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()
