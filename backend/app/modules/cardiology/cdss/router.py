"""
CDSS API Router for OpenHeart Cyprus.

Provides REST endpoints for clinical risk calculators.
All calculations are audited for GDPR compliance.
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from app.core.audit import log_cdss_calculation
from app.core.permissions import Permission, require_permission
from app.core.security import TokenPayload
from app.modules.cardiology.cdss.calculators import (
    calculate_cha2ds2vasc,
    calculate_euroscore_ii,
    calculate_grace_score,
    calculate_hasbled,
    calculate_prevent,
)
from app.modules.cardiology.cdss.models import (
    CHA2DS2VAScInput,
    CHA2DS2VAScResult,
    EuroSCOREIIInput,
    EuroSCOREIIResult,
    GRACEInput,
    GRACEResult,
    HASBLEDInput,
    HASBLEDResult,
    PREVENTInput,
    PREVENTResult,
)

router = APIRouter(prefix="/cdss", tags=["CDSS"])


@router.post(
    "/grace",
    response_model=GRACEResult,
    summary="Calculate GRACE Score",
    description="""
    Calculate the GRACE (Global Registry of Acute Coronary Events) Score
    for risk stratification in Acute Coronary Syndrome.

    **Risk Categories:**
    - **Low (≤108):** <1% in-hospital mortality. Conservative strategy.
    - **Intermediate (109-140):** 1-3% mortality. Early invasive (<72h).
    - **High (>140):** >3% mortality. Urgent invasive (<24h).

    All calculations are logged for clinical audit.
    """,
)
async def compute_grace_score(
    input_data: GRACEInput,
    patient_id: Annotated[
        Optional[int],
        Query(description="Optional patient ID to link calculation"),
    ] = None,
    user: TokenPayload = Depends(require_permission(Permission.CDSS_USE)),
) -> GRACEResult:
    """
    Calculate GRACE Score for ACS risk stratification.

    Returns score, risk category, and management recommendations.
    """
    result = calculate_grace_score(input_data)

    # Log calculation for audit
    await log_cdss_calculation(
        calculation_type="GRACE",
        patient_id=patient_id,
        input_params=input_data.model_dump(),
        result=result.model_dump(),
        user_id=user.sub,
        clinic_id=user.clinic_id,
    )

    return result


@router.post(
    "/cha2ds2vasc",
    response_model=CHA2DS2VAScResult,
    summary="Calculate CHA₂DS₂-VASc Score",
    description="""
    Calculate the CHA₂DS₂-VASc Score for stroke risk assessment
    in patients with atrial fibrillation.

    **Treatment Thresholds (sex-adjusted score):**
    - **0:** No anticoagulation needed
    - **1:** Consider anticoagulation (patient preference)
    - **≥2:** Oral anticoagulation recommended (DOAC preferred)

    Note: Female sex alone (score 1) does not warrant anticoagulation.
    """,
)
async def compute_cha2ds2vasc_score(
    input_data: CHA2DS2VAScInput,
    patient_id: Annotated[
        Optional[int],
        Query(description="Optional patient ID to link calculation"),
    ] = None,
    user: TokenPayload = Depends(require_permission(Permission.CDSS_USE)),
) -> CHA2DS2VAScResult:
    """
    Calculate CHA₂DS₂-VASc Score for AF stroke risk.

    Returns score, annual stroke risk, and anticoagulation recommendations.
    """
    result = calculate_cha2ds2vasc(input_data)

    # Log calculation for audit
    await log_cdss_calculation(
        calculation_type="CHA2DS2-VASc",
        patient_id=patient_id,
        input_params=input_data.model_dump(),
        result=result.model_dump(),
        user_id=user.sub,
        clinic_id=user.clinic_id,
    )

    return result


@router.post(
    "/hasbled",
    response_model=HASBLEDResult,
    summary="Calculate HAS-BLED Score",
    description="""
    Calculate the HAS-BLED Score for major bleeding risk assessment
    in patients on anticoagulation.

    **Risk Levels:**
    - **Low (0-1):** ~1%/year major bleeding
    - **Moderate (2):** ~2%/year major bleeding
    - **High (≥3):** ≥3.7%/year major bleeding

    **IMPORTANT:** High HAS-BLED does NOT contraindicate anticoagulation.
    It identifies modifiable risk factors requiring attention.
    """,
)
async def compute_hasbled_score(
    input_data: HASBLEDInput,
    patient_id: Annotated[
        Optional[int],
        Query(description="Optional patient ID to link calculation"),
    ] = None,
    user: TokenPayload = Depends(require_permission(Permission.CDSS_USE)),
) -> HASBLEDResult:
    """
    Calculate HAS-BLED Score for bleeding risk.

    Returns score, risk level, and modifiable factor recommendations.
    """
    result = calculate_hasbled(input_data)

    # Log calculation for audit
    await log_cdss_calculation(
        calculation_type="HAS-BLED",
        patient_id=patient_id,
        input_params=input_data.model_dump(),
        result=result.model_dump(),
        user_id=user.sub,
        clinic_id=user.clinic_id,
    )

    return result


@router.post(
    "/prevent",
    response_model=PREVENTResult,
    summary="Calculate PREVENT Risk Score",
    description="""
    Calculate the PREVENT Equations (AHA 2023) for ASCVD and Heart Failure risk.

    **Modern Standard:**
    - Race-agnostic (replaces Pooled Cohort Equations)
    - Includes eGFR (kidney function) as required input
    - Predicts both ASCVD and Heart Failure risk

    **Risk Categories (10-year ASCVD):**
    - **Low (<5%):** Lifestyle modifications
    - **Borderline (5-7.5%):** Consider risk enhancers
    - **Intermediate (7.5-20%):** Statin reasonable, consider CAC score
    - **High (≥20%):** High-intensity statin recommended

    Valid for ages 30-79 years.
    """,
)
async def compute_prevent_score(
    input_data: PREVENTInput,
    patient_id: Annotated[
        Optional[int],
        Query(description="Optional patient ID to link calculation"),
    ] = None,
    user: TokenPayload = Depends(require_permission(Permission.CDSS_USE)),
) -> PREVENTResult:
    """
    Calculate PREVENT Equations for ASCVD and Heart Failure risk.

    Returns 10-year ASCVD risk, HF risk, and statin recommendations.
    """
    result = calculate_prevent(input_data)

    # Log calculation for audit
    await log_cdss_calculation(
        calculation_type="PREVENT",
        patient_id=patient_id,
        input_params=input_data.model_dump(),
        result=result.model_dump(),
        user_id=user.sub,
        clinic_id=user.clinic_id,
    )

    return result


@router.post(
    "/euroscore",
    response_model=EuroSCOREIIResult,
    summary="Calculate EuroSCORE II",
    description="""
    Calculate EuroSCORE II for cardiac surgery mortality prediction.

    **Critical for Heart Team Decisions:**
    - CABG vs PCI revascularization strategy
    - SAVR vs TAVI for aortic stenosis
    - Surgical repair vs transcatheter intervention

    **Risk Thresholds:**
    - **Low (<2%):** Good surgical candidate
    - **Intermediate (2-5%):** Heart Team discussion
    - **High (5-10%):** Consider alternatives (TAVI, etc.)
    - **Very High (>10%):** Prohibitive surgical risk

    Uses logistic regression based on 22,381 patients from 154 centers.
    """,
)
async def compute_euroscore_ii(
    input_data: EuroSCOREIIInput,
    patient_id: Annotated[
        Optional[int],
        Query(description="Optional patient ID to link calculation"),
    ] = None,
    user: TokenPayload = Depends(require_permission(Permission.CDSS_USE)),
) -> EuroSCOREIIResult:
    """
    Calculate EuroSCORE II for cardiac surgery risk.

    Returns predicted mortality and Heart Team recommendations.
    """
    result = calculate_euroscore_ii(input_data)

    # Log calculation for audit
    await log_cdss_calculation(
        calculation_type="EuroSCORE-II",
        patient_id=patient_id,
        input_params=input_data.model_dump(),
        result=result.model_dump(),
        user_id=user.sub,
        clinic_id=user.clinic_id,
    )

    return result
