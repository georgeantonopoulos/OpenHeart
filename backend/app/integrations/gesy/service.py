"""
Gesy Integration Service.

Wraps IGesyProvider for dependency injection and provides
business logic for beneficiary, referral, and claim management.
"""

from datetime import date
from functools import lru_cache
from typing import Optional

from app.integrations.gesy.interface import GesyApiError, IGesyProvider
from app.integrations.gesy.mock_provider import MockGesyProvider
from app.integrations.gesy.schemas import (
    BeneficiaryStatus,
    GesyClaim,
    GesyClaimCreate,
    GesyClaimStatus,
    GesyReferral,
    GesyReferralCreate,
    GesyReferralStatus,
    GesySpecialty,
)


class GesyService:
    """Service layer for Gesy GHS operations."""

    def __init__(self, provider: IGesyProvider) -> None:
        self._provider = provider

    # =========================================================================
    # Beneficiary Verification
    # =========================================================================

    async def verify_beneficiary(
        self,
        beneficiary_id: str,
    ) -> Optional[BeneficiaryStatus]:
        """Verify beneficiary by Gesy ID."""
        return await self._provider.verify_beneficiary(beneficiary_id)

    async def verify_beneficiary_by_id_card(
        self,
        cyprus_id: str,
    ) -> Optional[BeneficiaryStatus]:
        """Look up beneficiary by Cyprus ID card number."""
        return await self._provider.verify_beneficiary_by_id_card(cyprus_id)

    # =========================================================================
    # Referrals
    # =========================================================================

    async def create_referral(
        self,
        data: GesyReferralCreate,
    ) -> GesyReferral:
        """Create a new specialist referral."""
        return await self._provider.create_referral(data)

    async def get_referral(
        self,
        referral_id: str,
    ) -> Optional[GesyReferral]:
        """Get referral by voucher ID."""
        return await self._provider.get_referral(referral_id)

    async def close_referral(
        self,
        referral_id: str,
        summary_notes: Optional[str] = None,
    ) -> GesyReferral:
        """Close a referral with summary notes after completing service."""
        return await self._provider.update_referral_status(
            referral_id, GesyReferralStatus.USED, summary_notes
        )

    async def list_patient_referrals(
        self,
        beneficiary_id: str,
        status: Optional[GesyReferralStatus] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> list[GesyReferral]:
        """List referrals for a patient with optional filters."""
        return await self._provider.list_patient_referrals(
            beneficiary_id, status, from_date, to_date
        )

    # =========================================================================
    # Claims
    # =========================================================================

    async def submit_claim(
        self,
        data: GesyClaimCreate,
    ) -> GesyClaim:
        """Submit a claim for reimbursement."""
        return await self._provider.submit_claim(data)

    async def get_claim(
        self,
        claim_id: str,
    ) -> Optional[GesyClaim]:
        """Get claim details and status."""
        return await self._provider.get_claim_status(claim_id)

    async def list_provider_claims(
        self,
        provider_id: str,
        status: Optional[GesyClaimStatus] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> list[GesyClaim]:
        """List claims for a provider."""
        return await self._provider.list_provider_claims(
            provider_id, status, from_date, to_date
        )

    # =========================================================================
    # Reference Data
    # =========================================================================

    async def list_specialties(self) -> list[GesySpecialty]:
        """Get list of Gesy specialties."""
        return await self._provider.list_specialties()

    async def validate_diagnosis_code(self, code: str) -> bool:
        """Validate an ICD-10 diagnosis code."""
        return await self._provider.validate_diagnosis_code(code)

    async def validate_procedure_code(self, code: str) -> bool:
        """Validate a CPT procedure code."""
        return await self._provider.validate_procedure_code(code)


@lru_cache()
def _get_gesy_provider() -> IGesyProvider:
    """Get singleton Gesy provider instance (mock for development)."""
    return MockGesyProvider()


def get_gesy_service() -> GesyService:
    """FastAPI dependency for GesyService."""
    return GesyService(_get_gesy_provider())
