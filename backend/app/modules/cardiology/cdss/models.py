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
