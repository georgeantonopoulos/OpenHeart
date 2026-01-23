"""
Patient Service Layer.

Handles business logic for patient management including:
- CRUD operations with PII encryption
- Full-text search across names and MRN
- Cyprus-specific identifier handling
- GDPR-compliant data access
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.encryption import (
    decrypt_pii,
    decrypt_pii_optional,
    encrypt_pii,
    encrypt_pii_optional,
    hash_identifier,
    mask_pii,
)
from app.db.session import set_tenant_context
from app.modules.patient.models import (
    ErasureRequestStatus,
    GDPRErasureRequest,
    Patient,
    PatientPII,
    PatientStatus,
)
from app.modules.patient.schemas import (
    Address,
    EmergencyContact,
    ErasureRequestCreate,
    ErasureRequestEvaluate,
    ErasureRequestResponse,
    PatientCreate,
    PatientResponse,
    PatientSearchQuery,
    PatientUpdate,
)

logger = logging.getLogger(__name__)


class PatientService:
    """Service for managing patients with encrypted PII."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ========================================================================
    # MRN Generation
    # ========================================================================

    async def _generate_mrn(self, clinic_id: int) -> str:
        """
        Generate a unique Medical Record Number.

        Format: {clinic_id}-{year}-{sequential}
        Example: 1-2026-00001
        """
        year = datetime.now().year

        # Get the count of patients for this clinic/year
        count_query = select(func.count(Patient.patient_id)).where(
            and_(
                Patient.clinic_id == clinic_id,
                func.extract("year", Patient.created_at) == year,
            )
        )
        result = await self.db.execute(count_query)
        count = result.scalar() or 0

        # Generate MRN with zero-padded sequential
        return f"{clinic_id}-{year}-{str(count + 1).zfill(5)}"

    # ========================================================================
    # Patient CRUD Operations
    # ========================================================================

    async def create_patient(
        self,
        data: PatientCreate,
        user_id: int,
        clinic_id: int,
    ) -> Patient:
        """
        Create a new patient with encrypted PII.

        Args:
            data: Patient creation data
            user_id: Creating user's ID
            clinic_id: Clinic ID for tenant isolation

        Returns:
            Created Patient with PII relationship
        """
        # Set RLS context
        await set_tenant_context(self.db, clinic_id)

        # Generate MRN
        mrn = await self._generate_mrn(clinic_id)

        # Create main patient record
        patient = Patient(
            clinic_id=clinic_id,
            mrn=mrn,
            birth_date=data.birth_date,
            gender=data.gender.value,
            status=PatientStatus.ACTIVE.value,
            gesy_beneficiary_id=data.gesy_beneficiary_id,
            referring_physician=data.referring_physician,
        )
        self.db.add(patient)
        await self.db.flush()  # Get patient_id

        # Create encrypted PII record
        address_json = json.dumps(data.address.model_dump()) if data.address else None
        emergency_json = (
            json.dumps(data.emergency_contact.model_dump())
            if data.emergency_contact
            else None
        )

        pii = PatientPII(
            patient_id=patient.patient_id,
            first_name_encrypted=encrypt_pii(data.first_name),
            last_name_encrypted=encrypt_pii(data.last_name),
            middle_name_encrypted=encrypt_pii_optional(data.middle_name),
            cyprus_id_encrypted=encrypt_pii_optional(data.cyprus_id),
            arc_number_encrypted=encrypt_pii_optional(data.arc_number),
            phone_encrypted=encrypt_pii_optional(data.phone),
            email_encrypted=encrypt_pii_optional(data.email),
            address_encrypted=encrypt_pii_optional(address_json),
            emergency_contact_encrypted=encrypt_pii_optional(emergency_json),
        )
        self.db.add(pii)
        patient.pii = pii

        await self.db.commit()
        await self.db.refresh(patient, ["pii"])

        return patient

    async def get_patient(
        self,
        patient_id: int,
        clinic_id: int,
        include_pii: bool = True,
    ) -> Optional[Patient]:
        """
        Get a patient by ID.

        Args:
            patient_id: Patient ID
            clinic_id: Clinic ID for RLS verification
            include_pii: Whether to load PII relationship

        Returns:
            Patient or None if not found/not authorized
        """
        await set_tenant_context(self.db, clinic_id)

        query = select(Patient).where(
            and_(
                Patient.patient_id == patient_id,
                Patient.clinic_id == clinic_id,
                Patient.is_deleted == False,  # noqa: E712
            )
        )

        if include_pii:
            query = query.options(selectinload(Patient.pii))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_patients(
        self,
        clinic_id: int,
        page: int = 1,
        page_size: int = 20,
        status: Optional[PatientStatus] = PatientStatus.ACTIVE,
    ) -> tuple[Sequence[Patient], int]:
        """
        Get paginated list of patients.

        Args:
            clinic_id: Clinic ID for RLS
            page: Page number (1-indexed)
            page_size: Items per page
            status: Filter by status

        Returns:
            Tuple of (patients list, total count)
        """
        await set_tenant_context(self.db, clinic_id)

        # Base query
        base_query = select(Patient).where(
            and_(
                Patient.clinic_id == clinic_id,
                Patient.is_deleted == False,  # noqa: E712
            )
        )

        if status:
            base_query = base_query.where(Patient.status == status.value)

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Fetch page
        offset = (page - 1) * page_size
        query = (
            base_query.options(selectinload(Patient.pii))
            .order_by(desc(Patient.updated_at))
            .offset(offset)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        patients = result.scalars().all()

        return patients, total

    async def update_patient(
        self,
        patient_id: int,
        data: PatientUpdate,
        user_id: int,
        clinic_id: int,
    ) -> Optional[Patient]:
        """
        Update a patient's information.

        Args:
            patient_id: Patient ID
            data: Update data
            user_id: Updating user's ID
            clinic_id: Clinic ID for RLS

        Returns:
            Updated patient or None if not found
        """
        await set_tenant_context(self.db, clinic_id)

        patient = await self.get_patient(patient_id, clinic_id, include_pii=True)
        if not patient:
            return None

        # Update non-PII fields
        if data.gender is not None:
            patient.gender = data.gender.value
        if data.status is not None:
            patient.status = data.status.value
        if data.gesy_beneficiary_id is not None:
            patient.gesy_beneficiary_id = data.gesy_beneficiary_id
        if data.referring_physician is not None:
            patient.referring_physician = data.referring_physician

        # Update PII fields
        if patient.pii:
            if data.first_name is not None:
                patient.pii.first_name_encrypted = encrypt_pii(data.first_name)
            if data.last_name is not None:
                patient.pii.last_name_encrypted = encrypt_pii(data.last_name)
            if data.middle_name is not None:
                patient.pii.middle_name_encrypted = encrypt_pii_optional(data.middle_name)
            if data.phone is not None:
                patient.pii.phone_encrypted = encrypt_pii_optional(data.phone)
            if data.email is not None:
                patient.pii.email_encrypted = encrypt_pii_optional(data.email)
            if data.address is not None:
                patient.pii.address_encrypted = encrypt_pii_optional(
                    json.dumps(data.address.model_dump())
                )
            if data.emergency_contact is not None:
                patient.pii.emergency_contact_encrypted = encrypt_pii_optional(
                    json.dumps(data.emergency_contact.model_dump())
                )

        patient.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(patient)

        return patient

    async def delete_patient(
        self,
        patient_id: int,
        user_id: int,
        clinic_id: int,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Tier 1: Administrative deactivation.

        Marks patient as inactive. PII remains encrypted and recoverable.
        This is reversible via reactivate_patient().

        Args:
            patient_id: Patient ID
            user_id: Deactivating user's ID
            clinic_id: Clinic ID for RLS
            reason: Why the patient is being deactivated

        Returns:
            True if deactivated, False if not found
        """
        await set_tenant_context(self.db, clinic_id)

        patient = await self.get_patient(patient_id, clinic_id)
        if not patient:
            return False

        patient.is_deleted = True
        patient.deleted_at = datetime.now(timezone.utc)
        patient.status = PatientStatus.INACTIVE.value
        patient.deactivation_reason = reason

        await self.db.commit()
        return True

    async def reactivate_patient(
        self,
        patient_id: int,
        user_id: int,
        clinic_id: int,
    ) -> Optional[Patient]:
        """
        Reverse a Tier 1 deactivation.

        Cannot reactivate if PII has been anonymized (Tier 2 executed).

        Args:
            patient_id: Patient ID
            user_id: Reactivating user's ID
            clinic_id: Clinic ID for RLS

        Returns:
            Reactivated patient, or None if not found/not eligible
        """
        await set_tenant_context(self.db, clinic_id)

        # Fetch including deleted patients
        query = select(Patient).where(
            and_(
                Patient.patient_id == patient_id,
                Patient.clinic_id == clinic_id,
                Patient.is_deleted == True,  # noqa: E712
            )
        ).options(selectinload(Patient.pii))

        result = await self.db.execute(query)
        patient = result.scalar_one_or_none()

        if not patient:
            return None

        # Cannot reactivate if PII was anonymized
        if patient.pii and patient.pii.anonymized_at:
            return None

        patient.is_deleted = False
        patient.deleted_at = None
        patient.status = PatientStatus.ACTIVE.value
        patient.deactivation_reason = None
        patient.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(patient)
        return patient

    # ========================================================================
    # Search
    # ========================================================================

    async def search_patients(
        self,
        query: PatientSearchQuery,
        clinic_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[Patient], int]:
        """
        Search patients by name, MRN, or other criteria.

        For PII search (name), we must decrypt and filter in Python
        since the data is encrypted. For large datasets, consider
        using a searchable hash index.

        Args:
            query: Search parameters
            clinic_id: Clinic ID for RLS
            page: Page number
            page_size: Items per page

        Returns:
            Tuple of (matching patients, total count)
        """
        await set_tenant_context(self.db, clinic_id)

        # Base query - get all candidates
        base_query = select(Patient).where(
            and_(
                Patient.clinic_id == clinic_id,
                Patient.is_deleted == False,  # noqa: E712
            )
        )

        # Apply non-PII filters
        if query.status:
            base_query = base_query.where(Patient.status == query.status.value)
        if query.birth_date:
            base_query = base_query.where(Patient.birth_date == query.birth_date)
        if query.gender:
            base_query = base_query.where(Patient.gender == query.gender.value)
        if query.gesy_only:
            base_query = base_query.where(Patient.gesy_beneficiary_id.isnot(None))

        # If searching by name/MRN, we need to filter in Python
        if query.q:
            search_term = query.q.lower()

            # First try MRN exact match (fast path)
            mrn_query = base_query.where(Patient.mrn.ilike(f"%{search_term}%"))
            mrn_result = await self.db.execute(
                mrn_query.options(selectinload(Patient.pii))
            )
            mrn_matches = list(mrn_result.scalars().all())

            # For name search, load all and filter by decrypted names
            # In production, you'd use a searchable hash index instead
            all_query = base_query.options(selectinload(Patient.pii))
            all_result = await self.db.execute(all_query)
            all_patients = list(all_result.scalars().all())

            # Filter by decrypted name
            name_matches = []
            for patient in all_patients:
                if patient.pii:
                    first = decrypt_pii(patient.pii.first_name_encrypted).lower()
                    last = decrypt_pii(patient.pii.last_name_encrypted).lower()
                    full_name = f"{first} {last}"
                    if search_term in first or search_term in last or search_term in full_name:
                        name_matches.append(patient)

            # Combine and deduplicate
            seen_ids = set()
            combined = []
            for p in mrn_matches + name_matches:
                if p.patient_id not in seen_ids:
                    seen_ids.add(p.patient_id)
                    combined.append(p)

            total = len(combined)
            offset = (page - 1) * page_size
            paginated = combined[offset : offset + page_size]

            return paginated, total

        # No text search - use database pagination
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        offset = (page - 1) * page_size
        final_query = (
            base_query.options(selectinload(Patient.pii))
            .order_by(desc(Patient.updated_at))
            .offset(offset)
            .limit(page_size)
        )

        result = await self.db.execute(final_query)
        patients = result.scalars().all()

        return patients, total

    # ========================================================================
    # Response Building
    # ========================================================================

    def build_patient_response(
        self,
        patient: Patient,
        include_pii: bool = True,
    ) -> PatientResponse:
        """
        Build a PatientResponse from a Patient model.

        Decrypts PII and masks sensitive identifiers.

        Args:
            patient: Patient model with loaded PII
            include_pii: Whether to include decrypted PII

        Returns:
            PatientResponse with masked/decrypted data
        """
        response = PatientResponse(
            patient_id=patient.patient_id,
            mrn=patient.mrn,
            birth_date=patient.birth_date,
            gender=patient.gender,
            status=patient.status,
            age=patient.age,
            gesy_beneficiary_id=patient.gesy_beneficiary_id,
            is_gesy_beneficiary=bool(patient.gesy_beneficiary_id),
            referring_physician=patient.referring_physician,
            primary_physician_id=patient.primary_physician_id,
            created_at=patient.created_at,
            updated_at=patient.updated_at,
        )

        if include_pii and patient.pii:
            pii = patient.pii

            # Decrypt names
            response.first_name = decrypt_pii(pii.first_name_encrypted)
            response.last_name = decrypt_pii(pii.last_name_encrypted)
            response.middle_name = decrypt_pii_optional(pii.middle_name_encrypted)

            # Decrypt contact
            response.phone = decrypt_pii_optional(pii.phone_encrypted)
            response.email = decrypt_pii_optional(pii.email_encrypted)

            # Mask Cyprus ID for display
            cyprus_id = decrypt_pii_optional(pii.cyprus_id_encrypted)
            if cyprus_id:
                response.cyprus_id_masked = mask_pii(cyprus_id, 4)

            # Flag if ARC exists
            arc = decrypt_pii_optional(pii.arc_number_encrypted)
            response.has_arc = bool(arc)

            # Decrypt address if present
            address_json = decrypt_pii_optional(pii.address_encrypted)
            if address_json:
                try:
                    response.address = Address(**json.loads(address_json))
                except (json.JSONDecodeError, TypeError):
                    pass

        return response

    async def get_patient_timeline(
        self,
        patient_id: int,
        clinic_id: int,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """
        Get patient activity timeline.

        Returns encounters, notes, observations in chronological order.
        This is a placeholder that will be expanded as other modules
        are implemented.

        Args:
            patient_id: Patient ID
            clinic_id: Clinic ID for RLS
            page: Page number
            page_size: Items per page

        Returns:
            Dictionary with timeline events
        """
        await set_tenant_context(self.db, clinic_id)

        # Verify patient access
        patient = await self.get_patient(patient_id, clinic_id)
        if not patient:
            return {"events": [], "total": 0}

        # Placeholder - will be populated with:
        # - Encounters
        # - Clinical notes
        # - Observations
        # - CDSS calculations
        # - DICOM studies

        return {
            "patient_id": patient_id,
            "events": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
        }

    # ========================================================================
    # GDPR Erasure Requests (Tier 2)
    # ========================================================================

    COOLOFF_HOURS = 72  # Mandatory delay between approval and execution

    async def create_erasure_request(
        self,
        patient_id: int,
        data: ErasureRequestCreate,
        user_id: int,
        clinic_id: int,
    ) -> Optional[GDPRErasureRequest]:
        """
        Submit a GDPR Article 17 erasure request on behalf of a patient.

        Args:
            patient_id: Patient ID
            data: Request details (method, legal basis)
            user_id: Staff member submitting on behalf of patient
            clinic_id: Clinic ID for RLS

        Returns:
            Created erasure request, or None if patient not found
        """
        await set_tenant_context(self.db, clinic_id)

        # Verify patient exists (including deactivated patients)
        query = select(Patient).where(
            and_(
                Patient.patient_id == patient_id,
                Patient.clinic_id == clinic_id,
            )
        )
        result = await self.db.execute(query)
        patient = result.scalar_one_or_none()
        if not patient:
            return None

        # Check for existing pending/approved request
        existing_query = select(GDPRErasureRequest).where(
            and_(
                GDPRErasureRequest.patient_id == patient_id,
                GDPRErasureRequest.evaluation_status.in_([
                    ErasureRequestStatus.PENDING.value,
                    ErasureRequestStatus.APPROVED.value,
                ]),
            )
        )
        existing = await self.db.execute(existing_query)
        if existing.scalar_one_or_none():
            logger.warning(
                f"Erasure request already exists for patient {patient_id}"
            )
            return None

        erasure_request = GDPRErasureRequest(
            patient_id=patient_id,
            requested_by=user_id,
            request_method=data.request_method.value,
            legal_basis_cited=data.legal_basis_cited.value,
            evaluation_status=ErasureRequestStatus.PENDING.value,
        )
        self.db.add(erasure_request)
        await self.db.commit()
        await self.db.refresh(erasure_request)

        return erasure_request

    async def get_erasure_requests(
        self,
        patient_id: int,
        clinic_id: int,
    ) -> Sequence[GDPRErasureRequest]:
        """Get all erasure requests for a patient."""
        await set_tenant_context(self.db, clinic_id)

        query = (
            select(GDPRErasureRequest)
            .join(Patient)
            .where(
                and_(
                    GDPRErasureRequest.patient_id == patient_id,
                    Patient.clinic_id == clinic_id,
                )
            )
            .order_by(desc(GDPRErasureRequest.requested_at))
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def evaluate_erasure_request(
        self,
        request_id: int,
        data: ErasureRequestEvaluate,
        user_id: int,
    ) -> Optional[GDPRErasureRequest]:
        """
        Approve or deny an erasure request.

        If approved, sets a 72-hour cooling-off period before execution.

        Args:
            request_id: Erasure request ID
            data: Evaluation decision
            user_id: Admin/DPO evaluating

        Returns:
            Updated request, or None if not found/not pending
        """
        query = select(GDPRErasureRequest).where(
            and_(
                GDPRErasureRequest.request_id == request_id,
                GDPRErasureRequest.evaluation_status == ErasureRequestStatus.PENDING.value,
            )
        )
        result = await self.db.execute(query)
        erasure_request = result.scalar_one_or_none()
        if not erasure_request:
            return None

        now = datetime.now(timezone.utc)
        erasure_request.evaluated_by = user_id
        erasure_request.evaluated_at = now
        erasure_request.evaluation_status = data.decision.value

        if data.decision == ErasureRequestStatus.APPROVED:
            erasure_request.cooloff_expires_at = now + timedelta(hours=self.COOLOFF_HOURS)
        else:
            erasure_request.denial_reason = data.denial_reason

        await self.db.commit()
        await self.db.refresh(erasure_request)
        return erasure_request

    async def cancel_approved_erasure(
        self,
        request_id: int,
        user_id: int,
        reason: str,
    ) -> Optional[GDPRErasureRequest]:
        """
        Cancel an approved erasure during the 72-hour cooling-off.

        Only valid while cooloff_expires_at has not passed.

        Args:
            request_id: Erasure request ID
            user_id: User cancelling
            reason: Why the erasure is being cancelled

        Returns:
            Updated request, or None if not found/not in cooloff
        """
        query = select(GDPRErasureRequest).where(
            and_(
                GDPRErasureRequest.request_id == request_id,
                GDPRErasureRequest.evaluation_status == ErasureRequestStatus.APPROVED.value,
            )
        )
        result = await self.db.execute(query)
        erasure_request = result.scalar_one_or_none()
        if not erasure_request:
            return None

        # Verify still within cooling-off period
        now = datetime.now(timezone.utc)
        if erasure_request.cooloff_expires_at and now >= erasure_request.cooloff_expires_at:
            logger.warning(
                f"Cannot cancel erasure {request_id}: cooling-off expired"
            )
            return None

        erasure_request.evaluation_status = ErasureRequestStatus.CANCELLED.value
        erasure_request.cancelled_at = now
        erasure_request.cancellation_reason = reason

        await self.db.commit()
        await self.db.refresh(erasure_request)
        return erasure_request

    async def execute_anonymization(
        self,
        request_id: int,
        user_id: int,
        clinic_id: int,
    ) -> Optional[dict]:
        """
        Tier 2: Execute PII anonymization after cooling-off period.

        Irreversibly overwrites encrypted PII fields with anonymized values.
        Clinical notes are LEFT INTACT per Article 17(3)(c) healthcare exemption.

        Args:
            request_id: Approved erasure request ID
            user_id: System admin executing
            clinic_id: Clinic ID for RLS

        Returns:
            Summary of anonymized fields, or None if not eligible
        """
        # Fetch the approved request
        query = select(GDPRErasureRequest).where(
            and_(
                GDPRErasureRequest.request_id == request_id,
                GDPRErasureRequest.evaluation_status == ErasureRequestStatus.APPROVED.value,
            )
        )
        result = await self.db.execute(query)
        erasure_request = result.scalar_one_or_none()
        if not erasure_request:
            return None

        # Verify cooling-off has elapsed
        now = datetime.now(timezone.utc)
        if erasure_request.cooloff_expires_at and now < erasure_request.cooloff_expires_at:
            logger.warning(
                f"Cannot execute erasure {request_id}: "
                f"cooling-off expires at {erasure_request.cooloff_expires_at}"
            )
            return None

        await set_tenant_context(self.db, clinic_id)

        # Fetch patient with PII
        patient_query = select(Patient).where(
            and_(
                Patient.patient_id == erasure_request.patient_id,
                Patient.clinic_id == clinic_id,
            )
        ).options(selectinload(Patient.pii))

        patient_result = await self.db.execute(patient_query)
        patient = patient_result.scalar_one_or_none()
        if not patient or not patient.pii:
            return None

        # Anonymize PII fields
        pii = patient.pii
        anonymized_fields = []

        if pii.first_name_encrypted:
            pii.first_name_encrypted = encrypt_pii("REDACTED")
            anonymized_fields.append("first_name")

        if pii.last_name_encrypted:
            pii.last_name_encrypted = encrypt_pii("REDACTED")
            anonymized_fields.append("last_name")

        if pii.middle_name_encrypted:
            pii.middle_name_encrypted = None
            anonymized_fields.append("middle_name")

        if pii.cyprus_id_encrypted:
            pii.cyprus_id_encrypted = None
            anonymized_fields.append("cyprus_id")

        if pii.arc_number_encrypted:
            pii.arc_number_encrypted = None
            anonymized_fields.append("arc_number")

        if pii.phone_encrypted:
            pii.phone_encrypted = None
            anonymized_fields.append("phone")

        if pii.email_encrypted:
            pii.email_encrypted = None
            anonymized_fields.append("email")

        if pii.address_encrypted:
            pii.address_encrypted = None
            anonymized_fields.append("address")

        if pii.emergency_contact_encrypted:
            pii.emergency_contact_encrypted = None
            anonymized_fields.append("emergency_contact")

        pii.anonymized_at = now

        # Ensure patient is marked as deleted/inactive
        if not patient.is_deleted:
            patient.is_deleted = True
            patient.deleted_at = now
            patient.status = PatientStatus.INACTIVE.value
            patient.deactivation_reason = "GDPR Article 17 erasure executed"

        # Update erasure request
        execution_details = {
            "anonymized_fields": anonymized_fields,
            "executed_by": user_id,
            "clinical_notes_preserved": True,
            "article_17_3_c_exemption": "Healthcare records retained",
        }
        erasure_request.evaluation_status = ErasureRequestStatus.EXECUTED.value
        erasure_request.executed_at = now
        erasure_request.execution_details = execution_details

        await self.db.commit()

        logger.info(
            f"GDPR erasure executed for patient {erasure_request.patient_id}: "
            f"anonymized {len(anonymized_fields)} PII fields"
        )

        return execution_details

    def build_erasure_response(
        self,
        request: GDPRErasureRequest,
    ) -> ErasureRequestResponse:
        """Build a response object for an erasure request."""
        now = datetime.now(timezone.utc)

        is_in_cooloff = (
            request.evaluation_status == ErasureRequestStatus.APPROVED.value
            and request.cooloff_expires_at is not None
            and now < request.cooloff_expires_at
        )
        can_execute = (
            request.evaluation_status == ErasureRequestStatus.APPROVED.value
            and request.cooloff_expires_at is not None
            and now >= request.cooloff_expires_at
        )

        return ErasureRequestResponse(
            request_id=request.request_id,
            patient_id=request.patient_id,
            requested_at=request.requested_at,
            requested_by=request.requested_by,
            request_method=request.request_method,
            legal_basis_cited=request.legal_basis_cited,
            evaluation_status=request.evaluation_status,
            evaluated_by=request.evaluated_by,
            evaluated_at=request.evaluated_at,
            denial_reason=request.denial_reason,
            retention_expiry_date=request.retention_expiry_date,
            cooloff_expires_at=request.cooloff_expires_at,
            cancelled_at=request.cancelled_at,
            cancellation_reason=request.cancellation_reason,
            executed_at=request.executed_at,
            execution_details=request.execution_details,
            is_in_cooloff=is_in_cooloff,
            can_execute=can_execute,
        )
