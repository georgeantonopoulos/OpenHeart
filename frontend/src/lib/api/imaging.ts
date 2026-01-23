/**
 * DICOM/Imaging API Client for OpenHeart Cyprus.
 *
 * Provides methods for querying DICOM studies, accessing
 * the OHIF viewer, and retrieving study metadata.
 */

import { apiClient } from "./client";

// =============================================================================
// Types
// =============================================================================

export type Modality = "US" | "XA" | "CT" | "MR" | "NM" | "ECG" | "HD" | "SR";

export type StudyStatus = "new" | "in_progress" | "preliminary" | "final" | "addendum";

export interface DicomPatient {
  patient_id: string;
  patient_name: string;
  birth_date?: string;
  sex?: string;
}

export interface DicomSeries {
  series_instance_uid: string;
  series_number?: number;
  series_description?: string;
  modality: Modality;
  body_part?: string;
  instance_count: number;
}

export interface DicomStudy {
  study_instance_uid: string;
  study_id?: string;
  accession_number?: string;
  study_date?: string;
  study_time?: string;
  study_description?: string;
  referring_physician?: string;
  institution_name?: string;
  patient?: DicomPatient;
  modalities: Modality[];
  series_count: number;
  series: DicomSeries[];
  status: StudyStatus;
  linked_patient_id?: number;
  linked_encounter_id?: number;
}

export interface DicomStudyList {
  studies: DicomStudy[];
  total: number;
  page: number;
  per_page: number;
}

export interface ViewerUrlResponse {
  viewer_url: string;
  study_instance_uid: string;
  expires_at?: string;
}

export interface StudySearchParams {
  patient_id?: string;
  patient_name?: string;
  accession_number?: string;
  modality?: Modality;
  study_date_from?: string;
  study_date_to?: string;
  study_description?: string;
  linked_patient_id?: number;
  page?: number;
  per_page?: number;
}

export interface EchoMeasurements {
  study_instance_uid: string;
  study_date?: string;
  performed_by?: string;
  interpreted_by?: string;
  lv: {
    lvef?: number;
    lvef_method?: string;
    lvidd?: number;
    lvids?: number;
    lv_mass?: number;
    lv_mass_index?: number;
    global_ls?: number;
  };
  diastolic: {
    e_velocity?: number;
    a_velocity?: number;
    e_a_ratio?: number;
    e_prime_septal?: number;
    e_prime_lateral?: number;
    e_e_prime_ratio?: number;
    grade?: string;
  };
  aortic_valve: {
    stenosis?: string;
    regurgitation?: string;
    peak_gradient?: number;
    mean_gradient?: number;
    valve_area?: number;
  };
  mitral_valve: {
    stenosis?: string;
    regurgitation?: string;
  };
  tricuspid_valve: {
    stenosis?: string;
    regurgitation?: string;
  };
  rvsp?: number;
  pericardial_effusion?: string;
  wall_motion_abnormality: boolean;
  findings?: string;
  impression?: string;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Search for DICOM studies.
 */
export async function searchStudies(
  accessToken: string,
  params: StudySearchParams
): Promise<DicomStudyList> {
  const searchParams = new URLSearchParams();

  if (params.patient_id) searchParams.append("patient_id", params.patient_id);
  if (params.patient_name)
    searchParams.append("patient_name", params.patient_name);
  if (params.accession_number)
    searchParams.append("accession_number", params.accession_number);
  if (params.modality) searchParams.append("modality", params.modality);
  if (params.study_date_from)
    searchParams.append("study_date_from", params.study_date_from);
  if (params.study_date_to)
    searchParams.append("study_date_to", params.study_date_to);
  if (params.study_description)
    searchParams.append("study_description", params.study_description);
  if (params.linked_patient_id)
    searchParams.append("linked_patient_id", String(params.linked_patient_id));
  if (params.page) searchParams.append("page", String(params.page));
  if (params.per_page) searchParams.append("per_page", String(params.per_page));

  return apiClient.get<DicomStudyList>(
    `/api/dicom/studies?${searchParams.toString()}`,
    accessToken
  );
}

/**
 * Get detailed study metadata including series.
 */
export async function getStudy(accessToken: string, studyUid: string): Promise<DicomStudy> {
  return apiClient.get<DicomStudy>(`/api/dicom/studies/${studyUid}`, accessToken);
}

/**
 * Get OHIF Viewer URL for a study.
 */
export async function getViewerUrl(
  accessToken: string,
  studyUid: string
): Promise<ViewerUrlResponse> {
  return apiClient.get<ViewerUrlResponse>(
    `/api/dicom/studies/${studyUid}/viewer-url`,
    accessToken
  );
}

/**
 * Get thumbnail URL for a study.
 */
export function getStudyThumbnailUrl(studyUid: string): string {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  return `${baseUrl}/api/dicom/studies/${studyUid}/thumbnail`;
}

/**
 * Get echo measurements from study structured report.
 */
export async function getEchoMeasurements(
  accessToken: string,
  studyUid: string
): Promise<EchoMeasurements> {
  return apiClient.get<EchoMeasurements>(
    `/api/dicom/studies/${studyUid}/echo-measurements`,
    accessToken
  );
}

/**
 * Get all studies for a patient.
 */
export async function getPatientStudies(
  accessToken: string,
  patientId: number,
  page: number = 1,
  perPage: number = 20
): Promise<DicomStudyList> {
  return apiClient.get<DicomStudyList>(
    `/api/dicom/patients/${patientId}/studies?page=${page}&per_page=${perPage}`,
    accessToken
  );
}

/**
 * Link a study to a patient.
 */
export async function linkStudyToPatient(
  accessToken: string,
  studyUid: string,
  patientId: number,
  encounterId?: number
): Promise<{ status: string; message: string }> {
  const params = new URLSearchParams();
  params.append("patient_id", String(patientId));
  if (encounterId) params.append("encounter_id", String(encounterId));

  return apiClient.post(`/api/dicom/studies/${studyUid}/link?${params.toString()}`, undefined, accessToken);
}

/**
 * Delete a study (admin only).
 */
export async function deleteStudy(accessToken: string, studyUid: string): Promise<void> {
  return apiClient.delete(`/api/dicom/studies/${studyUid}`, accessToken);
}

/**
 * Check DICOM service health.
 */
export async function checkDicomHealth(accessToken: string): Promise<{
  service: string;
  status: string;
}> {
  return apiClient.get("/api/dicom/health", accessToken);
}

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Format modality for display.
 */
export function formatModality(modality: Modality): string {
  const labels: Record<Modality, string> = {
    US: "Ultrasound (Echo)",
    XA: "X-Ray Angiography",
    CT: "CT Scan",
    MR: "MRI",
    NM: "Nuclear Medicine",
    ECG: "Electrocardiogram",
    HD: "Hemodynamic",
    SR: "Structured Report",
  };
  return labels[modality] || modality;
}

/**
 * Get modality color for badges.
 */
export function getModalityColor(modality: Modality): string {
  const colors: Record<Modality, string> = {
    US: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    XA: "bg-red-500/20 text-red-400 border-red-500/30",
    CT: "bg-purple-500/20 text-purple-400 border-purple-500/30",
    MR: "bg-indigo-500/20 text-indigo-400 border-indigo-500/30",
    NM: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    ECG: "bg-green-500/20 text-green-400 border-green-500/30",
    HD: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
    SR: "bg-slate-500/20 text-slate-400 border-slate-500/30",
  };
  return colors[modality] || "bg-slate-500/20 text-slate-400 border-slate-500/30";
}

/**
 * Format study date for display.
 */
export function formatStudyDate(dateStr?: string): string {
  if (!dateStr) return "Unknown";
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  } catch {
    return dateStr;
  }
}
