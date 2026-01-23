"""
DICOM Structured Report (SR) Parser for Echocardiography.

Parses TID 5100 (Echo) template content trees to extract quantitative
measurements. Uses LOINC and SNOMED-CT concept codes to identify
measurement types.

Supported measurements:
- LV: LVEF, LVIDd, LVIDs, IVSd, LVPWd, EDV, ESV
- Diastolic: E/A ratio, E/e' ratio, Deceleration Time
- RV: TAPSE

Graceful handling: unrecognized fields return None, never raises.
"""

import logging
from typing import Optional

from app.integrations.dicom.schemas import (
    DiastolicFunction,
    EchoMeasurements,
    LAMeasurements,
    LVMeasurements,
    RVMeasurements,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Concept Code Mappings
# =============================================================================

# Maps (CodingSchemeDesignator, CodeValue) -> measurement field path
# Includes LOINC, SNOMED-CT (SCT), and DICOM (DCM) codes commonly used
# in echo SR reports from various vendors.
CONCEPT_MAP: dict[tuple[str, str], str] = {
    # ---- LV Systolic Function ----
    # LVEF (%)
    ("LN", "18043-0"): "lv.lvef",
    ("LN", "8806-2"): "lv.lvef",
    ("SCT", "70822001"): "lv.lvef",
    ("DCM", "125071"): "lv.lvef",

    # LVIDd (cm -> mm conversion needed)
    ("LN", "18083-6"): "lv.lvidd",
    ("SCT", "399033003"): "lv.lvidd",
    ("DCM", "125072"): "lv.lvidd",

    # LVIDs (cm -> mm conversion needed)
    ("LN", "18085-1"): "lv.lvids",
    ("SCT", "399258004"): "lv.lvids",
    ("DCM", "125073"): "lv.lvids",

    # IVSd (cm -> mm)
    ("LN", "18154-5"): "lv.ivs_d",
    ("SCT", "399098007"): "lv.ivs_d",
    ("DCM", "125074"): "lv.ivs_d",

    # LVPWd (cm -> mm)
    ("LN", "18158-6"): "lv.lvpw_d",
    ("SCT", "399355003"): "lv.lvpw_d",
    ("DCM", "125075"): "lv.lvpw_d",

    # EDV (mL)
    ("LN", "18049-7"): "lv.lv_edv",
    ("SCT", "399344004"): "lv.lv_edv",

    # ESV (mL)
    ("LN", "18050-5"): "lv.lv_esv",
    ("SCT", "399038009"): "lv.lv_esv",

    # ---- Diastolic Function ----
    # E velocity (cm/s)
    ("SCT", "399223006"): "diastolic.e_velocity",
    ("DCM", "125200"): "diastolic.e_velocity",

    # A velocity (cm/s)
    ("SCT", "399221008"): "diastolic.a_velocity",
    ("DCM", "125201"): "diastolic.a_velocity",

    # E/A ratio
    ("LN", "18021-6"): "diastolic.e_a_ratio",
    ("SCT", "399208008"): "diastolic.e_a_ratio",

    # E/e' ratio
    ("LN", "77191-1"): "diastolic.e_e_prime_ratio",
    ("SCT", "443710006"): "diastolic.e_e_prime_ratio",

    # Deceleration time (ms)
    ("LN", "18099-2"): "diastolic.deceleration_time",
    ("SCT", "399355008"): "diastolic.deceleration_time",
    ("DCM", "125202"): "diastolic.deceleration_time",

    # e' septal (cm/s)
    ("SCT", "399240008"): "diastolic.e_prime_septal",

    # e' lateral (cm/s)
    ("SCT", "399241007"): "diastolic.e_prime_lateral",

    # ---- RV ----
    # TAPSE (mm)
    ("LN", "79965-5"): "rv.tapse",
    ("SCT", "399290001"): "rv.tapse",
    ("DCM", "125180"): "rv.tapse",

    # ---- LA ----
    # LA diameter (mm)
    ("LN", "18156-0"): "la.la_diameter",
    ("SCT", "399004009"): "la.la_diameter",

    # LA volume (mL)
    ("SCT", "399064006"): "la.la_volume",

    # LA volume index (mL/m2)
    ("SCT", "399065007"): "la.la_volume_index",
}

# Units that indicate the value is in centimeters (needs *10 for mm)
CM_UNITS = {"cm", "centimeter", "centimeters"}

# Measurement fields that should be stored in mm but may arrive in cm
MM_FIELDS = {
    "lv.lvidd", "lv.lvids", "lv.ivs_d", "lv.lvpw_d",
    "rv.tapse", "la.la_diameter",
}


def parse_sr_dataset(ds) -> Optional[EchoMeasurements]:
    """
    Parse a pydicom Dataset containing an Echo SR into EchoMeasurements.

    Args:
        ds: pydicom Dataset object with ContentSequence

    Returns:
        EchoMeasurements if any measurements were extracted, None otherwise
    """
    try:
        # Get study-level metadata
        study_uid = str(getattr(ds, "StudyInstanceUID", ""))
        if not study_uid:
            return None

        measurements: dict[str, float] = {}

        # Get the content sequence (root of SR tree)
        content_seq = getattr(ds, "ContentSequence", None)
        if content_seq:
            _traverse_content_tree(content_seq, measurements)

        if not measurements:
            return None

        # Build the EchoMeasurements response
        return _build_echo_measurements(study_uid, measurements, ds)

    except Exception as e:
        logger.error(f"Failed to parse SR dataset: {e}")
        return None


def _traverse_content_tree(
    items,
    measurements: dict[str, float],
) -> None:
    """
    Recursively traverse SR content sequence to extract NUM items.

    DICOM SR content trees are nested sequences of items, each with:
    - ValueType: CONTAINER, NUM, TEXT, CODE, etc.
    - ConceptNameCodeSequence: identifies what the item represents
    - ContentSequence: nested children (for CONTAINERs)
    """
    for item in items:
        value_type = str(getattr(item, "ValueType", ""))

        if value_type == "NUM":
            _extract_numeric_measurement(item, measurements)
        elif value_type == "CONTAINER":
            # Recurse into nested content
            nested = getattr(item, "ContentSequence", None)
            if nested:
                _traverse_content_tree(nested, measurements)


def _extract_numeric_measurement(
    item,
    measurements: dict[str, float],
) -> None:
    """
    Extract a numeric measurement from a NUM content item.

    A NUM item contains:
    - ConceptNameCodeSequence: what is being measured
    - MeasuredValueSequence: the numeric value and units
    """
    # Get concept code to identify the measurement
    concept_seq = getattr(item, "ConceptNameCodeSequence", None)
    if not concept_seq or not concept_seq[0]:
        return

    concept = concept_seq[0]
    scheme = str(getattr(concept, "CodingSchemeDesignator", ""))
    code_value = str(getattr(concept, "CodeValue", ""))

    # Look up the field path for this concept code
    field_path = CONCEPT_MAP.get((scheme, code_value))
    if not field_path:
        return

    # Extract the numeric value
    measured_seq = getattr(item, "MeasuredValueSequence", None)
    if not measured_seq or not measured_seq[0]:
        # Some vendors put value directly in NumericValue
        numeric_val = getattr(item, "NumericValue", None)
        if numeric_val is not None:
            try:
                value = float(str(numeric_val))
                measurements[field_path] = value
            except (ValueError, TypeError):
                pass
        return

    measured = measured_seq[0]
    numeric_value = getattr(measured, "NumericValue", None)
    if numeric_value is None:
        return

    try:
        value = float(str(numeric_value))
    except (ValueError, TypeError):
        return

    # Handle unit conversions (cm -> mm for dimension fields)
    units_seq = getattr(measured, "MeasurementUnitsCodeSequence", None)
    if units_seq and units_seq[0]:
        unit_code = str(getattr(units_seq[0], "CodeValue", ""))
        unit_meaning = str(getattr(units_seq[0], "CodeMeaning", "")).lower()

        if field_path in MM_FIELDS and (unit_code in CM_UNITS or unit_meaning in CM_UNITS):
            value *= 10.0  # Convert cm to mm

    measurements[field_path] = value


def _build_echo_measurements(
    study_uid: str,
    measurements: dict[str, float],
    ds,
) -> EchoMeasurements:
    """
    Build EchoMeasurements from extracted measurement dict.

    Maps flat "section.field" keys into the nested Pydantic model structure.
    """
    lv = LVMeasurements(
        lvef=measurements.get("lv.lvef"),
        lvidd=measurements.get("lv.lvidd"),
        lvids=measurements.get("lv.lvids"),
        ivs_d=measurements.get("lv.ivs_d"),
        lvpw_d=measurements.get("lv.lvpw_d"),
        lv_edv=measurements.get("lv.lv_edv"),
        lv_esv=measurements.get("lv.lv_esv"),
    )

    rv = RVMeasurements(
        tapse=measurements.get("rv.tapse"),
    )

    la = LAMeasurements(
        la_diameter=measurements.get("la.la_diameter"),
        la_volume=measurements.get("la.la_volume"),
        la_volume_index=measurements.get("la.la_volume_index"),
    )

    diastolic = DiastolicFunction(
        e_velocity=measurements.get("diastolic.e_velocity"),
        a_velocity=measurements.get("diastolic.a_velocity"),
        e_a_ratio=measurements.get("diastolic.e_a_ratio"),
        e_prime_septal=measurements.get("diastolic.e_prime_septal"),
        e_prime_lateral=measurements.get("diastolic.e_prime_lateral"),
        e_e_prime_ratio=measurements.get("diastolic.e_e_prime_ratio"),
        deceleration_time=measurements.get("diastolic.deceleration_time"),
    )

    # Extract study date from DICOM header
    study_date = None
    study_date_str = str(getattr(ds, "StudyDate", ""))
    if study_date_str and len(study_date_str) == 8:
        try:
            from datetime import date
            study_date = date(
                int(study_date_str[:4]),
                int(study_date_str[4:6]),
                int(study_date_str[6:8]),
            )
        except ValueError:
            pass

    return EchoMeasurements(
        study_instance_uid=study_uid,
        study_date=study_date,
        lv=lv,
        rv=rv,
        la=la,
        diastolic=diastolic,
        findings=f"Extracted {len(measurements)} measurements from SR",
    )
