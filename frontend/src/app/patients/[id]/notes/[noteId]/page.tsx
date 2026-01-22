'use client';

import { useState } from 'react';
import { useSession } from 'next-auth/react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  getNote,
  updateNote,
  lockNote,
  NoteUpdateInput,
  NoteVersion,
  getNoteTypeLabel,
  getNoteTypeColor,
} from '@/lib/api/notes';
import { getPatient } from '@/lib/api/patients';

/**
 * Note Detail Page.
 *
 * View, edit, and manage a clinical note with version history.
 */
export default function NoteDetailPage() {
  const { data: session } = useSession();
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const patientId = Number(params.id);
  const noteId = Number(params.noteId);

  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState('');
  const [editReason, setEditReason] = useState('');
  const [showVersions, setShowVersions] = useState(false);
  const [selectedVersion, setSelectedVersion] = useState<NoteVersion | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Fetch patient
  const { data: patient } = useQuery({
    queryKey: ['patient', patientId],
    queryFn: () => getPatient(session?.accessToken || '', patientId),
    enabled: !!session?.accessToken && !!patientId,
  });

  // Fetch note
  const { data: note, isLoading, error } = useQuery({
    queryKey: ['note', noteId],
    queryFn: () => getNote(session?.accessToken || '', noteId),
    enabled: !!session?.accessToken && !!noteId,
    onSuccess: (data) => {
      if (!isEditing && !editContent) {
        setEditContent(data.content_text || '');
      }
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data: NoteUpdateInput) =>
      updateNote(session?.accessToken || '', noteId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['note', noteId] });
      setIsEditing(false);
      setEditReason('');
    },
    onError: (error: Error) => {
      setErrors({ form: error.message });
    },
  });

  // Lock mutation
  const lockMutation = useMutation({
    mutationFn: (reason: string) => lockNote(session?.accessToken || '', noteId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['note', noteId] });
    },
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

  // Start editing
  const startEditing = () => {
    setEditContent(note?.content_text || '');
    setIsEditing(true);
    setErrors({});
  };

  // Save edit
  const saveEdit = () => {
    if (!editContent.trim()) {
      setErrors({ content: 'Content is required' });
      return;
    }
    if (!editReason.trim() || editReason.length < 3) {
      setErrors({ reason: 'Edit reason is required (min 3 characters)' });
      return;
    }

    updateMutation.mutate({
      content_text: editContent,
      edit_reason: editReason,
    });
  };

  // Handle lock
  const handleLock = () => {
    const reason = prompt('Enter reason for locking this note:');
    if (reason && reason.length >= 3) {
      lockMutation.mutate(reason);
    }
  };

  // View specific version
  const viewVersion = (version: NoteVersion) => {
    setSelectedVersion(version);
  };

  if (!session) {
    return null;
  }

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <div className="bg-slate-900 border-b border-slate-800">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link
                href={`/patients/${patientId}/notes`}
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
                <h1 className="text-xl font-bold text-white">
                  {note?.title || 'Clinical Note'}
                </h1>
                {patient && (
                  <p className="text-sm text-slate-400">
                    {patient.first_name} {patient.last_name} • {patient.mrn}
                  </p>
                )}
              </div>
            </div>

            {note && !note.is_locked && !isEditing && (
              <div className="flex items-center space-x-2">
                <button
                  onClick={startEditing}
                  className="px-4 py-2 bg-slate-800 text-white rounded-lg hover:bg-slate-700 transition-colors"
                >
                  Edit
                </button>
                <button
                  onClick={handleLock}
                  className="px-4 py-2 bg-amber-600/20 text-amber-400 rounded-lg hover:bg-amber-600/30 transition-colors"
                >
                  Lock
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Error State */}
        {error && (
          <div className="bg-red-900/20 border border-red-800 rounded-lg p-4 mb-6">
            <p className="text-red-400">Failed to load note. Please try again.</p>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-rose-500"></div>
          </div>
        )}

        {/* Note Content */}
        {!isLoading && note && (
          <div className="space-y-6">
            {/* Metadata Bar */}
            <div className="flex flex-wrap items-center gap-3">
              <span className={`px-2 py-1 text-xs rounded ${getNoteTypeColor(note.note_type)}`}>
                {getNoteTypeLabel(note.note_type)}
              </span>
              <span className="text-sm text-slate-400">
                Created {formatDate(note.created_at)}
              </span>
              {note.version_count > 1 && (
                <button
                  onClick={() => setShowVersions(!showVersions)}
                  className="text-sm text-rose-400 hover:text-rose-300"
                >
                  v{note.current_version} ({note.version_count} versions)
                </button>
              )}
              {note.is_locked && (
                <span className="flex items-center gap-1 px-2 py-1 text-xs bg-amber-500/20 text-amber-300 rounded">
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                    />
                  </svg>
                  Locked: {note.locked_reason}
                </span>
              )}
            </div>

            {/* Version History Panel */}
            {showVersions && (
              <div className="bg-slate-900 rounded-lg border border-slate-800 p-4">
                <h3 className="text-sm font-medium text-white mb-3">Version History</h3>
                <div className="space-y-2">
                  {note.versions.map((version) => (
                    <button
                      key={version.version_id}
                      onClick={() => viewVersion(version)}
                      className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                        selectedVersion?.version_id === version.version_id
                          ? 'bg-rose-900/20 border border-rose-800'
                          : 'bg-slate-800 hover:bg-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-white">
                          Version {version.version_number}
                        </span>
                        <span className="text-xs text-slate-400">
                          {formatDate(version.created_at)}
                        </span>
                      </div>
                      {version.edit_reason && (
                        <p className="text-xs text-slate-400 mt-1">
                          {version.edit_reason}
                        </p>
                      )}
                    </button>
                  ))}
                </div>
                {selectedVersion && (
                  <button
                    onClick={() => setSelectedVersion(null)}
                    className="mt-3 text-sm text-rose-400 hover:text-rose-300"
                  >
                    View current version
                  </button>
                )}
              </div>
            )}

            {/* Edit Form */}
            {isEditing && (
              <div className="bg-slate-900 rounded-lg border border-slate-800 p-6 space-y-4">
                {errors.form && (
                  <div className="bg-red-900/20 border border-red-800 rounded-lg p-3">
                    <p className="text-sm text-red-400">{errors.form}</p>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Content
                  </label>
                  <textarea
                    rows={15}
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    className={`w-full px-4 py-2 bg-slate-800 border rounded-lg text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-rose-500 ${
                      errors.content ? 'border-red-500' : 'border-slate-700'
                    }`}
                  />
                  {errors.content && (
                    <p className="mt-1 text-xs text-red-400">{errors.content}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Reason for Edit *
                  </label>
                  <input
                    type="text"
                    value={editReason}
                    onChange={(e) => setEditReason(e.target.value)}
                    className={`w-full px-4 py-2 bg-slate-800 border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-rose-500 ${
                      errors.reason ? 'border-red-500' : 'border-slate-700'
                    }`}
                    placeholder="e.g., Corrected medication dosage"
                  />
                  {errors.reason && (
                    <p className="mt-1 text-xs text-red-400">{errors.reason}</p>
                  )}
                </div>

                <div className="flex items-center justify-end space-x-3">
                  <button
                    onClick={() => {
                      setIsEditing(false);
                      setErrors({});
                    }}
                    className="px-4 py-2 text-slate-300 hover:text-white transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={saveEdit}
                    disabled={updateMutation.isPending}
                    className="px-6 py-2 bg-rose-600 text-white rounded-lg hover:bg-rose-700 disabled:opacity-50 transition-colors"
                  >
                    {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </div>
            )}

            {/* Note Content Display */}
            {!isEditing && (
              <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
                <div className="prose prose-invert prose-sm max-w-none">
                  <pre className="whitespace-pre-wrap font-sans text-slate-200 text-sm leading-relaxed">
                    {selectedVersion?.content_text || note.content_text}
                  </pre>
                </div>
              </div>
            )}

            {/* Attachments */}
            {note.attachments.length > 0 && (
              <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
                <h3 className="text-sm font-medium text-white mb-3">
                  Attachments ({note.attachments.length})
                </h3>
                <div className="space-y-2">
                  {note.attachments.map((attachment) => (
                    <div
                      key={attachment.attachment_id}
                      className="flex items-center justify-between px-3 py-2 bg-slate-800 rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <svg
                          className="w-5 h-5 text-slate-400"
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
                        <div>
                          <p className="text-sm text-white">
                            {attachment.original_file_name}
                          </p>
                          <p className="text-xs text-slate-400">
                            {(attachment.file_size_bytes / 1024).toFixed(1)} KB •{' '}
                            {attachment.file_type}
                          </p>
                        </div>
                      </div>
                      <button className="text-sm text-rose-400 hover:text-rose-300">
                        Download
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
