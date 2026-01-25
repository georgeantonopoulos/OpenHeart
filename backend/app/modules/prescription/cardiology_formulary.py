"""Curated cardiology drug formulary with sensible defaults.

Provides pre-configured drug templates for common cardiology medications,
enabling quick prescribing with appropriate default doses, frequencies,
and routes based on ESC 2024 guidelines.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DrugTemplate:
    """A formulary drug template with prescribing defaults."""

    generic_name: str
    atc_code: str
    category: str
    default_strength: str
    default_form: str = "tablet"
    default_frequency: str = "OD"
    default_route: str = "oral"
    is_chronic: bool = True
    available_strengths: list[str] = field(default_factory=list)
    common_indications: list[str] = field(default_factory=list)
    loading_dose: Optional[str] = None
    renal_adjustment: Optional[dict] = None


# =============================================================================
# Cardiology Formulary
# =============================================================================

CARDIOLOGY_FORMULARY: dict[str, list[DrugTemplate]] = {
    "antiplatelets": [
        DrugTemplate(
            generic_name="Aspirin",
            atc_code="B01AC06",
            category="antiplatelets",
            default_strength="75mg",
            available_strengths=["75mg", "100mg", "300mg"],
            common_indications=["Post-ACS", "Secondary prevention CVD", "Post-PCI"],
        ),
        DrugTemplate(
            generic_name="Clopidogrel",
            atc_code="B01AC04",
            category="antiplatelets",
            default_strength="75mg",
            available_strengths=["75mg", "300mg"],
            common_indications=["Post-ACS", "Post-PCI", "PAD", "Stroke prevention"],
            loading_dose="300mg STAT",
        ),
        DrugTemplate(
            generic_name="Ticagrelor",
            atc_code="B01AC24",
            category="antiplatelets",
            default_strength="90mg",
            default_frequency="BD",
            available_strengths=["60mg", "90mg"],
            common_indications=["ACS", "Post-MI prevention"],
            loading_dose="180mg STAT",
        ),
        DrugTemplate(
            generic_name="Prasugrel",
            atc_code="B01AC22",
            category="antiplatelets",
            default_strength="10mg",
            available_strengths=["5mg", "10mg"],
            common_indications=["ACS with PCI", "STEMI"],
            loading_dose="60mg STAT",
        ),
    ],

    "anticoagulants": [
        DrugTemplate(
            generic_name="Apixaban",
            atc_code="B01AF02",
            category="anticoagulants",
            default_strength="5mg",
            default_frequency="BD",
            available_strengths=["2.5mg", "5mg"],
            common_indications=["Atrial fibrillation", "DVT/PE treatment", "DVT/PE prophylaxis"],
            renal_adjustment={"egfr_threshold": 25, "adjusted_dose": "2.5mg BD"},
        ),
        DrugTemplate(
            generic_name="Rivaroxaban",
            atc_code="B01AF01",
            category="anticoagulants",
            default_strength="20mg",
            available_strengths=["2.5mg", "10mg", "15mg", "20mg"],
            common_indications=["Atrial fibrillation", "DVT/PE", "ACS (2.5mg)"],
            renal_adjustment={"egfr_threshold": 50, "adjusted_dose": "15mg OD"},
        ),
        DrugTemplate(
            generic_name="Edoxaban",
            atc_code="B01AF03",
            category="anticoagulants",
            default_strength="60mg",
            available_strengths=["30mg", "60mg"],
            common_indications=["Atrial fibrillation", "DVT/PE"],
            renal_adjustment={"egfr_threshold": 50, "adjusted_dose": "30mg OD"},
        ),
        DrugTemplate(
            generic_name="Dabigatran",
            atc_code="B01AE07",
            category="anticoagulants",
            default_strength="150mg",
            default_frequency="BD",
            available_strengths=["75mg", "110mg", "150mg"],
            common_indications=["Atrial fibrillation", "DVT/PE"],
            renal_adjustment={"egfr_threshold": 30, "adjusted_dose": "110mg BD"},
        ),
        DrugTemplate(
            generic_name="Warfarin",
            atc_code="B01AA03",
            category="anticoagulants",
            default_strength="5mg",
            available_strengths=["1mg", "3mg", "5mg"],
            common_indications=["Mechanical valve", "AF (if DOACs contraindicated)", "Antiphospholipid syndrome"],
        ),
        DrugTemplate(
            generic_name="Enoxaparin",
            atc_code="B01AB05",
            category="anticoagulants",
            default_strength="40mg",
            default_form="injection",
            default_route="SC",
            is_chronic=False,
            available_strengths=["20mg", "40mg", "60mg", "80mg", "100mg"],
            common_indications=["DVT prophylaxis", "ACS bridging", "DVT treatment"],
            renal_adjustment={"egfr_threshold": 30, "adjusted_dose": "Reduce by 50%"},
        ),
    ],

    "statins": [
        DrugTemplate(
            generic_name="Atorvastatin",
            atc_code="C10AA05",
            category="statins",
            default_strength="40mg",
            available_strengths=["10mg", "20mg", "40mg", "80mg"],
            common_indications=["Hyperlipidemia", "Secondary prevention CVD", "Post-ACS (80mg)"],
        ),
        DrugTemplate(
            generic_name="Rosuvastatin",
            atc_code="C10AA07",
            category="statins",
            default_strength="20mg",
            available_strengths=["5mg", "10mg", "20mg", "40mg"],
            common_indications=["Hyperlipidemia", "Secondary prevention CVD"],
            renal_adjustment={"egfr_threshold": 30, "adjusted_dose": "Max 10mg"},
        ),
        DrugTemplate(
            generic_name="Simvastatin",
            atc_code="C10AA01",
            category="statins",
            default_strength="20mg",
            default_frequency="nocte",
            available_strengths=["10mg", "20mg", "40mg"],
            common_indications=["Hyperlipidemia"],
        ),
        DrugTemplate(
            generic_name="Pravastatin",
            atc_code="C10AA03",
            category="statins",
            default_strength="40mg",
            default_frequency="nocte",
            available_strengths=["10mg", "20mg", "40mg"],
            common_indications=["Hyperlipidemia", "Statin intolerance (lower myalgia risk)"],
        ),
    ],

    "beta_blockers": [
        DrugTemplate(
            generic_name="Bisoprolol",
            atc_code="C07AB07",
            category="beta_blockers",
            default_strength="5mg",
            available_strengths=["1.25mg", "2.5mg", "5mg", "10mg"],
            common_indications=["Heart failure", "Rate control AF", "Hypertension", "Angina"],
        ),
        DrugTemplate(
            generic_name="Metoprolol Succinate",
            atc_code="C07AB02",
            category="beta_blockers",
            default_strength="50mg",
            available_strengths=["25mg", "50mg", "100mg", "200mg"],
            common_indications=["Heart failure", "Post-MI", "Rate control AF"],
        ),
        DrugTemplate(
            generic_name="Carvedilol",
            atc_code="C07AG02",
            category="beta_blockers",
            default_strength="6.25mg",
            default_frequency="BD",
            available_strengths=["3.125mg", "6.25mg", "12.5mg", "25mg"],
            common_indications=["Heart failure", "Hypertension"],
        ),
        DrugTemplate(
            generic_name="Nebivolol",
            atc_code="C07AB12",
            category="beta_blockers",
            default_strength="5mg",
            available_strengths=["2.5mg", "5mg", "10mg"],
            common_indications=["Hypertension", "Heart failure (elderly)"],
        ),
        DrugTemplate(
            generic_name="Atenolol",
            atc_code="C07AB03",
            category="beta_blockers",
            default_strength="50mg",
            available_strengths=["25mg", "50mg", "100mg"],
            common_indications=["Hypertension", "Angina"],
            renal_adjustment={"egfr_threshold": 35, "adjusted_dose": "Max 50mg"},
        ),
    ],

    "ace_inhibitors": [
        DrugTemplate(
            generic_name="Ramipril",
            atc_code="C09AA05",
            category="ace_inhibitors",
            default_strength="5mg",
            available_strengths=["1.25mg", "2.5mg", "5mg", "10mg"],
            common_indications=["Heart failure", "Post-MI", "Hypertension", "Renal protection"],
        ),
        DrugTemplate(
            generic_name="Perindopril",
            atc_code="C09AA04",
            category="ace_inhibitors",
            default_strength="5mg",
            available_strengths=["2mg", "4mg", "5mg", "8mg", "10mg"],
            common_indications=["Hypertension", "Stable CAD", "Heart failure"],
        ),
        DrugTemplate(
            generic_name="Enalapril",
            atc_code="C09AA02",
            category="ace_inhibitors",
            default_strength="10mg",
            default_frequency="BD",
            available_strengths=["2.5mg", "5mg", "10mg", "20mg"],
            common_indications=["Heart failure", "Hypertension"],
        ),
        DrugTemplate(
            generic_name="Lisinopril",
            atc_code="C09AA03",
            category="ace_inhibitors",
            default_strength="10mg",
            available_strengths=["2.5mg", "5mg", "10mg", "20mg"],
            common_indications=["Hypertension", "Heart failure", "Post-MI"],
        ),
    ],

    "arbs": [
        DrugTemplate(
            generic_name="Valsartan",
            atc_code="C09CA03",
            category="arbs",
            default_strength="80mg",
            default_frequency="BD",
            available_strengths=["40mg", "80mg", "160mg"],
            common_indications=["Heart failure", "Hypertension", "Post-MI (ACE-I intolerant)"],
        ),
        DrugTemplate(
            generic_name="Candesartan",
            atc_code="C09CA06",
            category="arbs",
            default_strength="8mg",
            available_strengths=["4mg", "8mg", "16mg", "32mg"],
            common_indications=["Heart failure", "Hypertension"],
        ),
        DrugTemplate(
            generic_name="Irbesartan",
            atc_code="C09CA04",
            category="arbs",
            default_strength="150mg",
            available_strengths=["75mg", "150mg", "300mg"],
            common_indications=["Hypertension", "Diabetic nephropathy"],
        ),
        DrugTemplate(
            generic_name="Losartan",
            atc_code="C09CA01",
            category="arbs",
            default_strength="50mg",
            available_strengths=["25mg", "50mg", "100mg"],
            common_indications=["Hypertension", "Diabetic nephropathy"],
        ),
        DrugTemplate(
            generic_name="Telmisartan",
            atc_code="C09CA07",
            category="arbs",
            default_strength="40mg",
            available_strengths=["20mg", "40mg", "80mg"],
            common_indications=["Hypertension", "CV risk reduction"],
        ),
    ],

    "ccbs": [
        DrugTemplate(
            generic_name="Amlodipine",
            atc_code="C08CA01",
            category="ccbs",
            default_strength="5mg",
            available_strengths=["2.5mg", "5mg", "10mg"],
            common_indications=["Hypertension", "Angina"],
        ),
        DrugTemplate(
            generic_name="Nifedipine MR",
            atc_code="C08CA05",
            category="ccbs",
            default_strength="30mg",
            available_strengths=["20mg", "30mg", "60mg"],
            common_indications=["Hypertension", "Angina"],
        ),
        DrugTemplate(
            generic_name="Diltiazem",
            atc_code="C08DB01",
            category="ccbs",
            default_strength="120mg",
            available_strengths=["60mg", "90mg", "120mg", "180mg", "240mg"],
            common_indications=["Rate control AF", "Angina", "Hypertension"],
        ),
        DrugTemplate(
            generic_name="Verapamil",
            atc_code="C08DA01",
            category="ccbs",
            default_strength="80mg",
            default_frequency="TDS",
            available_strengths=["40mg", "80mg", "120mg", "240mg"],
            common_indications=["Rate control AF/SVT", "Angina", "Hypertension"],
        ),
    ],

    "diuretics": [
        DrugTemplate(
            generic_name="Furosemide",
            atc_code="C03CA01",
            category="diuretics",
            default_strength="40mg",
            available_strengths=["20mg", "40mg", "80mg", "250mg"],
            common_indications=["Heart failure", "Edema", "Pulmonary edema"],
        ),
        DrugTemplate(
            generic_name="Bumetanide",
            atc_code="C03CA02",
            category="diuretics",
            default_strength="1mg",
            available_strengths=["0.5mg", "1mg", "2mg"],
            common_indications=["Heart failure (furosemide-resistant)", "Edema"],
        ),
        DrugTemplate(
            generic_name="Spironolactone",
            atc_code="C03DA01",
            category="diuretics",
            default_strength="25mg",
            available_strengths=["25mg", "50mg", "100mg"],
            common_indications=["Heart failure (HFrEF)", "Resistant hypertension", "Ascites"],
        ),
        DrugTemplate(
            generic_name="Eplerenone",
            atc_code="C03DA04",
            category="diuretics",
            default_strength="25mg",
            available_strengths=["25mg", "50mg"],
            common_indications=["Heart failure post-MI", "HFrEF"],
        ),
        DrugTemplate(
            generic_name="Hydrochlorothiazide",
            atc_code="C03AA03",
            category="diuretics",
            default_strength="12.5mg",
            available_strengths=["12.5mg", "25mg"],
            common_indications=["Hypertension"],
        ),
        DrugTemplate(
            generic_name="Indapamide",
            atc_code="C03BA11",
            category="diuretics",
            default_strength="1.5mg",
            available_strengths=["1.5mg", "2.5mg"],
            common_indications=["Hypertension"],
        ),
    ],

    "antiarrhythmics": [
        DrugTemplate(
            generic_name="Amiodarone",
            atc_code="C01BD01",
            category="antiarrhythmics",
            default_strength="200mg",
            available_strengths=["100mg", "200mg"],
            common_indications=["AF rhythm control", "VT", "Cardiac arrest"],
            loading_dose="200mg TDS for 1 week, then 200mg BD for 1 week, then 200mg OD",
        ),
        DrugTemplate(
            generic_name="Flecainide",
            atc_code="C01BC04",
            category="antiarrhythmics",
            default_strength="100mg",
            default_frequency="BD",
            available_strengths=["50mg", "100mg", "150mg"],
            common_indications=["AF rhythm control (structurally normal heart)", "SVT"],
        ),
        DrugTemplate(
            generic_name="Dronedarone",
            atc_code="C01BD07",
            category="antiarrhythmics",
            default_strength="400mg",
            default_frequency="BD",
            available_strengths=["400mg"],
            common_indications=["AF rhythm control (alternative to amiodarone)"],
        ),
        DrugTemplate(
            generic_name="Sotalol",
            atc_code="C07AA07",
            category="antiarrhythmics",
            default_strength="80mg",
            default_frequency="BD",
            available_strengths=["40mg", "80mg", "160mg"],
            common_indications=["AF rhythm control", "VT prevention"],
            renal_adjustment={"egfr_threshold": 40, "adjusted_dose": "Reduce dose, extend interval"},
        ),
    ],

    "nitrates": [
        DrugTemplate(
            generic_name="Glyceryl Trinitrate (GTN)",
            atc_code="C01DA02",
            category="nitrates",
            default_strength="0.5mg",
            default_form="sublingual tablet",
            default_route="sublingual",
            is_chronic=False,
            available_strengths=["0.3mg", "0.5mg", "0.6mg"],
            common_indications=["Acute angina", "Angina prophylaxis"],
        ),
        DrugTemplate(
            generic_name="Isosorbide Dinitrate (ISDN)",
            atc_code="C01DA08",
            category="nitrates",
            default_strength="20mg",
            default_frequency="BD",
            available_strengths=["10mg", "20mg", "40mg"],
            common_indications=["Angina prophylaxis", "Heart failure (with hydralazine)"],
        ),
        DrugTemplate(
            generic_name="Isosorbide Mononitrate (ISMN)",
            atc_code="C01DA14",
            category="nitrates",
            default_strength="60mg",
            available_strengths=["20mg", "30mg", "60mg", "120mg"],
            common_indications=["Angina prophylaxis"],
        ),
    ],

    "heart_failure": [
        DrugTemplate(
            generic_name="Sacubitril/Valsartan",
            atc_code="C09DX04",
            category="heart_failure",
            default_strength="49/51mg",
            default_frequency="BD",
            available_strengths=["24/26mg", "49/51mg", "97/103mg"],
            common_indications=["HFrEF (LVEF <=40%)", "Replaces ACE-I/ARB in HFrEF"],
        ),
        DrugTemplate(
            generic_name="Ivabradine",
            atc_code="C01EB17",
            category="heart_failure",
            default_strength="5mg",
            default_frequency="BD",
            available_strengths=["2.5mg", "5mg", "7.5mg"],
            common_indications=["HFrEF (HR >70 on max beta-blocker)", "Stable angina (if beta-blocker contraindicated)"],
        ),
        DrugTemplate(
            generic_name="Dapagliflozin",
            atc_code="A10BK01",
            category="heart_failure",
            default_strength="10mg",
            available_strengths=["5mg", "10mg"],
            common_indications=["HFrEF", "HFpEF", "Type 2 DM with CVD"],
        ),
        DrugTemplate(
            generic_name="Empagliflozin",
            atc_code="A10BK03",
            category="heart_failure",
            default_strength="10mg",
            available_strengths=["10mg", "25mg"],
            common_indications=["HFrEF", "HFpEF", "Type 2 DM with CVD"],
        ),
    ],

    "other_cardiovascular": [
        DrugTemplate(
            generic_name="Ranolazine",
            atc_code="C01EB18",
            category="other_cardiovascular",
            default_strength="500mg",
            default_frequency="BD",
            available_strengths=["375mg", "500mg", "750mg"],
            common_indications=["Refractory angina (add-on therapy)"],
        ),
        DrugTemplate(
            generic_name="Digoxin",
            atc_code="C01AA05",
            category="other_cardiovascular",
            default_strength="125mcg",
            available_strengths=["62.5mcg", "125mcg", "250mcg"],
            common_indications=["Rate control AF (if beta-blocker insufficient)", "HFrEF with AF"],
            renal_adjustment={"egfr_threshold": 50, "adjusted_dose": "62.5mcg OD, monitor levels"},
        ),
        DrugTemplate(
            generic_name="Hydralazine",
            atc_code="C02DB02",
            category="other_cardiovascular",
            default_strength="25mg",
            default_frequency="TDS",
            available_strengths=["25mg", "50mg"],
            common_indications=["HFrEF (with ISDN if ACE-I/ARB not tolerated)", "Hypertension in pregnancy"],
        ),
    ],
}


def get_all_formulary_drugs() -> list[DrugTemplate]:
    """Get a flat list of all drugs in the formulary."""
    drugs = []
    for category_drugs in CARDIOLOGY_FORMULARY.values():
        drugs.extend(category_drugs)
    return drugs


def search_formulary(query: str) -> list[DrugTemplate]:
    """Search formulary by drug name or ATC code (case-insensitive)."""
    query_lower = query.lower()
    results = []
    for category_drugs in CARDIOLOGY_FORMULARY.values():
        for drug in category_drugs:
            if (
                query_lower in drug.generic_name.lower()
                or query_lower in drug.atc_code.lower()
                or any(query_lower in ind.lower() for ind in drug.common_indications)
            ):
                results.append(drug)
    return results


def get_drug_by_atc(atc_code: str) -> Optional[DrugTemplate]:
    """Get a drug template by exact ATC code."""
    for category_drugs in CARDIOLOGY_FORMULARY.values():
        for drug in category_drugs:
            if drug.atc_code == atc_code:
                return drug
    return None
