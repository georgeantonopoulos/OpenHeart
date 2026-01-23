/**
 * Encounters API Client.
 *
 * Provides typed functions for clinical encounters and vitals.
 */

import { apiFetch, buildQueryString } from './client';

// ============================================================================
// Types
// ============================================================================

export type EncounterType =
    | 'outpatient'
    | 'inpatient'
    | 'emergency'
    | 'telehealth'
    | 'home_visit';

export type EncounterStatus =
    | 'planned'
    | 'in_progress'
    | 'completed'
    | 'cancelled'
    | 'no_show';

export type BillingStatus =
    | 'pending'
    | 'submitted'
    | 'approved'
    | 'rejected'
    | 'paid';

export interface Encounter {
    encounter_id: number;
    patient_id: number;
    patient_name?: string;
    patient_mrn?: string;
    attending_physician_id: number;
    clinic_id: number;
    start_time: string;
    end_time?: string;
    encounter_type: EncounterType;
    status: EncounterStatus;
    billing_status: BillingStatus;
    primary_diagnosis?: string;
    appointment_id?: number;
    created_at: string;
}

export interface EncounterCreate {
    patient_id: number;
    encounter_type: EncounterType;
    appointment_id?: number;
    planned_start_time?: string;
}

export interface EncounterStart {
    actual_start_time?: string;
}

export interface EncounterComplete {
    actual_end_time?: string;
    discharge_summary?: string;
    diagnoses?: string[];
}

export interface EncounterListResponse {
    items: Encounter[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * List encounters for the current clinic.
 */
export async function listEncounters(
    accessToken: string,
    params: {
        patient_id?: number;
        status?: EncounterStatus;
        encounter_type?: EncounterType;
        page?: number;
        page_size?: number;
    } = {}
): Promise<EncounterListResponse> {
    const queryString = buildQueryString(params);
    return apiFetch<EncounterListResponse>(
        `/api/encounters${queryString}`,
        { method: 'GET' },
        accessToken
    );
}

/**
 * Get encounters for today (physician-scoped).
 */
export async function getTodayEncounters(
    accessToken: string
): Promise<Encounter[]> {
    return apiFetch<Encounter[]>(
        '/api/encounters/today',
        { method: 'GET' },
        accessToken
    );
}

/**
 * Create a new encounter.
 */
export async function createEncounter(
    accessToken: string,
    data: EncounterCreate
): Promise<Encounter> {
    return apiFetch<Encounter>(
        '/api/encounters',
        {
            method: 'POST',
            body: JSON.stringify(data),
        },
        accessToken
    );
}

/**
 * Get encounter by ID.
 */
export async function getEncounter(
    accessToken: string,
    encounter_id: number
): Promise<Encounter> {
    return apiFetch<Encounter>(
        `/api/encounters/${encounter_id}`,
        { method: 'GET' },
        accessToken
    );
}

/**
 * Start an encounter (set to in_progress).
 */
export async function startEncounter(
    accessToken: string,
    encounter_id: number,
    data: EncounterStart = {}
): Promise<Encounter> {
    return apiFetch<Encounter>(
        `/api/encounters/${encounter_id}/start`,
        {
            method: 'POST',
            body: JSON.stringify(data),
        },
        accessToken
    );
}

/**
 * Complete an encounter (set to completed).
 */
export async function completeEncounter(
    accessToken: string,
    encounter_id: number,
    data: EncounterComplete = {}
): Promise<Encounter> {
    return apiFetch<Encounter>(
        `/api/encounters/${encounter_id}/complete`,
        {
            method: 'POST',
            body: JSON.stringify(data),
        },
        accessToken
    );
}

/**
 * Cancel an encounter.
 */
export async function cancelEncounter(
    accessToken: string,
    encounter_id: number,
    reason?: string
): Promise<Encounter> {
    const params = reason ? `?reason=${encodeURIComponent(reason)}` : '';
    return apiFetch<Encounter>(
        `/api/encounters/${encounter_id}/cancel${params}`,
        { method: 'POST' },
        accessToken
    );
}
