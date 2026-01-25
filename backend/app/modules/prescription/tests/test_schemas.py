"""
Prescription Schema Validation Tests.

Validates Pydantic schema constraints and validators.
"""

import pytest
from datetime import date
from pydantic import ValidationError

from app.modules.prescription.schemas import (
    PrescriptionCreate,
    PrescriptionUpdate,
    PrescriptionDiscontinue,
    PrescriptionRenew,
    PrescriptionHold,
    InteractionCheckRequest,
    FREQUENCY_DISPLAY_MAP,
)


class TestPrescriptionCreate:
    """Test PrescriptionCreate schema validation."""

    def test_valid_minimal_prescription(self):
        """Should accept minimal valid prescription data."""
        data = PrescriptionCreate(
            patient_id=1,
            drug_name="Aspirin",
        )
        assert data.patient_id == 1
        assert data.drug_name == "Aspirin"
        assert data.frequency == "OD"  # Default
        assert data.route == "oral"  # Default

    def test_valid_full_prescription(self):
        """Should accept full prescription data."""
        data = PrescriptionCreate(
            patient_id=1,
            encounter_id=10,
            gesy_medication_id=100,
            drug_name="Atorvastatin",
            atc_code="C10AA05",
            generic_name="Atorvastatin",
            form="tablet",
            strength="40mg",
            dosage="1 tablet",
            quantity=30,
            frequency="OD",
            route="oral",
            duration_days=90,
            start_date=date.today(),
            refills_allowed=2,
            is_chronic=True,
            linked_diagnosis_icd10="E78.0",
            linked_diagnosis_description="Hyperlipidemia",
            indication="Primary prevention",
            prescriber_notes="Take at night",
        )
        assert data.is_chronic is True
        assert data.quantity == 30

    def test_invalid_patient_id_zero(self):
        """Should reject patient_id of 0."""
        with pytest.raises(ValidationError):
            PrescriptionCreate(
                patient_id=0,
                drug_name="Aspirin",
            )

    def test_invalid_patient_id_negative(self):
        """Should reject negative patient_id."""
        with pytest.raises(ValidationError):
            PrescriptionCreate(
                patient_id=-1,
                drug_name="Aspirin",
            )

    def test_drug_name_required(self):
        """Should require drug_name."""
        with pytest.raises(ValidationError):
            PrescriptionCreate(
                patient_id=1,
                drug_name="",
            )

    def test_drug_name_stripped(self):
        """Should strip whitespace from drug_name."""
        data = PrescriptionCreate(
            patient_id=1,
            drug_name="  Aspirin  ",
        )
        assert data.drug_name == "Aspirin"

    def test_valid_frequencies(self):
        """Should accept all valid frequencies."""
        valid = ["OD", "BD", "TDS", "QDS", "PRN", "STAT", "nocte", "mane", "custom"]
        for freq in valid:
            data = PrescriptionCreate(
                patient_id=1,
                drug_name="Aspirin",
                frequency=freq,
            )
            assert data.frequency == freq

    def test_invalid_frequency(self):
        """Should reject invalid frequency."""
        with pytest.raises(ValidationError):
            PrescriptionCreate(
                patient_id=1,
                drug_name="Aspirin",
                frequency="INVALID",
            )

    def test_valid_routes(self):
        """Should accept all valid routes."""
        valid = ["oral", "sublingual", "IV", "IM", "SC", "topical", "inhaled", "transdermal", "rectal", "nasal"]
        for route in valid:
            data = PrescriptionCreate(
                patient_id=1,
                drug_name="Test Drug",
                route=route,
            )
            assert data.route == route

    def test_invalid_route(self):
        """Should reject invalid route."""
        with pytest.raises(ValidationError):
            PrescriptionCreate(
                patient_id=1,
                drug_name="Aspirin",
                route="invalid_route",
            )

    def test_duration_days_positive(self):
        """Should only accept positive duration_days."""
        with pytest.raises(ValidationError):
            PrescriptionCreate(
                patient_id=1,
                drug_name="Aspirin",
                duration_days=0,
            )

    def test_quantity_positive(self):
        """Should only accept positive quantity."""
        with pytest.raises(ValidationError):
            PrescriptionCreate(
                patient_id=1,
                drug_name="Aspirin",
                quantity=0,
            )


class TestPrescriptionDiscontinue:
    """Test PrescriptionDiscontinue schema validation."""

    def test_valid_discontinue(self):
        """Should accept valid discontinuation data."""
        data = PrescriptionDiscontinue(
            reason="Patient developed adverse reaction",
        )
        assert len(data.reason) > 0

    def test_reason_required(self):
        """Should require reason."""
        with pytest.raises(ValidationError):
            PrescriptionDiscontinue(reason="")

    def test_reason_min_length(self):
        """Should require minimum 3 characters."""
        with pytest.raises(ValidationError):
            PrescriptionDiscontinue(reason="ab")

    def test_reason_stripped(self):
        """Should strip whitespace from reason."""
        data = PrescriptionDiscontinue(reason="   Patient request   ")
        assert data.reason == "Patient request"

    def test_reason_stripped_too_short(self):
        """Should reject if stripped reason is too short."""
        with pytest.raises(ValidationError):
            PrescriptionDiscontinue(reason="   a   ")

    def test_effective_date_optional(self):
        """Effective date should be optional."""
        data = PrescriptionDiscontinue(reason="Patient request")
        assert data.effective_date is None

    def test_effective_date_accepted(self):
        """Should accept effective_date."""
        data = PrescriptionDiscontinue(
            reason="Patient request",
            effective_date=date.today(),
        )
        assert data.effective_date == date.today()


class TestPrescriptionRenew:
    """Test PrescriptionRenew schema validation."""

    def test_empty_renewal(self):
        """Should accept empty renewal (uses original values)."""
        data = PrescriptionRenew()
        assert data.duration_days is None
        assert data.quantity is None
        assert data.notes is None

    def test_renewal_with_overrides(self):
        """Should accept renewal with overridden values."""
        data = PrescriptionRenew(
            duration_days=90,
            quantity=90,
            notes="Renewed for 3 months",
        )
        assert data.duration_days == 90
        assert data.quantity == 90

    def test_duration_days_positive(self):
        """Should only accept positive duration_days."""
        with pytest.raises(ValidationError):
            PrescriptionRenew(duration_days=0)


class TestPrescriptionHold:
    """Test PrescriptionHold schema validation."""

    def test_valid_hold(self):
        """Should accept valid hold data."""
        data = PrescriptionHold(reason="Pre-operative hold")
        assert data.reason == "Pre-operative hold"

    def test_reason_required(self):
        """Should require reason."""
        with pytest.raises(ValidationError):
            PrescriptionHold(reason="")

    def test_reason_min_length(self):
        """Should require minimum 3 characters."""
        with pytest.raises(ValidationError):
            PrescriptionHold(reason="ab")


class TestInteractionCheckRequest:
    """Test InteractionCheckRequest schema validation."""

    def test_valid_request(self):
        """Should accept valid interaction check request."""
        data = InteractionCheckRequest(
            patient_id=1,
            drug_name="Aspirin",
            atc_code="B01AC06",
        )
        assert data.patient_id == 1
        assert data.drug_name == "Aspirin"

    def test_patient_id_required(self):
        """Should require patient_id."""
        with pytest.raises(ValidationError):
            InteractionCheckRequest(
                patient_id=0,
                drug_name="Aspirin",
            )

    def test_drug_name_required(self):
        """Should require drug_name."""
        with pytest.raises(ValidationError):
            InteractionCheckRequest(
                patient_id=1,
                drug_name="",
            )

    def test_atc_code_optional(self):
        """ATC code should be optional."""
        data = InteractionCheckRequest(
            patient_id=1,
            drug_name="Unknown Drug",
        )
        assert data.atc_code is None


class TestFrequencyDisplayMap:
    """Test frequency display labels."""

    def test_all_standard_frequencies_mapped(self):
        """All standard frequencies should have display labels."""
        expected = ["OD", "BD", "TDS", "QDS", "PRN", "STAT", "nocte", "mane"]
        for freq in expected:
            assert freq in FREQUENCY_DISPLAY_MAP
            assert len(FREQUENCY_DISPLAY_MAP[freq]) > 0

    def test_od_is_once_daily(self):
        """OD should map to 'Once daily'."""
        assert "once daily" in FREQUENCY_DISPLAY_MAP["OD"].lower()

    def test_bd_is_twice_daily(self):
        """BD should map to 'Twice daily'."""
        assert "twice daily" in FREQUENCY_DISPLAY_MAP["BD"].lower()
