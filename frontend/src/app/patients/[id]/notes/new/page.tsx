'use client';

import { useState } from 'react';
import { useSession } from 'next-auth/react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  createNote,
  NoteCreateInput,
  NoteType,
  getNoteTypeLabel,
  SOAPContent,
  uploadAttachment,
} from '@/lib/api/notes';
import { getPatient } from '@/lib/api/patients';
import { ApiClientError } from '@/lib/api/client';
import { Paperclip, X } from 'lucide-react';

/**
 * New Clinical Note Page.
 *
 * Supports multiple note types including structured SOAP format.
 */
export default function NewNotePage() {
  const { data: session } = useSession();
  const params = useParams();
  const router = useRouter();
  const patientId = Number(params.id);

  // Form state
  const [noteType, setNoteType] = useState<NoteType>('soap');
  const [title, setTitle] = useState('');
  const [freeTextContent, setFreeTextContent] = useState('');
  const [soapContent, setSoapContent] = useState<SOAPContent>({
    subjective: '',
    objective: '',
    assessment: '',
    plan: '',
  });
  const [attachments, setAttachments] = useState<File[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [uploading, setUploading] = useState(false);

  // Fetch patient
  const { data: patient } = useQuery({
    queryKey: ['patient', patientId],
    queryFn: () => getPatient(session?.accessToken || '', patientId),
    enabled: !!session?.accessToken && !!patientId,
  });

  // Create mutation
  const mutation = useMutation({
    mutationFn: async (data: NoteCreateInput) => {
      const note = await createNote(session?.accessToken || '', data);

      // Upload attachments if any
      if (attachments.length > 0) {
        setUploading(true);
        try {
          await Promise.all(
            attachments.map((file) =>
              uploadAttachment(session?.accessToken || '', note.note_id, file)
            )
          );
        } catch (err) {
          console.error('Failed to upload attachments:', err);
          // We don't fail the whole creation, just log it. 
          // Ideally we'd show a toast warning that attachments failed.
        } finally {
          setUploading(false);
        }
      }
      return note;
    },
    onSuccess: (note) => {
      router.push(`/patients/${patientId}/notes/${note.note_id}`);
    },
    onError: (error: Error) => {
      const message = error instanceof ApiClientError ? error.detail : error.message;
      setErrors({ form: message });
      setUploading(false);
    },
  });

  // Validation
  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!title.trim()) {
      newErrors.title = 'Title is required';
    }

    if (noteType === 'soap') {
      if (!soapContent.assessment.trim()) {
        newErrors.assessment = 'Assessment is required';
      }
    } else {
      if (!freeTextContent.trim()) {
        newErrors.content = 'Content is required';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Build content text from SOAP
  const buildSOAPText = (): string => {
    let text = '';
    if (soapContent.subjective) {
      text += `## Subjective\n${soapContent.subjective}\n\n`;
    }
    if (soapContent.objective) {
      text += `## Objective\n${soapContent.objective}\n\n`;
    }
    if (soapContent.assessment) {
      text += `## Assessment\n${soapContent.assessment}\n\n`;
    }
    if (soapContent.plan) {
      text += `## Plan\n${soapContent.plan}\n`;
    }
    return text.trim();
  };

  // Handle submit
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    const data: NoteCreateInput = {
      patient_id: patientId,
      note_type: noteType,
      title: title.trim(),
      content_text: noteType === 'soap' ? buildSOAPText() : freeTextContent,
      structured_data: noteType === 'soap' ? soapContent : undefined,
    };

    mutation.mutate(data);
  };

  // Note type options
  const noteTypes: { value: NoteType; label: string; description: string }[] = [
    { value: 'soap', label: 'SOAP Note', description: 'Structured clinical note' },
    { value: 'free_text', label: 'Free Text', description: 'Unstructured narrative' },
    { value: 'progress', label: 'Progress Note', description: 'Follow-up documentation' },
    { value: 'procedure', label: 'Procedure', description: 'Intervention documentation' },
    { value: 'consultation', label: 'Consultation', description: 'Specialist consultation' },
    { value: 'discharge', label: 'Discharge', description: 'Discharge summary' },
  ];

  if (!session) {
    return null;
  }

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <div className="bg-slate-900 border-b border-slate-800">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
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
              <h1 className="text-2xl font-bold text-white">New Clinical Note</h1>
              {patient && (
                <p className="text-sm text-slate-400">
                  {patient.first_name} {patient.last_name} • {patient.mrn}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Error Alert */}
          {errors.form && (
            <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
              <p className="text-red-400">{errors.form}</p>
            </div>
          )}

          {/* Note Type Selection */}
          <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Note Type</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {noteTypes.map((type) => (
                <button
                  key={type.value}
                  type="button"
                  onClick={() => setNoteType(type.value)}
                  className={`p-3 rounded-lg border text-left transition-all ${noteType === type.value
                    ? 'border-rose-500 bg-rose-900/20'
                    : 'border-slate-700 bg-slate-800/50 hover:border-slate-600'
                    }`}
                >
                  <p className="text-sm font-medium text-white">{type.label}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{type.description}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Title */}
          <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
            <label
              htmlFor="title"
              className="block text-sm font-medium text-slate-300 mb-2"
            >
              Title *
            </label>
            <input
              type="text"
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className={`w-full px-4 py-2 bg-slate-800 border rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-rose-500 ${errors.title ? 'border-red-500' : 'border-slate-700'
                }`}
              placeholder="e.g., Follow-up Visit - CHF Management"
            />
            {errors.title && (
              <p className="mt-1 text-xs text-red-400">{errors.title}</p>
            )}
          </div>

          {/* Content - SOAP Format */}
          {noteType === 'soap' && (
            <div className="bg-slate-900 rounded-lg border border-slate-800 p-6 space-y-4">
              <h2 className="text-lg font-semibold text-white">SOAP Content</h2>

              {/* Subjective */}
              <div>
                <label
                  htmlFor="subjective"
                  className="block text-sm font-medium text-slate-300 mb-1"
                >
                  <span className="text-blue-400 font-bold">S</span>ubjective
                </label>
                <p className="text-xs text-slate-500 mb-2">
                  Chief complaint, history of present illness, patient symptoms
                </p>
                <textarea
                  id="subjective"
                  rows={4}
                  value={soapContent.subjective}
                  onChange={(e) =>
                    setSoapContent((prev) => ({ ...prev, subjective: e.target.value }))
                  }
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-rose-500"
                  placeholder="Patient reports..."
                />
              </div>

              {/* Objective */}
              <div>
                <label
                  htmlFor="objective"
                  className="block text-sm font-medium text-slate-300 mb-1"
                >
                  <span className="text-teal-400 font-bold">O</span>bjective
                </label>
                <p className="text-xs text-slate-500 mb-2">
                  Physical exam findings, vitals, test results
                </p>
                <textarea
                  id="objective"
                  rows={4}
                  value={soapContent.objective}
                  onChange={(e) =>
                    setSoapContent((prev) => ({ ...prev, objective: e.target.value }))
                  }
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-rose-500"
                  placeholder="BP 130/80, HR 72 regular..."
                />
              </div>

              {/* Assessment */}
              <div>
                <label
                  htmlFor="assessment"
                  className="block text-sm font-medium text-slate-300 mb-1"
                >
                  <span className="text-amber-400 font-bold">A</span>ssessment *
                </label>
                <p className="text-xs text-slate-500 mb-2">
                  Diagnosis, clinical impression, problem list
                </p>
                <textarea
                  id="assessment"
                  rows={4}
                  value={soapContent.assessment}
                  onChange={(e) =>
                    setSoapContent((prev) => ({ ...prev, assessment: e.target.value }))
                  }
                  className={`w-full px-4 py-2 bg-slate-800 border rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-rose-500 ${errors.assessment ? 'border-red-500' : 'border-slate-700'
                    }`}
                  placeholder="1. CHF NYHA Class II - stable on current therapy..."
                />
                {errors.assessment && (
                  <p className="mt-1 text-xs text-red-400">{errors.assessment}</p>
                )}
              </div>

              {/* Plan */}
              <div>
                <label
                  htmlFor="plan"
                  className="block text-sm font-medium text-slate-300 mb-1"
                >
                  <span className="text-purple-400 font-bold">P</span>lan
                </label>
                <p className="text-xs text-slate-500 mb-2">
                  Treatment plan, medications, follow-up instructions
                </p>
                <textarea
                  id="plan"
                  rows={4}
                  value={soapContent.plan}
                  onChange={(e) =>
                    setSoapContent((prev) => ({ ...prev, plan: e.target.value }))
                  }
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-rose-500"
                  placeholder="1. Continue current medications&#10;2. Echo in 3 months&#10;3. Follow up in 6 weeks"
                />
              </div>
            </div>
          )}

          {/* Content - Free Text */}
          {noteType !== 'soap' && (
            <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
              <label
                htmlFor="content"
                className="block text-sm font-medium text-slate-300 mb-2"
              >
                Content *
              </label>
              <p className="text-xs text-slate-500 mb-2">
                Supports Markdown formatting
              </p>
              <textarea
                id="content"
                rows={12}
                value={freeTextContent}
                onChange={(e) => setFreeTextContent(e.target.value)}
                className={`w-full px-4 py-2 bg-slate-800 border rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-rose-500 font-mono text-sm ${errors.content ? 'border-red-500' : 'border-slate-700'
                  }`}
                placeholder="Enter clinical note content..."
              />
              {errors.content && (
                <p className="mt-1 text-xs text-red-400">{errors.content}</p>
              )}
            </div>
          )}

          {/* Attachments */}
          <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Attachments
            </label>
            <p className="text-xs text-slate-500 mb-4">
              Add relevant documents (PDF, DOCX, Images). Max 10MB per file.
            </p>

            <div className="space-y-3">
              {/* File List */}
              {attachments.length > 0 && (
                <div className="space-y-2 mb-4">
                  {attachments.map((file, index) => (
                    <div
                      key={`${file.name}-${index}`}
                      className="flex items-center justify-between p-2 bg-slate-800 rounded border border-slate-700"
                    >
                      <div className="flex items-center space-x-2 truncate">
                        <Paperclip className="w-4 h-4 text-slate-400 flex-shrink-0" />
                        <span className="text-sm text-slate-200 truncate">{file.name}</span>
                        <span className="text-xs text-slate-500 flex-shrink-0">
                          ({(file.size / 1024 / 1024).toFixed(2)} MB)
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => setAttachments(prev => prev.filter((_, i) => i !== index))}
                        className="text-slate-400 hover:text-rose-400 transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Upload Button */}
              <div className="relative">
                <input
                  type="file"
                  id="file-upload"
                  multiple
                  className="hidden"
                  onChange={(e) => {
                    if (e.target.files) {
                      setAttachments(prev => [...prev, ...Array.from(e.target.files || [])]);
                    }
                    // Reset input so same file can be selected again if deleted
                    e.target.value = '';
                  }}
                />
                <label
                  htmlFor="file-upload"
                  className="flex flex-col items-center justify-center w-full h-32 border-2 border-slate-700 border-dashed rounded-lg cursor-pointer bg-slate-800/30 hover:bg-slate-800/50 hover:border-slate-600 transition-all"
                >
                  <div className="flex flex-col items-center justify-center pt-5 pb-6">
                    <Paperclip className="w-8 h-8 text-slate-500 mb-2" />
                    <p className="text-sm text-slate-400">
                      <span className="font-semibold">Click to upload</span> or drag and drop
                    </p>
                    <p className="text-xs text-slate-500">PDF, DOCX, PNG, JPG</p>
                  </div>
                </label>
              </div>
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex items-center justify-end space-x-4">
            <Link
              href={`/patients/${patientId}/notes`}
              className="px-4 py-2 text-slate-300 hover:text-white transition-colors"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={mutation.isPending}
              className="px-6 py-2 bg-rose-600 text-white rounded-lg hover:bg-rose-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
            >
              {mutation.isPending ? (
                <>
                  <svg
                    className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                  {uploading ? 'Uploading Files...' : 'Saving...'}
                </>
              ) : (
                'Save Note'
              )}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
