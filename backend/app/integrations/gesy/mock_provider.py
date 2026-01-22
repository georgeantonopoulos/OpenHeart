"""
Mock Gesy Provider Implementation.

Provides a mock implementation of IGesyProvider for development and testing.
Simulates Gesy API responses with realistic data.
"""

import uuid
from datetime import date, datetime, timedelta
from typing import Optional

from app.integrations.gesy.interface import GesyApiError, IGesyProvider
from app.integrations.gesy.schemas import (
    BeneficiaryStatus,
    BeneficiaryType,
    GesyClaim,
    GesyClaimCreate,
    GesyClaimLineItem,
    GesyClaimStatus,
    GesyProviderInfo,
    GesyReferral,
    GesyReferralCreate,
    GesyReferralStatus,
    GesySpecialty,
)


class MockGesyProvider(IGesyProvider):
    """
    Mock implementation of Gesy provider for development.

    Stores data in memory and simulates API behavior.
    """

    def __init__(self) -> None:
        # In-memory storage
        self._beneficiaries: dict[str, BeneficiaryStatus] = {}
        self._referrals: dict[str, GesyReferral] = {}
        self._claims: dict[str, GesyClaim] = {}
        self._providers: dict[str, GesyProviderInfo] = {}

        # Initialize with sample data
        self._init_sample_data()

    def _init_sample_data(self) -> None:
        """Initialize with sample beneficiaries and providers."""
        # Sample beneficiaries
        self._beneficiaries["GHS100001"] = BeneficiaryStatus(
            beneficiary_id="GHS100001",
            is_active=True,
            beneficiary_type=BeneficiaryType.CITIZEN,
            registration_date=date(2019, 6, 1),
            primary_doctor_id="PD001",
            coverage_category="A",
            verified_at=datetime.utcnow(),
        )
        self._beneficiaries["GHS100002"] = BeneficiaryStatus(
            beneficiary_id="GHS100002",
            is_active=True,
            beneficiary_type=BeneficiaryType.EU_NATIONAL,
            registration_date=date(2020, 3, 15),
            primary_doctor_id="PD002",
            coverage_category="A",
            verified_at=datetime.utcnow(),
        )
        self._beneficiaries["GHS100003"] = BeneficiaryStatus(
            beneficiary_id="GHS100003",
            is_active=False,  # Inactive beneficiary
            beneficiary_type=BeneficiaryType.CITIZEN,
            registration_date=date(2019, 6, 1),
            expiry_date=date(2023, 12, 31),
            coverage_category="B",
            verified_at=datetime.utcnow(),
        )

        # Sample providers
        self._providers["CARD001"] = GesyProviderInfo(
            provider_id="CARD001",
            name="Cyprus Heart Center",
            provider_type="specialist",
            specialty_codes=["CAR"],
            address="123 Cardiac Ave, Nicosia",
            phone="+35722123456",
            email="info@cyprusheartcenter.cy",
        )
        self._providers["PD001"] = GesyProviderInfo(
            provider_id="PD001",
            name="Dr. Yiannis Papadopoulos",
            provider_type="personal_doctor",
            specialty_codes=["GP"],
            address="45 Health St, Limassol",
            phone="+35725654321",
        )

    # =========================================================================
    # Beneficiary Verification
    # =========================================================================

    async def verify_beneficiary(
        self,
        beneficiary_id: str,
    ) -> Optional[BeneficiaryStatus]:
        """Verify beneficiary by Gesy ID."""
        beneficiary = self._beneficiaries.get(beneficiary_id)
        if beneficiary:
            # Update verification timestamp
            beneficiary.verified_at = datetime.utcnow()
            return beneficiary
        return None

    async def verify_beneficiary_by_id_card(
        self,
        cyprus_id: str,
    ) -> Optional[BeneficiaryStatus]:
        """Look up beneficiary by Cyprus ID (mock mapping)."""
        # Mock mapping: assume ID cards map to beneficiary IDs
        mock_mapping = {
            "1234567": "GHS100001",
            "7654321": "GHS100002",
            "1111111": "GHS100003",
        }
        beneficiary_id = mock_mapping.get(cyprus_id)
        if beneficiary_id:
            return await self.verify_beneficiary(beneficiary_id)
        return None

    # =========================================================================
    # Referrals
    # =========================================================================

    async def create_referral(
        self,
        referral: GesyReferralCreate,
    ) -> GesyReferral:
        """Create a new referral."""
        # Verify beneficiary exists and is active
        beneficiary = await self.verify_beneficiary(referral.beneficiary_id)
        if not beneficiary or not beneficiary.is_active:
            raise GesyApiError(
                "Beneficiary not found or inactive",
                error_code="BEN001",
            )

        # Generate referral ID
        referral_id = f"REF{uuid.uuid4().hex[:8].upper()}"

        # Create referral
        today = date.today()
        new_referral = GesyReferral(
            referral_id=referral_id,
            beneficiary_id=referral.beneficiary_id,
            referring_doctor_id=referral.referring_doctor_id,
            specialty_code=referral.specialty_code,
            diagnosis_code=referral.diagnosis_code,
            diagnosis_description=referral.diagnosis_description,
            status=GesyReferralStatus.APPROVED,  # Auto-approve in mock
            urgency=referral.urgency,
            issued_date=today,
            valid_from=today,
            valid_until=today + timedelta(days=30),  # 30-day validity
            clinical_notes=referral.clinical_notes,
            requested_procedures=referral.requested_procedures,
            approved_procedures=referral.requested_procedures,  # Auto-approve all
        )

        self._referrals[referral_id] = new_referral
        return new_referral

    async def get_referral(
        self,
        referral_id: str,
    ) -> Optional[GesyReferral]:
        """Get referral by ID."""
        return self._referrals.get(referral_id)

    async def update_referral_status(
        self,
        referral_id: str,
        status: GesyReferralStatus,
        notes: Optional[str] = None,
    ) -> GesyReferral:
        """Update referral status."""
        referral = self._referrals.get(referral_id)
        if not referral:
            raise GesyApiError(
                f"Referral {referral_id} not found",
                error_code="REF001",
            )

        referral.status = status
        if status == GesyReferralStatus.USED:
            referral.used_date = date.today()

        return referral

    async def list_patient_referrals(
        self,
        beneficiary_id: str,
        status: Optional[GesyReferralStatus] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> list[GesyReferral]:
        """List referrals for a patient."""
        results = []
        for referral in self._referrals.values():
            if referral.beneficiary_id != beneficiary_id:
                continue
            if status and referral.status != status:
                continue
            if from_date and referral.issued_date < from_date:
                continue
            if to_date and referral.issued_date > to_date:
                continue
            results.append(referral)
        return results

    # =========================================================================
    # Claims
    # =========================================================================

    async def submit_claim(
        self,
        claim: GesyClaimCreate,
    ) -> GesyClaim:
        """Submit a new claim."""
        # Verify referral exists and is valid
        referral = await self.get_referral(claim.referral_id)
        if not referral:
            raise GesyApiError(
                f"Referral {claim.referral_id} not found",
                error_code="CLM001",
            )
        if referral.status not in [GesyReferralStatus.APPROVED, GesyReferralStatus.USED]:
            raise GesyApiError(
                f"Referral {claim.referral_id} is not valid for claims",
                error_code="CLM002",
            )

        # Calculate totals
        total_claimed = sum(item.total_price for item in claim.line_items)

        # Generate claim ID
        claim_id = f"CLM{uuid.uuid4().hex[:8].upper()}"

        # Create claim (auto-approve in mock)
        approved_items = []
        total_approved = 0.0
        for item in claim.line_items:
            approved_item = GesyClaimLineItem(
                line_number=item.line_number,
                procedure_code=item.procedure_code,
                procedure_description=item.procedure_description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
                diagnosis_codes=item.diagnosis_codes,
                approved=True,
                approved_amount=item.total_price,
            )
            approved_items.append(approved_item)
            total_approved += item.total_price

        new_claim = GesyClaim(
            claim_id=claim_id,
            referral_id=claim.referral_id,
            provider_id=claim.provider_id,
            beneficiary_id=claim.beneficiary_id,
            service_date=claim.service_date,
            encounter_type=claim.encounter_type,
            diagnosis_codes=claim.diagnosis_codes,
            primary_diagnosis_code=claim.primary_diagnosis_code,
            line_items=approved_items,
            total_claimed=total_claimed,
            total_approved=total_approved,
            status=GesyClaimStatus.APPROVED,
            submitted_at=datetime.utcnow(),
            reviewed_at=datetime.utcnow(),
        )

        self._claims[claim_id] = new_claim

        # Mark referral as used
        await self.update_referral_status(
            claim.referral_id,
            GesyReferralStatus.USED,
        )

        return new_claim

    async def get_claim_status(
        self,
        claim_id: str,
    ) -> Optional[GesyClaim]:
        """Get claim by ID."""
        return self._claims.get(claim_id)

    async def list_provider_claims(
        self,
        provider_id: str,
        status: Optional[GesyClaimStatus] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> list[GesyClaim]:
        """List claims for a provider."""
        results = []
        for claim in self._claims.values():
            if claim.provider_id != provider_id:
                continue
            if status and claim.status != status:
                continue
            if from_date and claim.service_date < from_date:
                continue
            if to_date and claim.service_date > to_date:
                continue
            results.append(claim)
        return results

    # =========================================================================
    # Provider & Reference Data
    # =========================================================================

    async def get_provider_info(
        self,
        provider_id: str,
    ) -> Optional[GesyProviderInfo]:
        """Get provider information."""
        return self._providers.get(provider_id)

    async def list_specialties(self) -> list[GesySpecialty]:
        """Get list of Gesy specialties."""
        return [
            GesySpecialty(
                code="CAR",
                name_en="Cardiology",
                name_el="Καρδιολογία",
                category="medical",
                requires_referral=True,
            ),
            GesySpecialty(
                code="CTS",
                name_en="Cardiothoracic Surgery",
                name_el="Καρδιοθωρακοχειρουργική",
                category="surgical",
                requires_referral=True,
            ),
            GesySpecialty(
                code="INT",
                name_en="Internal Medicine",
                name_el="Παθολογία",
                category="medical",
                requires_referral=True,
            ),
            GesySpecialty(
                code="GP",
                name_en="General Practice",
                name_el="Γενική Ιατρική",
                category="medical",
                requires_referral=False,
            ),
            GesySpecialty(
                code="RAD",
                name_en="Radiology",
                name_el="Ακτινολογία",
                category="diagnostic",
                requires_referral=True,
            ),
            GesySpecialty(
                code="NUC",
                name_en="Nuclear Medicine",
                name_el="Πυρηνική Ιατρική",
                category="diagnostic",
                requires_referral=True,
            ),
        ]

    async def validate_diagnosis_code(
        self,
        code: str,
    ) -> bool:
        """Validate ICD-10 code (mock - accepts common cardiology codes)."""
        valid_codes = {
            # Ischemic heart disease
            "I20", "I20.0", "I20.1", "I20.8", "I20.9",  # Angina
            "I21", "I21.0", "I21.1", "I21.2", "I21.3", "I21.4", "I21.9",  # AMI
            "I25", "I25.0", "I25.1", "I25.2", "I25.5", "I25.9",  # Chronic IHD
            # Hypertension
            "I10", "I11", "I11.0", "I11.9", "I12", "I13",
            # Heart failure
            "I50", "I50.0", "I50.1", "I50.9",
            # Arrhythmias
            "I48", "I48.0", "I48.1", "I48.2", "I48.9",  # AFib
            "I49", "I49.0", "I49.1", "I49.9",  # Other arrhythmias
            # Valvular
            "I34", "I35", "I36", "I37",
        }
        # Accept code or any code that starts with a valid prefix
        return code in valid_codes or any(code.startswith(c) for c in valid_codes)

    async def validate_procedure_code(
        self,
        code: str,
    ) -> bool:
        """Validate CPT code (mock - accepts common cardiology codes)."""
        valid_codes = {
            # ECG
            "93000", "93005", "93010",
            # Echocardiography
            "93303", "93304", "93306", "93307", "93308", "93312", "93315",
            # Stress testing
            "93015", "93016", "93017", "93018",
            # Holter
            "93224", "93225", "93226", "93227",
            # Cardiac catheterization
            "93451", "93452", "93453", "93454", "93455", "93456", "93457", "93458",
            # PCI
            "92920", "92921", "92924", "92925", "92928", "92929",
            # Pacemaker
            "33206", "33207", "33208", "33210", "33211",
            # Consultation
            "99201", "99202", "99203", "99204", "99205",
            "99211", "99212", "99213", "99214", "99215",
        }
        return code in valid_codes
