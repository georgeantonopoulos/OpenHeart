"""
Clinical Decision Support System (CDSS) for OpenHeart Cyprus.

Provides validated risk calculators for cardiology:
- GRACE Score (Acute Coronary Syndrome)
- CHA₂DS₂-VASc Score (AF Stroke Risk)
- HAS-BLED Score (Bleeding Risk)
- ASCVD/PREVENT (10-Year CVD Risk)
"""

from app.modules.cardiology.cdss.calculators import (
    calculate_cha2ds2vasc,
    calculate_grace_score,
    calculate_hasbled,
)
from app.modules.cardiology.cdss.models import (
    CHA2DS2VAScInput,
    CHA2DS2VAScResult,
    GRACEInput,
    GRACEResult,
    HASBLEDInput,
    HASBLEDResult,
    KillipClass,
)

__all__ = [
    # GRACE
    "GRACEInput",
    "GRACEResult",
    "KillipClass",
    "calculate_grace_score",
    # CHA2DS2-VASc
    "CHA2DS2VAScInput",
    "CHA2DS2VAScResult",
    "calculate_cha2ds2vasc",
    # HAS-BLED
    "HASBLEDInput",
    "HASBLEDResult",
    "calculate_hasbled",
]
