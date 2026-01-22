"""
CDSS Risk Calculators for OpenHeart Cyprus.

Validated implementations of clinical risk scoring algorithms.
All point tables have been verified against published guidelines:
- GRACE: ESC Guidelines on ACS
- CHA₂DS₂-VASc: ESC Guidelines on AF
- HAS-BLED: ESC Guidelines on AF

IMPORTANT: These algorithms are for clinical decision support only.
Final treatment decisions must be made by qualified healthcare professionals.
"""

from datetime import datetime, timezone

from app.modules.cardiology.cdss.models import (
    CHA2DS2VAScInput,
    CHA2DS2VAScResult,
    GRACEInput,
    GRACEResult,
    HASBLEDInput,
    HASBLEDResult,
    KillipClass,
)


# =============================================================================
# GRACE Score Calculator
# =============================================================================

# Validated point tables from GRACE ACS Risk Calculator
# Source: https://www.outcomes-umassmed.org/grace/

GRACE_AGE_POINTS = [
    (30, 0),    # <30 years
    (40, 8),    # 30-39 years
    (50, 25),   # 40-49 years
    (60, 41),   # 50-59 years
    (70, 58),   # 60-69 years
    (80, 75),   # 70-79 years
    (90, 91),   # 80-89 years
    (float("inf"), 100),  # ≥90 years
]

GRACE_HR_POINTS = [
    (50, 0),    # <50 bpm
    (70, 3),    # 50-69 bpm
    (90, 9),    # 70-89 bpm
    (110, 15),  # 90-109 bpm
    (150, 24),  # 110-149 bpm
    (200, 38),  # 150-199 bpm
    (float("inf"), 46),  # ≥200 bpm
]

# Note: Lower SBP = higher points (worse prognosis in ACS)
GRACE_SBP_POINTS = [
    (80, 58),   # <80 mmHg
    (100, 53),  # 80-99 mmHg
    (120, 43),  # 100-119 mmHg
    (140, 34),  # 120-139 mmHg
    (160, 24),  # 140-159 mmHg
    (200, 10),  # 160-199 mmHg
    (float("inf"), 0),  # ≥200 mmHg
]

GRACE_CREATININE_POINTS = [
    (0.4, 1),   # 0-0.39 mg/dL
    (0.8, 4),   # 0.4-0.79 mg/dL
    (1.2, 7),   # 0.8-1.19 mg/dL
    (1.6, 10),  # 1.2-1.59 mg/dL
    (2.0, 13),  # 1.6-1.99 mg/dL
    (4.0, 21),  # 2.0-3.99 mg/dL
    (float("inf"), 28),  # ≥4.0 mg/dL
]

GRACE_KILLIP_POINTS = {
    KillipClass.I: 0,    # No heart failure
    KillipClass.II: 20,  # Rales, S3 gallop, venous hypertension
    KillipClass.III: 39, # Frank pulmonary edema
    KillipClass.IV: 59,  # Cardiogenic shock
}


def _get_points_from_table(value: float, table: list[tuple[float, int]]) -> int:
    """Get points from a threshold table."""
    for threshold, points in table:
        if value < threshold:
            return points
    return table[-1][1]  # Return last value if beyond all thresholds


def calculate_grace_score(input_data: GRACEInput) -> GRACEResult:
    """
    Calculate GRACE Score for ACS risk stratification.

    The GRACE (Global Registry of Acute Coronary Events) Score
    estimates in-hospital mortality risk for patients with
    Acute Coronary Syndrome (STEMI, NSTEMI, Unstable Angina).

    Validated against ESC Guidelines and GRACE ACS Risk Calculator.
    Maximum possible score: 372

    Args:
        input_data: GRACE input parameters

    Returns:
        GRACEResult with score, risk category, and recommendations
    """
    breakdown: dict[str, int] = {}
    total_score = 0

    # Age points (CORRECTED from original implementation)
    age_points = _get_points_from_table(input_data.age, GRACE_AGE_POINTS)
    breakdown["age"] = age_points
    total_score += age_points

    # Heart rate points
    hr_points = _get_points_from_table(input_data.heart_rate, GRACE_HR_POINTS)
    breakdown["heart_rate"] = hr_points
    total_score += hr_points

    # Systolic BP points (lower is worse)
    sbp_points = _get_points_from_table(input_data.systolic_bp, GRACE_SBP_POINTS)
    breakdown["systolic_bp"] = sbp_points
    total_score += sbp_points

    # Creatinine points
    cr_points = _get_points_from_table(
        input_data.creatinine_mg_dl, GRACE_CREATININE_POINTS
    )
    breakdown["creatinine"] = cr_points
    total_score += cr_points

    # Killip class points
    killip_points = GRACE_KILLIP_POINTS[input_data.killip_class]
    breakdown["killip_class"] = killip_points
    total_score += killip_points

    # Binary factors
    if input_data.cardiac_arrest_at_admission:
        breakdown["cardiac_arrest"] = 39
        total_score += 39

    if input_data.st_segment_deviation:
        breakdown["st_deviation"] = 28
        total_score += 28

    if input_data.elevated_cardiac_enzymes:
        breakdown["elevated_enzymes"] = 14
        total_score += 14

    # Risk stratification based on validated thresholds
    if total_score <= 108:
        risk_category = "Low"
        mortality_estimate = "<1%"
        recommendation = (
            "Conservative strategy appropriate. "
            "Consider non-invasive risk stratification with stress testing. "
            "Discharge may be considered if stress test is negative."
        )
    elif total_score <= 140:
        risk_category = "Intermediate"
        mortality_estimate = "1-3%"
        recommendation = (
            "Early invasive strategy recommended within 72 hours. "
            "Continue dual antiplatelet therapy and anticoagulation. "
            "Monitor closely for clinical deterioration."
        )
    else:
        risk_category = "High"
        mortality_estimate = ">3%"
        recommendation = (
            "URGENT invasive strategy within 24 hours. "
            "Transfer to facility with catheterization capability if needed. "
            "ICU-level monitoring recommended. "
            "Ensure adequate antithrombotic therapy."
        )

    return GRACEResult(
        total_score=total_score,
        risk_category=risk_category,
        in_hospital_mortality_estimate=mortality_estimate,
        recommendation=recommendation,
        score_breakdown=breakdown,
        calculation_timestamp=datetime.now(timezone.utc),
    )


# =============================================================================
# CHA₂DS₂-VASc Score Calculator
# =============================================================================

# Annual stroke risk by CHA₂DS₂-VASc score (from ESC Guidelines)
CHA2DS2VASC_STROKE_RISK = {
    0: "0%",
    1: "1.3%",
    2: "2.2%",
    3: "3.2%",
    4: "4.0%",
    5: "6.7%",
    6: "9.8%",
    7: "9.6%",
    8: "6.7%",
    9: "15.2%",
}


def calculate_cha2ds2vasc(input_data: CHA2DS2VAScInput) -> CHA2DS2VAScResult:
    """
    Calculate CHA₂DS₂-VASc Score for stroke risk in atrial fibrillation.

    The CHA₂DS₂-VASc Score estimates annual stroke risk in patients
    with non-valvular atrial fibrillation to guide anticoagulation decisions.

    Maximum score: 9 points

    Args:
        input_data: CHA₂DS₂-VASc input parameters

    Returns:
        CHA2DS2VAScResult with score, stroke risk, and recommendations
    """
    breakdown: dict[str, int] = {}
    total_score = 0

    # C - Congestive heart failure / LV dysfunction (1 point)
    if input_data.congestive_heart_failure:
        breakdown["CHF"] = 1
        total_score += 1

    # H - Hypertension (1 point)
    if input_data.hypertension:
        breakdown["Hypertension"] = 1
        total_score += 1

    # A₂ - Age ≥75 years (2 points)
    if input_data.age >= 75:
        breakdown["Age_75_or_older"] = 2
        total_score += 2
    # A - Age 65-74 years (1 point)
    elif input_data.age >= 65:
        breakdown["Age_65_to_74"] = 1
        total_score += 1

    # D - Diabetes (1 point)
    if input_data.diabetes:
        breakdown["Diabetes"] = 1
        total_score += 1

    # S₂ - Stroke/TIA/Thromboembolism (2 points)
    if input_data.stroke_tia_thromboembolism:
        breakdown["Stroke_TIA"] = 2
        total_score += 2

    # V - Vascular disease (1 point)
    if input_data.vascular_disease:
        breakdown["Vascular_disease"] = 1
        total_score += 1

    # Sc - Sex category: female (1 point)
    if input_data.sex == "female":
        breakdown["Female"] = 1
        total_score += 1

    # Sex-adjusted score for treatment decisions
    # Female sex alone (score 1) does not warrant anticoagulation
    adjusted_score = total_score if input_data.sex == "male" else max(0, total_score - 1)

    # Get stroke risk
    stroke_risk = CHA2DS2VASC_STROKE_RISK.get(total_score, ">15%")

    # Generate recommendation based on adjusted score
    if adjusted_score == 0:
        recommendation = (
            "No anticoagulation recommended. "
            "Female sex alone does not warrant anticoagulation. "
            "Reassess periodically for new risk factors."
        )
    elif adjusted_score == 1:
        recommendation = (
            "Consider anticoagulation based on individual patient assessment, "
            "bleeding risk (HAS-BLED), and patient preferences. "
            "If anticoagulation chosen, DOAC preferred over warfarin."
        )
    else:
        recommendation = (
            "Oral anticoagulation is recommended to prevent stroke. "
            "DOAC (apixaban, rivaroxaban, edoxaban, or dabigatran) preferred "
            "over warfarin unless contraindicated (mechanical valve, "
            "moderate-severe mitral stenosis). "
            "Assess bleeding risk with HAS-BLED score."
        )

    return CHA2DS2VAScResult(
        total_score=total_score,
        adjusted_score=adjusted_score,
        annual_stroke_risk=stroke_risk,
        recommendation=recommendation,
        score_breakdown=breakdown,
        calculation_timestamp=datetime.now(timezone.utc),
    )


# =============================================================================
# HAS-BLED Score Calculator
# =============================================================================

# Annual major bleeding risk by HAS-BLED score
HASBLED_BLEEDING_RISK = {
    0: "1.13%",
    1: "1.02%",
    2: "1.88%",
    3: "3.74%",
    4: "8.70%",
    5: "12.50%",
}


def calculate_hasbled(input_data: HASBLEDInput) -> HASBLEDResult:
    """
    Calculate HAS-BLED Score for bleeding risk assessment.

    The HAS-BLED Score estimates annual major bleeding risk in patients
    on anticoagulation for atrial fibrillation.

    IMPORTANT: A high HAS-BLED score does NOT contraindicate anticoagulation.
    It identifies modifiable risk factors and patients requiring closer monitoring.

    Maximum score: 9 points

    Args:
        input_data: HAS-BLED input parameters

    Returns:
        HASBLEDResult with score, risk level, and modifiable factors
    """
    breakdown: dict[str, int] = {}
    modifiable_factors: list[str] = []
    total_score = 0

    # H - Hypertension uncontrolled (1 point) - MODIFIABLE
    if input_data.hypertension_uncontrolled:
        breakdown["Hypertension"] = 1
        total_score += 1
        modifiable_factors.append("Optimize blood pressure control (target SBP <160)")

    # A - Abnormal renal function (1 point)
    if input_data.abnormal_renal_function:
        breakdown["Abnormal_renal"] = 1
        total_score += 1

    # A - Abnormal liver function (1 point)
    if input_data.abnormal_liver_function:
        breakdown["Abnormal_liver"] = 1
        total_score += 1

    # S - Stroke history (1 point)
    if input_data.stroke_history:
        breakdown["Stroke"] = 1
        total_score += 1

    # B - Bleeding history (1 point)
    if input_data.bleeding_history:
        breakdown["Bleeding"] = 1
        total_score += 1

    # L - Labile INR (1 point) - MODIFIABLE
    if input_data.labile_inr:
        breakdown["Labile_INR"] = 1
        total_score += 1
        modifiable_factors.append(
            "Consider switching from warfarin to DOAC for more stable anticoagulation"
        )

    # E - Elderly >65 (1 point)
    if input_data.elderly:
        breakdown["Elderly"] = 1
        total_score += 1

    # D - Drugs: antiplatelet/NSAIDs (1 point) - MODIFIABLE
    if input_data.antiplatelet_or_nsaid:
        breakdown["Drugs"] = 1
        total_score += 1
        modifiable_factors.append(
            "Review necessity of antiplatelet agents and NSAIDs; "
            "avoid unless clearly indicated"
        )

    # D - Alcohol abuse (1 point) - MODIFIABLE
    if input_data.alcohol_abuse:
        breakdown["Alcohol"] = 1
        total_score += 1
        modifiable_factors.append(
            "Address alcohol consumption; recommend limiting to <8 drinks/week"
        )

    # Risk stratification
    if total_score <= 1:
        risk_level = "Low"
        bleeding_rate = HASBLED_BLEEDING_RISK.get(total_score, "~1%")
        recommendation = (
            "Low bleeding risk. "
            "Anticoagulation can be initiated without additional precautions. "
            "Standard monitoring is appropriate."
        )
    elif total_score == 2:
        risk_level = "Moderate"
        bleeding_rate = HASBLED_BLEEDING_RISK.get(total_score, "~2%")
        recommendation = (
            "Moderate bleeding risk. "
            "Anticoagulation is still generally beneficial if indicated. "
            "Address modifiable risk factors and ensure regular follow-up."
        )
    else:
        risk_level = "High"
        bleeding_rate = HASBLED_BLEEDING_RISK.get(total_score, "≥3.74%")
        recommendation = (
            "High bleeding risk - but this does NOT contraindicate anticoagulation. "
            "The stroke risk in AF typically outweighs bleeding risk. "
            "Focus on addressing modifiable factors, ensure closer INR monitoring "
            "if on warfarin (consider DOAC), and schedule more frequent follow-up."
        )

    return HASBLEDResult(
        total_score=total_score,
        risk_level=risk_level,
        annual_bleeding_rate=bleeding_rate,
        recommendation=recommendation,
        modifiable_factors=modifiable_factors,
        score_breakdown=breakdown,
        calculation_timestamp=datetime.now(timezone.utc),
    )
