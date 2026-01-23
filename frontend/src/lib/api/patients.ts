/**
 * Patient API Client.
 *
 * Provides typed API functions for patient management.
 */

import { apiFetch, buildQueryString } from './client';

// ============================================================================
// Types
// ============================================================================

export interface Address {
  street: string;
  city: string;
  postal_code: string;
  district?: string;
  country: string;
}

export interface EmergencyContact {
  name: string;
  relationship: string;
  phone: string;
}

export interface Patient {
  patient_id: number;
  mrn: string;
  birth_date: string;
  gender: 'male' | 'female' | 'other' | 'unknown';
  status: 'active' | 'inactive' | 'deceased';
  age: number;
  first_name?: string;
  last_name?: string;
  middle_name?: string;
  phone?: string;
  email?: string;
  address?: Address;
  cyprus_id_masked?: string;
  has_arc: boolean;
  gesy_beneficiary_id?: string;
  is_gesy_beneficiary: boolean;
  referring_physician?: string;
  primary_physician_id?: number;
  created_at: string;
  updated_at: string;
}

export interface PatientListResponse {
  items: Patient[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface PatientCreateInput {
  first_name: string;
  last_name: string;
  birth_date: string;
  gender?: 'male' | 'female' | 'other' | 'unknown';
  middle_name?: string;
  cyprus_id?: string;
  arc_number?: string;
  phone?: string;
  email?: string;
  address?: Address;
  emergency_contact?: EmergencyContact;
  gesy_beneficiary_id?: string;
  referring_physician?: string;
}

export interface PatientUpdateInput {
  first_name?: string;
  last_name?: string;
  middle_name?: string;
  gender?: 'male' | 'female' | 'other' | 'unknown';
  status?: 'active' | 'inactive' | 'deceased';
  phone?: string;
  email?: string;
  address?: Address;
  emergency_contact?: EmergencyContact;
  gesy_beneficiary_id?: string;
  referring_physician?: string;
}

export interface PatientSearchParams {
  q?: string;
  birth_date?: string;
  gender?: 'male' | 'female' | 'other' | 'unknown';
  status?: 'active' | 'inactive' | 'deceased';
  gesy_only?: boolean;
  page?: number;
  page_size?: number;
}

export interface PatientTimeline {
  patient_id: number;
  events: TimelineEvent[];
  total: number;
  page: number;
  page_size: number;
}

export interface TimelineEvent {
  id: string;
  type: 'encounter' | 'note' | 'observation' | 'cdss' | 'dicom';
  title: string;
  description?: string;
  timestamp: string;
  user_name?: string;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * List patients with pagination.
 */
export async function listPatients(
  accessToken: string,
  params: { page?: number; page_size?: number; status?: string } = {}
): Promise<PatientListResponse> {
  const queryString = buildQueryString(params);
  return apiFetch<PatientListResponse>(
    `/api/patients/${queryString}`,
    { method: 'GET' },
    accessToken
  );
}

/**
 * Search patients by name, MRN, or filters.
 */
export async function searchPatients(
  accessToken: string,
  params: PatientSearchParams
): Promise<PatientListResponse> {
  const queryString = buildQueryString(params as Record<string, string | number | boolean | undefined | null>);
  return apiFetch<PatientListResponse>(
    `/api/patients/search/${queryString}`,
    { method: 'GET' },
    accessToken
  );
}

/**
 * Get a single patient by ID.
 */
export async function getPatient(
  accessToken: string,
  patientId: number
): Promise<Patient> {
  return apiFetch<Patient>(
    `/api/patients/${patientId}`,
    { method: 'GET' },
    accessToken
  );
}

/**
 * Create a new patient.
 */
export async function createPatient(
  accessToken: string,
  data: PatientCreateInput
): Promise<Patient> {
  return apiFetch<Patient>(
    '/api/patients/',
    {
      method: 'POST',
      body: JSON.stringify(data),
    },
    accessToken
  );
}

/**
 * Update an existing patient.
 */
export async function updatePatient(
  accessToken: string,
  patientId: number,
  data: PatientUpdateInput
): Promise<Patient> {
  return apiFetch<Patient>(
    `/api/patients/${patientId}`,
    {
      method: 'PUT',
      body: JSON.stringify(data),
    },
    accessToken
  );
}

/**
 * Delete a patient (soft delete).
 */
export async function deletePatient(
  accessToken: string,
  patientId: number
): Promise<void> {
  return apiFetch<void>(
    `/api/patients/${patientId}`,
    { method: 'DELETE' },
    accessToken
  );
}

/**
 * Get patient timeline (encounters, notes, etc.).
 */
export async function getPatientTimeline(
  accessToken: string,
  patientId: number,
  params: { page?: number; page_size?: number } = {}
): Promise<PatientTimeline> {
  const queryString = buildQueryString(params);
  return apiFetch<PatientTimeline>(
    `/api/patients/${patientId}/timeline${queryString}`,
    { method: 'GET' },
    accessToken
  );
}
