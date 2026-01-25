"""Drug-drug interaction checking engine for cardiology prescriptions.

Implements rule-based interaction detection using ATC code matching.
Covers the most clinically significant cardiology drug interactions
based on ESC 2024 guidelines.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

from app.modules.prescription.schemas import InteractionDetail

logger = logging.getLogger(__name__)


@dataclass
class InteractionRule:
    """A single drug-drug interaction rule."""

    severity: str  # minor, moderate, major, contraindicated
    interaction_type: str  # pharmacodynamic, pharmacokinetic, therapeutic_duplication
    description: str
    management: str

    # Matching criteria (at least one of these must be set for each drug)
    drug_a_atc: Optional[str] = None  # Exact ATC code
    drug_a_atc_prefix: Optional[str] = None  # ATC prefix match
    drug_b_atc: Optional[str] = None
    drug_b_atc_prefix: Optional[str] = None
    drug_b_atc_codes: list[str] = field(default_factory=list)  # Multiple exact codes


def _matches_atc(drug_atc: Optional[str], rule_atc: Optional[str], rule_prefix: Optional[str], rule_codes: list[str]) -> bool:
    """Check if a drug's ATC code matches a rule's criteria."""
    if not drug_atc:
        return False
    if rule_atc and drug_atc == rule_atc:
        return True
    if rule_prefix and drug_atc.startswith(rule_prefix):
        return True
    if rule_codes and drug_atc in rule_codes:
        return True
    return False


# =============================================================================
# Cardiology-Specific Interaction Rules
# =============================================================================

CARDIOLOGY_INTERACTIONS: list[InteractionRule] = [
    # -------------------------------------------------------------------------
    # Anticoagulant + Antiplatelet = Bleeding Risk
    # -------------------------------------------------------------------------
    InteractionRule(
        drug_a_atc_prefix="B01AF",  # DOACs (Apixaban, Rivaroxaban, Edoxaban, Dabigatran)
        drug_b_atc_prefix="B01AC",  # Antiplatelets (Aspirin, Clopidogrel, Ticagrelor, Prasugrel)
        severity="major",
        interaction_type="pharmacodynamic",
        description="Combined anticoagulant and antiplatelet therapy significantly increases bleeding risk",
        management="Triple therapy (OAC+DAPT) should be limited to 1-4 weeks (ESC 2024). Prefer clopidogrel as the single antiplatelet for long-term dual therapy. Monitor for bleeding signs. Consider PPI co-prescription.",
    ),

    # -------------------------------------------------------------------------
    # Digoxin + Amiodarone = Toxicity
    # -------------------------------------------------------------------------
    InteractionRule(
        drug_a_atc="C01AA05",  # Digoxin
        drug_b_atc="C01BD01",  # Amiodarone
        severity="major",
        interaction_type="pharmacokinetic",
        description="Amiodarone increases digoxin levels by 70-100%, risking toxicity",
        management="Reduce digoxin dose by 50% when initiating amiodarone. Monitor digoxin levels.",
    ),

    # -------------------------------------------------------------------------
    # ACE-I + K-sparing diuretic = Hyperkalemia
    # -------------------------------------------------------------------------
    InteractionRule(
        drug_a_atc_prefix="C09A",   # ACE inhibitors
        drug_b_atc_prefix="C03DA",  # K-sparing diuretics (Spironolactone, Eplerenone)
        severity="major",
        interaction_type="pharmacodynamic",
        description="Risk of life-threatening hyperkalemia",
        management="Monitor potassium closely. Start K-sparing diuretic at low dose. Check K+ within 1 week.",
    ),

    # -------------------------------------------------------------------------
    # ARB + K-sparing diuretic = Hyperkalemia
    # -------------------------------------------------------------------------
    InteractionRule(
        drug_a_atc_prefix="C09C",   # ARBs
        drug_b_atc_prefix="C03DA",  # K-sparing diuretics
        severity="major",
        interaction_type="pharmacodynamic",
        description="Risk of life-threatening hyperkalemia",
        management="Monitor potassium closely. Start K-sparing diuretic at low dose. Check K+ within 1 week.",
    ),

    # -------------------------------------------------------------------------
    # Statin + Fibrate = Rhabdomyolysis
    # -------------------------------------------------------------------------
    InteractionRule(
        drug_a_atc_prefix="C10AA",  # Statins
        drug_b_atc_prefix="C10AB",  # Fibrates
        severity="major",
        interaction_type="pharmacokinetic",
        description="Increased risk of myopathy and rhabdomyolysis",
        management="Prefer fenofibrate over gemfibrozil. Monitor CK levels. Educate patient on myalgia symptoms.",
    ),

    # -------------------------------------------------------------------------
    # Beta-blocker + Non-dihydropyridine CCB = Heart Block
    # -------------------------------------------------------------------------
    InteractionRule(
        drug_a_atc_prefix="C07",    # Beta-blockers
        drug_b_atc_codes=["C08DA01", "C08DB01"],  # Verapamil, Diltiazem
        severity="contraindicated",
        interaction_type="pharmacodynamic",
        description="Combined negative chronotropic/dromotropic effects risk severe bradycardia or heart block. CONTRAINDICATED in Heart Failure or LVEF <40%.",
        management="CONTRAINDICATED in patients with clinical Heart Failure or LVEF <40%. Use dihydropyridine CCB (Amlodipine) instead if CCB needed.",
    ),

    # -------------------------------------------------------------------------
    # Warfarin + Amiodarone = INR elevation
    # -------------------------------------------------------------------------
    InteractionRule(
        drug_a_atc="B01AA03",  # Warfarin
        drug_b_atc="C01BD01",  # Amiodarone
        severity="major",
        interaction_type="pharmacokinetic",
        description="Amiodarone inhibits warfarin metabolism, increasing INR by 30-50%",
        management="Reduce warfarin dose by 30-50%. Check INR weekly for 4-6 weeks.",
    ),

    # -------------------------------------------------------------------------
    # DOAC + Strong CYP3A4/P-gp inhibitors
    # -------------------------------------------------------------------------
    InteractionRule(
        drug_a_atc_prefix="B01AF",  # DOACs
        drug_b_atc_codes=["J02AC01", "J02AC02", "J02AC03"],  # Ketoconazole, Itraconazole, Voriconazole
        severity="contraindicated",
        interaction_type="pharmacokinetic",
        description="Strong CYP3A4/P-gp inhibition markedly increases DOAC levels",
        management="AVOID combination. Consider alternative antifungal or switch to warfarin with INR monitoring.",
    ),

    # -------------------------------------------------------------------------
    # Therapeutic duplication: Two anticoagulants
    # -------------------------------------------------------------------------
    InteractionRule(
        drug_a_atc_prefix="B01A",
        drug_b_atc_prefix="B01A",
        severity="major",
        interaction_type="therapeutic_duplication",
        description="Duplicate anticoagulant therapy - extreme bleeding risk",
        management="Review if intentional bridging therapy. Ensure single anticoagulant for maintenance.",
    ),

    # -------------------------------------------------------------------------
    # Nitrate + PDE5 inhibitor = Severe hypotension
    # -------------------------------------------------------------------------
    InteractionRule(
        drug_a_atc_prefix="C01DA",  # Nitrates
        drug_b_atc_prefix="G04BE",  # PDE5 inhibitors (Sildenafil, Tadalafil)
        severity="contraindicated",
        interaction_type="pharmacodynamic",
        description="Synergistic vasodilation causing potentially fatal hypotension",
        management="ABSOLUTE contraindication. Wait 24-48h after PDE5i before nitrate use.",
    ),

    # -------------------------------------------------------------------------
    # Warfarin + NSAIDs = Bleeding
    # -------------------------------------------------------------------------
    InteractionRule(
        drug_a_atc="B01AA03",  # Warfarin
        drug_b_atc_prefix="M01A",  # NSAIDs
        severity="major",
        interaction_type="pharmacodynamic",
        description="NSAIDs increase bleeding risk with warfarin via GI ulceration and platelet inhibition",
        management="Avoid combination if possible. If essential, use lowest NSAID dose for shortest duration. Add PPI. Monitor INR.",
    ),

    # -------------------------------------------------------------------------
    # DOAC + NSAIDs = Bleeding
    # -------------------------------------------------------------------------
    InteractionRule(
        drug_a_atc_prefix="B01AF",  # DOACs
        drug_b_atc_prefix="M01A",   # NSAIDs
        severity="major",
        interaction_type="pharmacodynamic",
        description="NSAIDs significantly increase bleeding risk with DOACs",
        management="Avoid combination. If essential, use lowest NSAID dose for shortest duration. Add PPI.",
    ),

    # -------------------------------------------------------------------------
    # Two Antiarrhythmics = QT prolongation / proarrhythmia
    # -------------------------------------------------------------------------
    InteractionRule(
        drug_a_atc_prefix="C01B",  # Antiarrhythmics
        drug_b_atc_prefix="C01B",  # Antiarrhythmics
        severity="major",
        interaction_type="therapeutic_duplication",
        description="Combination of antiarrhythmics increases proarrhythmic risk and QT prolongation",
        management="Avoid combination. If switching, ensure adequate washout period.",
    ),

    # -------------------------------------------------------------------------
    # ACE-I + ARB = Hyperkalemia + Renal impairment
    # -------------------------------------------------------------------------
    InteractionRule(
        drug_a_atc_prefix="C09A",  # ACE inhibitors
        drug_b_atc_prefix="C09C",  # ARBs
        severity="contraindicated",
        interaction_type="pharmacodynamic",
        description="Dual RAAS blockade increases risk of hyperkalemia, hypotension, and renal failure (ONTARGET trial)",
        management="AVOID combination. Use one RAAS blocker only.",
    ),

    # -------------------------------------------------------------------------
    # Sacubitril/Valsartan + ACE-I = Angioedema
    # -------------------------------------------------------------------------
    InteractionRule(
        drug_a_atc="C09DX04",  # Sacubitril/Valsartan
        drug_b_atc_prefix="C09A",  # ACE inhibitors
        severity="contraindicated",
        interaction_type="pharmacodynamic",
        description="Combined neprilysin and ACE inhibition dramatically increases angioedema risk",
        management="CONTRAINDICATED. Stop ACE-I for at least 36 hours before starting Sacubitril/Valsartan.",
    ),
]


# =============================================================================
# Interaction Engine
# =============================================================================


class InteractionEngine:
    """Checks drug-drug interactions for cardiology prescriptions."""

    def __init__(self, rules: Optional[list[InteractionRule]] = None):
        self.rules = rules or CARDIOLOGY_INTERACTIONS

    def check_interactions(
        self,
        new_drug_atc: Optional[str],
        new_drug_name: str,
        active_medications: list[dict],
    ) -> list[InteractionDetail]:
        """
        Check a proposed drug against active medications for interactions.

        Args:
            new_drug_atc: ATC code of the proposed drug (may be None)
            new_drug_name: Name of the proposed drug
            active_medications: List of dicts with keys: drug_name, atc_code, prescription_id

        Returns:
            List of InteractionDetail sorted by severity (most severe first)
        """
        if not new_drug_atc:
            return []

        interactions: list[InteractionDetail] = []
        seen_rules: set[int] = set()  # Avoid duplicate alerts

        for med in active_medications:
            existing_atc = med.get("atc_code")
            if not existing_atc:
                continue

            for i, rule in enumerate(self.rules):
                if i in seen_rules:
                    continue

                # Check both directions: new_drug as A and existing as B, then vice versa
                match = self._check_rule(rule, new_drug_atc, existing_atc)
                if match:
                    interactions.append(
                        InteractionDetail(
                            interacting_drug=med["drug_name"],
                            interacting_atc=existing_atc,
                            interacting_prescription_id=med.get("prescription_id"),
                            severity=rule.severity,
                            interaction_type=rule.interaction_type,
                            description=rule.description,
                            management=rule.management,
                        )
                    )
                    seen_rules.add(i)

        # Also check therapeutic duplication (same ATC level 4)
        dup = self._check_therapeutic_duplication(new_drug_atc, new_drug_name, active_medications)
        if dup and not any(
            i.interaction_type == "therapeutic_duplication" for i in interactions
        ):
            interactions.append(dup)

        # Sort by severity: contraindicated > major > moderate > minor
        severity_order = {"contraindicated": 0, "major": 1, "moderate": 2, "minor": 3}
        interactions.sort(key=lambda x: severity_order.get(x.severity, 4))

        return interactions

    def _check_rule(self, rule: InteractionRule, drug_a_atc: str, drug_b_atc: str) -> bool:
        """Check if a rule matches a pair of ATC codes (bidirectional)."""
        # Forward: drug_a matches rule.drug_a_*, drug_b matches rule.drug_b_*
        forward = (
            _matches_atc(drug_a_atc, rule.drug_a_atc, rule.drug_a_atc_prefix, [])
            and _matches_atc(drug_b_atc, rule.drug_b_atc, rule.drug_b_atc_prefix, rule.drug_b_atc_codes)
        )
        # Reverse: drug_a matches rule.drug_b_*, drug_b matches rule.drug_a_*
        reverse = (
            _matches_atc(drug_a_atc, rule.drug_b_atc, rule.drug_b_atc_prefix, rule.drug_b_atc_codes)
            and _matches_atc(drug_b_atc, rule.drug_a_atc, rule.drug_a_atc_prefix, [])
        )
        return forward or reverse

    def _check_therapeutic_duplication(
        self,
        new_atc: str,
        new_drug_name: str,
        active_medications: list[dict],
    ) -> Optional[InteractionDetail]:
        """Flag if same therapeutic subgroup (ATC level 4) already prescribed."""
        if len(new_atc) < 5:
            return None

        # ATC level 4 = first 5 characters (e.g., C10AA for HMG CoA reductase inhibitors)
        new_level4 = new_atc[:5]

        for med in active_medications:
            existing_atc = med.get("atc_code", "")
            if existing_atc and existing_atc[:5] == new_level4 and existing_atc != new_atc:
                return InteractionDetail(
                    interacting_drug=med["drug_name"],
                    interacting_atc=existing_atc,
                    interacting_prescription_id=med.get("prescription_id"),
                    severity="moderate",
                    interaction_type="therapeutic_duplication",
                    description=f"Therapeutic duplication: both {new_drug_name} and {med['drug_name']} are in the same therapeutic subgroup ({new_level4})",
                    management="Review if both drugs in the same subgroup are clinically justified. Consider discontinuing one.",
                )
        return None
