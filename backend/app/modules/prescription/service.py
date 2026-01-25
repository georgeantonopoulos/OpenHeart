"""Business logic service for the prescription module."""

import logging
from datetime import date, datetime, timezone
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import and_, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.prescription.interactions import InteractionEngine
from app.modules.prescription.models import (
    MedicationHistory,
    Prescription,
    PrescriptionInteraction,
)
from app.modules.prescription.schemas import (
    FREQUENCY_DISPLAY_MAP,
    InteractionCheckRequest,
    InteractionCheckResponse,
    InteractionDetail,
    PrescriptionCreate,
    PrescriptionDiscontinue,
    PrescriptionHold,
    PrescriptionRenew,
    PrescriptionUpdate,
)

logger = logging.getLogger(__name__)


class PrescriptionService:
    """Service for managing prescriptions."""

    def __init__(self, db: AsyncSession, clinic_id: int, user_id: int) -> None:
        self.db = db
        self.clinic_id = clinic_id
        self.user_id = user_id
        self.interaction_engine = InteractionEngine()

    # ========================================================================
    # Prescription CRUD
    # ========================================================================

    async def create_prescription(self, data: PrescriptionCreate) -> Prescription:
        """
        Create a new prescription with interaction checking.

        Args:
            data: Prescription creation data

        Returns:
            Created Prescription with interactions attached

        Raises:
            ValueError: If contraindicated interactions exist and not acknowledged
        """
        # Calculate end_date if duration specified
        end_date = None
        if data.duration_days:
            from datetime import timedelta
            end_date = data.start_date + timedelta(days=data.duration_days)

        # Generate frequency display
        frequency_display = FREQUENCY_DISPLAY_MAP.get(data.frequency, data.frequency_custom or data.frequency)

        # Create prescription
        prescription = Prescription(
            patient_id=data.patient_id,
            encounter_id=data.encounter_id,
            prescriber_id=self.user_id,
            clinic_id=self.clinic_id,
            gesy_medication_id=data.gesy_medication_id,
            drug_name=data.drug_name,
            atc_code=data.atc_code,
            generic_name=data.generic_name,
            form=data.form,
            strength=data.strength,
            dosage=data.dosage,
            quantity=data.quantity,
            frequency=data.frequency,
            frequency_custom=data.frequency_custom,
            frequency_display=frequency_display,
            route=data.route,
            duration_days=data.duration_days,
            start_date=data.start_date,
            end_date=end_date,
            refills_allowed=data.refills_allowed,
            is_chronic=data.is_chronic,
            status="active",
            linked_diagnosis_icd10=data.linked_diagnosis_icd10,
            linked_diagnosis_description=data.linked_diagnosis_description,
            indication=data.indication,
            prescriber_notes=data.prescriber_notes,
        )
        self.db.add(prescription)
        await self.db.flush()

        # Check interactions against active medications
        interactions = await self._check_and_record_interactions(
            prescription, data.acknowledge_interactions
        )

        # Log creation in medication history
        history = MedicationHistory(
            prescription_id=prescription.id,
            previous_status=None,
            new_status="active",
            changed_by=self.user_id,
            change_type="created",
            details={"drug_name": data.drug_name, "strength": data.strength},
        )
        self.db.add(history)

        await self.db.flush()
        await self.db.refresh(prescription, ["interactions", "history"])

        return prescription

    async def get_prescription(self, prescription_id: UUID) -> Optional[Prescription]:
        """Get a single prescription by ID with interactions and history."""
        query = (
            select(Prescription)
            .where(
                and_(
                    Prescription.id == prescription_id,
                    Prescription.clinic_id == self.clinic_id,
                    Prescription.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(Prescription.interactions),
                selectinload(Prescription.history),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_medications(self, patient_id: int) -> Sequence[Prescription]:
        """Get all active prescriptions for a patient."""
        query = (
            select(Prescription)
            .where(
                and_(
                    Prescription.patient_id == patient_id,
                    Prescription.clinic_id == self.clinic_id,
                    Prescription.status == "active",
                    Prescription.deleted_at.is_(None),
                )
            )
            .options(selectinload(Prescription.interactions))
            .order_by(desc(Prescription.created_at))
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_chronic_medications(self, patient_id: int) -> Sequence[Prescription]:
        """Get chronic prescriptions for a patient."""
        query = (
            select(Prescription)
            .where(
                and_(
                    Prescription.patient_id == patient_id,
                    Prescription.clinic_id == self.clinic_id,
                    Prescription.is_chronic.is_(True),
                    Prescription.status == "active",
                    Prescription.deleted_at.is_(None),
                )
            )
            .order_by(desc(Prescription.created_at))
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def list_prescriptions(
        self,
        patient_id: int,
        status: Optional[str] = None,
        include_inactive: bool = True,
    ) -> tuple[Sequence[Prescription], int]:
        """
        List prescriptions for a patient with optional status filter.

        Returns:
            Tuple of (prescriptions, total_count)
        """
        conditions = [
            Prescription.patient_id == patient_id,
            Prescription.clinic_id == self.clinic_id,
            Prescription.deleted_at.is_(None),
        ]

        if status:
            conditions.append(Prescription.status == status)
        elif not include_inactive:
            conditions.append(Prescription.status == "active")

        # Count
        count_query = select(func.count()).select_from(Prescription).where(and_(*conditions))
        result = await self.db.execute(count_query)
        total = result.scalar() or 0

        # Fetch
        query = (
            select(Prescription)
            .where(and_(*conditions))
            .options(selectinload(Prescription.interactions))
            .order_by(desc(Prescription.created_at))
        )
        result = await self.db.execute(query)
        prescriptions = result.scalars().all()

        return prescriptions, total

    async def update_prescription(
        self, prescription_id: UUID, data: PrescriptionUpdate
    ) -> Optional[Prescription]:
        """Update prescription details (dose change, notes)."""
        prescription = await self.get_prescription(prescription_id)
        if not prescription:
            return None

        if prescription.status != "active":
            raise ValueError(f"Cannot update prescription with status '{prescription.status}'")

        # Track changes for history
        changes = {}
        update_data = data.model_dump(exclude_unset=True)

        for field_name, new_value in update_data.items():
            old_value = getattr(prescription, field_name, None)
            if old_value != new_value:
                changes[field_name] = {"old": str(old_value), "new": str(new_value)}
                setattr(prescription, field_name, new_value)

        if changes:
            # Update frequency display if frequency changed
            if "frequency" in changes:
                prescription.frequency_display = FREQUENCY_DISPLAY_MAP.get(
                    prescription.frequency, prescription.frequency_custom or prescription.frequency
                )

            prescription.updated_at = datetime.now(timezone.utc)

            history = MedicationHistory(
                prescription_id=prescription.id,
                previous_status="active",
                new_status="active",
                changed_by=self.user_id,
                change_type="dose_change",
                details=changes,
            )
            self.db.add(history)
            await self.db.flush()

        return prescription

    # ========================================================================
    # Prescription Lifecycle Actions
    # ========================================================================

    async def discontinue(
        self, prescription_id: UUID, data: PrescriptionDiscontinue
    ) -> Optional[Prescription]:
        """Discontinue a prescription with reason."""
        prescription = await self.get_prescription(prescription_id)
        if not prescription:
            return None

        if prescription.status not in ("active", "on_hold"):
            raise ValueError(f"Cannot discontinue prescription with status '{prescription.status}'")

        old_status = prescription.status
        prescription.status = "discontinued"
        prescription.discontinued_at = datetime.now(timezone.utc)
        prescription.discontinued_by = self.user_id
        prescription.discontinuation_reason = data.reason
        prescription.updated_at = datetime.now(timezone.utc)

        if data.effective_date:
            prescription.end_date = data.effective_date

        history = MedicationHistory(
            prescription_id=prescription.id,
            previous_status=old_status,
            new_status="discontinued",
            changed_by=self.user_id,
            change_type="discontinued",
            reason=data.reason,
        )
        self.db.add(history)
        await self.db.flush()

        return prescription

    async def renew_prescription(
        self, prescription_id: UUID, data: PrescriptionRenew
    ) -> Prescription:
        """
        Renew a chronic prescription by creating a new linked prescription.

        Raises:
            ValueError: If prescription is not chronic or not active
        """
        original = await self.get_prescription(prescription_id)
        if not original:
            raise ValueError("Prescription not found")

        if not original.is_chronic:
            raise ValueError("Only chronic prescriptions can be renewed")

        if original.status != "active":
            raise ValueError(f"Cannot renew prescription with status '{original.status}'")

        # Calculate new dates
        from datetime import timedelta

        duration_days = data.duration_days or original.duration_days
        start_date = date.today()
        end_date = start_date + timedelta(days=duration_days) if duration_days else None

        # Create new prescription copying original details
        new_rx = Prescription(
            patient_id=original.patient_id,
            prescriber_id=self.user_id,
            clinic_id=self.clinic_id,
            gesy_medication_id=original.gesy_medication_id,
            drug_name=original.drug_name,
            atc_code=original.atc_code,
            generic_name=original.generic_name,
            form=original.form,
            strength=original.strength,
            dosage=original.dosage,
            quantity=data.quantity or original.quantity,
            frequency=original.frequency,
            frequency_custom=original.frequency_custom,
            frequency_display=original.frequency_display,
            route=original.route,
            duration_days=duration_days,
            start_date=start_date,
            end_date=end_date,
            refills_allowed=original.refills_allowed,
            is_chronic=True,
            status="active",
            linked_diagnosis_icd10=original.linked_diagnosis_icd10,
            linked_diagnosis_description=original.linked_diagnosis_description,
            indication=original.indication,
            original_prescription_id=original.id,
            renewal_count=original.renewal_count + 1,
            prescriber_notes=data.notes or original.prescriber_notes,
        )
        self.db.add(new_rx)
        await self.db.flush()

        # Re-check interactions (patient meds may have changed)
        await self._check_and_record_interactions(new_rx, [])

        # Log history on both
        history_new = MedicationHistory(
            prescription_id=new_rx.id,
            previous_status=None,
            new_status="active",
            changed_by=self.user_id,
            change_type="renewed",
            details={"renewed_from": str(original.id), "renewal_count": new_rx.renewal_count},
        )
        self.db.add(history_new)

        # Mark original as completed
        original.status = "completed"
        original.end_date = date.today()
        original.updated_at = datetime.now(timezone.utc)

        history_orig = MedicationHistory(
            prescription_id=original.id,
            previous_status="active",
            new_status="completed",
            changed_by=self.user_id,
            change_type="renewed",
            details={"renewed_to": str(new_rx.id)},
        )
        self.db.add(history_orig)

        await self.db.flush()
        await self.db.refresh(new_rx, ["interactions", "history"])

        return new_rx

    async def hold_prescription(
        self, prescription_id: UUID, data: PrescriptionHold
    ) -> Optional[Prescription]:
        """Put a prescription on hold (e.g., pre-surgery)."""
        prescription = await self.get_prescription(prescription_id)
        if not prescription:
            return None

        if prescription.status != "active":
            raise ValueError(f"Cannot hold prescription with status '{prescription.status}'")

        prescription.status = "on_hold"
        prescription.updated_at = datetime.now(timezone.utc)

        history = MedicationHistory(
            prescription_id=prescription.id,
            previous_status="active",
            new_status="on_hold",
            changed_by=self.user_id,
            change_type="status_change",
            reason=data.reason,
        )
        self.db.add(history)
        await self.db.flush()

        return prescription

    async def resume_prescription(self, prescription_id: UUID) -> Optional[Prescription]:
        """Resume a prescription from on_hold status."""
        prescription = await self.get_prescription(prescription_id)
        if not prescription:
            return None

        if prescription.status != "on_hold":
            raise ValueError(f"Cannot resume prescription with status '{prescription.status}'")

        prescription.status = "active"
        prescription.updated_at = datetime.now(timezone.utc)

        history = MedicationHistory(
            prescription_id=prescription.id,
            previous_status="on_hold",
            new_status="active",
            changed_by=self.user_id,
            change_type="status_change",
            reason="Resumed from hold",
        )
        self.db.add(history)
        await self.db.flush()

        return prescription

    # ========================================================================
    # Interaction Checking
    # ========================================================================

    async def check_interactions(
        self, request: InteractionCheckRequest
    ) -> InteractionCheckResponse:
        """Check proposed drug interactions against patient's active medications."""
        active_meds = await self.get_active_medications(request.patient_id)

        # Build medication list for engine
        med_list = [
            {
                "drug_name": rx.drug_name,
                "atc_code": rx.atc_code,
                "prescription_id": rx.id,
            }
            for rx in active_meds
            if rx.id != request.exclude_prescription_id
        ]

        interactions = self.interaction_engine.check_interactions(
            new_drug_atc=request.atc_code,
            new_drug_name=request.drug_name,
            active_medications=med_list,
        )

        can_proceed = not any(i.severity == "contraindicated" for i in interactions)

        return InteractionCheckResponse(
            has_interactions=len(interactions) > 0,
            interactions=interactions,
            can_proceed=can_proceed,
        )

    async def get_prescription_history(self, prescription_id: UUID) -> Sequence[MedicationHistory]:
        """Get full change history for a prescription."""
        query = (
            select(MedicationHistory)
            .where(MedicationHistory.prescription_id == prescription_id)
            .order_by(MedicationHistory.changed_at)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    # ========================================================================
    # Background Tasks
    # ========================================================================

    async def expire_completed_prescriptions(self) -> int:
        """Mark prescriptions past end_date as 'expired'. Returns count expired."""
        today = date.today()
        stmt = (
            update(Prescription)
            .where(
                and_(
                    Prescription.status == "active",
                    Prescription.end_date.isnot(None),
                    Prescription.end_date < today,
                    Prescription.is_chronic.is_(False),
                    Prescription.deleted_at.is_(None),
                )
            )
            .values(status="expired", updated_at=datetime.now(timezone.utc))
        )
        result = await self.db.execute(stmt)
        return result.rowcount

    # ========================================================================
    # Private Helpers
    # ========================================================================

    async def _check_and_record_interactions(
        self, prescription: Prescription, acknowledged_ids: list[UUID]
    ) -> list[InteractionDetail]:
        """Check interactions and persist as PrescriptionInteraction records."""
        active_meds = await self.get_active_medications(prescription.patient_id)

        med_list = [
            {
                "drug_name": rx.drug_name,
                "atc_code": rx.atc_code,
                "prescription_id": rx.id,
            }
            for rx in active_meds
            if rx.id != prescription.id
        ]

        interactions = self.interaction_engine.check_interactions(
            new_drug_atc=prescription.atc_code,
            new_drug_name=prescription.drug_name,
            active_medications=med_list,
        )

        # Persist interaction records
        for interaction in interactions:
            record = PrescriptionInteraction(
                prescription_id=prescription.id,
                interacting_prescription_id=interaction.interacting_prescription_id,
                interacting_drug_name=interaction.interacting_drug,
                interacting_atc_code=interaction.interacting_atc,
                severity=interaction.severity,
                interaction_type=interaction.interaction_type,
                description=interaction.description,
                management_recommendation=interaction.management,
            )
            self.db.add(record)

        await self.db.flush()
        return interactions
