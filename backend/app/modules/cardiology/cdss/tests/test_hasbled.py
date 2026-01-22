"""
HAS-BLED Score Calculator Tests.

Validates the HAS-BLED score implementation and modifiable factor identification.
"""

import pytest

from app.modules.cardiology.cdss.calculators import calculate_hasbled
from app.modules.cardiology.cdss.models import HASBLEDInput


class TestHASBLEDScoring:
    """Test individual component scoring."""

    def test_baseline_score_zero(self):
        """Patient with no risk factors should score 0."""
        input_data = HASBLEDInput(
            hypertension_uncontrolled=False,
            abnormal_renal_function=False,
            abnormal_liver_function=False,
            stroke_history=False,
            bleeding_history=False,
            labile_inr=False,
            elderly=False,
            antiplatelet_or_nsaid=False,
            alcohol_abuse=False,
        )
        result = calculate_hasbled(input_data)
        assert result.total_score == 0
        assert result.risk_level == "Low"

    def test_hypertension_adds_1_point(self):
        """Uncontrolled hypertension should add 1 point."""
        input_data = HASBLEDInput(
            hypertension_uncontrolled=True,
            abnormal_renal_function=False,
            abnormal_liver_function=False,
            stroke_history=False,
            bleeding_history=False,
            labile_inr=False,
            elderly=False,
            antiplatelet_or_nsaid=False,
            alcohol_abuse=False,
        )
        result = calculate_hasbled(input_data)
        assert result.score_breakdown.get("Hypertension") == 1
        assert result.total_score == 1

    def test_renal_function_adds_1_point(self):
        """Abnormal renal function should add 1 point."""
        input_data = HASBLEDInput(
            hypertension_uncontrolled=False,
            abnormal_renal_function=True,
            abnormal_liver_function=False,
            stroke_history=False,
            bleeding_history=False,
            labile_inr=False,
            elderly=False,
            antiplatelet_or_nsaid=False,
            alcohol_abuse=False,
        )
        result = calculate_hasbled(input_data)
        assert result.score_breakdown.get("Abnormal_renal") == 1
        assert result.total_score == 1

    def test_liver_function_adds_1_point(self):
        """Abnormal liver function should add 1 point."""
        input_data = HASBLEDInput(
            hypertension_uncontrolled=False,
            abnormal_renal_function=False,
            abnormal_liver_function=True,
            stroke_history=False,
            bleeding_history=False,
            labile_inr=False,
            elderly=False,
            antiplatelet_or_nsaid=False,
            alcohol_abuse=False,
        )
        result = calculate_hasbled(input_data)
        assert result.score_breakdown.get("Abnormal_liver") == 1
        assert result.total_score == 1

    def test_stroke_history_adds_1_point(self):
        """Stroke history should add 1 point."""
        input_data = HASBLEDInput(
            hypertension_uncontrolled=False,
            abnormal_renal_function=False,
            abnormal_liver_function=False,
            stroke_history=True,
            bleeding_history=False,
            labile_inr=False,
            elderly=False,
            antiplatelet_or_nsaid=False,
            alcohol_abuse=False,
        )
        result = calculate_hasbled(input_data)
        assert result.score_breakdown.get("Stroke") == 1
        assert result.total_score == 1

    def test_bleeding_history_adds_1_point(self):
        """Bleeding history should add 1 point."""
        input_data = HASBLEDInput(
            hypertension_uncontrolled=False,
            abnormal_renal_function=False,
            abnormal_liver_function=False,
            stroke_history=False,
            bleeding_history=True,
            labile_inr=False,
            elderly=False,
            antiplatelet_or_nsaid=False,
            alcohol_abuse=False,
        )
        result = calculate_hasbled(input_data)
        assert result.score_breakdown.get("Bleeding") == 1
        assert result.total_score == 1

    def test_labile_inr_adds_1_point(self):
        """Labile INR should add 1 point."""
        input_data = HASBLEDInput(
            hypertension_uncontrolled=False,
            abnormal_renal_function=False,
            abnormal_liver_function=False,
            stroke_history=False,
            bleeding_history=False,
            labile_inr=True,
            elderly=False,
            antiplatelet_or_nsaid=False,
            alcohol_abuse=False,
        )
        result = calculate_hasbled(input_data)
        assert result.score_breakdown.get("Labile_INR") == 1
        assert result.total_score == 1

    def test_elderly_adds_1_point(self):
        """Elderly (>65) should add 1 point."""
        input_data = HASBLEDInput(
            hypertension_uncontrolled=False,
            abnormal_renal_function=False,
            abnormal_liver_function=False,
            stroke_history=False,
            bleeding_history=False,
            labile_inr=False,
            elderly=True,
            antiplatelet_or_nsaid=False,
            alcohol_abuse=False,
        )
        result = calculate_hasbled(input_data)
        assert result.score_breakdown.get("Elderly") == 1
        assert result.total_score == 1

    def test_drugs_adds_1_point(self):
        """Antiplatelet/NSAID use should add 1 point."""
        input_data = HASBLEDInput(
            hypertension_uncontrolled=False,
            abnormal_renal_function=False,
            abnormal_liver_function=False,
            stroke_history=False,
            bleeding_history=False,
            labile_inr=False,
            elderly=False,
            antiplatelet_or_nsaid=True,
            alcohol_abuse=False,
        )
        result = calculate_hasbled(input_data)
        assert result.score_breakdown.get("Drugs") == 1
        assert result.total_score == 1

    def test_alcohol_adds_1_point(self):
        """Alcohol abuse should add 1 point."""
        input_data = HASBLEDInput(
            hypertension_uncontrolled=False,
            abnormal_renal_function=False,
            abnormal_liver_function=False,
            stroke_history=False,
            bleeding_history=False,
            labile_inr=False,
            elderly=False,
            antiplatelet_or_nsaid=False,
            alcohol_abuse=True,
        )
        result = calculate_hasbled(input_data)
        assert result.score_breakdown.get("Alcohol") == 1
        assert result.total_score == 1


class TestHASBLEDRiskLevels:
    """Test risk level stratification."""

    def test_score_0_low_risk(self):
        """Score 0 should be Low risk."""
        input_data = HASBLEDInput(
            hypertension_uncontrolled=False,
            abnormal_renal_function=False,
            abnormal_liver_function=False,
            stroke_history=False,
            bleeding_history=False,
            labile_inr=False,
            elderly=False,
            antiplatelet_or_nsaid=False,
            alcohol_abuse=False,
        )
        result = calculate_hasbled(input_data)
        assert result.risk_level == "Low"

    def test_score_1_low_risk(self):
        """Score 1 should be Low risk."""
        input_data = HASBLEDInput(
            hypertension_uncontrolled=False,
            abnormal_renal_function=False,
            abnormal_liver_function=False,
            stroke_history=False,
            bleeding_history=False,
            labile_inr=False,
            elderly=True,  # 1 point
            antiplatelet_or_nsaid=False,
            alcohol_abuse=False,
        )
        result = calculate_hasbled(input_data)
        assert result.total_score == 1
        assert result.risk_level == "Low"

    def test_score_2_moderate_risk(self):
        """Score 2 should be Moderate risk."""
        input_data = HASBLEDInput(
            hypertension_uncontrolled=False,
            abnormal_renal_function=False,
            abnormal_liver_function=False,
            stroke_history=False,
            bleeding_history=True,  # 1 point
            labile_inr=False,
            elderly=True,  # 1 point
            antiplatelet_or_nsaid=False,
            alcohol_abuse=False,
        )
        result = calculate_hasbled(input_data)
        assert result.total_score == 2
        assert result.risk_level == "Moderate"

    def test_score_3_high_risk(self):
        """Score ≥3 should be High risk."""
        input_data = HASBLEDInput(
            hypertension_uncontrolled=True,  # 1 point
            abnormal_renal_function=False,
            abnormal_liver_function=False,
            stroke_history=False,
            bleeding_history=True,  # 1 point
            labile_inr=False,
            elderly=True,  # 1 point
            antiplatelet_or_nsaid=False,
            alcohol_abuse=False,
        )
        result = calculate_hasbled(input_data)
        assert result.total_score == 3
        assert result.risk_level == "High"


class TestHASBLEDModifiableFactors:
    """Test modifiable risk factor identification."""

    def test_hypertension_is_modifiable(self):
        """Hypertension should be identified as modifiable."""
        input_data = HASBLEDInput(
            hypertension_uncontrolled=True,
            abnormal_renal_function=False,
            abnormal_liver_function=False,
            stroke_history=False,
            bleeding_history=False,
            labile_inr=False,
            elderly=False,
            antiplatelet_or_nsaid=False,
            alcohol_abuse=False,
        )
        result = calculate_hasbled(input_data)
        assert len(result.modifiable_factors) == 1
        assert "blood pressure" in result.modifiable_factors[0].lower()

    def test_labile_inr_is_modifiable(self):
        """Labile INR should suggest DOAC."""
        input_data = HASBLEDInput(
            hypertension_uncontrolled=False,
            abnormal_renal_function=False,
            abnormal_liver_function=False,
            stroke_history=False,
            bleeding_history=False,
            labile_inr=True,
            elderly=False,
            antiplatelet_or_nsaid=False,
            alcohol_abuse=False,
        )
        result = calculate_hasbled(input_data)
        assert len(result.modifiable_factors) == 1
        assert "doac" in result.modifiable_factors[0].lower()

    def test_drugs_is_modifiable(self):
        """Drug use should be identified as modifiable."""
        input_data = HASBLEDInput(
            hypertension_uncontrolled=False,
            abnormal_renal_function=False,
            abnormal_liver_function=False,
            stroke_history=False,
            bleeding_history=False,
            labile_inr=False,
            elderly=False,
            antiplatelet_or_nsaid=True,
            alcohol_abuse=False,
        )
        result = calculate_hasbled(input_data)
        assert len(result.modifiable_factors) == 1
        assert "nsaid" in result.modifiable_factors[0].lower()

    def test_alcohol_is_modifiable(self):
        """Alcohol abuse should be identified as modifiable."""
        input_data = HASBLEDInput(
            hypertension_uncontrolled=False,
            abnormal_renal_function=False,
            abnormal_liver_function=False,
            stroke_history=False,
            bleeding_history=False,
            labile_inr=False,
            elderly=False,
            antiplatelet_or_nsaid=False,
            alcohol_abuse=True,
        )
        result = calculate_hasbled(input_data)
        assert len(result.modifiable_factors) == 1
        assert "alcohol" in result.modifiable_factors[0].lower()

    def test_multiple_modifiable_factors(self):
        """Multiple modifiable factors should all be listed."""
        input_data = HASBLEDInput(
            hypertension_uncontrolled=True,
            abnormal_renal_function=False,
            abnormal_liver_function=False,
            stroke_history=False,
            bleeding_history=False,
            labile_inr=True,
            elderly=False,
            antiplatelet_or_nsaid=True,
            alcohol_abuse=True,
        )
        result = calculate_hasbled(input_data)
        assert len(result.modifiable_factors) == 4


class TestHASBLEDRecommendations:
    """Test that high score doesn't contraindicate anticoagulation."""

    def test_high_score_does_not_contraindicate_anticoag(self):
        """High HAS-BLED should NOT contraindicate anticoagulation."""
        input_data = HASBLEDInput(
            hypertension_uncontrolled=True,
            abnormal_renal_function=True,
            abnormal_liver_function=True,
            stroke_history=True,
            bleeding_history=True,
            labile_inr=True,
            elderly=True,
            antiplatelet_or_nsaid=True,
            alcohol_abuse=True,
        )
        result = calculate_hasbled(input_data)
        assert result.total_score == 9
        assert result.risk_level == "High"
        # Critical: should NOT say to stop anticoagulation
        assert "not contraindicate" in result.recommendation.lower()
