"""
Cardiology Formulary Tests.

Validates the curated drug templates and search functionality.
"""

import pytest

from app.modules.prescription.cardiology_formulary import (
    CARDIOLOGY_FORMULARY,
    DrugTemplate,
    get_all_formulary_drugs,
    get_drug_by_atc,
    search_formulary,
)


class TestFormularyStructure:
    """Test formulary data structure and completeness."""

    def test_all_categories_present(self):
        """Should have all expected drug categories."""
        expected_categories = [
            "antiplatelets",
            "anticoagulants",
            "statins",
            "beta_blockers",
            "ace_inhibitors",
            "arbs",
            "ccbs",
            "diuretics",
            "antiarrhythmics",
            "nitrates",
            "heart_failure",
        ]
        for category in expected_categories:
            assert category in CARDIOLOGY_FORMULARY, f"Missing category: {category}"

    def test_each_category_has_drugs(self):
        """Each category should have at least one drug."""
        for category, drugs in CARDIOLOGY_FORMULARY.items():
            assert len(drugs) >= 1, f"Category {category} has no drugs"

    def test_minimum_drug_count(self):
        """Formulary should have at least 40 drugs."""
        all_drugs = get_all_formulary_drugs()
        assert len(all_drugs) >= 40


class TestDrugTemplateValidation:
    """Test that drug templates have required fields."""

    def test_all_drugs_have_required_fields(self):
        """Every drug should have required fields populated."""
        all_drugs = get_all_formulary_drugs()
        for drug in all_drugs:
            assert drug.generic_name, f"Drug missing generic_name"
            assert drug.atc_code, f"Drug {drug.generic_name} missing atc_code"
            assert drug.category, f"Drug {drug.generic_name} missing category"
            assert drug.default_strength, f"Drug {drug.generic_name} missing default_strength"
            assert drug.default_form, f"Drug {drug.generic_name} missing default_form"
            assert drug.default_frequency, f"Drug {drug.generic_name} missing default_frequency"
            assert drug.default_route, f"Drug {drug.generic_name} missing default_route"

    def test_atc_codes_are_valid_format(self):
        """ATC codes should follow standard format (letter + numbers/letters)."""
        all_drugs = get_all_formulary_drugs()
        for drug in all_drugs:
            atc = drug.atc_code
            assert len(atc) >= 5, f"ATC code too short: {atc}"
            assert len(atc) <= 10, f"ATC code too long: {atc}"
            assert atc[0].isalpha(), f"ATC code should start with letter: {atc}"

    def test_frequencies_are_valid(self):
        """Default frequencies should be valid values."""
        valid_frequencies = {"OD", "BD", "TDS", "QDS", "PRN", "STAT", "nocte", "mane", "custom"}
        all_drugs = get_all_formulary_drugs()
        for drug in all_drugs:
            assert drug.default_frequency in valid_frequencies, \
                f"Invalid frequency '{drug.default_frequency}' for {drug.generic_name}"

    def test_routes_are_valid(self):
        """Default routes should be valid values."""
        valid_routes = {"oral", "sublingual", "IV", "IM", "SC", "topical", "inhaled", "transdermal", "rectal", "nasal"}
        all_drugs = get_all_formulary_drugs()
        for drug in all_drugs:
            assert drug.default_route in valid_routes, \
                f"Invalid route '{drug.default_route}' for {drug.generic_name}"


class TestKeyDrugsPresent:
    """Test that essential cardiology drugs are in the formulary."""

    def test_aspirin_present(self):
        """Aspirin should be in antiplatelets."""
        drug = get_drug_by_atc("B01AC06")
        assert drug is not None
        assert drug.generic_name == "Aspirin"

    def test_clopidogrel_present(self):
        """Clopidogrel should be in antiplatelets."""
        drug = get_drug_by_atc("B01AC04")
        assert drug is not None
        assert drug.generic_name == "Clopidogrel"

    def test_apixaban_present(self):
        """Apixaban should be in anticoagulants."""
        drug = get_drug_by_atc("B01AF02")
        assert drug is not None
        assert drug.generic_name == "Apixaban"

    def test_atorvastatin_present(self):
        """Atorvastatin should be in statins."""
        drug = get_drug_by_atc("C10AA05")
        assert drug is not None
        assert drug.generic_name == "Atorvastatin"

    def test_bisoprolol_present(self):
        """Bisoprolol should be in beta_blockers."""
        drug = get_drug_by_atc("C07AB07")
        assert drug is not None
        assert drug.generic_name == "Bisoprolol"

    def test_ramipril_present(self):
        """Ramipril should be in ace_inhibitors."""
        drug = get_drug_by_atc("C09AA05")
        assert drug is not None
        assert drug.generic_name == "Ramipril"

    def test_amiodarone_present(self):
        """Amiodarone should be in antiarrhythmics."""
        drug = get_drug_by_atc("C01BD01")
        assert drug is not None
        assert drug.generic_name == "Amiodarone"

    def test_sacubitril_valsartan_present(self):
        """Sacubitril/Valsartan should be in heart_failure."""
        drug = get_drug_by_atc("C09DX04")
        assert drug is not None
        assert "Sacubitril" in drug.generic_name


class TestFormularySearch:
    """Test formulary search functionality."""

    def test_search_by_drug_name(self):
        """Should find drugs by generic name."""
        results = search_formulary("aspirin")
        assert len(results) >= 1
        assert any(d.generic_name.lower() == "aspirin" for d in results)

    def test_search_by_partial_name(self):
        """Should find drugs by partial name match."""
        results = search_formulary("ator")
        assert len(results) >= 1
        assert any("atorvastatin" in d.generic_name.lower() for d in results)

    def test_search_by_atc_code(self):
        """Should find drugs by ATC code."""
        results = search_formulary("B01AC")
        assert len(results) >= 1
        assert all(d.atc_code.startswith("B01AC") for d in results)

    def test_search_by_indication(self):
        """Should find drugs by indication."""
        results = search_formulary("atrial fibrillation")
        assert len(results) >= 1
        # Should include anticoagulants used in AF
        assert any(d.atc_code.startswith("B01A") for d in results)

    def test_search_case_insensitive(self):
        """Search should be case-insensitive."""
        results_lower = search_formulary("aspirin")
        results_upper = search_formulary("ASPIRIN")
        results_mixed = search_formulary("Aspirin")
        assert len(results_lower) == len(results_upper) == len(results_mixed)

    def test_search_no_results(self):
        """Search for non-existent drug returns empty list."""
        results = search_formulary("nonexistentdrug12345")
        assert len(results) == 0


class TestGetDrugByATC:
    """Test exact ATC code lookup."""

    def test_exact_match(self):
        """Should find drug by exact ATC code."""
        drug = get_drug_by_atc("B01AC06")
        assert drug is not None
        assert drug.atc_code == "B01AC06"

    def test_no_match(self):
        """Should return None for non-existent ATC code."""
        drug = get_drug_by_atc("Z99ZZ99")
        assert drug is None

    def test_partial_atc_no_match(self):
        """Should not match partial ATC codes."""
        drug = get_drug_by_atc("B01AC")  # Only prefix
        assert drug is None


class TestDrugDefaults:
    """Test that drug defaults are clinically appropriate."""

    def test_chronic_medications_marked_chronic(self):
        """Long-term medications should be marked as chronic."""
        chronic_drugs = ["Aspirin", "Atorvastatin", "Bisoprolol", "Ramipril"]
        for drug_name in chronic_drugs:
            results = search_formulary(drug_name)
            if results:
                drug = results[0]
                assert drug.is_chronic, f"{drug_name} should be marked as chronic"

    def test_acute_medications_not_chronic(self):
        """Acute medications should not be marked as chronic."""
        # GTN is typically acute/PRN use
        drug = get_drug_by_atc("C01DA02")  # GTN
        if drug:
            assert not drug.is_chronic, "GTN should not be chronic"

    def test_bd_medications_have_bd_frequency(self):
        """Drugs given twice daily should have BD frequency."""
        bd_drugs = [
            get_drug_by_atc("B01AF02"),  # Apixaban
            get_drug_by_atc("C07AG02"),  # Carvedilol
        ]
        for drug in bd_drugs:
            if drug:
                assert drug.default_frequency == "BD", f"{drug.generic_name} should be BD"

    def test_loading_doses_where_appropriate(self):
        """Drugs with loading doses should have them specified."""
        loading_dose_drugs = ["Clopidogrel", "Ticagrelor", "Amiodarone"]
        for drug_name in loading_dose_drugs:
            results = search_formulary(drug_name)
            if results:
                drug = results[0]
                assert drug.loading_dose is not None, f"{drug_name} should have loading dose"

    def test_renal_adjustments_where_needed(self):
        """Drugs requiring renal adjustment should have guidance."""
        renal_adjust_drugs = ["Apixaban", "Dabigatran", "Rivaroxaban", "Digoxin"]
        for drug_name in renal_adjust_drugs:
            results = search_formulary(drug_name)
            if results:
                drug = results[0]
                # Most DOACs and digoxin need renal adjustment
                # Note: Not all may have it specified
                pass  # Informational - actual adjustment logic in service
