/**
 * Gesy (GHS) API Client.
 *
 * Provides typed functions for Cyprus General Healthcare System integration:
 * - Beneficiary verification
 * - Referral management
 * - Claims submission and tracking
 */

import { apiFetch, buildQueryString } from './client';

// ============================================================================
// Types
// ============================================================================

export type BeneficiaryType = 'citizen' | 'eu_national' | 'third_country' | 'dependent';

export interface BeneficiaryStatus {
  beneficiary_id: string;
  is_active: boolean;
  beneficiary_type: BeneficiaryType;
  registration_date: string;
  expiry_date?: string;
  primary_doctor_id?: string;
  coverage_category: string;
  verified_at: string;
  verification_source: string;
}

export type ReferralStatus = 'pending' | 'approved' | 'rejected' | 'used' | 'expired' | 'cancelled';

export interface GesyReferral {
  referral_id: string;
  beneficiary_id: string;
  referring_doctor_id: string;
  specialist_id?: string;
  specialty_code: string;
  diagnosis_code: string;
  diagnosis_description: string;
  status: ReferralStatus;
  urgency: string;
  issued_date: string;
  valid_from: string;
  valid_until: string;
  used_date?: string;
  used_by_provider_id?: string;
  clinical_notes?: string;
  requested_procedures?: string[];
  approved_procedures?: string[];
}

export interface ReferralCreateInput {
  beneficiary_id: string;
  referring_doctor_id: string;
  specialty_code: string;
  diagnosis_code: string;
  diagnosis_description: string;
  urgency?: string;
  clinical_notes?: string;
  requested_procedures?: string[];
}

export type ClaimStatus =
  | 'draft'
  | 'submitted'
  | 'under_review'
  | 'approved'
  | 'partially_approved'
  | 'rejected'
  | 'paid';

export interface ClaimLineItem {
  line_number: number;
  procedure_code: string;
  procedure_description: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  diagnosis_codes: string[];
  approved?: boolean;
  approved_amount?: number;
  rejection_reason?: string;
}

export interface GesyClaim {
  claim_id: string;
  referral_id: string;
  provider_id: string;
  beneficiary_id: string;
  service_date: string;
  encounter_type: string;
  diagnosis_codes: string[];
  primary_diagnosis_code: string;
  line_items: ClaimLineItem[];
  total_claimed: number;
  total_approved?: number;
  total_paid?: number;
  status: ClaimStatus;
  submitted_at?: string;
  reviewed_at?: string;
  paid_at?: string;
  reviewer_notes?: string;
  rejection_reason?: string;
}

export interface ClaimCreateInput {
  referral_id: string;
  provider_id: string;
  beneficiary_id: string;
  service_date: string;
  encounter_type?: string;
  diagnosis_codes: string[];
  primary_diagnosis_code: string;
  line_items: ClaimLineItem[];
  clinical_notes?: string;
}

export interface GesySpecialty {
  code: string;
  name_en: string;
  name_el: string;
  category: string;
  requires_referral: boolean;
}

// ============================================================================
// Beneficiary API Functions
// ============================================================================

export async function verifyBeneficiary(
  accessToken: string,
  beneficiaryId: string
): Promise<BeneficiaryStatus> {
  return apiFetch<BeneficiaryStatus>(
    `/api/gesy/beneficiary/${beneficiaryId}`,
    { method: 'GET' },
    accessToken
  );
}

export async function lookupBeneficiaryByIdCard(
  accessToken: string,
  cyprusId: string
): Promise<BeneficiaryStatus> {
  return apiFetch<BeneficiaryStatus>(
    `/api/gesy/beneficiary/lookup/${cyprusId}`,
    { method: 'GET' },
    accessToken
  );
}

// ============================================================================
// Referral API Functions
// ============================================================================

export async function createReferral(
  accessToken: string,
  data: ReferralCreateInput
): Promise<GesyReferral> {
  return apiFetch<GesyReferral>(
    '/api/gesy/referrals',
    { method: 'POST', body: JSON.stringify(data) },
    accessToken
  );
}

export async function getReferral(
  accessToken: string,
  referralId: string
): Promise<GesyReferral> {
  return apiFetch<GesyReferral>(
    `/api/gesy/referrals/${referralId}`,
    { method: 'GET' },
    accessToken
  );
}

export async function closeReferral(
  accessToken: string,
  referralId: string,
  summaryNotes?: string
): Promise<GesyReferral> {
  const params: Record<string, string> = {};
  if (summaryNotes) params.summary_notes = summaryNotes;
  const queryString = buildQueryString(params);
  return apiFetch<GesyReferral>(
    `/api/gesy/referrals/${referralId}/close${queryString}`,
    { method: 'PUT' },
    accessToken
  );
}

export async function listReferrals(
  accessToken: string,
  params: {
    beneficiary_id: string;
    status?: ReferralStatus;
    from_date?: string;
    to_date?: string;
  }
): Promise<GesyReferral[]> {
  const queryString = buildQueryString(params as Record<string, string>);
  return apiFetch<GesyReferral[]>(
    `/api/gesy/referrals${queryString}`,
    { method: 'GET' },
    accessToken
  );
}

// ============================================================================
// Claims API Functions
// ============================================================================

export async function submitClaim(
  accessToken: string,
  data: ClaimCreateInput
): Promise<GesyClaim> {
  return apiFetch<GesyClaim>(
    '/api/gesy/claims',
    { method: 'POST', body: JSON.stringify(data) },
    accessToken
  );
}

export async function getClaim(
  accessToken: string,
  claimId: string
): Promise<GesyClaim> {
  return apiFetch<GesyClaim>(
    `/api/gesy/claims/${claimId}`,
    { method: 'GET' },
    accessToken
  );
}

export async function listClaims(
  accessToken: string,
  params: {
    status?: ClaimStatus;
    from_date?: string;
    to_date?: string;
  } = {}
): Promise<GesyClaim[]> {
  const queryString = buildQueryString(params as Record<string, string>);
  return apiFetch<GesyClaim[]>(
    `/api/gesy/claims${queryString}`,
    { method: 'GET' },
    accessToken
  );
}

// ============================================================================
// Reference Data
// ============================================================================

export async function listSpecialties(
  accessToken: string
): Promise<GesySpecialty[]> {
  return apiFetch<GesySpecialty[]>(
    '/api/gesy/specialties',
    { method: 'GET' },
    accessToken
  );
}

export async function validateDiagnosisCode(
  accessToken: string,
  code: string
): Promise<{ code: string; valid: boolean }> {
  return apiFetch<{ code: string; valid: boolean }>(
    `/api/gesy/validate/diagnosis/${code}`,
    { method: 'GET' },
    accessToken
  );
}

export async function validateProcedureCode(
  accessToken: string,
  code: string
): Promise<{ code: string; valid: boolean }> {
  return apiFetch<{ code: string; valid: boolean }>(
    `/api/gesy/validate/procedure/${code}`,
    { method: 'GET' },
    accessToken
  );
}

// ============================================================================
// Utility Functions
// ============================================================================

export function getReferralStatusColor(status: ReferralStatus): string {
  const colors: Record<ReferralStatus, string> = {
    pending: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    approved: 'bg-teal-500/20 text-teal-400 border-teal-500/30',
    rejected: 'bg-red-500/20 text-red-400 border-red-500/30',
    used: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
    expired: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    cancelled: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  };
  return colors[status] || 'bg-slate-500/20 text-slate-400 border-slate-500/30';
}

export function getClaimStatusColor(status: ClaimStatus): string {
  const colors: Record<ClaimStatus, string> = {
    draft: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
    submitted: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    under_review: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    approved: 'bg-teal-500/20 text-teal-400 border-teal-500/30',
    partially_approved: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    rejected: 'bg-red-500/20 text-red-400 border-red-500/30',
    paid: 'bg-green-500/20 text-green-400 border-green-500/30',
  };
  return colors[status] || 'bg-slate-500/20 text-slate-400 border-slate-500/30';
}

export function formatClaimStatus(status: ClaimStatus): string {
  const labels: Record<ClaimStatus, string> = {
    draft: 'Draft',
    submitted: 'Submitted',
    under_review: 'Under Review',
    approved: 'Approved',
    partially_approved: 'Partially Approved',
    rejected: 'Rejected',
    paid: 'Paid',
  };
  return labels[status] || status;
}

export function formatReferralStatus(status: ReferralStatus): string {
  const labels: Record<ReferralStatus, string> = {
    pending: 'Pending',
    approved: 'Approved',
    rejected: 'Rejected',
    used: 'Used',
    expired: 'Expired',
    cancelled: 'Cancelled',
  };
  return labels[status] || status;
}
