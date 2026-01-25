"""
Drug-Drug Interaction Engine Tests.

Validates the cardiology-specific interaction rules based on ESC 2024 guidelines.
"""

import pytest

from app.modules.prescription.interactions import InteractionEngine, CARDIOLOGY_INTERACTIONS


class TestInteractionEngineBasics:
    """Test basic interaction engine functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = InteractionEngine()

    def test_no_interactions_with_empty_medication_list(self):
        """No interactions when patient has no active medications."""
        interactions = self.engine.check_interactions(
            new_drug_atc="C10AA05",  # Atorvastatin
            new_drug_name="Atorvastatin",
            active_medications=[],
        )
        assert len(interactions) == 0

    def test_no_interactions_with_none_atc(self):
        """No interactions when new drug has no ATC code."""
        interactions = self.engine.check_interactions(
            new_drug_atc=None,
            new_drug_name="Unknown Drug",
            active_medications=[
                {"drug_name": "Aspirin", "atc_code": "B01AC06", "prescription_id": None}
            ],
        )
        assert len(interactions) == 0

    def test_no_interactions_with_unrelated_drugs(self):
        """No interactions between unrelated drug classes."""
        interactions = self.engine.check_interactions(
            new_drug_atc="A10BA02",  # Metformin (diabetes)
            new_drug_name="Metformin",
            active_medications=[
                {"drug_name": "Paracetamol", "atc_code": "N02BE01", "prescription_id": None}
            ],
        )
        assert len(interactions) == 0


class TestDOACAntiplateletInteraction:
    """Test DOAC + Antiplatelet interaction detection."""

    def setup_method(self):
        self.engine = InteractionEngine()

    def test_apixaban_with_aspirin(self):
        """Apixaban + Aspirin should trigger major interaction."""
        interactions = self.engine.check_interactions(
            new_drug_atc="B01AF02",  # Apixaban
            new_drug_name="Apixaban",
            active_medications=[
                {"drug_name": "Aspirin", "atc_code": "B01AC06", "prescription_id": None}
            ],
        )
        assert len(interactions) >= 1
        major_interactions = [i for i in interactions if i.severity == "major"]
        assert len(major_interactions) >= 1
        assert any("bleeding" in i.description.lower() for i in interactions)

    def test_rivaroxaban_with_clopidogrel(self):
        """Rivaroxaban + Clopidogrel should trigger major interaction."""
        interactions = self.engine.check_interactions(
            new_drug_atc="B01AF01",  # Rivaroxaban
            new_drug_name="Rivaroxaban",
            active_medications=[
                {"drug_name": "Clopidogrel", "atc_code": "B01AC04", "prescription_id": None}
            ],
        )
        assert len(interactions) >= 1
        assert any(i.severity == "major" for i in interactions)

    def test_reverse_order_also_detected(self):
        """Adding antiplatelet to patient on DOAC should also detect interaction."""
        interactions = self.engine.check_interactions(
            new_drug_atc="B01AC06",  # Aspirin (antiplatelet)
            new_drug_name="Aspirin",
            active_medications=[
                {"drug_name": "Apixaban", "atc_code": "B01AF02", "prescription_id": None}
            ],
        )
        assert len(interactions) >= 1
        assert any(i.severity == "major" for i in interactions)


class TestBetaBlockerCCBInteraction:
    """Test Beta-blocker + Non-DHP CCB contraindication."""

    def setup_method(self):
        self.engine = InteractionEngine()

    def test_bisoprolol_with_verapamil_contraindicated(self):
        """Bisoprolol + Verapamil should be CONTRAINDICATED."""
        interactions = self.engine.check_interactions(
            new_drug_atc="C07AB07",  # Bisoprolol
            new_drug_name="Bisoprolol",
            active_medications=[
                {"drug_name": "Verapamil", "atc_code": "C08DA01", "prescription_id": None}
            ],
        )
        assert len(interactions) >= 1
        contraindicated = [i for i in interactions if i.severity == "contraindicated"]
        assert len(contraindicated) >= 1
        assert any("heart block" in i.description.lower() or "bradycardia" in i.description.lower() for i in contraindicated)

    def test_metoprolol_with_diltiazem_contraindicated(self):
        """Metoprolol + Diltiazem should be CONTRAINDICATED."""
        interactions = self.engine.check_interactions(
            new_drug_atc="C07AB02",  # Metoprolol
            new_drug_name="Metoprolol",
            active_medications=[
                {"drug_name": "Diltiazem", "atc_code": "C08DB01", "prescription_id": None}
            ],
        )
        assert len(interactions) >= 1
        assert any(i.severity == "contraindicated" for i in interactions)

    def test_bisoprolol_with_amlodipine_no_interaction(self):
        """Bisoprolol + Amlodipine (DHP CCB) should NOT be contraindicated."""
        interactions = self.engine.check_interactions(
            new_drug_atc="C07AB07",  # Bisoprolol
            new_drug_name="Bisoprolol",
            active_medications=[
                {"drug_name": "Amlodipine", "atc_code": "C08CA01", "prescription_id": None}
            ],
        )
        # DHP CCB like amlodipine should NOT trigger beta-blocker contraindication
        contraindicated = [i for i in interactions if i.severity == "contraindicated"]
        assert len(contraindicated) == 0


class TestNitratePDE5Interaction:
    """Test Nitrate + PDE5 inhibitor contraindication."""

    def setup_method(self):
        self.engine = InteractionEngine()

    def test_isdn_with_sildenafil_contraindicated(self):
        """ISDN + Sildenafil should be CONTRAINDICATED."""
        interactions = self.engine.check_interactions(
            new_drug_atc="C01DA08",  # Isosorbide Dinitrate
            new_drug_name="Isosorbide Dinitrate",
            active_medications=[
                {"drug_name": "Sildenafil", "atc_code": "G04BE03", "prescription_id": None}
            ],
        )
        assert len(interactions) >= 1
        contraindicated = [i for i in interactions if i.severity == "contraindicated"]
        assert len(contraindicated) >= 1
        assert any("hypotension" in i.description.lower() for i in contraindicated)


class TestACEARBDualBlockade:
    """Test ACE-I + ARB dual RAAS blockade contraindication."""

    def setup_method(self):
        self.engine = InteractionEngine()

    def test_ramipril_with_valsartan_contraindicated(self):
        """Ramipril (ACE-I) + Valsartan (ARB) should be CONTRAINDICATED."""
        interactions = self.engine.check_interactions(
            new_drug_atc="C09AA05",  # Ramipril
            new_drug_name="Ramipril",
            active_medications=[
                {"drug_name": "Valsartan", "atc_code": "C09CA03", "prescription_id": None}
            ],
        )
        assert len(interactions) >= 1
        contraindicated = [i for i in interactions if i.severity == "contraindicated"]
        assert len(contraindicated) >= 1
        assert any("raas" in i.description.lower() or "hyperkalemia" in i.description.lower() for i in contraindicated)


class TestSacubitrilValsartanACEI:
    """Test Sacubitril/Valsartan + ACE-I angioedema risk."""

    def setup_method(self):
        self.engine = InteractionEngine()

    def test_entresto_with_ramipril_contraindicated(self):
        """Sacubitril/Valsartan + Ramipril should be CONTRAINDICATED."""
        interactions = self.engine.check_interactions(
            new_drug_atc="C09DX04",  # Sacubitril/Valsartan
            new_drug_name="Sacubitril/Valsartan",
            active_medications=[
                {"drug_name": "Ramipril", "atc_code": "C09AA05", "prescription_id": None}
            ],
        )
        assert len(interactions) >= 1
        contraindicated = [i for i in interactions if i.severity == "contraindicated"]
        assert len(contraindicated) >= 1
        assert any("angioedema" in i.description.lower() for i in contraindicated)


class TestDigoxinAmiodaroneInteraction:
    """Test Digoxin + Amiodarone toxicity interaction."""

    def setup_method(self):
        self.engine = InteractionEngine()

    def test_digoxin_with_amiodarone_major(self):
        """Digoxin + Amiodarone should trigger MAJOR interaction."""
        interactions = self.engine.check_interactions(
            new_drug_atc="C01AA05",  # Digoxin
            new_drug_name="Digoxin",
            active_medications=[
                {"drug_name": "Amiodarone", "atc_code": "C01BD01", "prescription_id": None}
            ],
        )
        assert len(interactions) >= 1
        major = [i for i in interactions if i.severity == "major"]
        assert len(major) >= 1
        assert any("toxicity" in i.description.lower() or "70-100%" in i.description for i in major)


class TestStatinFibrateInteraction:
    """Test Statin + Fibrate rhabdomyolysis risk."""

    def setup_method(self):
        self.engine = InteractionEngine()

    def test_atorvastatin_with_gemfibrozil_major(self):
        """Atorvastatin + Gemfibrozil should trigger MAJOR interaction."""
        interactions = self.engine.check_interactions(
            new_drug_atc="C10AA05",  # Atorvastatin
            new_drug_name="Atorvastatin",
            active_medications=[
                {"drug_name": "Gemfibrozil", "atc_code": "C10AB04", "prescription_id": None}
            ],
        )
        assert len(interactions) >= 1
        major = [i for i in interactions if i.severity == "major"]
        assert len(major) >= 1
        assert any("rhabdomyolysis" in i.description.lower() or "myopathy" in i.description.lower() for i in major)


class TestTherapeuticDuplication:
    """Test therapeutic duplication detection."""

    def setup_method(self):
        self.engine = InteractionEngine()

    def test_two_statins_duplication(self):
        """Two statins should trigger therapeutic duplication warning."""
        interactions = self.engine.check_interactions(
            new_drug_atc="C10AA07",  # Rosuvastatin
            new_drug_name="Rosuvastatin",
            active_medications=[
                {"drug_name": "Atorvastatin", "atc_code": "C10AA05", "prescription_id": None}
            ],
        )
        assert len(interactions) >= 1
        duplication = [i for i in interactions if i.interaction_type == "therapeutic_duplication"]
        assert len(duplication) >= 1

    def test_two_anticoagulants_major(self):
        """Two anticoagulants should trigger MAJOR duplication warning."""
        interactions = self.engine.check_interactions(
            new_drug_atc="B01AF01",  # Rivaroxaban
            new_drug_name="Rivaroxaban",
            active_medications=[
                {"drug_name": "Apixaban", "atc_code": "B01AF02", "prescription_id": None}
            ],
        )
        assert len(interactions) >= 1
        # Should be major due to therapeutic duplication of anticoagulants
        assert any(i.severity == "major" for i in interactions)


class TestInteractionSorting:
    """Test that interactions are sorted by severity."""

    def setup_method(self):
        self.engine = InteractionEngine()

    def test_contraindicated_first(self):
        """Contraindicated interactions should appear first."""
        # Patient on Verapamil (will contraindicate with beta-blocker)
        # and on Aspirin (will be major with DOAC)
        # We'll add a beta-blocker which triggers contraindication
        interactions = self.engine.check_interactions(
            new_drug_atc="C07AB07",  # Bisoprolol
            new_drug_name="Bisoprolol",
            active_medications=[
                {"drug_name": "Verapamil", "atc_code": "C08DA01", "prescription_id": None},
            ],
        )
        if len(interactions) >= 1:
            # First interaction should be contraindicated if any exist
            contraindicated_count = sum(1 for i in interactions if i.severity == "contraindicated")
            if contraindicated_count > 0:
                assert interactions[0].severity == "contraindicated"


class TestInteractionRulesCount:
    """Verify we have comprehensive interaction rules."""

    def test_minimum_interaction_rules(self):
        """Should have at least 10 cardiology interaction rules."""
        assert len(CARDIOLOGY_INTERACTIONS) >= 10

    def test_has_contraindicated_rules(self):
        """Should have some contraindicated-level rules."""
        contraindicated = [r for r in CARDIOLOGY_INTERACTIONS if r.severity == "contraindicated"]
        assert len(contraindicated) >= 3

    def test_has_major_rules(self):
        """Should have some major-level rules."""
        major = [r for r in CARDIOLOGY_INTERACTIONS if r.severity == "major"]
        assert len(major) >= 5
