/**
 * Medical Coding API Client.
 *
 * Provides typed search functions for ICD-10, CPT, LOINC, ATC,
 * HIO service codes, and Gesy medications.
 */

import { apiFetch } from './client';

// ============================================================================
// Types
// ============================================================================

export interface ICD10Code {
  code: string;
  description_en: string;
  description_el?: string;
  chapter?: string;
  category?: string;
  is_billable: boolean;
}

export interface ICPC2Code {
  code: string;
  description_en: string;
  description_el?: string;
  component?: string;
  chapter?: string;
}

export interface LOINCCode {
  code: string;
  long_name: string;
  short_name?: string;
  component?: string;
  class_type?: string;
}

export interface ATCCode {
  code: string;
  name: string;
  level: number;
  parent_code?: string;
  ddd?: string;
}

export interface CPTCode {
  code: string;
  description: string;
  category?: string;
  relative_value?: number;
}

export interface HIOServiceCode {
  code: string;
  description_en: string;
  description_el?: string;
  service_type?: string;
  specialty_code?: string;
  base_price_eur?: number;
}

export interface GesyMedication {
  hio_product_id: string;
  atc_code: string;
  brand_name: string;
  generic_name?: string;
  strength?: string;
  form?: string;
  pack_size?: number;
  manufacturer?: string;
  price_eur?: number;
  requires_pre_auth: boolean;
}

// ============================================================================
// Search Functions
// ============================================================================

export async function searchICD10(
  accessToken: string,
  query: string,
  limit: number = 20
): Promise<ICD10Code[]> {
  return apiFetch<ICD10Code[]>(
    `/api/codes/icd10/search?q=${encodeURIComponent(query)}&limit=${limit}`,
    { method: 'GET' },
    accessToken
  );
}

export async function getICD10(
  accessToken: string,
  code: string
): Promise<ICD10Code> {
  return apiFetch<ICD10Code>(
    `/api/codes/icd10/${encodeURIComponent(code)}`,
    { method: 'GET' },
    accessToken
  );
}

export async function searchICPC2(
  accessToken: string,
  query: string,
  limit: number = 20
): Promise<ICPC2Code[]> {
  return apiFetch<ICPC2Code[]>(
    `/api/codes/icpc2/search?q=${encodeURIComponent(query)}&limit=${limit}`,
    { method: 'GET' },
    accessToken
  );
}

export async function searchCPT(
  accessToken: string,
  query: string,
  limit: number = 20
): Promise<CPTCode[]> {
  return apiFetch<CPTCode[]>(
    `/api/codes/cpt/search?q=${encodeURIComponent(query)}&limit=${limit}`,
    { method: 'GET' },
    accessToken
  );
}

export async function getCPT(
  accessToken: string,
  code: string
): Promise<CPTCode> {
  return apiFetch<CPTCode>(
    `/api/codes/cpt/${encodeURIComponent(code)}`,
    { method: 'GET' },
    accessToken
  );
}

export async function searchHIO(
  accessToken: string,
  query: string,
  specialty?: string,
  limit: number = 20
): Promise<HIOServiceCode[]> {
  let url = `/api/codes/hio/search?q=${encodeURIComponent(query)}&limit=${limit}`;
  if (specialty) url += `&specialty=${encodeURIComponent(specialty)}`;
  return apiFetch<HIOServiceCode[]>(url, { method: 'GET' }, accessToken);
}

export async function searchLOINC(
  accessToken: string,
  query: string,
  limit: number = 20
): Promise<LOINCCode[]> {
  return apiFetch<LOINCCode[]>(
    `/api/codes/loinc/search?q=${encodeURIComponent(query)}&limit=${limit}`,
    { method: 'GET' },
    accessToken
  );
}

export async function searchATC(
  accessToken: string,
  query: string,
  limit: number = 20
): Promise<ATCCode[]> {
  return apiFetch<ATCCode[]>(
    `/api/codes/atc/search?q=${encodeURIComponent(query)}&limit=${limit}`,
    { method: 'GET' },
    accessToken
  );
}

export async function searchMedications(
  accessToken: string,
  query: string,
  limit: number = 20
): Promise<GesyMedication[]> {
  return apiFetch<GesyMedication[]>(
    `/api/codes/medications/search?q=${encodeURIComponent(query)}&limit=${limit}`,
    { method: 'GET' },
    accessToken
  );
}

export async function getMedication(
  accessToken: string,
  hioProductId: string
): Promise<GesyMedication> {
  return apiFetch<GesyMedication>(
    `/api/codes/medications/${encodeURIComponent(hioProductId)}`,
    { method: 'GET' },
    accessToken
  );
}
