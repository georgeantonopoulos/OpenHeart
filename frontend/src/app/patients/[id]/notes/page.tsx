'use client';

import { useState } from 'react';
import { useSession } from 'next-auth/react';
import { useQuery } from '@tanstack/react-query';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  listPatientNotes,
  Note,
  NoteType,
  getNoteTypeLabel,
  getNoteTypeColor,
} from '@/lib/api/notes';
import { getPatient } from '@/lib/api/patients';

/**
 * Patient Notes List Page.
 *
 * Displays all clinical notes for a patient with filtering by type.
 */
export default function PatientNotesPage() {
  const { data: session } = useSession();
  const params = useParams();
  const router = useRouter();
  const patientId = Number(params.id);

  const [noteTypeFilter, setNoteTypeFilter] = useState<NoteType | ''>('');
  const [page, setPage] = useState(1);

  // Fetch patient
  const { data: patient } = useQuery({
    queryKey: ['patient', patientId],
    queryFn: () => getPatient(session?.accessToken || '', patientId),
    enabled: !!session?.accessToken && !!patientId,
  });

  // Fetch notes
  const { data, isLoading, error } = useQuery({
    queryKey: ['patient-notes', patientId, noteTypeFilter, page],
    queryFn: () =>
      listPatientNotes(session?.accessToken || '', patientId, {
        note_type: noteTypeFilter || undefined,
        page,
        page_size: 20,
      }),
    enabled: !!session?.accessToken && !!patientId,
  });

  // Format date
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-CY', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Truncate content for preview
  const getPreview = (content?: string, maxLength = 150) => {
    if (!content) return '';
    const stripped = content.replace(/[#*_`]/g, '').trim();
    if (stripped.length <= maxLength) return stripped;
    return stripped.substring(0, maxLength) + '...';
  };

  if (!session) {
    return null;
  }

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <div className="bg-slate-900 border-b border-slate-800">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link
                href={`/patients/${patientId}`}
                className="text-slate-400 hover:text-slate-200 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10 19l-7-7m0 0l7-7m-7 7h18"
                  />
                </svg>
              </Link>
              <div>
                <h1 className="text-2xl font-bold text-white">Clinical Notes</h1>
                {patient && (
                  <p className="text-sm text-slate-400">
                    {patient.first_name} {patient.last_name} • {patient.mrn}
                  </p>
                )}
              </div>
            </div>
            <Link
              href={`/patients/${patientId}/notes/new`}
              className="inline-flex items-center px-4 py-2 bg-rose-600 text-white rounded-lg hover:bg-rose-700 transition-colors"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4v16m8-8H4"
                />
              </svg>
              New Note
            </Link>
          </div>
        </div>
      </div>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Filters */}
        <div className="mb-6 flex items-center gap-4">
          <select
            value={noteTypeFilter}
            onChange={(e) => {
              setNoteTypeFilter(e.target.value as NoteType | '');
              setPage(1);
            }}
            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-rose-500"
          >
            <option value="">All Types</option>
            <option value="soap">SOAP Notes</option>
            <option value="free_text">Free Text</option>
            <option value="procedure">Procedures</option>
            <option value="consultation">Consultations</option>
            <option value="discharge">Discharge</option>
            <option value="progress">Progress Notes</option>
          </select>

          {data && (
            <span className="text-sm text-slate-400">
              {data.total} note{data.total !== 1 ? 's' : ''} found
            </span>
          )}
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-red-900/20 border border-red-800 rounded-lg p-4 mb-6">
            <p className="text-red-400">Failed to load notes. Please try again.</p>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-rose-500"></div>
          </div>
        )}

        {/* Notes List */}
        {!isLoading && data && (
          <>
            {data.items.length === 0 ? (
              <div className="bg-slate-900 rounded-lg border border-slate-800 p-12 text-center">
                <svg
                  className="mx-auto h-12 w-12 text-slate-500 mb-3"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                <p className="text-slate-400 mb-4">No clinical notes found</p>
                <Link
                  href={`/patients/${patientId}/notes/new`}
                  className="inline-flex items-center px-4 py-2 bg-rose-600 text-white rounded-lg hover:bg-rose-700 transition-colors"
                >
                  Create First Note
                </Link>
              </div>
            ) : (
              <div className="space-y-4">
                {data.items.map((note: Note) => (
                  <Link
                    key={note.note_id}
                    href={`/patients/${patientId}/notes/${note.note_id}`}
                    className="block bg-slate-900 rounded-lg border border-slate-800 p-4 hover:border-slate-700 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        {/* Title & Type */}
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="text-lg font-medium text-white truncate">
                            {note.title}
                          </h3>
                          <span
                            className={`px-2 py-0.5 text-xs rounded ${getNoteTypeColor(
                              note.note_type
                            )}`}
                          >
                            {getNoteTypeLabel(note.note_type)}
                          </span>
                          {note.is_locked && (
                            <span className="px-2 py-0.5 text-xs bg-amber-500/20 text-amber-300 rounded flex items-center gap-1">
                              <svg
                                className="w-3 h-3"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                                />
                              </svg>
                              Locked
                            </span>
                          )}
                        </div>

                        {/* Preview */}
                        <p className="text-sm text-slate-400 line-clamp-2 mb-2">
                          {getPreview(note.content_text)}
                        </p>

                        {/* Meta */}
                        <div className="flex items-center gap-4 text-xs text-slate-500">
                          <span>{formatDate(note.created_at)}</span>
                          {note.version_count > 1 && (
                            <span>v{note.current_version}</span>
                          )}
                          {note.attachment_count > 0 && (
                            <span className="flex items-center gap-1">
                              <svg
                                className="w-3 h-3"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
                                />
                              </svg>
                              {note.attachment_count}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Arrow */}
                      <svg
                        className="w-5 h-5 text-slate-500 flex-shrink-0"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 5l7 7-7 7"
                        />
                      </svg>
                    </div>
                  </Link>
                ))}
              </div>
            )}

            {/* Pagination */}
            {data.total_pages > 1 && (
              <div className="flex items-center justify-between mt-6">
                <p className="text-sm text-slate-400">
                  Showing {(page - 1) * 20 + 1} to {Math.min(page * 20, data.total)} of{' '}
                  {data.total}
                </p>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-3 py-1 bg-slate-800 text-slate-300 rounded hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Previous
                  </button>
                  <span className="px-3 py-1 text-slate-400">
                    Page {page} of {data.total_pages}
                  </span>
                  <button
                    onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                    disabled={page === data.total_pages}
                    className="px-3 py-1 bg-slate-800 text-slate-300 rounded hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
