"""
DICOM Schemas for OpenHeart Cyprus.

Defines Pydantic models for DICOM metadata and cardiology-specific
structured reports (Echo, Cath Lab).
"""

from datetime import date, datetime
from typing import Optional
from enum import Enum

from pydantic import BaseModel, Field


class Modality(str, Enum):
    """DICOM Modality codes for cardiology imaging."""

    US = "US"  # Ultrasound (Echocardiography)
    XA = "XA"  # X-Ray Angiography (Cath Lab)
    CT = "CT"  # Computed Tomography
    MR = "MR"  # Magnetic Resonance
    NM = "NM"  # Nuclear Medicine (SPECT, PET)
    ECG = "ECG"  # Electrocardiography
    HD = "HD"  # Hemodynamic Waveform
    SR = "SR"  # Structured Report


class StudyStatus(str, Enum):
    """Status of DICOM study in OpenHeart."""

    NEW = "new"
    IN_PROGRESS = "in_progress"
    PRELIMINARY = "preliminary"
    FINAL = "final"
    ADDENDUM = "addendum"


# =============================================================================
# Core DICOM Models
# =============================================================================


class DicomPatient(BaseModel):
    """Patient demographics from DICOM header."""

    patient_id: str = Field(..., description="Patient ID (DICOM 0010,0020)")
    patient_name: str = Field(..., description="Patient name (DICOM 0010,0010)")
    birth_date: Optional[date] = Field(None, description="Birth date (DICOM 0010,0030)")
    sex: Optional[str] = Field(None, description="Patient sex M/F/O (DICOM 0010,0040)")


class DicomInstance(BaseModel):
    """Single DICOM instance (image or document)."""

    sop_instance_uid: str = Field(..., description="Instance UID (DICOM 0008,0018)")
    sop_class_uid: str = Field(..., description="SOP Class UID (DICOM 0008,0016)")
    instance_number: Optional[int] = Field(None, description="Instance number (DICOM 0020,0013)")
    transfer_syntax: Optional[str] = Field(None, description="Transfer syntax UID")
    rows: Optional[int] = Field(None, description="Image rows (DICOM 0028,0010)")
    columns: Optional[int] = Field(None, description="Image columns (DICOM 0028,0011)")
    frames: Optional[int] = Field(None, description="Number of frames (DICOM 0028,0008)")


class DicomSeries(BaseModel):
    """DICOM series containing multiple instances."""

    series_instance_uid: str = Field(..., description="Series UID (DICOM 0020,000E)")
    series_number: Optional[int] = Field(None, description="Series number (DICOM 0020,0011)")
    series_description: Optional[str] = Field(None, description="Series description (DICOM 0008,103E)")
    modality: Modality = Field(..., description="Modality (DICOM 0008,0060)")
    body_part: Optional[str] = Field(None, description="Body part examined (DICOM 0018,0015)")
    instance_count: int = Field(0, description="Number of instances")
    instances: list[DicomInstance] = Field(default_factory=list)


class DicomStudy(BaseModel):
    """DICOM study representing a single imaging exam."""

    study_instance_uid: str = Field(..., description="Study UID (DICOM 0020,000D)")
    study_id: Optional[str] = Field(None, description="Study ID (DICOM 0020,0010)")
    accession_number: Optional[str] = Field(None, description="Accession number (DICOM 0008,0050)")
    study_date: Optional[date] = Field(None, description="Study date (DICOM 0008,0020)")
    study_time: Optional[str] = Field(None, description="Study time (DICOM 0008,0030)")
    study_description: Optional[str] = Field(None, description="Study description (DICOM 0008,1030)")
    referring_physician: Optional[str] = Field(None, description="Referring physician (DICOM 0008,0090)")
    institution_name: Optional[str] = Field(None, description="Institution (DICOM 0008,0080)")

    # Patient info from DICOM header
    patient: Optional[DicomPatient] = None

    # Modalities in study (may have multiple)
    modalities: list[Modality] = Field(default_factory=list)

    # Series within study
    series_count: int = Field(0, description="Number of series")
    series: list[DicomSeries] = Field(default_factory=list)

    # OpenHeart tracking
    status: StudyStatus = Field(StudyStatus.NEW)
    linked_patient_id: Optional[int] = Field(None, description="OpenHeart patient ID")
    linked_encounter_id: Optional[int] = Field(None, description="OpenHeart encounter ID")


class DicomStudyList(BaseModel):
    """Paginated list of DICOM studies."""

    studies: list[DicomStudy]
    total: int
    page: int
    per_page: int


# =============================================================================
# Echocardiography Measurements (DICOM SR)
# =============================================================================


class LVMeasurements(BaseModel):
    """Left Ventricle measurements from Echo."""

    lvef: Optional[float] = Field(None, ge=0, le=100, description="LV Ejection Fraction (%)")
    lvef_method: Optional[str] = Field(None, description="Method: Simpson, Teichholz, etc.")
    lvidd: Optional[float] = Field(None, ge=0, description="LV Internal Diameter Diastole (mm)")
    lvids: Optional[float] = Field(None, ge=0, description="LV Internal Diameter Systole (mm)")
    lv_mass: Optional[float] = Field(None, ge=0, description="LV Mass (g)")
    lv_mass_index: Optional[float] = Field(None, ge=0, description="LV Mass Index (g/m2)")
    ivs_d: Optional[float] = Field(None, ge=0, description="IVS Diastole thickness (mm)")
    lvpw_d: Optional[float] = Field(None, ge=0, description="LV Post Wall Diastole thickness (mm)")
    lv_edv: Optional[float] = Field(None, ge=0, description="LV End Diastolic Volume (ml)")
    lv_esv: Optional[float] = Field(None, ge=0, description="LV End Systolic Volume (ml)")
    global_ls: Optional[float] = Field(None, description="Global Longitudinal Strain (%)")


class RVMeasurements(BaseModel):
    """Right Ventricle measurements from Echo."""

    tapse: Optional[float] = Field(None, ge=0, description="TAPSE (mm)")
    rv_fac: Optional[float] = Field(None, ge=0, le=100, description="RV Fractional Area Change (%)")
    rv_basal_diameter: Optional[float] = Field(None, ge=0, description="RV Basal Diameter (mm)")
    rv_mid_diameter: Optional[float] = Field(None, ge=0, description="RV Mid Diameter (mm)")
    rv_s_prime: Optional[float] = Field(None, ge=0, description="RV S' TDI (cm/s)")


class LAMeasurements(BaseModel):
    """Left Atrium measurements."""

    la_diameter: Optional[float] = Field(None, ge=0, description="LA Diameter (mm)")
    la_area: Optional[float] = Field(None, ge=0, description="LA Area (cm2)")
    la_volume: Optional[float] = Field(None, ge=0, description="LA Volume (ml)")
    la_volume_index: Optional[float] = Field(None, ge=0, description="LA Volume Index (ml/m2)")


class DiastolicFunction(BaseModel):
    """Diastolic function parameters."""

    e_velocity: Optional[float] = Field(None, ge=0, description="Mitral E velocity (cm/s)")
    a_velocity: Optional[float] = Field(None, ge=0, description="Mitral A velocity (cm/s)")
    e_a_ratio: Optional[float] = Field(None, ge=0, description="E/A ratio")
    e_prime_septal: Optional[float] = Field(None, ge=0, description="e' septal (cm/s)")
    e_prime_lateral: Optional[float] = Field(None, ge=0, description="e' lateral (cm/s)")
    e_e_prime_ratio: Optional[float] = Field(None, ge=0, description="E/e' ratio")
    deceleration_time: Optional[float] = Field(None, ge=0, description="E decel time (ms)")
    tr_velocity: Optional[float] = Field(None, ge=0, description="TR Velocity (m/s)")
    grade: Optional[str] = Field(None, description="Grade: Normal, I, II, III")


class ValveStatus(str, Enum):
    """Valve function status."""

    NORMAL = "normal"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    TRIVIAL = "trivial"


class ValveMeasurements(BaseModel):
    """Valve assessment for a single valve."""

    stenosis: Optional[ValveStatus] = Field(None)
    regurgitation: Optional[ValveStatus] = Field(None)
    peak_gradient: Optional[float] = Field(None, ge=0, description="Peak gradient (mmHg)")
    mean_gradient: Optional[float] = Field(None, ge=0, description="Mean gradient (mmHg)")
    valve_area: Optional[float] = Field(None, ge=0, description="Valve area (cm2)")
    vena_contracta: Optional[float] = Field(None, ge=0, description="Vena contracta (mm)")
    eroa: Optional[float] = Field(None, ge=0, description="Effective ROA (cm2)")
    regurgitant_volume: Optional[float] = Field(None, ge=0, description="Regurgitant volume (ml)")
    notes: Optional[str] = None


class EchoMeasurements(BaseModel):
    """Complete Echocardiogram structured report."""

    study_instance_uid: str
    study_date: Optional[date] = None
    performed_by: Optional[str] = None
    interpreted_by: Optional[str] = None

    # Chamber measurements
    lv: LVMeasurements = Field(default_factory=LVMeasurements)
    rv: RVMeasurements = Field(default_factory=RVMeasurements)
    la: LAMeasurements = Field(default_factory=LAMeasurements)
    ra_area: Optional[float] = Field(None, ge=0, description="RA Area (cm2)")

    # Diastolic function
    diastolic: DiastolicFunction = Field(default_factory=DiastolicFunction)

    # Valve assessments
    aortic_valve: ValveMeasurements = Field(default_factory=ValveMeasurements)
    mitral_valve: ValveMeasurements = Field(default_factory=ValveMeasurements)
    tricuspid_valve: ValveMeasurements = Field(default_factory=ValveMeasurements)
    pulmonic_valve: ValveMeasurements = Field(default_factory=ValveMeasurements)

    # Aorta
    aortic_root: Optional[float] = Field(None, ge=0, description="Aortic root (mm)")
    ascending_aorta: Optional[float] = Field(None, ge=0, description="Ascending aorta (mm)")

    # Pulmonary
    rvsp: Optional[float] = Field(None, ge=0, description="RV Systolic Pressure (mmHg)")
    pa_systolic: Optional[float] = Field(None, ge=0, description="PA Systolic Pressure (mmHg)")

    # Pericardium
    pericardial_effusion: Optional[str] = Field(None, description="None/Trivial/Small/Moderate/Large")

    # Wall motion
    wall_motion_abnormality: bool = Field(False)
    wall_motion_description: Optional[str] = None

    # Overall interpretation
    findings: Optional[str] = Field(None, description="Key findings summary")
    impression: Optional[str] = Field(None, description="Overall impression")


# =============================================================================
# Cath Lab (Angiography/Interventional) Report
# =============================================================================


class StenosisGrade(str, Enum):
    """Coronary stenosis severity."""

    NONE = "none"
    MINIMAL = "minimal"  # <25%
    MILD = "mild"  # 25-49%
    MODERATE = "moderate"  # 50-69%
    SEVERE = "severe"  # 70-99%
    TOTAL = "total"  # 100% (CTO)


class AccessSite(str, Enum):
    """Vascular access site."""

    RADIAL_RIGHT = "right_radial"
    RADIAL_LEFT = "left_radial"
    FEMORAL_RIGHT = "right_femoral"
    FEMORAL_LEFT = "left_femoral"
    BRACHIAL = "brachial"


class LesionCharacteristics(BaseModel):
    """Coronary lesion description."""

    vessel: str = Field(..., description="Vessel name: LAD, LCX, RCA, etc.")
    segment: Optional[str] = Field(None, description="Segment: proximal, mid, distal")
    stenosis_percent: Optional[int] = Field(None, ge=0, le=100)
    stenosis_grade: StenosisGrade = StenosisGrade.NONE
    lesion_length: Optional[float] = Field(None, ge=0, description="Lesion length (mm)")
    calcification: Optional[str] = Field(None, description="None/Mild/Moderate/Severe")
    thrombus: bool = Field(False)
    bifurcation: bool = Field(False)
    ctO: bool = Field(False, description="Chronic Total Occlusion")
    timi_flow: Optional[int] = Field(None, ge=0, le=3, description="TIMI flow grade 0-3")


class StentDeployed(BaseModel):
    """Stent deployment details."""

    vessel: str
    segment: Optional[str] = None
    stent_type: str = Field(..., description="DES brand or BMS")
    stent_length: float = Field(..., ge=0, description="Stent length (mm)")
    stent_diameter: float = Field(..., ge=0, description="Stent diameter (mm)")
    deployment_pressure: Optional[float] = Field(None, ge=0, description="Deployment ATM")
    post_dilation: bool = Field(False)
    post_dilation_pressure: Optional[float] = Field(None, ge=0, description="Post-dilation ATM")


class HemodynamicData(BaseModel):
    """Hemodynamic measurements from cath."""

    lvedp: Optional[float] = Field(None, description="LV End Diastolic Pressure (mmHg)")
    aortic_systolic: Optional[float] = Field(None, description="Aortic systolic (mmHg)")
    aortic_diastolic: Optional[float] = Field(None, description="Aortic diastolic (mmHg)")
    pcwp: Optional[float] = Field(None, description="Pulmonary Capillary Wedge (mmHg)")
    pa_systolic: Optional[float] = Field(None, description="PA systolic (mmHg)")
    pa_diastolic: Optional[float] = Field(None, description="PA diastolic (mmHg)")
    cardiac_output: Optional[float] = Field(None, description="Cardiac output (L/min)")
    cardiac_index: Optional[float] = Field(None, description="Cardiac index (L/min/m2)")


class CathLabReport(BaseModel):
    """Complete Cardiac Catheterization / PCI Report."""

    study_instance_uid: str
    procedure_date: Optional[date] = None
    procedure_type: str = Field(..., description="Diagnostic/PCI/Combined")
    operator: Optional[str] = None
    assistant: Optional[str] = None

    # Access
    access_site: AccessSite
    sheath_size: Optional[int] = Field(None, description="French size")
    closure_device: Optional[str] = None

    # Contrast & Radiation
    contrast_volume: Optional[float] = Field(None, ge=0, description="Contrast (ml)")
    contrast_type: Optional[str] = None
    fluoroscopy_time: Optional[float] = Field(None, ge=0, description="Fluoro time (min)")
    dose_area_product: Optional[float] = Field(None, ge=0, description="DAP (Gy.cm2)")
    air_kerma: Optional[float] = Field(None, ge=0, description="Air Kerma (mGy)")

    # Coronary anatomy
    dominance: Optional[str] = Field(None, description="Right/Left/Codominant")
    lm: Optional[LesionCharacteristics] = Field(None, description="Left Main")
    lad: list[LesionCharacteristics] = Field(default_factory=list)
    lcx: list[LesionCharacteristics] = Field(default_factory=list)
    rca: list[LesionCharacteristics] = Field(default_factory=list)
    other_vessels: list[LesionCharacteristics] = Field(default_factory=list)

    # Graft assessment (CABG patients)
    grafts: list[LesionCharacteristics] = Field(default_factory=list)

    # Intervention
    intervention_performed: bool = Field(False)
    target_vessels: list[str] = Field(default_factory=list)
    stents: list[StentDeployed] = Field(default_factory=list)
    drug_eluting_balloon: bool = Field(False)
    atherectomy: bool = Field(False)
    ivus_used: bool = Field(False)
    oct_used: bool = Field(False)
    ffr_ifr_values: Optional[str] = Field(None, description="FFR/iFR values if measured")

    # Hemodynamics
    hemodynamics: HemodynamicData = Field(default_factory=HemodynamicData)

    # LV assessment
    lv_gram_ef: Optional[float] = Field(None, ge=0, le=100, description="LV gram EF (%)")
    wall_motion: Optional[str] = None

    # Complications
    complications: list[str] = Field(default_factory=list)

    # Conclusions
    syntax_score: Optional[float] = Field(None, ge=0, description="SYNTAX Score")
    findings: Optional[str] = None
    impression: Optional[str] = None
    recommendations: Optional[str] = None


# =============================================================================
# Request/Response Models
# =============================================================================


class StudySearchRequest(BaseModel):
    """Search parameters for DICOM studies."""

    patient_id: Optional[str] = Field(None, description="DICOM Patient ID")
    patient_name: Optional[str] = Field(None, description="Patient name (wildcard *)")
    accession_number: Optional[str] = None
    study_date_from: Optional[date] = None
    study_date_to: Optional[date] = None
    modality: Optional[Modality] = None
    study_description: Optional[str] = None
    linked_patient_id: Optional[int] = Field(None, description="OpenHeart patient ID")
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)


class StudyLinkRequest(BaseModel):
    """Link DICOM study to OpenHeart patient."""

    study_instance_uid: str
    patient_id: int = Field(..., description="OpenHeart patient ID")
    encounter_id: Optional[int] = Field(None, description="OpenHeart encounter ID")


class ViewerUrlResponse(BaseModel):
    """Response with OHIF Viewer URL."""

    viewer_url: str
    study_instance_uid: str
    expires_at: Optional[datetime] = None
