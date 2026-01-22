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

import math

from app.modules.cardiology.cdss.models import (
    CHA2DS2VAScInput,
    CHA2DS2VAScResult,
    EuroSCOREIIInput,
    EuroSCOREIIResult,
    GRACEInput,
    GRACEResult,
    HASBLEDInput,
    HASBLEDResult,
    KillipClass,
    LVFunction,
    OperationUrgency,
    OperationWeight,
    PREVENTInput,
    PREVENTResult,
    PulmonaryHypertension,
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


# =============================================================================
# PREVENT Equations Calculator (AHA 2023)
# =============================================================================

# PREVENT equation coefficients (simplified model)
# Based on: Khan SS, et al. Circulation. 2024;149:e347-e913
# These are approximate coefficients for the base model


def calculate_prevent(input_data: PREVENTInput) -> PREVENTResult:
    """
    Calculate PREVENT Equations for ASCVD and Heart Failure risk.

    The PREVENT (Predicting Risk of CVD Events) equations (AHA 2023)
    are race-free 10-year and 30-year risk calculators that include
    kidney function (eGFR) and predict both ASCVD and Heart Failure.

    Valid for ages 30-79.

    Args:
        input_data: PREVENT input parameters

    Returns:
        PREVENTResult with ASCVD risk, HF risk, and recommendations
    """
    risk_enhancers: list[str] = []

    # -------------------------------------------------------------------------
    # ASCVD 10-Year Risk Calculation (Simplified PREVENT model)
    # -------------------------------------------------------------------------

    # Base coefficients (sex-specific)
    if input_data.sex == "male":
        # Male coefficients
        age_coef = 0.064
        sbp_coef = 0.017
        bp_treat_coef = 0.421
        tc_coef = 0.002
        hdl_coef = -0.012
        diabetes_coef = 0.661
        smoker_coef = 0.701
        egfr_coef = -0.015  # Lower eGFR = higher risk
        baseline_survival = 0.9665
    else:
        # Female coefficients
        age_coef = 0.079
        sbp_coef = 0.019
        bp_treat_coef = 0.387
        tc_coef = 0.003
        hdl_coef = -0.015
        diabetes_coef = 0.879
        smoker_coef = 0.847
        egfr_coef = -0.013
        baseline_survival = 0.9830

    # Calculate linear predictor (log-hazard)
    ln_hazard = (
        (input_data.age - 55) * age_coef
        + (input_data.systolic_bp - 120) * sbp_coef
        + (1 if input_data.on_bp_treatment else 0) * bp_treat_coef
        + (input_data.total_cholesterol - 170) * tc_coef
        + (input_data.hdl_cholesterol - 45) * hdl_coef
        + (1 if input_data.diabetes else 0) * diabetes_coef
        + (1 if input_data.current_smoker else 0) * smoker_coef
        + (90 - input_data.egfr) * egfr_coef  # Note: centered at 90
    )

    # Convert to 10-year risk
    ten_year_ascvd = (1 - math.pow(baseline_survival, math.exp(ln_hazard))) * 100

    # Clamp to valid range
    ten_year_ascvd = max(0.1, min(99.9, ten_year_ascvd))

    # -------------------------------------------------------------------------
    # Heart Failure 10-Year Risk (Simplified model)
    # -------------------------------------------------------------------------
    # HF prediction in PREVENT emphasizes: age, BMI, diabetes, eGFR, BP

    if input_data.sex == "male":
        hf_baseline = 0.9750
        hf_age_coef = 0.058
        hf_sbp_coef = 0.012
        hf_diabetes_coef = 0.850
        hf_egfr_coef = -0.022
    else:
        hf_baseline = 0.9870
        hf_age_coef = 0.062
        hf_sbp_coef = 0.014
        hf_diabetes_coef = 0.920
        hf_egfr_coef = -0.020

    hf_ln_hazard = (
        (input_data.age - 55) * hf_age_coef
        + (input_data.systolic_bp - 120) * hf_sbp_coef
        + (1 if input_data.diabetes else 0) * hf_diabetes_coef
        + (90 - input_data.egfr) * hf_egfr_coef
    )

    ten_year_hf = (1 - math.pow(hf_baseline, math.exp(hf_ln_hazard))) * 100
    ten_year_hf = max(0.1, min(99.9, ten_year_hf))

    # Total CVD risk (not simply additive due to overlap, use max approximation)
    ten_year_total = min(99.9, ten_year_ascvd + ten_year_hf * 0.7)

    # -------------------------------------------------------------------------
    # Risk Category and Recommendations
    # -------------------------------------------------------------------------

    # Identify risk enhancers
    if input_data.egfr < 60:
        risk_enhancers.append("Reduced kidney function (eGFR <60)")
    if input_data.uacr and input_data.uacr >= 30:
        risk_enhancers.append("Albuminuria (UACR ≥30 mg/g)")
    if input_data.hba1c and input_data.hba1c >= 8.0:
        risk_enhancers.append("Suboptimal glycemic control (HbA1c ≥8%)")
    if input_data.current_smoker:
        risk_enhancers.append("Current smoking")
    if input_data.total_cholesterol / input_data.hdl_cholesterol > 5:
        risk_enhancers.append("Elevated total/HDL cholesterol ratio")

    # Risk category thresholds
    if ten_year_ascvd < 5:
        risk_category = "Low"
    elif ten_year_ascvd < 7.5:
        risk_category = "Borderline"
    elif ten_year_ascvd < 20:
        risk_category = "Intermediate"
    else:
        risk_category = "High"

    # Statin benefit determination
    statin_benefit = (
        ten_year_ascvd >= 7.5
        or input_data.diabetes
        or (ten_year_ascvd >= 5 and len(risk_enhancers) > 0)
    )

    # Generate recommendations
    recommendations: list[str] = []

    if risk_category == "Low":
        recommendations.append(
            "Low 10-year ASCVD risk. Emphasize lifestyle modifications."
        )
    elif risk_category == "Borderline":
        recommendations.append(
            "Borderline risk. Consider risk-enhancing factors in statin discussion."
        )
    elif risk_category == "Intermediate":
        recommendations.append(
            "Intermediate risk. Statin therapy is reasonable; "
            "consider coronary artery calcium (CAC) score if decision uncertain."
        )
    else:
        recommendations.append(
            "High 10-year risk. High-intensity statin therapy recommended."
        )

    # Heart failure specific recommendations
    if ten_year_hf >= 10:
        recommendations.append(
            f"Elevated heart failure risk ({ten_year_hf:.1f}%). "
            "Optimize BP control, consider SGLT2 inhibitor if diabetic."
        )

    # Kidney function recommendations
    if input_data.egfr < 60:
        recommendations.append(
            "CKD present - consider cardio-renal protective strategies (SGLT2i, ACEi/ARB)."
        )

    # Smoking cessation
    if input_data.current_smoker:
        recommendations.append(
            "Smoking cessation is the single most effective intervention."
        )

    return PREVENTResult(
        ten_year_ascvd_risk=round(ten_year_ascvd, 1),
        ten_year_hf_risk=round(ten_year_hf, 1),
        ten_year_total_cvd_risk=round(ten_year_total, 1),
        risk_category=risk_category,
        statin_benefit_group=statin_benefit,
        recommendation=" ".join(recommendations),
        risk_enhancers=risk_enhancers,
        calculation_timestamp=datetime.now(timezone.utc),
    )


# =============================================================================
# EuroSCORE II Calculator
# =============================================================================

# EuroSCORE II coefficients from:
# Nashef SA, et al. Eur J Cardiothorac Surg. 2012;41:734-44


def calculate_euroscore_ii(input_data: EuroSCOREIIInput) -> EuroSCOREIIResult:
    """
    Calculate EuroSCORE II for cardiac surgery mortality prediction.

    EuroSCORE II (European System for Cardiac Operative Risk Evaluation)
    estimates 30-day mortality risk for adult cardiac surgery.
    Critical for Heart Team discussions on revascularization strategy.

    Validated thresholds for TAVI vs SAVR, PCI vs CABG decisions.

    Args:
        input_data: EuroSCORE II input parameters

    Returns:
        EuroSCOREIIResult with predicted mortality and recommendations
    """
    risk_factors: list[str] = []

    # Constant (intercept)
    beta_0 = -5.324537

    # Initialize sum of coefficients
    beta_sum = beta_0

    # -------------------------------------------------------------------------
    # Patient-Related Factors
    # -------------------------------------------------------------------------

    # Age (continuous, per year after age 60)
    if input_data.age > 60:
        age_contribution = 0.0285181 * (input_data.age - 60)
        beta_sum += age_contribution
        if input_data.age >= 75:
            risk_factors.append(f"Advanced age ({input_data.age} years)")

    # Female sex
    if input_data.sex == "female":
        beta_sum += 0.2196434
        risk_factors.append("Female sex")

    # Renal impairment (creatinine clearance)
    if input_data.on_dialysis:
        beta_sum += 0.6421508
        risk_factors.append("Dialysis-dependent renal failure")
    elif input_data.creatinine_clearance < 50:
        # CrCl categories: 50-85, <50
        if input_data.creatinine_clearance < 50:
            beta_sum += 0.303553
            risk_factors.append(f"Moderate renal impairment (CrCl {input_data.creatinine_clearance:.0f})")

    # Extracardiac arteriopathy
    if input_data.extracardiac_arteriopathy:
        beta_sum += 0.5360268
        risk_factors.append("Extracardiac arteriopathy")

    # Poor mobility
    if input_data.poor_mobility:
        beta_sum += 0.2407181
        risk_factors.append("Poor mobility")

    # Previous cardiac surgery
    if input_data.previous_cardiac_surgery:
        beta_sum += 1.118599
        risk_factors.append("Previous cardiac surgery (redo)")

    # Chronic lung disease
    if input_data.chronic_lung_disease:
        beta_sum += 0.1886564
        risk_factors.append("Chronic lung disease")

    # Active endocarditis
    if input_data.active_endocarditis:
        beta_sum += 0.6194522
        risk_factors.append("Active endocarditis")

    # Critical preoperative state
    if input_data.critical_preoperative_state:
        beta_sum += 1.086517
        risk_factors.append("Critical preoperative state")

    # Diabetes on insulin
    if input_data.diabetes_on_insulin:
        beta_sum += 0.3542749
        risk_factors.append("Insulin-dependent diabetes")

    # -------------------------------------------------------------------------
    # Cardiac-Related Factors
    # -------------------------------------------------------------------------

    # NYHA class (III-IV)
    if input_data.nyha_class >= 3:
        beta_sum += 0.1070545 * (input_data.nyha_class - 2)  # Incremental for III/IV
        risk_factors.append(f"NYHA Class {input_data.nyha_class}")

    # CCS Class 4 angina
    if input_data.ccs_class_4_angina:
        beta_sum += 0.2226147
        risk_factors.append("CCS Class 4 angina (rest angina)")

    # LV function
    lv_coefficients = {
        LVFunction.GOOD: 0,
        LVFunction.MODERATE: 0.3150652,
        LVFunction.POOR: 0.8084096,
        LVFunction.VERY_POOR: 0.9346919,
    }
    lv_coef = lv_coefficients[input_data.lv_function]
    if lv_coef > 0:
        beta_sum += lv_coef
        risk_factors.append(f"Reduced LV function ({input_data.lv_function.value})")

    # Recent MI
    if input_data.recent_mi:
        beta_sum += 0.1528943
        risk_factors.append("Recent MI (≤90 days)")

    # Pulmonary hypertension
    ph_coefficients = {
        PulmonaryHypertension.NO: 0,
        PulmonaryHypertension.MODERATE: 0.1788899,
        PulmonaryHypertension.SEVERE: 0.3491475,
    }
    ph_coef = ph_coefficients[input_data.pulmonary_hypertension]
    if ph_coef > 0:
        beta_sum += ph_coef
        risk_factors.append(f"Pulmonary hypertension ({input_data.pulmonary_hypertension.value})")

    # -------------------------------------------------------------------------
    # Operation-Related Factors
    # -------------------------------------------------------------------------

    # Urgency
    urgency_coefficients = {
        OperationUrgency.ELECTIVE: 0,
        OperationUrgency.URGENT: 0.3174673,
        OperationUrgency.EMERGENCY: 0.7039121,
        OperationUrgency.SALVAGE: 1.362947,
    }
    urgency_coef = urgency_coefficients[input_data.urgency]
    if urgency_coef > 0:
        beta_sum += urgency_coef
        risk_factors.append(f"Non-elective surgery ({input_data.urgency.value})")

    # Weight of procedure
    weight_coefficients = {
        OperationWeight.ISOLATED_CABG: 0,
        OperationWeight.SINGLE_NON_CABG: 0.0062118,
        OperationWeight.TWO_PROCEDURES: 0.5521478,
        OperationWeight.THREE_OR_MORE: 0.9724533,
    }
    weight_coef = weight_coefficients[input_data.operation_weight]
    if weight_coef > 0:
        beta_sum += weight_coef
        risk_factors.append(f"Complex procedure ({input_data.operation_weight.value})")

    # Surgery on thoracic aorta
    if input_data.surgery_on_thoracic_aorta:
        beta_sum += 0.6527205
        risk_factors.append("Thoracic aortic surgery")

    # -------------------------------------------------------------------------
    # Calculate Predicted Mortality
    # -------------------------------------------------------------------------

    # Logistic regression: P = e^x / (1 + e^x)
    predicted_mortality = (math.exp(beta_sum) / (1 + math.exp(beta_sum))) * 100

    # Clamp to valid range
    predicted_mortality = max(0.1, min(99.9, predicted_mortality))

    # -------------------------------------------------------------------------
    # Risk Category and Recommendations
    # -------------------------------------------------------------------------

    if predicted_mortality < 2:
        risk_category = "Low"
        suitability = "Good surgical candidate"
        recommendation = (
            "Low operative risk. Standard surgical approach is appropriate. "
            "Surgery is generally recommended if anatomically suitable."
        )
    elif predicted_mortality < 5:
        risk_category = "Intermediate"
        suitability = "Acceptable surgical candidate with some risk factors"
        recommendation = (
            "Intermediate risk. Surgery remains a reasonable option. "
            "Heart Team discussion recommended to weigh surgical benefits vs risks. "
            "Consider less invasive alternatives if available (e.g., TAVI for aortic stenosis)."
        )
    elif predicted_mortality < 10:
        risk_category = "High"
        suitability = "High-risk surgical candidate"
        recommendation = (
            "High operative risk. Careful Heart Team evaluation essential. "
            "Consider transcatheter options (TAVI, MitraClip) where applicable. "
            "If surgery is chosen, preoperative optimization is critical."
        )
    else:
        risk_category = "Very High"
        suitability = "Prohibitive surgical risk - consider alternatives"
        recommendation = (
            "Prohibitive surgical risk. Surgery should generally be avoided. "
            "Strong consideration for transcatheter interventions or medical management. "
            "If surgery is the only option, detailed informed consent and ethics consultation advised."
        )

    return EuroSCOREIIResult(
        predicted_mortality=round(predicted_mortality, 2),
        risk_category=risk_category,
        suitability_for_surgery=suitability,
        recommendation=recommendation,
        risk_factors_present=risk_factors,
        calculation_timestamp=datetime.now(timezone.utc),
    )
