"""
CHA₂DS₂-VASc Score Calculator Tests.

Validates the CHA₂DS₂-VASc score implementation against ESC Guidelines.
"""

import pytest

from app.modules.cardiology.cdss.calculators import calculate_cha2ds2vasc
from app.modules.cardiology.cdss.models import CHA2DS2VAScInput


class TestCHA2DS2VAScScoring:
    """Test individual component scoring."""

    def test_baseline_score_zero(self):
        """Young male with no risk factors should score 0."""
        input_data = CHA2DS2VAScInput(
            age=50,
            sex="male",
            congestive_heart_failure=False,
            hypertension=False,
            diabetes=False,
            stroke_tia_thromboembolism=False,
            vascular_disease=False,
        )
        result = calculate_cha2ds2vasc(input_data)
        assert result.total_score == 0
        assert result.adjusted_score == 0
        assert "no anticoagulation" in result.recommendation.lower()

    def test_chf_adds_1_point(self):
        """CHF should add 1 point."""
        input_data = CHA2DS2VAScInput(
            age=50,
            sex="male",
            congestive_heart_failure=True,
            hypertension=False,
            diabetes=False,
            stroke_tia_thromboembolism=False,
            vascular_disease=False,
        )
        result = calculate_cha2ds2vasc(input_data)
        assert result.score_breakdown.get("CHF") == 1
        assert result.total_score == 1

    def test_hypertension_adds_1_point(self):
        """Hypertension should add 1 point."""
        input_data = CHA2DS2VAScInput(
            age=50,
            sex="male",
            congestive_heart_failure=False,
            hypertension=True,
            diabetes=False,
            stroke_tia_thromboembolism=False,
            vascular_disease=False,
        )
        result = calculate_cha2ds2vasc(input_data)
        assert result.score_breakdown.get("Hypertension") == 1
        assert result.total_score == 1

    def test_age_75_or_older_adds_2_points(self):
        """Age ≥75 should add 2 points."""
        input_data = CHA2DS2VAScInput(
            age=75,
            sex="male",
            congestive_heart_failure=False,
            hypertension=False,
            diabetes=False,
            stroke_tia_thromboembolism=False,
            vascular_disease=False,
        )
        result = calculate_cha2ds2vasc(input_data)
        assert result.score_breakdown.get("Age_75_or_older") == 2
        assert result.total_score == 2

    def test_age_65_to_74_adds_1_point(self):
        """Age 65-74 should add 1 point."""
        input_data = CHA2DS2VAScInput(
            age=70,
            sex="male",
            congestive_heart_failure=False,
            hypertension=False,
            diabetes=False,
            stroke_tia_thromboembolism=False,
            vascular_disease=False,
        )
        result = calculate_cha2ds2vasc(input_data)
        assert result.score_breakdown.get("Age_65_to_74") == 1
        assert result.total_score == 1

    def test_diabetes_adds_1_point(self):
        """Diabetes should add 1 point."""
        input_data = CHA2DS2VAScInput(
            age=50,
            sex="male",
            congestive_heart_failure=False,
            hypertension=False,
            diabetes=True,
            stroke_tia_thromboembolism=False,
            vascular_disease=False,
        )
        result = calculate_cha2ds2vasc(input_data)
        assert result.score_breakdown.get("Diabetes") == 1
        assert result.total_score == 1

    def test_stroke_adds_2_points(self):
        """Prior stroke/TIA should add 2 points."""
        input_data = CHA2DS2VAScInput(
            age=50,
            sex="male",
            congestive_heart_failure=False,
            hypertension=False,
            diabetes=False,
            stroke_tia_thromboembolism=True,
            vascular_disease=False,
        )
        result = calculate_cha2ds2vasc(input_data)
        assert result.score_breakdown.get("Stroke_TIA") == 2
        assert result.total_score == 2

    def test_vascular_disease_adds_1_point(self):
        """Vascular disease should add 1 point."""
        input_data = CHA2DS2VAScInput(
            age=50,
            sex="male",
            congestive_heart_failure=False,
            hypertension=False,
            diabetes=False,
            stroke_tia_thromboembolism=False,
            vascular_disease=True,
        )
        result = calculate_cha2ds2vasc(input_data)
        assert result.score_breakdown.get("Vascular_disease") == 1
        assert result.total_score == 1

    def test_female_adds_1_point(self):
        """Female sex should add 1 point."""
        input_data = CHA2DS2VAScInput(
            age=50,
            sex="female",
            congestive_heart_failure=False,
            hypertension=False,
            diabetes=False,
            stroke_tia_thromboembolism=False,
            vascular_disease=False,
        )
        result = calculate_cha2ds2vasc(input_data)
        assert result.score_breakdown.get("Female") == 1
        assert result.total_score == 1


class TestCHA2DS2VAScSexAdjustment:
    """Test sex-adjusted score for treatment decisions."""

    def test_female_alone_adjusted_to_zero(self):
        """Female sex alone should have adjusted score of 0."""
        input_data = CHA2DS2VAScInput(
            age=50,
            sex="female",
            congestive_heart_failure=False,
            hypertension=False,
            diabetes=False,
            stroke_tia_thromboembolism=False,
            vascular_disease=False,
        )
        result = calculate_cha2ds2vasc(input_data)
        assert result.total_score == 1  # Raw score
        assert result.adjusted_score == 0  # Sex-adjusted
        assert "no anticoagulation" in result.recommendation.lower()

    def test_female_with_one_risk_factor(self):
        """Female with 1 risk factor should have adjusted score of 1."""
        input_data = CHA2DS2VAScInput(
            age=50,
            sex="female",
            congestive_heart_failure=False,
            hypertension=True,  # 1 point
            diabetes=False,
            stroke_tia_thromboembolism=False,
            vascular_disease=False,
        )
        result = calculate_cha2ds2vasc(input_data)
        assert result.total_score == 2  # Raw: female + HTN
        assert result.adjusted_score == 1  # Adjusted
        assert "consider" in result.recommendation.lower()

    def test_male_score_equals_adjusted(self):
        """Male score should equal adjusted score."""
        input_data = CHA2DS2VAScInput(
            age=70,
            sex="male",
            congestive_heart_failure=False,
            hypertension=True,
            diabetes=False,
            stroke_tia_thromboembolism=False,
            vascular_disease=False,
        )
        result = calculate_cha2ds2vasc(input_data)
        assert result.total_score == result.adjusted_score


class TestCHA2DS2VAScRecommendations:
    """Test anticoagulation recommendations."""

    def test_score_0_no_anticoag(self):
        """Score 0 - no anticoagulation."""
        input_data = CHA2DS2VAScInput(
            age=50,
            sex="male",
            congestive_heart_failure=False,
            hypertension=False,
            diabetes=False,
            stroke_tia_thromboembolism=False,
            vascular_disease=False,
        )
        result = calculate_cha2ds2vasc(input_data)
        assert result.adjusted_score == 0
        assert "no anticoagulation" in result.recommendation.lower()

    def test_score_1_consider_anticoag(self):
        """Score 1 - consider anticoagulation."""
        input_data = CHA2DS2VAScInput(
            age=70,  # 1 point
            sex="male",
            congestive_heart_failure=False,
            hypertension=False,
            diabetes=False,
            stroke_tia_thromboembolism=False,
            vascular_disease=False,
        )
        result = calculate_cha2ds2vasc(input_data)
        assert result.adjusted_score == 1
        assert "consider" in result.recommendation.lower()

    def test_score_2_or_more_anticoag_recommended(self):
        """Score ≥2 - anticoagulation recommended."""
        input_data = CHA2DS2VAScInput(
            age=75,  # 2 points
            sex="male",
            congestive_heart_failure=False,
            hypertension=False,
            diabetes=False,
            stroke_tia_thromboembolism=False,
            vascular_disease=False,
        )
        result = calculate_cha2ds2vasc(input_data)
        assert result.adjusted_score >= 2
        assert "recommended" in result.recommendation.lower()
        assert "doac" in result.recommendation.lower()


class TestCHA2DS2VAScMaxScore:
    """Test maximum score scenario."""

    def test_maximum_score_is_9(self):
        """Maximum possible score should be 9."""
        input_data = CHA2DS2VAScInput(
            age=80,  # 2 points
            sex="female",  # 1 point
            congestive_heart_failure=True,  # 1 point
            hypertension=True,  # 1 point
            diabetes=True,  # 1 point
            stroke_tia_thromboembolism=True,  # 2 points
            vascular_disease=True,  # 1 point
        )
        result = calculate_cha2ds2vasc(input_data)
        assert result.total_score == 9
