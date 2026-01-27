---
title: Clinical Decision Support System (CDSS) Algorithms
version: 1.0
status: planning
created: 2026-01-21
description: Validated cardiology risk scoring algorithms for OpenHeart Cyprus EMR.
---

# Clinical Decision Support System (CDSS) Algorithms

## 1. Overview

OpenHeart Cyprus implements evidence-based risk calculators aligned with ESC (European Society of Cardiology) guidelines. All algorithms must be validated against published nomograms before production use.

## 2. GRACE Score (Acute Coronary Syndrome)

### GRACE Purpose

Estimates in-hospital mortality risk for patients with ACS (STEMI/NSTEMI/Unstable Angina).

### GRACE Algorithm (Maximum Score: 372)

#### Age Points

| Age (years) | Points |
|-------------|--------|
| <30         | 0      |
| 30-39       | 8      |
| 40-49       | 25     |
| 50-59       | 41     |
| 60-69       | 58     |
| 70-79       | 75     |
| 80-89       | 91     |
| ≥90         | 100    |

#### Heart Rate Points

| HR (bpm)  | Points |
|-----------|--------|
| <50       | 0      |
| 50-69     | 3      |
| 70-89     | 9      |
| 90-109    | 15     |
| 110-149   | 24     |
| 150-199   | 38     |
| ≥200      | 46     |

#### Systolic Blood Pressure Points

| SBP (mmHg) | Points |
|------------|--------|
| <80        | 58     |
| 80-99      | 53     |
| 100-119    | 43     |
| 120-139    | 34     |
| 140-159    | 24     |
| 160-199    | 10     |
| ≥200       | 0      |

#### Serum Creatinine Points

| Creatinine (mg/dL) | Points |
|--------------------|--------|
| 0-0.39             | 1      |
| 0.4-0.79           | 4      |
| 0.8-1.19           | 7      |
| 1.2-1.59           | 10     |
| 1.6-1.99           | 13     |
| 2.0-3.99           | 21     |
| ≥4.0               | 28     |

#### Killip Class Points

| Killip Class | Description                              | Points |
|--------------|------------------------------------------|--------|
| I            | No heart failure                         | 0      |
| II           | Rales, S3 gallop, venous hypertension   | 20     |
| III          | Frank pulmonary edema                    | 39     |
| IV           | Cardiogenic shock                        | 59     |

#### Binary Risk Factors

| Factor                        | Points if Present |
|-------------------------------|-------------------|
| Cardiac arrest at admission   | 39                |
| ST-segment deviation          | 28                |
| Elevated cardiac enzymes      | 14                |

### Risk Stratification

| Score Range | Risk Category  | In-Hospital Mortality | Recommendation |
|-------------|----------------|----------------------|----------------|
| ≤108        | Low            | <1%                  | Conservative strategy, discharge if stress test negative |
| 109-140     | Intermediate   | 1-3%                 | Early invasive strategy (<72h) |
| >140        | High           | >3%                  | Urgent invasive strategy (<24h), ICU monitoring |

---

## 3. CHA₂DS₂-VASc Score (Stroke Risk in Atrial Fibrillation)

### CHA₂DS₂-VASc Purpose

Estimates annual stroke risk in patients with non-valvular atrial fibrillation to guide anticoagulation decisions.

### CHA₂DS₂-VASc Algorithm (Maximum Score: 9)

| Criterion                                | Points |
|------------------------------------------|--------|
| **C** - Congestive heart failure / LV dysfunction | 1 |
| **H** - Hypertension                     | 1      |
| **A₂** - Age ≥75 years                   | **2**  |
| **D** - Diabetes mellitus                | 1      |
| **S₂** - Stroke / TIA / Thromboembolism  | **2**  |
| **V** - Vascular disease (MI, PAD, aortic plaque) | 1 |
| **A** - Age 65-74 years                  | 1      |
| **Sc** - Sex category (female)           | 1      |

### CHA₂DS₂-VASc Risk Stratification & Treatment

| Score (Male) | Score (Female) | Annual Stroke Risk | Recommendation |
|--------------|----------------|-------------------|----------------|
| 0            | 1              | ~0%               | No anticoagulation |
| 1            | 2              | ~1.3%             | Consider OAC (patient preference) |
| ≥2           | ≥3             | ≥2.2%             | OAC recommended (DOAC preferred over warfarin) |

**Note**: Female sex alone does not warrant anticoagulation; it's a risk modifier.

---

## 4. HAS-BLED Score (Bleeding Risk on Anticoagulation)

### HAS-BLED Purpose

Assesses major bleeding risk in AF patients on anticoagulation. Does NOT contraindicate anticoagulation but identifies modifiable risk factors.

### HAS-BLED Algorithm (Maximum Score: 9)

| Letter | Criterion                              | Points |
|--------|----------------------------------------|--------|
| **H**  | Hypertension (uncontrolled, SBP >160)  | 1      |
| **A**  | Abnormal renal/liver function (1 each) | 1-2    |
| **S**  | Stroke history                         | 1      |
| **B**  | Bleeding history or predisposition     | 1      |
| **L**  | Labile INR (if on warfarin, TTR <60%)  | 1      |
| **E**  | Elderly (age >65)                      | 1      |
| **D**  | Drugs (aspirin, NSAIDs) or alcohol     | 1-2    |

### Abnormal Function Definitions

- **Renal**: Dialysis, transplant, Cr >2.3 mg/dL
- **Liver**: Cirrhosis, bilirubin >2x normal, AST/ALT/ALP >3x normal

### Risk Stratification

| Score | Risk Level | Major Bleeding Rate |
|-------|------------|---------------------|
| 0-1   | Low        | ~1%/year            |
| 2     | Moderate   | ~1.9%/year          |
| ≥3    | High       | ≥3.7%/year          |

### Clinical Action

High HAS-BLED score should prompt:

- More frequent INR monitoring (if on warfarin)
- Consider DOAC over warfarin
- Address modifiable factors (BP control, discontinue NSAIDs)
- **NOT** a reason to withhold anticoagulation

---

## 5. ASCVD Risk Calculator (10-Year Cardiovascular Risk)

### ASCVD Purpose

Estimates 10-year risk of atherosclerotic cardiovascular disease (heart attack, stroke) for primary prevention decisions.

### ASCVD Required Inputs

- Age (40-79 years)
- Sex
- Race/Ethnicity
- Total cholesterol (mg/dL)
- HDL cholesterol (mg/dL)
- Systolic blood pressure (mmHg)
- Blood pressure treatment status
- Diabetes status
- Smoking status

### ASCVD Algorithm

Uses Pooled Cohort Equations (PCE). **Note**: Moving towards PREVENT equations (see below) is recommended for better equity and accuracy.

```python
# Simplified structure - full coefficients in implementation
def calculate_ascvd_risk(
    age: int,
    sex: str,  # "male" or "female"
    race: str,  # "white", "african_american", "other"
    total_cholesterol: float,
    hdl_cholesterol: float,
    systolic_bp: float,
    bp_treatment: bool,
    diabetes: bool,
    smoker: bool
) -> float:
    """Returns 10-year ASCVD risk as percentage."""

    # Select coefficient set based on sex and race
    coefficients = get_coefficients(sex, race)

    # Calculate individual terms
    ln_age = math.log(age)
    ln_tc = math.log(total_cholesterol)
    ln_hdl = math.log(hdl_cholesterol)
    ln_sbp = math.log(systolic_bp)

    # ... apply coefficients and sum
    # ... calculate baseline survival
    # ... return 1 - S0^exp(sum)

    return risk_percentage
```

### Risk Thresholds (ACC/AHA Guidelines)

| 10-Year Risk | Category          | Statin Consideration |
|--------------|-------------------|---------------------|
| <5%          | Low               | Lifestyle only      |
| 5-7.5%       | Borderline        | Risk discussion     |
| ≥20%         | High              | High-intensity statin |

---

## 6. PREVENT Equations (AHA 2023 - Modern Standard)

### PREVENT Purpose

The Predict Risk of Cardiovascular Disease Events (PREVENT) equations provide 10-year and 30-year risk for ASCVD and Heart Failure.

### Key Advantages over ASCVD PCE

- **Race-Agnostic**: Does not use race as a biological predictor, addressing health inequities.
- **Heart Failure Prediction**: Includes HF as a distinct outcome (critical for cardiology).
- **Kidney Health**: Integrates eGFR and UACR (Urine Albumin-to-Creatinine Ratio).
- **Expanded Age Range**: Validated from age 30 to 79.

### Required Inputs

- Age (30-79)
- Sex
- Systolic BP
- BP Treatment status
- Total & HDL Cholesterol
- Diabetes status
- Smoking status
- **eGFR** (Kidney function)

### Optional Inputs (Full Model)

- HbA1c
- UACR
- Social Deprivation Index (SDI)

### Implementation Note

The PREVENT equations involve complex sex-specific coefficients and multiple outcome models. It is the recommended primary risk engine for OpenHeart Cyprus.

---

## 7. EuroSCORE II (Surgical Risk)

### EuroSCORE II Purpose

Predicts in-hospital mortality after cardiac surgery. Essential for Heart Team decisions (PCI vs CABG, TAVI vs SAVR).

### Key Parameters

- **Patient Factors**: Age, Sex, Renal impairment, Extracardiac arteriopathy, Poor mobility, Previous cardiac surgery, Chronic lung disease, Active endocarditis, Critical preoperative state.
- **Cardiac Factors**: NYHA class, CCS class 4 angina, LV function (LVEF), Recent MI, Pulmonary hypertension.
- **Operation Factors**: Urgency, Weight of the procedure, Surgery on thoracic aorta.

### Risk Category

- High risk typically defined as EuroSCORE II > 4-6% depending on the procedure.

---

## 8. Implementation Guidelines

### Validation Requirements

1. Unit test all score calculations against published examples
2. Edge case testing (boundary values for each parameter)
3. Clinical validation by cardiologist before deployment

### User Interface Requirements

1. Display score with risk category
2. Show breakdown of contributing factors
3. Provide guideline-based recommendations
4. Include disclaimer: "For clinical decision support only"

### Audit Trail

All CDSS calculations must be logged:

```python
@dataclass
class CDSSAuditEntry:
    calculation_type: str  # "GRACE", "CHA2DS2-VASc", etc.
    patient_id: int
    input_parameters: dict
    calculated_score: int
    risk_category: str
    recommendation: str
    clinician_id: int
    timestamp: datetime
    acknowledged: bool  # Clinician reviewed result
    override_reason: str  # If clinician disagrees with algorithm
```

### Context-Aware Alerts (UX)

To prevent alert fatigue:

1. **Passive Indicators**: Show risks in a "Clinical Banner" rather than pop-up modals.
2. **Trend Mapping**: Visualize risk scores over time (e.g., ASCVD risk 2 years ago vs now).
3. **Actionable Alerts**: Only show high-priority alerts (e.g., GRACE > 140) with immediate "Order Consultation" buttons.

---

## 9. Future Algorithms to Implement

| Algorithm | Purpose | Priority |
|-----------|---------|----------|
| SYNTAX Score | PCI vs CABG decision | Medium |
| TIMI Score | ACS risk (alternative to GRACE) | Medium |
| HEART Score | Chest pain evaluation in ED | Medium |
| Framingham Risk Score | CVD risk (International ref) | Low |
