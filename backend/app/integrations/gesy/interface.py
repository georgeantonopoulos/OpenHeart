"""
Gesy Provider Interface.

Defines the abstract interface for Gesy integration.
Allows swapping between mock and real implementations.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

from app.integrations.gesy.schemas import (
    BeneficiaryStatus,
    GesyClaim,
    GesyClaimCreate,
    GesyClaimStatus,
    GesyProviderInfo,
    GesyReferral,
    GesyReferralCreate,
    GesyReferralStatus,
    GesySpecialty,
)


class IGesyProvider(ABC):
    """
    Abstract interface for Gesy (GHS) integration.

    Implementations:
    - MockGesyProvider: For development and testing
    - RealGesyProvider: For production (requires HIO enrollment)
    """

    # =========================================================================
    # Beneficiary Verification
    # =========================================================================

    @abstractmethod
    async def verify_beneficiary(
        self,
        beneficiary_id: str,
    ) -> Optional[BeneficiaryStatus]:
        """
        Verify a patient's Gesy beneficiary status.

        Args:
            beneficiary_id: The Gesy beneficiary ID

        Returns:
            BeneficiaryStatus if found and active, None otherwise
        """
        pass

    @abstractmethod
    async def verify_beneficiary_by_id_card(
        self,
        cyprus_id: str,
    ) -> Optional[BeneficiaryStatus]:
        """
        Look up beneficiary by Cyprus ID card number.

        Args:
            cyprus_id: Cyprus ID card number

        Returns:
            BeneficiaryStatus if found, None otherwise
        """
        pass

    # =========================================================================
    # Referrals
    # =========================================================================

    @abstractmethod
    async def create_referral(
        self,
        referral: GesyReferralCreate,
    ) -> GesyReferral:
        """
        Create a new specialist referral.

        Args:
            referral: Referral creation data

        Returns:
            Created GesyReferral with voucher ID

        Raises:
            GesyApiError: If creation fails
        """
        pass

    @abstractmethod
    async def get_referral(
        self,
        referral_id: str,
    ) -> Optional[GesyReferral]:
        """
        Get referral details by ID.

        Args:
            referral_id: Referral voucher ID

        Returns:
            GesyReferral if found, None otherwise
        """
        pass

    @abstractmethod
    async def update_referral_status(
        self,
        referral_id: str,
        status: GesyReferralStatus,
        notes: Optional[str] = None,
    ) -> GesyReferral:
        """
        Update referral status (e.g., mark as used).

        Args:
            referral_id: Referral voucher ID
            status: New status
            notes: Optional status notes

        Returns:
            Updated GesyReferral
        """
        pass

    @abstractmethod
    async def list_patient_referrals(
        self,
        beneficiary_id: str,
        status: Optional[GesyReferralStatus] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> list[GesyReferral]:
        """
        List referrals for a patient.

        Args:
            beneficiary_id: Patient's Gesy ID
            status: Optional status filter
            from_date: Optional start date filter
            to_date: Optional end date filter

        Returns:
            List of GesyReferral objects
        """
        pass

    # =========================================================================
    # Claims
    # =========================================================================

    @abstractmethod
    async def submit_claim(
        self,
        claim: GesyClaimCreate,
    ) -> GesyClaim:
        """
        Submit a claim for reimbursement.

        Args:
            claim: Claim submission data

        Returns:
            Submitted GesyClaim with claim ID

        Raises:
            GesyApiError: If submission fails
        """
        pass

    @abstractmethod
    async def get_claim_status(
        self,
        claim_id: str,
    ) -> Optional[GesyClaim]:
        """
        Get current status of a claim.

        Args:
            claim_id: Claim ID

        Returns:
            GesyClaim with current status, None if not found
        """
        pass

    @abstractmethod
    async def list_provider_claims(
        self,
        provider_id: str,
        status: Optional[GesyClaimStatus] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> list[GesyClaim]:
        """
        List claims for a provider.

        Args:
            provider_id: Healthcare provider Gesy ID
            status: Optional status filter
            from_date: Optional start date filter
            to_date: Optional end date filter

        Returns:
            List of GesyClaim objects
        """
        pass

    # =========================================================================
    # Provider & Reference Data
    # =========================================================================

    @abstractmethod
    async def get_provider_info(
        self,
        provider_id: str,
    ) -> Optional[GesyProviderInfo]:
        """
        Get information about a healthcare provider.

        Args:
            provider_id: Provider's Gesy ID

        Returns:
            GesyProviderInfo if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_specialties(self) -> list[GesySpecialty]:
        """
        Get list of all Gesy specialties.

        Returns:
            List of GesySpecialty objects
        """
        pass

    @abstractmethod
    async def validate_diagnosis_code(
        self,
        code: str,
    ) -> bool:
        """
        Validate an ICD-10 diagnosis code.

        Args:
            code: ICD-10 code

        Returns:
            True if valid, False otherwise
        """
        pass

    @abstractmethod
    async def validate_procedure_code(
        self,
        code: str,
    ) -> bool:
        """
        Validate a CPT procedure code.

        Args:
            code: CPT code

        Returns:
            True if valid, False otherwise
        """
        pass


class GesyApiError(Exception):
    """Exception raised for Gesy API errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}
