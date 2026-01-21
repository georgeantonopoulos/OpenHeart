"""
OpenHeart Cyprus - Clinical Decision Support System (CDSS) Engine.
Based on "The Construction and Application of a CDSS for Cardiovascular Diseases" 
and standard cardiology guidelines.
"""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict

class KillipClass(str, Enum):
    I = "I"     # No heart failure
    II = "II"   # Rales, S3 gallop, or venous hypertension
    III = "III" # Frank pulmonary edema
    IV = "IV"   # Cardiogenic shock

class CardiacEvent(BaseModel):
    age: int = Field(..., ge=0, le=120)
    heart_rate: int = Field(..., ge=0, le=300)
    systolic_bp: int = Field(..., ge=0, le=300)
    creatinine: float = Field(..., description="Serum creatinine in mg/dL")
    killip: KillipClass
    cardiac_arrest_at_admission: bool
    st_segment_deviation: bool
    elevated_enzymes: bool

def calculate_grace_score(patient: CardiacEvent) -> Dict[str, str]:
    """
    Calculates the GRACE Risk Score for ACS (Acute Coronary Syndrome).
    Note: This is a simplified implementation for the MVP. 
    The full nomogram values should be verified against the latest ESC guidelines.
    """
    score = 0
    
    # 1. Age Score
    if patient.age < 30: score += 0
    elif patient.age < 40: score += 18
    elif patient.age < 50: score += 36
    elif patient.age < 60: score += 55
    elif patient.age < 70: score += 73
    elif patient.age < 80: score += 91
    else: score += 100

    # 2. Heart Rate
    if patient.heart_rate < 50: score += 0
    elif patient.heart_rate < 70: score += 3
    elif patient.heart_rate < 90: score += 9
    elif patient.heart_rate < 110: score += 15
    elif patient.heart_rate < 150: score += 24
    elif patient.heart_rate < 200: score += 38
    else: score += 46

    # 3. Systolic BP (Lower is worse in ACS context)
    if patient.systolic_bp < 80: score += 58
    elif patient.systolic_bp < 100: score += 53
    elif patient.systolic_bp < 120: score += 43
    elif patient.systolic_bp < 140: score += 34
    elif patient.systolic_bp < 160: score += 24
    elif patient.systolic_bp < 200: score += 10
    else: score += 0

    # 4. Killip Class
    killip_scores = {
        KillipClass.I: 0,
        KillipClass.II: 20,
        KillipClass.III: 39,
        KillipClass.IV: 59
    }
    score += killip_scores[patient.killip]

    # 5. Other Factors
    if patient.creatinine > 0:
        # Simplified creatinine mapping
        if patient.creatinine < 0.4: score += 1
        elif patient.creatinine < 0.8: score += 5
        elif patient.creatinine < 1.2: score += 7
        elif patient.creatinine < 1.6: score += 10
        elif patient.creatinine < 2.0: score += 13
        elif patient.creatinine < 4.0: score += 21
        else: score += 28

    if patient.cardiac_arrest_at_admission: score += 39
    if patient.st_segment_deviation: score += 28
    if patient.elevated_enzymes: score += 14

    # Interpretation (In-hospital mortality risk)
    risk_category = "Low"
    if score > 140:
        risk_category = "High"
    elif score > 109:
        risk_category = "Intermediate"

    return {
        "score": str(score),
        "risk_category": risk_category,
        "recommendation": _get_recommendation(risk_category)
    }

def _get_recommendation(risk_category: str) -> str:
    if risk_category == "High":
        return "Urgent invasive strategy (<24h). Monitor in ICU."
    elif risk_category == "Intermediate":
        return "Early invasive strategy (<72h) recommended."
    else:
        return "Conservative strategy. Discharge if stress test negative."

# Example usage for testing
if __name__ == "__main__":
    sample_patient = CardiacEvent(
        age=65,
        heart_rate=95,
        systolic_bp=110,
        creatinine=1.1,
        killip=KillipClass.I,
        cardiac_arrest_at_admission=False,
        st_segment_deviation=True,
        elevated_enzymes=True
    )
    result = calculate_grace_score(sample_patient)
    print(f"GRACE Score Calculation: {result}")