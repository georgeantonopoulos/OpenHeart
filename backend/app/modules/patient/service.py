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
from datetime import datetime
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
from app.modules.patient.models import Patient, PatientPII, PatientStatus
from app.modules.patient.schemas import (
    Address,
    EmergencyContact,
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

        await self.db.commit()
        await self.db.refresh(patient)

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
    ) -> bool:
        """
        Soft-delete a patient (GDPR anonymization).

        The patient record is retained for medical record keeping
        but marked as deleted and PII can be anonymized.

        Args:
            patient_id: Patient ID
            user_id: Deleting user's ID
            clinic_id: Clinic ID for RLS

        Returns:
            True if deleted, False if not found
        """
        await set_tenant_context(self.db, clinic_id)

        patient = await self.get_patient(patient_id, clinic_id)
        if not patient:
            return False

        patient.is_deleted = True
        patient.deleted_at = datetime.utcnow()
        patient.status = PatientStatus.INACTIVE.value

        await self.db.commit()
        return True

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
