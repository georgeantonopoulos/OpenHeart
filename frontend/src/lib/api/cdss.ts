/**
 * CDSS API Client.
 *
 * Clinical Decision Support System calculators.
 */

import { apiFetch } from './client';

// ============================================================================
// Types
// ============================================================================

export type KillipClass = 'I' | 'II' | 'III' | 'IV';
export type Sex = 'male' | 'female';
export type RiskCategory = 'Low' | 'Intermediate' | 'High';
export type RiskLevel = 'Low' | 'Moderate' | 'High';
export type PREVENTRiskCategory = 'Low' | 'Borderline' | 'Intermediate' | 'High';
export type EuroSCORERiskCategory = 'Low' | 'Intermediate' | 'High' | 'Very High';
export type LVFunction = 'good' | 'moderate' | 'poor' | 'very_poor';
export type PulmonaryHypertension = 'no' | 'moderate' | 'severe';
export type OperationUrgency = 'elective' | 'urgent' | 'emergency' | 'salvage';
export type OperationWeight = 'isolated_cabg' | 'single_non_cabg' | 'two_procedures' | 'three_or_more';

// GRACE Score
export interface GRACEInput {
  age: number;
  heart_rate: number;
  systolic_bp: number;
  creatinine_mg_dl: number;
  killip_class: KillipClass;
  cardiac_arrest_at_admission: boolean;
  st_segment_deviation: boolean;
  elevated_cardiac_enzymes: boolean;
}

export interface GRACEResult {
  total_score: number;
  risk_category: RiskCategory;
  in_hospital_mortality_estimate: string;
  recommendation: string;
  score_breakdown: Record<string, number>;
  calculation_timestamp: string;
}

// CHA2DS2-VASc Score
export interface CHA2DS2VAScInput {
  age: number;
  sex: Sex;
  congestive_heart_failure: boolean;
  hypertension: boolean;
  diabetes: boolean;
  stroke_tia_thromboembolism: boolean;
  vascular_disease: boolean;
}

export interface CHA2DS2VAScResult {
  total_score: number;
  adjusted_score: number;
  annual_stroke_risk: string;
  recommendation: string;
  score_breakdown: Record<string, number>;
  calculation_timestamp: string;
}

// HAS-BLED Score
export interface HASBLEDInput {
  hypertension_uncontrolled: boolean;
  abnormal_renal_function: boolean;
  abnormal_liver_function: boolean;
  stroke_history: boolean;
  bleeding_history: boolean;
  labile_inr: boolean;
  elderly: boolean;
  antiplatelet_or_nsaid: boolean;
  alcohol_abuse: boolean;
}

export interface HASBLEDResult {
  total_score: number;
  risk_level: RiskLevel;
  annual_bleeding_rate: string;
  recommendation: string;
  modifiable_factors: string[];
  score_breakdown: Record<string, number>;
  calculation_timestamp: string;
}

// PREVENT Equations (AHA 2023)
export interface PREVENTInput {
  age: number;
  sex: Sex;
  systolic_bp: number;
  total_cholesterol: number;
  hdl_cholesterol: number;
  egfr: number;
  diabetes: boolean;
  current_smoker: boolean;
  on_bp_treatment: boolean;
  on_statin: boolean;
  hba1c?: number;
  uacr?: number;
}

export interface PREVENTResult {
  ten_year_ascvd_risk: number;
  ten_year_hf_risk: number;
  ten_year_total_cvd_risk: number;
  risk_category: PREVENTRiskCategory;
  statin_benefit_group: boolean;
  recommendation: string;
  risk_enhancers: string[];
  calculation_timestamp: string;
}

// EuroSCORE II
export interface EuroSCOREIIInput {
  // Patient factors
  age: number;
  sex: Sex;
  creatinine_clearance: number;
  on_dialysis: boolean;
  extracardiac_arteriopathy: boolean;
  poor_mobility: boolean;
  previous_cardiac_surgery: boolean;
  chronic_lung_disease: boolean;
  active_endocarditis: boolean;
  critical_preoperative_state: boolean;
  diabetes_on_insulin: boolean;
  // Cardiac factors
  nyha_class: 1 | 2 | 3 | 4;
  ccs_class_4_angina: boolean;
  lv_function: LVFunction;
  recent_mi: boolean;
  pulmonary_hypertension: PulmonaryHypertension;
  // Operation factors
  urgency: OperationUrgency;
  operation_weight: OperationWeight;
  surgery_on_thoracic_aorta: boolean;
}

export interface EuroSCOREIIResult {
  predicted_mortality: number;
  risk_category: EuroSCORERiskCategory;
  suitability_for_surgery: string;
  recommendation: string;
  risk_factors_present: string[];
  calculation_timestamp: string;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Calculate GRACE Score for ACS risk stratification.
 */
export async function calculateGRACE(
  token: string,
  input: GRACEInput,
  patientId?: number
): Promise<GRACEResult> {
  const url = patientId ? `/api/cdss/grace?patient_id=${patientId}` : '/api/cdss/grace';
  return apiFetch<GRACEResult>(url, {
    method: 'POST',
    body: JSON.stringify(input),
  }, token);
}

/**
 * Calculate CHA2DS2-VASc Score for stroke risk in AF.
 */
export async function calculateCHA2DS2VASc(
  token: string,
  input: CHA2DS2VAScInput,
  patientId?: number
): Promise<CHA2DS2VAScResult> {
  const url = patientId ? `/api/cdss/cha2ds2vasc?patient_id=${patientId}` : '/api/cdss/cha2ds2vasc';
  return apiFetch<CHA2DS2VAScResult>(url, {
    method: 'POST',
    body: JSON.stringify(input),
  }, token);
}

/**
 * Calculate HAS-BLED Score for bleeding risk.
 */
export async function calculateHASBLED(
  token: string,
  input: HASBLEDInput,
  patientId?: number
): Promise<HASBLEDResult> {
  const url = patientId ? `/api/cdss/hasbled?patient_id=${patientId}` : '/api/cdss/hasbled';
  return apiFetch<HASBLEDResult>(url, {
    method: 'POST',
    body: JSON.stringify(input),
  }, token);
}

/**
 * Calculate PREVENT Equations for ASCVD and HF risk.
 */
export async function calculatePREVENT(
  token: string,
  input: PREVENTInput,
  patientId?: number
): Promise<PREVENTResult> {
  const url = patientId ? `/api/cdss/prevent?patient_id=${patientId}` : '/api/cdss/prevent';
  return apiFetch<PREVENTResult>(url, {
    method: 'POST',
    body: JSON.stringify(input),
  }, token);
}

/**
 * Calculate EuroSCORE II for cardiac surgery risk.
 */
export async function calculateEuroSCOREII(
  token: string,
  input: EuroSCOREIIInput,
  patientId?: number
): Promise<EuroSCOREIIResult> {
  const url = patientId ? `/api/cdss/euroscore?patient_id=${patientId}` : '/api/cdss/euroscore';
  return apiFetch<EuroSCOREIIResult>(url, {
    method: 'POST',
    body: JSON.stringify(input),
  }, token);
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Get color classes for risk category.
 */
export function getRiskCategoryColor(
  category: RiskCategory | RiskLevel | PREVENTRiskCategory | EuroSCORERiskCategory
): {
  bg: string;
  text: string;
  border: string;
} {
  switch (category) {
    case 'Low':
      return {
        bg: 'bg-green-500/20',
        text: 'text-green-400',
        border: 'border-green-500',
      };
    case 'Borderline':
      return {
        bg: 'bg-blue-500/20',
        text: 'text-blue-400',
        border: 'border-blue-500',
      };
    case 'Moderate':
    case 'Intermediate':
      return {
        bg: 'bg-amber-500/20',
        text: 'text-amber-400',
        border: 'border-amber-500',
      };
    case 'High':
      return {
        bg: 'bg-rose-500/20',
        text: 'text-rose-400',
        border: 'border-rose-500',
      };
    case 'Very High':
      return {
        bg: 'bg-red-900/30',
        text: 'text-red-400',
        border: 'border-red-700',
      };
    default:
      return {
        bg: 'bg-slate-500/20',
        text: 'text-slate-400',
        border: 'border-slate-500',
      };
  }
}

/**
 * Killip class descriptions.
 */
export const KILLIP_DESCRIPTIONS: Record<KillipClass, string> = {
  I: 'No heart failure',
  II: 'Rales, S3 gallop, or venous hypertension',
  III: 'Frank pulmonary edema',
  IV: 'Cardiogenic shock',
};

/**
 * LV Function descriptions for EuroSCORE II.
 */
export const LV_FUNCTION_DESCRIPTIONS: Record<LVFunction, string> = {
  good: 'Good (LVEF >50%)',
  moderate: 'Moderate (LVEF 31-50%)',
  poor: 'Poor (LVEF 21-30%)',
  very_poor: 'Very Poor (LVEF ≤20%)',
};

/**
 * Pulmonary hypertension descriptions.
 */
export const PULMONARY_HTN_DESCRIPTIONS: Record<PulmonaryHypertension, string> = {
  no: 'No (PA systolic <31 mmHg)',
  moderate: 'Moderate (31-55 mmHg)',
  severe: 'Severe (>55 mmHg)',
};

/**
 * Operation urgency descriptions.
 */
export const URGENCY_DESCRIPTIONS: Record<OperationUrgency, string> = {
  elective: 'Elective (routine admission)',
  urgent: 'Urgent (within current admission)',
  emergency: 'Emergency (before next working day)',
  salvage: 'Salvage (CPR, ECMO, or IABP pre-OR)',
};

/**
 * Operation weight descriptions.
 */
export const OPERATION_WEIGHT_DESCRIPTIONS: Record<OperationWeight, string> = {
  isolated_cabg: 'Isolated CABG',
  single_non_cabg: 'Single non-CABG (valve, ASD, etc.)',
  two_procedures: 'Two procedures (CABG + valve)',
  three_or_more: 'Three or more procedures',
};

/**
 * NYHA class descriptions.
 */
export const NYHA_DESCRIPTIONS: Record<1 | 2 | 3 | 4, string> = {
  1: 'Class I - No limitation',
  2: 'Class II - Slight limitation',
  3: 'Class III - Marked limitation',
  4: 'Class IV - Symptoms at rest',
};
