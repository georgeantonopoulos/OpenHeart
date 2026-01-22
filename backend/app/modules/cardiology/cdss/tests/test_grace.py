"""
GRACE Score Calculator Tests.

Validates the GRACE score implementation against published point tables
and known clinical scenarios.
"""

import pytest

from app.modules.cardiology.cdss.calculators import calculate_grace_score
from app.modules.cardiology.cdss.models import GRACEInput, KillipClass


class TestGRACEAgePoints:
    """Test age scoring against validated table."""

    @pytest.mark.parametrize(
        "age,expected_points",
        [
            (25, 0),    # <30
            (29, 0),    # <30
            (30, 8),    # 30-39
            (35, 8),    # 30-39
            (39, 8),    # 30-39
            (40, 25),   # 40-49
            (45, 25),   # 40-49
            (50, 41),   # 50-59
            (55, 41),   # 50-59
            (60, 58),   # 60-69
            (65, 58),   # 60-69
            (70, 75),   # 70-79
            (75, 75),   # 70-79
            (80, 91),   # 80-89
            (85, 91),   # 80-89
            (90, 100),  # ≥90
            (95, 100),  # ≥90
        ],
    )
    def test_age_points_correct(self, age: int, expected_points: int):
        """Verify age points match validated table."""
        input_data = GRACEInput(
            age=age,
            heart_rate=50,  # 0 points
            systolic_bp=200,  # 0 points
            creatinine_mg_dl=0.3,  # 1 point
            killip_class=KillipClass.I,  # 0 points
            cardiac_arrest_at_admission=False,
            st_segment_deviation=False,
            elevated_cardiac_enzymes=False,
        )
        result = calculate_grace_score(input_data)
        assert result.score_breakdown["age"] == expected_points


class TestGRACEHeartRatePoints:
    """Test heart rate scoring against validated table."""

    @pytest.mark.parametrize(
        "hr,expected_points",
        [
            (40, 0),    # <50
            (50, 3),    # 50-69
            (60, 3),    # 50-69
            (70, 9),    # 70-89
            (80, 9),    # 70-89
            (90, 15),   # 90-109
            (100, 15),  # 90-109
            (110, 24),  # 110-149
            (140, 24),  # 110-149
            (150, 38),  # 150-199
            (180, 38),  # 150-199
            (200, 46),  # ≥200
            (220, 46),  # ≥200
        ],
    )
    def test_heart_rate_points_correct(self, hr: int, expected_points: int):
        """Verify heart rate points match validated table."""
        input_data = GRACEInput(
            age=25,  # 0 points
            heart_rate=hr,
            systolic_bp=200,  # 0 points
            creatinine_mg_dl=0.3,  # 1 point
            killip_class=KillipClass.I,  # 0 points
            cardiac_arrest_at_admission=False,
            st_segment_deviation=False,
            elevated_cardiac_enzymes=False,
        )
        result = calculate_grace_score(input_data)
        assert result.score_breakdown["heart_rate"] == expected_points


class TestGRACESystolicBPPoints:
    """Test systolic BP scoring (lower BP = higher risk)."""

    @pytest.mark.parametrize(
        "sbp,expected_points",
        [
            (60, 58),   # <80 (cardiogenic shock range)
            (80, 53),   # 80-99
            (90, 53),   # 80-99
            (100, 43),  # 100-119
            (110, 43),  # 100-119
            (120, 34),  # 120-139
            (130, 34),  # 120-139
            (140, 24),  # 140-159
            (150, 24),  # 140-159
            (160, 10),  # 160-199
            (180, 10),  # 160-199
            (200, 0),   # ≥200
            (220, 0),   # ≥200
        ],
    )
    def test_systolic_bp_points_correct(self, sbp: int, expected_points: int):
        """Verify systolic BP points match validated table."""
        input_data = GRACEInput(
            age=25,  # 0 points
            heart_rate=40,  # 0 points
            systolic_bp=sbp,
            creatinine_mg_dl=0.3,  # 1 point
            killip_class=KillipClass.I,  # 0 points
            cardiac_arrest_at_admission=False,
            st_segment_deviation=False,
            elevated_cardiac_enzymes=False,
        )
        result = calculate_grace_score(input_data)
        assert result.score_breakdown["systolic_bp"] == expected_points


class TestGRACEKillipClass:
    """Test Killip class scoring."""

    @pytest.mark.parametrize(
        "killip,expected_points",
        [
            (KillipClass.I, 0),
            (KillipClass.II, 20),
            (KillipClass.III, 39),
            (KillipClass.IV, 59),
        ],
    )
    def test_killip_points_correct(self, killip: KillipClass, expected_points: int):
        """Verify Killip class points."""
        input_data = GRACEInput(
            age=25,
            heart_rate=40,
            systolic_bp=200,
            creatinine_mg_dl=0.3,
            killip_class=killip,
            cardiac_arrest_at_admission=False,
            st_segment_deviation=False,
            elevated_cardiac_enzymes=False,
        )
        result = calculate_grace_score(input_data)
        assert result.score_breakdown["killip_class"] == expected_points


class TestGRACEBinaryFactors:
    """Test binary risk factor scoring."""

    def test_cardiac_arrest_adds_39_points(self):
        """Cardiac arrest at admission adds 39 points."""
        input_data = GRACEInput(
            age=25,
            heart_rate=40,
            systolic_bp=200,
            creatinine_mg_dl=0.3,
            killip_class=KillipClass.I,
            cardiac_arrest_at_admission=True,
            st_segment_deviation=False,
            elevated_cardiac_enzymes=False,
        )
        result = calculate_grace_score(input_data)
        assert result.score_breakdown.get("cardiac_arrest") == 39

    def test_st_deviation_adds_28_points(self):
        """ST-segment deviation adds 28 points."""
        input_data = GRACEInput(
            age=25,
            heart_rate=40,
            systolic_bp=200,
            creatinine_mg_dl=0.3,
            killip_class=KillipClass.I,
            cardiac_arrest_at_admission=False,
            st_segment_deviation=True,
            elevated_cardiac_enzymes=False,
        )
        result = calculate_grace_score(input_data)
        assert result.score_breakdown.get("st_deviation") == 28

    def test_elevated_enzymes_adds_14_points(self):
        """Elevated cardiac enzymes adds 14 points."""
        input_data = GRACEInput(
            age=25,
            heart_rate=40,
            systolic_bp=200,
            creatinine_mg_dl=0.3,
            killip_class=KillipClass.I,
            cardiac_arrest_at_admission=False,
            st_segment_deviation=False,
            elevated_cardiac_enzymes=True,
        )
        result = calculate_grace_score(input_data)
        assert result.score_breakdown.get("elevated_enzymes") == 14


class TestGRACERiskStratification:
    """Test risk category thresholds."""

    def test_low_risk_at_108(self):
        """Score of 108 should be Low risk."""
        # Need to construct a patient with exactly 108 points
        input_data = GRACEInput(
            age=60,      # 58 points
            heart_rate=90,  # 15 points
            systolic_bp=120,  # 34 points
            creatinine_mg_dl=0.3,  # 1 point = 108 total
            killip_class=KillipClass.I,
            cardiac_arrest_at_admission=False,
            st_segment_deviation=False,
            elevated_cardiac_enzymes=False,
        )
        result = calculate_grace_score(input_data)
        assert result.total_score == 108
        assert result.risk_category == "Low"

    def test_intermediate_risk_at_109(self):
        """Score of 109 should be Intermediate risk."""
        input_data = GRACEInput(
            age=60,      # 58 points
            heart_rate=90,  # 15 points
            systolic_bp=120,  # 34 points
            creatinine_mg_dl=0.5,  # 4 points = 111 total
            killip_class=KillipClass.I,
            cardiac_arrest_at_admission=False,
            st_segment_deviation=False,
            elevated_cardiac_enzymes=False,
        )
        result = calculate_grace_score(input_data)
        assert result.total_score > 108
        assert result.total_score <= 140
        assert result.risk_category == "Intermediate"

    def test_high_risk_above_140(self):
        """Score above 140 should be High risk."""
        input_data = GRACEInput(
            age=80,      # 91 points
            heart_rate=120,  # 24 points
            systolic_bp=80,  # 53 points
            creatinine_mg_dl=1.5,  # 10 points
            killip_class=KillipClass.II,  # 20 points
            cardiac_arrest_at_admission=False,
            st_segment_deviation=True,  # 28 points
            elevated_cardiac_enzymes=True,  # 14 points
        )
        result = calculate_grace_score(input_data)
        assert result.total_score > 140
        assert result.risk_category == "High"


class TestGRACEClinicalScenarios:
    """Test realistic clinical scenarios."""

    def test_typical_stemi_patient(self):
        """65yo male with STEMI - should be high risk."""
        input_data = GRACEInput(
            age=65,
            heart_rate=95,
            systolic_bp=110,
            creatinine_mg_dl=1.1,
            killip_class=KillipClass.I,
            cardiac_arrest_at_admission=False,
            st_segment_deviation=True,
            elevated_cardiac_enzymes=True,
        )
        result = calculate_grace_score(input_data)
        # Should be elevated due to ST deviation and enzymes
        assert result.total_score >= 108  # At least intermediate
        assert "invasive" in result.recommendation.lower()

    def test_low_risk_unstable_angina(self):
        """45yo with chest pain, negative enzymes - should be low risk."""
        input_data = GRACEInput(
            age=45,
            heart_rate=75,
            systolic_bp=140,
            creatinine_mg_dl=0.9,
            killip_class=KillipClass.I,
            cardiac_arrest_at_admission=False,
            st_segment_deviation=False,
            elevated_cardiac_enzymes=False,
        )
        result = calculate_grace_score(input_data)
        assert result.risk_category == "Low"
        assert "conservative" in result.recommendation.lower()

    def test_elderly_with_cardiogenic_shock(self):
        """85yo with cardiogenic shock - should be very high risk."""
        input_data = GRACEInput(
            age=85,
            heart_rate=130,
            systolic_bp=70,
            creatinine_mg_dl=2.5,
            killip_class=KillipClass.IV,
            cardiac_arrest_at_admission=True,
            st_segment_deviation=True,
            elevated_cardiac_enzymes=True,
        )
        result = calculate_grace_score(input_data)
        assert result.risk_category == "High"
        assert result.total_score > 200  # Very high score
        assert "urgent" in result.recommendation.lower()
