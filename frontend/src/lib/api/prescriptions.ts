/**
 * Prescription API client for OpenHeart Cyprus.
 */

import { apiFetch, buildQueryString } from './client';

// ============================================================================
// Types
// ============================================================================

export type PrescriptionStatus =
  | 'active'
  | 'completed'
  | 'discontinued'
  | 'cancelled'
  | 'on_hold'
  | 'expired';

export type Frequency = 'OD' | 'BD' | 'TDS' | 'QDS' | 'PRN' | 'STAT' | 'nocte' | 'mane' | 'custom';

export type Route = 'oral' | 'sublingual' | 'IV' | 'IM' | 'SC' | 'topical' | 'inhaled' | 'transdermal' | 'rectal' | 'nasal';

export type InteractionSeverity = 'minor' | 'moderate' | 'major' | 'contraindicated';

export interface InteractionResponse {
  id: string;
  interacting_drug_name: string;
  interacting_atc_code?: string;
  severity: InteractionSeverity;
  interaction_type?: string;
  description: string;
  management_recommendation?: string;
  acknowledged_at?: string;
  override_reason?: string;
}

export interface Prescription {
  id: string;
  patient_id: number;
  encounter_id?: number;
  prescriber_id: number;
  clinic_id: number;

  // Drug info
  gesy_medication_id?: number;
  drug_name: string;
  atc_code?: string;
  generic_name?: string;

  // Details
  form?: string;
  strength?: string;
  dosage?: string;
  quantity?: number;
  frequency: string;
  frequency_custom?: string;
  frequency_display?: string;
  route: string;

  // Duration
  duration_days?: number;
  start_date: string;
  end_date?: string;

  // Refills
  refills_allowed: number;
  refills_used: number;

  // Status
  status: PrescriptionStatus;
  is_chronic: boolean;

  // Clinical
  linked_diagnosis_icd10?: string;
  linked_diagnosis_description?: string;
  indication?: string;

  // Discontinuation
  discontinued_at?: string;
  discontinuation_reason?: string;

  // Chain
  original_prescription_id?: string;
  renewal_count: number;

  // Gesy
  requires_prior_auth: boolean;
  prior_auth_status?: string;

  // Notes
  prescriber_notes?: string;

  // Timestamps
  created_at: string;
  updated_at: string;

  // Computed
  can_renew: boolean;
  days_remaining?: number;
  prescriber_name?: string;

  // Related
  interactions: InteractionResponse[];
}

export interface PrescriptionListResponse {
  items: Prescription[];
  total: number;
}

export interface PrescriptionCreateInput {
  patient_id: number;
  encounter_id?: number;
  gesy_medication_id?: number;
  drug_name: string;
  atc_code?: string;
  generic_name?: string;
  form?: string;
  strength?: string;
  dosage?: string;
  quantity?: number;
  frequency?: string;
  frequency_custom?: string;
  route?: string;
  duration_days?: number;
  start_date?: string;
  refills_allowed?: number;
  is_chronic?: boolean;
  linked_diagnosis_icd10?: string;
  linked_diagnosis_description?: string;
  indication?: string;
  prescriber_notes?: string;
  acknowledge_interactions?: string[];
}

export interface PrescriptionUpdateInput {
  dosage?: string;
  strength?: string;
  frequency?: string;
  frequency_custom?: string;
  quantity?: number;
  prescriber_notes?: string;
  indication?: string;
}

export interface InteractionCheckInput {
  patient_id: number;
  drug_name: string;
  atc_code?: string;
  exclude_prescription_id?: string;
}

export interface InteractionDetail {
  interacting_drug: string;
  interacting_atc?: string;
  interacting_prescription_id?: string;
  severity: InteractionSeverity;
  interaction_type: string;
  description: string;
  management?: string;
}

export interface InteractionCheckResponse {
  has_interactions: boolean;
  interactions: InteractionDetail[];
  can_proceed: boolean;
}

export interface MedicationHistoryEntry {
  id: string;
  previous_status?: string;
  new_status: string;
  changed_by: number;
  changed_at: string;
  reason?: string;
  change_type: string;
  details?: Record<string, unknown>;
}

export interface DrugTemplate {
  generic_name: string;
  atc_code: string;
  category: string;
  default_strength: string;
  default_form: string;
  default_frequency: string;
  default_route: string;
  is_chronic: boolean;
  available_strengths: string[];
  common_indications: string[];
  loading_dose?: string;
  renal_adjustment?: Record<string, unknown>;
}

export interface FormularyResponse {
  categories: Record<string, DrugTemplate[]>;
  total_drugs: number;
}

// ============================================================================
// API Functions
// ============================================================================

// --- Patient Prescriptions ---

export async function createPrescription(
  token: string,
  patientId: number,
  data: PrescriptionCreateInput
): Promise<Prescription> {
  return apiFetch<Prescription>(`/api/prescriptions/patients/${patientId}`, {
    method: 'POST',
    body: JSON.stringify(data),
  }, token);
}

export async function listPrescriptions(
  token: string,
  patientId: number,
  options: { status?: string; include_inactive?: boolean } = {}
): Promise<PrescriptionListResponse> {
  const queryString = buildQueryString({
    status: options.status,
    include_inactive: options.include_inactive,
  });
  return apiFetch<PrescriptionListResponse>(
    `/api/prescriptions/patients/${patientId}${queryString}`,
    { method: 'GET' },
    token
  );
}

export async function getActiveMedications(
  token: string,
  patientId: number
): Promise<Prescription[]> {
  return apiFetch<Prescription[]>(
    `/api/prescriptions/patients/${patientId}/active`,
    { method: 'GET' },
    token
  );
}

export async function getChronicMedications(
  token: string,
  patientId: number
): Promise<Prescription[]> {
  return apiFetch<Prescription[]>(
    `/api/prescriptions/patients/${patientId}/chronic`,
    { method: 'GET' },
    token
  );
}

// --- Individual Prescription ---

export async function getPrescription(
  token: string,
  prescriptionId: string
): Promise<Prescription> {
  return apiFetch<Prescription>(
    `/api/prescriptions/${prescriptionId}`,
    { method: 'GET' },
    token
  );
}

export async function updatePrescription(
  token: string,
  prescriptionId: string,
  data: PrescriptionUpdateInput
): Promise<Prescription> {
  return apiFetch<Prescription>(
    `/api/prescriptions/${prescriptionId}`,
    { method: 'PUT', body: JSON.stringify(data) },
    token
  );
}

// --- Lifecycle Actions ---

export async function discontinuePrescription(
  token: string,
  prescriptionId: string,
  reason: string,
  effectiveDate?: string
): Promise<Prescription> {
  return apiFetch<Prescription>(
    `/api/prescriptions/${prescriptionId}/discontinue`,
    {
      method: 'POST',
      body: JSON.stringify({ reason, effective_date: effectiveDate }),
    },
    token
  );
}

export async function renewPrescription(
  token: string,
  prescriptionId: string,
  data?: { duration_days?: number; quantity?: number; notes?: string }
): Promise<Prescription> {
  return apiFetch<Prescription>(
    `/api/prescriptions/${prescriptionId}/renew`,
    { method: 'POST', body: JSON.stringify(data || {}) },
    token
  );
}

export async function holdPrescription(
  token: string,
  prescriptionId: string,
  reason: string
): Promise<Prescription> {
  return apiFetch<Prescription>(
    `/api/prescriptions/${prescriptionId}/hold`,
    { method: 'POST', body: JSON.stringify({ reason }) },
    token
  );
}

export async function resumePrescription(
  token: string,
  prescriptionId: string
): Promise<Prescription> {
  return apiFetch<Prescription>(
    `/api/prescriptions/${prescriptionId}/resume`,
    { method: 'POST', body: JSON.stringify({}) },
    token
  );
}

// --- Interactions ---

export async function checkInteractions(
  token: string,
  data: InteractionCheckInput
): Promise<InteractionCheckResponse> {
  return apiFetch<InteractionCheckResponse>(
    '/api/prescriptions/interactions/check',
    { method: 'POST', body: JSON.stringify(data) },
    token
  );
}

// --- History ---

export async function getPrescriptionHistory(
  token: string,
  prescriptionId: string
): Promise<MedicationHistoryEntry[]> {
  return apiFetch<MedicationHistoryEntry[]>(
    `/api/prescriptions/${prescriptionId}/history`,
    { method: 'GET' },
    token
  );
}

// --- Formulary ---

export async function getCardiologyFormulary(
  token: string
): Promise<FormularyResponse> {
  return apiFetch<FormularyResponse>(
    '/api/prescriptions/formulary/cardiology',
    { method: 'GET' },
    token
  );
}

export async function searchFormulary(
  token: string,
  query: string
): Promise<DrugTemplate[]> {
  const queryString = buildQueryString({ q: query });
  return apiFetch<DrugTemplate[]>(
    `/api/prescriptions/formulary/search${queryString}`,
    { method: 'GET' },
    token
  );
}

export async function getFormularyCategories(
  token: string
): Promise<string[]> {
  return apiFetch<string[]>(
    '/api/prescriptions/formulary/categories',
    { method: 'GET' },
    token
  );
}

export async function getDrugDefaults(
  token: string,
  atcCode: string
): Promise<DrugTemplate> {
  return apiFetch<DrugTemplate>(
    `/api/prescriptions/formulary/${atcCode}/defaults`,
    { method: 'GET' },
    token
  );
}

// ============================================================================
// Helper Functions
// ============================================================================

export const FREQUENCY_LABELS: Record<string, string> = {
  OD: 'Once daily',
  BD: 'Twice daily',
  TDS: 'Three times daily',
  QDS: 'Four times daily',
  PRN: 'As needed',
  STAT: 'Immediately',
  nocte: 'At night',
  mane: 'In the morning',
  custom: 'Custom',
};

export const ROUTE_LABELS: Record<string, string> = {
  oral: 'Oral',
  sublingual: 'Sublingual',
  IV: 'Intravenous',
  IM: 'Intramuscular',
  SC: 'Subcutaneous',
  topical: 'Topical',
  inhaled: 'Inhaled',
  transdermal: 'Transdermal',
  rectal: 'Rectal',
  nasal: 'Nasal',
};

export function getStatusColor(status: PrescriptionStatus): string {
  const colors: Record<PrescriptionStatus, string> = {
    active: 'bg-green-500/20 text-green-300 border-green-500/30',
    completed: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    discontinued: 'bg-red-500/20 text-red-300 border-red-500/30',
    cancelled: 'bg-gray-500/20 text-gray-300 border-gray-500/30',
    on_hold: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
    expired: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  };
  return colors[status] || colors.active;
}

export function getSeverityColor(severity: InteractionSeverity): string {
  const colors: Record<InteractionSeverity, string> = {
    minor: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    moderate: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
    major: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
    contraindicated: 'bg-red-500/20 text-red-300 border-red-500/30',
  };
  return colors[severity] || colors.minor;
}

export function getCategoryLabel(category: string): string {
  const labels: Record<string, string> = {
    antiplatelets: 'Antiplatelets',
    anticoagulants: 'Anticoagulants',
    statins: 'Statins',
    beta_blockers: 'Beta-Blockers',
    ace_inhibitors: 'ACE Inhibitors',
    arbs: 'ARBs',
    ccbs: 'Calcium Channel Blockers',
    diuretics: 'Diuretics',
    antiarrhythmics: 'Antiarrhythmics',
    nitrates: 'Nitrates',
    heart_failure: 'Heart Failure',
    other_cardiovascular: 'Other CV',
  };
  return labels[category] || category;
}

export function formatPrescriptionLine(rx: Prescription): string {
  const parts = [rx.drug_name];
  if (rx.strength) parts.push(rx.strength);
  if (rx.frequency_display) parts.push(rx.frequency_display);
  else if (rx.frequency) parts.push(FREQUENCY_LABELS[rx.frequency] || rx.frequency);
  if (rx.route && rx.route !== 'oral') parts.push(ROUTE_LABELS[rx.route] || rx.route);
  return parts.join(' ');
}
