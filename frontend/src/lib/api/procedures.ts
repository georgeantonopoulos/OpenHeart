/**
 * Procedure Scheduling API Client.
 *
 * Provides typed API functions for Modality Worklist (MWL) operations.
 * Allows scheduling imaging procedures that sync to Echo/Cath equipment.
 */

import { apiFetch, buildQueryString } from './client';

// ============================================================================
// Types
// ============================================================================

export type ImagingModality = 'US' | 'XA' | 'CT' | 'MR' | 'NM';

export type ProcedureStatus = 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';

export type ProcedurePriority = 'STAT' | 'URGENT' | 'ROUTINE';

export interface ScheduledProcedure {
  id: string;
  patient_id: number;
  clinic_id: number;
  accession_number: string;
  station_ae_title: string;
  station_name?: string;
  modality: ImagingModality;
  procedure_description?: string;
  scheduled_datetime: string;
  status: ProcedureStatus;
  priority: ProcedurePriority;
  reason_for_exam?: string;
  performing_physician_id?: number;
  study_instance_uid?: string;
  created_at: string;
}

export interface WorklistItem {
  PatientID: string;
  PatientName: string;
  PatientBirthDate: string;
  PatientSex: string;
  AccessionNumber: string;
  Modality: string;
  ScheduledProcedureStepStartDate: string;
  ScheduledProcedureStepStartTime: string;
  ScheduledStationAETitle: string;
  ScheduledProcedureStepDescription: string;
  ScheduledProcedureStepStatus: string;
  ScheduledPerformingPhysicianName: string;
  StudyInstanceUID: string;
}

export interface WorklistStation {
  id: number;
  ae_title: string;
  station_name: string;
  modality: ImagingModality;
  location?: string;
  manufacturer?: string;
  model?: string;
  is_active: boolean;
  last_query_at?: string;
}

export interface ScheduleProcedureInput {
  patient_id: number;
  modality: ImagingModality;
  scheduled_datetime: string;
  station_ae_title: string;
  procedure_description?: string;
  procedure_code?: string;
  performing_physician_id?: number;
  referring_physician_name?: string;
  reason_for_exam?: string;
  priority?: ProcedurePriority;
  encounter_id?: number;
  expected_duration_minutes?: number;
  notes?: string;
}

export interface UpdateStatusInput {
  status: ProcedureStatus;
  actual_start_datetime?: string;
  actual_end_datetime?: string;
  study_instance_uid?: string;
}

export interface CancelProcedureInput {
  cancellation_reason: string;
}

export interface CreateStationInput {
  ae_title: string;
  station_name: string;
  modality: ImagingModality;
  location?: string;
  manufacturer?: string;
  model?: string;
}

export interface WorklistSearchParams {
  scheduled_date?: string;
  station_ae_title?: string;
  modality?: ImagingModality;
  patient_id?: number;
  include_completed?: boolean;
}

// ============================================================================
// API Functions - Procedure Scheduling
// ============================================================================

/**
 * Schedule a new imaging procedure.
 * Creates a record in the Modality Worklist.
 */
export async function scheduleProcedure(
  accessToken: string,
  data: ScheduleProcedureInput
): Promise<ScheduledProcedure> {
  return apiFetch<ScheduledProcedure>(
    '/api/procedures/schedule',
    {
      method: 'POST',
      body: JSON.stringify(data),
    },
    accessToken
  );
}

/**
 * List scheduled procedures (worklist view).
 */
export async function listScheduledProcedures(
  accessToken: string,
  params: WorklistSearchParams = {}
): Promise<ScheduledProcedure[]> {
  const queryString = buildQueryString(params as Record<string, string | number | boolean | undefined | null>);
  return apiFetch<ScheduledProcedure[]>(
    `/api/procedures/scheduled${queryString}`,
    { method: 'GET' },
    accessToken
  );
}

/**
 * Get worklist in DICOM-compatible format.
 */
export async function getWorklist(
  accessToken: string,
  params: WorklistSearchParams = {}
): Promise<WorklistItem[]> {
  const queryString = buildQueryString(params as Record<string, string | number | boolean | undefined | null>);
  return apiFetch<WorklistItem[]>(
    `/api/procedures/worklist${queryString}`,
    { method: 'GET' },
    accessToken
  );
}

/**
 * Get a specific procedure by ID.
 */
export async function getProcedure(
  accessToken: string,
  procedureId: string
): Promise<ScheduledProcedure> {
  return apiFetch<ScheduledProcedure>(
    `/api/procedures/${procedureId}`,
    { method: 'GET' },
    accessToken
  );
}

/**
 * Update procedure status (MPPS integration).
 */
export async function updateProcedureStatus(
  accessToken: string,
  procedureId: string,
  data: UpdateStatusInput
): Promise<{ status: string; new_status: ProcedureStatus }> {
  return apiFetch<{ status: string; new_status: ProcedureStatus }>(
    `/api/procedures/${procedureId}/status`,
    {
      method: 'PUT',
      body: JSON.stringify(data),
    },
    accessToken
  );
}

/**
 * Cancel a scheduled procedure.
 */
export async function cancelProcedure(
  accessToken: string,
  procedureId: string,
  data: CancelProcedureInput
): Promise<{ status: string; accession_number: string }> {
  return apiFetch<{ status: string; accession_number: string }>(
    `/api/procedures/${procedureId}/cancel`,
    {
      method: 'POST',
      body: JSON.stringify(data),
    },
    accessToken
  );
}

/**
 * Get all procedures for a patient.
 */
export async function getPatientProcedures(
  accessToken: string,
  patientId: number,
  includeCancelled: boolean = false
): Promise<ScheduledProcedure[]> {
  const queryString = buildQueryString({ include_cancelled: includeCancelled });
  return apiFetch<ScheduledProcedure[]>(
    `/api/procedures/patient/${patientId}${queryString}`,
    { method: 'GET' },
    accessToken
  );
}

// ============================================================================
// API Functions - Station Management
// ============================================================================

/**
 * List configured worklist stations for the clinic.
 */
export async function listStations(
  accessToken: string
): Promise<WorklistStation[]> {
  return apiFetch<WorklistStation[]>(
    '/api/procedures/stations',
    { method: 'GET' },
    accessToken
  );
}

/**
 * Create or update a worklist station.
 */
export async function createStation(
  accessToken: string,
  data: CreateStationInput
): Promise<WorklistStation> {
  return apiFetch<WorklistStation>(
    '/api/procedures/stations',
    {
      method: 'POST',
      body: JSON.stringify(data),
    },
    accessToken
  );
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Format modality for display.
 */
export function formatModality(modality: ImagingModality): string {
  const labels: Record<ImagingModality, string> = {
    US: 'Echocardiogram',
    XA: 'Catheterization',
    CT: 'CT Angiography',
    MR: 'Cardiac MRI',
    NM: 'Nuclear Imaging',
  };
  return labels[modality] || modality;
}

/**
 * Get modality icon name for UI.
 */
export function getModalityIcon(modality: ImagingModality): string {
  const icons: Record<ImagingModality, string> = {
    US: 'heart-pulse', // Echo
    XA: 'crosshair', // Cath
    CT: 'scan', // CT
    MR: 'magnet', // MRI
    NM: 'radiation', // Nuclear
  };
  return icons[modality] || 'image';
}

/**
 * Get modality color for badges.
 */
export function getModalityColor(modality: ImagingModality): string {
  const colors: Record<ImagingModality, string> = {
    US: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    XA: 'bg-red-500/20 text-red-400 border-red-500/30',
    CT: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    MR: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30',
    NM: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  };
  return colors[modality] || 'bg-slate-500/20 text-slate-400 border-slate-500/30';
}

/**
 * Get status color for badges.
 */
export function getStatusColor(status: ProcedureStatus): string {
  const colors: Record<ProcedureStatus, string> = {
    SCHEDULED: 'bg-teal-500/20 text-teal-400 border-teal-500/30',
    IN_PROGRESS: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    COMPLETED: 'bg-green-500/20 text-green-400 border-green-500/30',
    CANCELLED: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
  };
  return colors[status] || 'bg-slate-500/20 text-slate-400 border-slate-500/30';
}

/**
 * Get priority color for badges.
 */
export function getPriorityColor(priority: ProcedurePriority): string {
  const colors: Record<ProcedurePriority, string> = {
    STAT: 'bg-red-500/20 text-red-400 border-red-500/30',
    URGENT: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    ROUTINE: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
  };
  return colors[priority] || 'bg-slate-500/20 text-slate-400 border-slate-500/30';
}

/**
 * Format scheduled datetime for display.
 */
export function formatScheduledTime(dateStr: string): string {
  try {
    const date = new Date(dateStr);
    return date.toLocaleString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateStr;
  }
}

/**
 * Format time only for display.
 */
export function formatTimeOnly(dateStr: string): string {
  try {
    const date = new Date(dateStr);
    return date.toLocaleTimeString('en-GB', {
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateStr;
  }
}
