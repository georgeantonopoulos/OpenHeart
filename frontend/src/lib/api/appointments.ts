/**
 * Appointments API Client.
 *
 * Provides typed functions for appointment management:
 * - CRUD operations
 * - Conflict detection
 * - Check-in workflow
 * - Encounter handover
 */

import { apiFetch, buildQueryString } from './client';

// ============================================================================
// Types
// ============================================================================

export type AppointmentType =
  | 'consultation'
  | 'follow_up'
  | 'echo'
  | 'stress_test'
  | 'holter'
  | 'procedure'
  | 'ecg'
  | 'pre_op';

export type AppointmentStatus =
  | 'scheduled'
  | 'confirmed'
  | 'checked_in'
  | 'in_progress'
  | 'completed'
  | 'cancelled'
  | 'no_show';

export interface Appointment {
  appointment_id: number;
  clinic_id: number;
  patient_id: number;
  patient_name?: string;
  provider_id: number;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  expected_duration_minutes?: number;
  appointment_type: AppointmentType;
  status: AppointmentStatus;
  reason?: string;
  notes?: string;
  location?: string;
  gesy_referral_id?: string;
  encounter_id?: number;
  cancelled_at?: string;
  cancellation_reason?: string;
  duration_warning?: string;
  created_at: string;
}

export interface AppointmentCreateInput {
  patient_id: number;
  provider_id: number;
  start_time: string;
  duration_minutes: number;
  appointment_type: AppointmentType;
  reason?: string;
  notes?: string;
  location?: string;
  gesy_referral_id?: string;
}

export interface AppointmentUpdateInput {
  start_time?: string;
  duration_minutes?: number;
  appointment_type?: AppointmentType;
  reason?: string;
  notes?: string;
  location?: string;
  provider_id?: number;
}

export interface ConflictInfo {
  conflicting_appointment_id: number;
  patient_id: number;
  start_time: string;
  end_time: string;
  appointment_type: string;
}

export interface AvailableSlot {
  start_time: string;
  end_time: string;
  duration_minutes: number;
}

export interface StartEncounterResponse {
  encounter_id: number;
  appointment_id: number;
  status: string;
  message: string;
}

// Expected durations (matches backend)
export const EXPECTED_DURATIONS: Record<AppointmentType, number> = {
  consultation: 20,
  follow_up: 15,
  echo: 30,
  stress_test: 45,
  holter: 15,
  procedure: 60,
  ecg: 10,
  pre_op: 30,
};

// ============================================================================
// API Functions
// ============================================================================

export async function createAppointment(
  accessToken: string,
  data: AppointmentCreateInput
): Promise<Appointment> {
  return apiFetch<Appointment>(
    '/api/appointments',
    { method: 'POST', body: JSON.stringify(data) },
    accessToken
  );
}

export async function listAppointments(
  accessToken: string,
  params: {
    from_date?: string;
    to_date?: string;
    provider_id?: number;
    patient_id?: number;
    status?: AppointmentStatus;
  } = {}
): Promise<Appointment[]> {
  const queryString = buildQueryString(params as Record<string, string>);
  return apiFetch<Appointment[]>(
    `/api/appointments${queryString}`,
    { method: 'GET' },
    accessToken
  );
}

export async function getTodayAppointments(
  accessToken: string
): Promise<Appointment[]> {
  const today = new Date().toISOString().split('T')[0];
  return listAppointments(accessToken, { from_date: today, to_date: today });
}

export async function getAppointment(
  accessToken: string,
  appointmentId: number
): Promise<Appointment> {
  return apiFetch<Appointment>(
    `/api/appointments/${appointmentId}`,
    { method: 'GET' },
    accessToken
  );
}

export async function updateAppointment(
  accessToken: string,
  appointmentId: number,
  data: AppointmentUpdateInput
): Promise<Appointment> {
  return apiFetch<Appointment>(
    `/api/appointments/${appointmentId}`,
    { method: 'PUT', body: JSON.stringify(data) },
    accessToken
  );
}

export async function cancelAppointment(
  accessToken: string,
  appointmentId: number,
  reason?: string
): Promise<Appointment> {
  const params = reason ? `?reason=${encodeURIComponent(reason)}` : '';
  return apiFetch<Appointment>(
    `/api/appointments/${appointmentId}${params}`,
    { method: 'DELETE' },
    accessToken
  );
}

export async function checkInAppointment(
  accessToken: string,
  appointmentId: number
): Promise<Appointment> {
  return apiFetch<Appointment>(
    `/api/appointments/${appointmentId}/check-in`,
    { method: 'POST' },
    accessToken
  );
}

export async function startEncounterFromAppointment(
  accessToken: string,
  appointmentId: number
): Promise<StartEncounterResponse> {
  return apiFetch<StartEncounterResponse>(
    `/api/appointments/${appointmentId}/start-encounter`,
    { method: 'POST' },
    accessToken
  );
}

export async function getAvailableSlots(
  accessToken: string,
  providerId: number,
  targetDate: string,
  durationMinutes: number = 30
): Promise<AvailableSlot[]> {
  return apiFetch<AvailableSlot[]>(
    `/api/appointments/slots/available?provider_id=${providerId}&target_date=${targetDate}&duration_minutes=${durationMinutes}`,
    { method: 'GET' },
    accessToken
  );
}

export async function checkConflicts(
  accessToken: string,
  providerId: number,
  startTime: string,
  endTime: string,
  excludeId?: number
): Promise<ConflictInfo[]> {
  let url = `/api/appointments/conflicts/check?provider_id=${providerId}&start_time=${encodeURIComponent(startTime)}&end_time=${encodeURIComponent(endTime)}`;
  if (excludeId) url += `&exclude_id=${excludeId}`;
  return apiFetch<ConflictInfo[]>(url, { method: 'GET' }, accessToken);
}

// ============================================================================
// Utility Functions
// ============================================================================

export function getAppointmentStatusColor(status: AppointmentStatus): string {
  const colors: Record<AppointmentStatus, string> = {
    scheduled: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    confirmed: 'bg-teal-500/20 text-teal-400 border-teal-500/30',
    checked_in: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    in_progress: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    completed: 'bg-green-500/20 text-green-400 border-green-500/30',
    cancelled: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
    no_show: 'bg-red-500/20 text-red-400 border-red-500/30',
  };
  return colors[status] || 'bg-slate-500/20 text-slate-400 border-slate-500/30';
}

export function formatAppointmentType(type: AppointmentType): string {
  const labels: Record<AppointmentType, string> = {
    consultation: 'Consultation',
    follow_up: 'Follow-up',
    echo: 'Echocardiogram',
    stress_test: 'Stress Test',
    holter: 'Holter Monitor',
    procedure: 'Procedure',
    ecg: 'ECG',
    pre_op: 'Pre-Op Assessment',
  };
  return labels[type] || type;
}

export function formatAppointmentStatus(status: AppointmentStatus): string {
  const labels: Record<AppointmentStatus, string> = {
    scheduled: 'Scheduled',
    confirmed: 'Confirmed',
    checked_in: 'Checked In',
    in_progress: 'In Progress',
    completed: 'Completed',
    cancelled: 'Cancelled',
    no_show: 'No Show',
  };
  return labels[status] || status;
}
