"""
CDSS Data Models for OpenHeart Cyprus.

Pydantic models for clinical risk calculator inputs and outputs.
All models include strict validation to ensure clinical accuracy.
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# =============================================================================
# GRACE Score Models
# =============================================================================


class KillipClass(str, Enum):
    """
    Killip Classification for heart failure severity in ACS.

    Used in GRACE Score calculation.
    """

    I = "I"  # No heart failure
    II = "II"  # Rales, S3 gallop, or venous hypertension
    III = "III"  # Frank pulmonary edema
    IV = "IV"  # Cardiogenic shock


class GRACEInput(BaseModel):
    """
    Input parameters for GRACE Score calculation.

    GRACE (Global Registry of Acute Coronary Events) Score
    estimates in-hospital mortality risk for ACS patients.
    """

    age: int = Field(
        ...,
        ge=0,
        le=120,
        description="Patient age in years",
        json_schema_extra={"example": 65},
    )
    heart_rate: int = Field(
        ...,
        ge=20,
        le=300,
        description="Heart rate in beats per minute",
        json_schema_extra={"example": 90},
    )
    systolic_bp: int = Field(
        ...,
        ge=40,
        le=300,
        description="Systolic blood pressure in mmHg",
        json_schema_extra={"example": 120},
    )
    creatinine_mg_dl: float = Field(
        ...,
        ge=0,
        le=20,
        description="Serum creatinine in mg/dL",
        json_schema_extra={"example": 1.0},
    )
    killip_class: KillipClass = Field(
        ...,
        description="Killip classification for heart failure",
        json_schema_extra={"example": "I"},
    )
    cardiac_arrest_at_admission: bool = Field(
        default=False,
        description="Cardiac arrest at time of admission",
    )
    st_segment_deviation: bool = Field(
        default=False,
        description="ST-segment deviation on ECG",
    )
    elevated_cardiac_enzymes: bool = Field(
        default=False,
        description="Elevated cardiac enzymes (troponin)",
    )


class GRACEResult(BaseModel):
    """
    GRACE Score calculation result.

    Includes score, risk category, and clinical recommendations.
    """

    total_score: int = Field(..., description="Total GRACE score (0-372)")
    risk_category: Literal["Low", "Intermediate", "High"] = Field(
        ..., description="Risk stratification category"
    )
    in_hospital_mortality_estimate: str = Field(
        ..., description="Estimated in-hospital mortality"
    )
    recommendation: str = Field(..., description="Clinical management recommendation")
    score_breakdown: dict[str, int] = Field(
        ..., description="Points contribution from each factor"
    )
    calculation_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of calculation",
    )


# =============================================================================
# CHA₂DS₂-VASc Score Models
# =============================================================================


class CHA2DS2VAScInput(BaseModel):
    """
    Input parameters for CHA₂DS₂-VASc Score calculation.

    Used to assess stroke risk in patients with atrial fibrillation.
    """

    age: int = Field(
        ...,
        ge=0,
        le=120,
        description="Patient age in years",
        json_schema_extra={"example": 70},
    )
    sex: Literal["male", "female"] = Field(
        ...,
        description="Biological sex",
        json_schema_extra={"example": "male"},
    )
    congestive_heart_failure: bool = Field(
        default=False,
        description="History of CHF or LV dysfunction (LVEF ≤40%)",
    )
    hypertension: bool = Field(
        default=False,
        description="History of hypertension or on antihypertensive therapy",
    )
    diabetes: bool = Field(
        default=False,
        description="History of diabetes mellitus",
    )
    stroke_tia_thromboembolism: bool = Field(
        default=False,
        description="Prior stroke, TIA, or systemic thromboembolism",
    )
    vascular_disease: bool = Field(
        default=False,
        description="Prior MI, peripheral artery disease, or aortic plaque",
    )


class CHA2DS2VAScResult(BaseModel):
    """
    CHA₂DS₂-VASc Score calculation result.

    Includes stroke risk and anticoagulation recommendations.
    """

    total_score: int = Field(..., ge=0, le=9, description="Total score (0-9)")
    adjusted_score: int = Field(
        ...,
        description="Sex-adjusted score for treatment decisions",
    )
    annual_stroke_risk: str = Field(..., description="Estimated annual stroke risk")
    recommendation: str = Field(..., description="Anticoagulation recommendation")
    score_breakdown: dict[str, int] = Field(
        ..., description="Points contribution from each factor"
    )
    calculation_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of calculation",
    )


# =============================================================================
# HAS-BLED Score Models
# =============================================================================


class HASBLEDInput(BaseModel):
    """
    Input parameters for HAS-BLED Score calculation.

    Assesses major bleeding risk in patients on anticoagulation.
    """

    hypertension_uncontrolled: bool = Field(
        default=False,
        description="Uncontrolled hypertension (SBP >160 mmHg)",
    )
    abnormal_renal_function: bool = Field(
        default=False,
        description="Dialysis, transplant, Cr >2.3 mg/dL, or eGFR <30",
    )
    abnormal_liver_function: bool = Field(
        default=False,
        description="Cirrhosis, bilirubin >2x normal, or AST/ALT/ALP >3x normal",
    )
    stroke_history: bool = Field(
        default=False,
        description="Previous stroke",
    )
    bleeding_history: bool = Field(
        default=False,
        description="Major bleeding history or bleeding predisposition",
    )
    labile_inr: bool = Field(
        default=False,
        description="Labile INR (time in therapeutic range <60%) if on warfarin",
    )
    elderly: bool = Field(
        default=False,
        description="Age >65 years",
    )
    antiplatelet_or_nsaid: bool = Field(
        default=False,
        description="Concomitant antiplatelet or NSAID use",
    )
    alcohol_abuse: bool = Field(
        default=False,
        description="Alcohol abuse (≥8 drinks/week)",
    )


class HASBLEDResult(BaseModel):
    """
    HAS-BLED Score calculation result.

    Includes bleeding risk and modifiable factor recommendations.
    """

    total_score: int = Field(..., ge=0, le=9, description="Total score (0-9)")
    risk_level: Literal["Low", "Moderate", "High"] = Field(
        ..., description="Bleeding risk level"
    )
    annual_bleeding_rate: str = Field(
        ..., description="Estimated annual major bleeding rate"
    )
    recommendation: str = Field(..., description="Clinical recommendation")
    modifiable_factors: list[str] = Field(
        default_factory=list,
        description="Modifiable risk factors to address",
    )
    score_breakdown: dict[str, int] = Field(
        ..., description="Points contribution from each factor"
    )
    calculation_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of calculation",
    )


# =============================================================================
# PREVENT Equations Models (AHA 2023)
# =============================================================================


class PREVENTInput(BaseModel):
    """
    Input parameters for PREVENT Equations calculation.

    AHA PREVENT (2023) - Race-agnostic ASCVD and Heart Failure risk prediction.
    Replaces Pooled Cohort Equations (PCE) as the modern standard.
    """

    age: int = Field(
        ...,
        ge=30,
        le=79,
        description="Patient age in years (valid: 30-79)",
        json_schema_extra={"example": 55},
    )
    sex: Literal["male", "female"] = Field(
        ...,
        description="Biological sex",
        json_schema_extra={"example": "male"},
    )
    systolic_bp: int = Field(
        ...,
        ge=80,
        le=250,
        description="Systolic blood pressure in mmHg",
        json_schema_extra={"example": 130},
    )
    total_cholesterol: float = Field(
        ...,
        ge=100,
        le=400,
        description="Total cholesterol in mg/dL",
        json_schema_extra={"example": 200},
    )
    hdl_cholesterol: float = Field(
        ...,
        ge=20,
        le=150,
        description="HDL cholesterol in mg/dL",
        json_schema_extra={"example": 50},
    )
    egfr: float = Field(
        ...,
        ge=5,
        le=200,
        description="Estimated GFR in mL/min/1.73m² (required for PREVENT)",
        json_schema_extra={"example": 90},
    )
    diabetes: bool = Field(
        default=False,
        description="History of diabetes mellitus",
    )
    current_smoker: bool = Field(
        default=False,
        description="Current cigarette smoker",
    )
    on_bp_treatment: bool = Field(
        default=False,
        description="Currently on antihypertensive medication",
    )
    on_statin: bool = Field(
        default=False,
        description="Currently on statin therapy",
    )
    # Optional enhanced inputs
    hba1c: float | None = Field(
        default=None,
        ge=4.0,
        le=20.0,
        description="HbA1c in % (optional, for enhanced model)",
    )
    uacr: float | None = Field(
        default=None,
        ge=0,
        le=10000,
        description="Urine albumin-to-creatinine ratio in mg/g (optional)",
    )


class PREVENTResult(BaseModel):
    """
    PREVENT Equations calculation result.

    Includes 10-year and 30-year ASCVD risk, plus Heart Failure risk.
    """

    ten_year_ascvd_risk: float = Field(
        ..., ge=0, le=100, description="10-year ASCVD risk (%)"
    )
    ten_year_hf_risk: float = Field(
        ..., ge=0, le=100, description="10-year Heart Failure risk (%)"
    )
    ten_year_total_cvd_risk: float = Field(
        ..., ge=0, le=100, description="10-year total CVD risk (ASCVD + HF)"
    )
    risk_category: Literal["Low", "Borderline", "Intermediate", "High"] = Field(
        ..., description="ASCVD risk category"
    )
    statin_benefit_group: bool = Field(
        ..., description="Patient likely to benefit from statin therapy"
    )
    recommendation: str = Field(..., description="Clinical recommendations")
    risk_enhancers: list[str] = Field(
        default_factory=list,
        description="Present risk-enhancing factors",
    )
    calculation_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of calculation",
    )


# =============================================================================
# EuroSCORE II Models
# =============================================================================


class LVFunction(str, Enum):
    """Left ventricular function categories for EuroSCORE II."""

    GOOD = "good"  # LVEF >50%
    MODERATE = "moderate"  # LVEF 31-50%
    POOR = "poor"  # LVEF 21-30%
    VERY_POOR = "very_poor"  # LVEF ≤20%


class PulmonaryHypertension(str, Enum):
    """Pulmonary hypertension severity for EuroSCORE II."""

    NO = "no"  # <31 mmHg
    MODERATE = "moderate"  # 31-55 mmHg
    SEVERE = "severe"  # >55 mmHg


class OperationUrgency(str, Enum):
    """Urgency classification for cardiac surgery."""

    ELECTIVE = "elective"  # Routine admission
    URGENT = "urgent"  # Not elective, within current admission
    EMERGENCY = "emergency"  # Before next working day
    SALVAGE = "salvage"  # CPR ongoing or ECMO/IABP pre-OR


class OperationWeight(str, Enum):
    """Type/weight of cardiac procedure."""

    ISOLATED_CABG = "isolated_cabg"
    SINGLE_NON_CABG = "single_non_cabg"  # Single valve, ASD closure, etc.
    TWO_PROCEDURES = "two_procedures"  # CABG + valve, two valves
    THREE_OR_MORE = "three_or_more"  # Triple valve, CABG + 2 valves


class EuroSCOREIIInput(BaseModel):
    """
    Input parameters for EuroSCORE II calculation.

    Estimates operative mortality risk for cardiac surgery.
    Essential for Heart Team discussions (CABG vs PCI, SAVR vs TAVI).
    """

    # Patient factors
    age: int = Field(
        ...,
        ge=18,
        le=100,
        description="Patient age in years",
        json_schema_extra={"example": 70},
    )
    sex: Literal["male", "female"] = Field(
        ...,
        description="Biological sex",
        json_schema_extra={"example": "male"},
    )
    # Renal function
    creatinine_clearance: float = Field(
        ...,
        ge=0,
        le=200,
        description="Creatinine clearance (Cockcroft-Gault) in mL/min",
        json_schema_extra={"example": 85},
    )
    on_dialysis: bool = Field(
        default=False,
        description="Patient on chronic dialysis",
    )
    # Comorbidities
    extracardiac_arteriopathy: bool = Field(
        default=False,
        description="Claudication, carotid stenosis >50%, amputation, or prior aortic surgery",
    )
    poor_mobility: bool = Field(
        default=False,
        description="Severe impairment from musculoskeletal/neurological dysfunction",
    )
    previous_cardiac_surgery: bool = Field(
        default=False,
        description="Prior cardiac surgery requiring pericardium opening",
    )
    chronic_lung_disease: bool = Field(
        default=False,
        description="Long-term bronchodilator or steroid use for lung disease",
    )
    active_endocarditis: bool = Field(
        default=False,
        description="Patient still on antibiotic treatment for endocarditis at surgery",
    )
    critical_preoperative_state: bool = Field(
        default=False,
        description="VT/VF, cardiac massage, ventilation, inotropes, IABP, or anuria pre-op",
    )
    diabetes_on_insulin: bool = Field(
        default=False,
        description="Diabetes requiring insulin therapy",
    )
    # Cardiac factors
    nyha_class: Literal[1, 2, 3, 4] = Field(
        default=1,
        description="NYHA functional class (1-4)",
    )
    ccs_class_4_angina: bool = Field(
        default=False,
        description="CCS Class 4 angina (angina at rest)",
    )
    lv_function: LVFunction = Field(
        default=LVFunction.GOOD,
        description="Left ventricular function",
    )
    recent_mi: bool = Field(
        default=False,
        description="MI within 90 days before surgery",
    )
    pulmonary_hypertension: PulmonaryHypertension = Field(
        default=PulmonaryHypertension.NO,
        description="Pulmonary hypertension severity (PA systolic pressure)",
    )
    # Operation factors
    urgency: OperationUrgency = Field(
        default=OperationUrgency.ELECTIVE,
        description="Urgency of operation",
    )
    operation_weight: OperationWeight = Field(
        default=OperationWeight.ISOLATED_CABG,
        description="Type/weight of procedure",
    )
    surgery_on_thoracic_aorta: bool = Field(
        default=False,
        description="Surgery on thoracic aorta",
    )


class EuroSCOREIIResult(BaseModel):
    """
    EuroSCORE II calculation result.

    Provides operative mortality risk for Heart Team decision-making.
    """

    predicted_mortality: float = Field(
        ..., ge=0, le=100, description="Predicted operative mortality (%)"
    )
    risk_category: Literal["Low", "Intermediate", "High", "Very High"] = Field(
        ..., description="Risk category for surgical decision-making"
    )
    suitability_for_surgery: str = Field(
        ..., description="General guidance on surgical candidacy"
    )
    recommendation: str = Field(..., description="Heart Team consideration points")
    risk_factors_present: list[str] = Field(
        default_factory=list,
        description="List of risk factors contributing to score",
    )
    calculation_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of calculation",
    )
