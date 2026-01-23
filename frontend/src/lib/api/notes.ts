/**
 * Notes API Client.
 *
 * Provides TypeScript-safe API calls for clinical notes.
 */

import { apiFetch, buildQueryString } from './client';

// ============================================================================
// Types
// ============================================================================

export type NoteType = 'free_text' | 'soap' | 'procedure' | 'consultation' | 'discharge' | 'progress';

export interface SOAPContent {
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
}

export interface NoteVersion {
  version_id: number;
  version_number: number;
  content_text: string;
  content_html?: string;
  structured_data?: Record<string, unknown>;
  diff_from_previous?: Record<string, unknown>;
  edited_by: number;
  edit_reason?: string;
  word_count: number;
  char_count: number;
  created_at: string;
}

export interface NoteAttachment {
  attachment_id: number;
  file_name: string;
  original_file_name: string;
  file_type: string;
  mime_type: string;
  file_size_bytes: number;
  extraction_status: string;
  page_count?: number;
  image_width?: number;
  image_height?: number;
  uploaded_by: number;
  uploaded_at: string;
}

export interface Note {
  note_id: number;
  patient_id: number;
  encounter_id?: number;
  note_type: NoteType;
  title: string;
  current_version: number;
  is_locked: boolean;
  locked_at?: string;
  locked_reason?: string;
  created_by: number;
  created_at: string;
  updated_at: string;
  content_text?: string;
  content_html?: string;
  structured_data?: Record<string, unknown>;
  attachment_count: number;
  version_count: number;
}

export interface NoteDetail extends Note {
  versions: NoteVersion[];
  attachments: NoteAttachment[];
}

export interface NoteListResponse {
  items: Note[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface NoteCreateInput {
  patient_id: number;
  encounter_id?: number;
  note_type?: NoteType;
  title: string;
  content_text: string;
  content_html?: string;
  structured_data?: SOAPContent;
}

export interface NoteUpdateInput {
  content_text: string;
  content_html?: string;
  structured_data?: SOAPContent;
  edit_reason: string;
}

export interface SearchHighlight {
  field: string;
  text: string;
  score: number;
}

export interface NoteSearchResult {
  note_id: number;
  patient_id: number;
  title: string;
  note_type: string;
  created_at: string;
  author_name: string;
  highlights: SearchHighlight[];
  relevance_score: number;
}

export interface NoteSearchResponse {
  query: string;
  results: NoteSearchResult[];
  total: number;
  page: number;
  page_size: number;
  search_time_ms: number;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * List notes for a patient.
 */
export async function listPatientNotes(
  token: string,
  patientId: number,
  options: {
    page?: number;
    page_size?: number;
    note_type?: NoteType;
  } = {}
): Promise<NoteListResponse> {
  const queryString = buildQueryString({
    page: options.page || 1,
    page_size: options.page_size || 20,
    note_type: options.note_type,
  });

  return apiFetch<NoteListResponse>(`/api/notes/patient/${patientId}${queryString}`, {
    method: 'GET',
  }, token);
}

/**
 * Get a specific note with details.
 */
export async function getNote(token: string, noteId: number): Promise<NoteDetail> {
  return apiFetch<NoteDetail>(`/api/notes/${noteId}`, {
    method: 'GET',
  }, token);
}

/**
 * Create a new note.
 */
export async function createNote(token: string, data: NoteCreateInput): Promise<Note> {
  return apiFetch<Note>('/api/notes/', {
    method: 'POST',
    body: JSON.stringify(data),
  }, token);
}

/**
 * Update a note (creates new version).
 */
export async function updateNote(
  token: string,
  noteId: number,
  data: NoteUpdateInput
): Promise<Note> {
  return apiFetch<Note>(`/api/notes/${noteId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }, token);
}

/**
 * Lock a note to prevent edits.
 */
export async function lockNote(
  token: string,
  noteId: number,
  reason: string
): Promise<Note> {
  return apiFetch<Note>(`/api/notes/${noteId}/lock?reason=${encodeURIComponent(reason)}`, {
    method: 'POST',
  }, token);
}

/**
 * Get all versions of a note.
 */
export async function getNoteVersions(
  token: string,
  noteId: number
): Promise<NoteVersion[]> {
  return apiFetch<NoteVersion[]>(`/api/notes/${noteId}/versions`, {
    method: 'GET',
  }, token);
}

/**
 * Get a specific version.
 */
export async function getNoteVersion(
  token: string,
  noteId: number,
  versionNumber: number
): Promise<NoteVersion> {
  return apiFetch<NoteVersion>(`/api/notes/${noteId}/versions/${versionNumber}`, {
    method: 'GET',
  }, token);
}

/**
 * Search notes.
 */
export async function searchNotes(
  token: string,
  query: string,
  options: {
    patient_id?: number;
    note_type?: NoteType;
    author_id?: number;
    page?: number;
    page_size?: number;
  } = {}
): Promise<NoteSearchResponse> {
  const queryString = buildQueryString({
    q: query,
    patient_id: options.patient_id,
    note_type: options.note_type,
    author_id: options.author_id,
    page: options.page || 1,
    page_size: options.page_size || 20,
  });

  return apiFetch<NoteSearchResponse>(`/api/notes/search${queryString}`, {
    method: 'GET',
  }, token);
}

/**
 * Upload an attachment to a note.
 */
export async function uploadAttachment(
  token: string,
  noteId: number,
  file: File
): Promise<{ attachment_id: number; file_name: string; extraction_status: string }> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/notes/${noteId}/attachments`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(error.detail || 'Upload failed');
  }

  return response.json();
}

/**
 * Get download URL for attachment.
 */
export async function getAttachmentDownloadUrl(
  token: string,
  noteId: number,
  attachmentId: number
): Promise<{ download_url: string; expires_in_seconds: number }> {
  return apiFetch(`/api/notes/${noteId}/attachments/${attachmentId}/download`, {
    method: 'GET',
  }, token);
}

/**
 * Delete an attachment.
 */
export async function deleteAttachment(
  token: string,
  noteId: number,
  attachmentId: number
): Promise<void> {
  await apiFetch(`/api/notes/${noteId}/attachments/${attachmentId}`, {
    method: 'DELETE',
  }, token);
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Get note type display label.
 */
export function getNoteTypeLabel(type: NoteType): string {
  const labels: Record<NoteType, string> = {
    free_text: 'Free Text',
    soap: 'SOAP Note',
    procedure: 'Procedure',
    consultation: 'Consultation',
    discharge: 'Discharge',
    progress: 'Progress Note',
  };
  return labels[type] || type;
}

/**
 * Get note type color class.
 */
export function getNoteTypeColor(type: NoteType): string {
  const colors: Record<NoteType, string> = {
    free_text: 'bg-slate-500/20 text-slate-300',
    soap: 'bg-blue-500/20 text-blue-300',
    procedure: 'bg-rose-500/20 text-rose-300',
    consultation: 'bg-purple-500/20 text-purple-300',
    discharge: 'bg-amber-500/20 text-amber-300',
    progress: 'bg-teal-500/20 text-teal-300',
  };
  return colors[type] || colors.free_text;
}
