'use client';

import { useState } from 'react';
import { useSession } from 'next-auth/react';
import { useMutation } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { createInvitation, ROLE_LABELS, InvitationCreateData } from '@/lib/api/auth';

/**
 * Invite User Form Page.
 *
 * Allows admins to create new user invitations.
 */
export default function InviteUserPage() {
  const { data: session } = useSession();
  const router = useRouter();

  const [formData, setFormData] = useState<InvitationCreateData>({
    email: '',
    first_name: '',
    last_name: '',
    role: 'nurse',
    clinic_id: session?.user?.clinicId || 1,
    title: '',
    specialty: '',
    license_number: '',
    message: '',
  });

  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  // Create invitation mutation
  const mutation = useMutation({
    mutationFn: () => createInvitation(session?.accessToken || '', formData),
    onSuccess: () => {
      setSuccess(true);
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    mutation.mutate();
  };

  const updateField = <K extends keyof InvitationCreateData>(
    field: K,
    value: InvitationCreateData[K]
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  if (!session) {
    return null;
  }

  // Success state
  if (success) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-slate-900 rounded-xl border border-slate-800 p-8 text-center">
          <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg
              className="w-8 h-8 text-green-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">Invitation Sent!</h1>
          <p className="text-slate-400 mb-6">
            An invitation email has been sent to {formData.email}. They will have 7 days to accept
            the invitation.
          </p>
          <div className="flex gap-3">
            <button
              onClick={() => {
                setSuccess(false);
                setFormData({
                  ...formData,
                  email: '',
                  first_name: '',
                  last_name: '',
                  title: '',
                  specialty: '',
                  license_number: '',
                  message: '',
                });
              }}
              className="flex-1 py-3 bg-slate-800 text-slate-300 rounded-lg font-medium hover:bg-slate-700 transition-colors"
            >
              Invite Another
            </button>
            <Link
              href="/admin/users"
              className="flex-1 py-3 bg-rose-600 text-white rounded-lg font-medium hover:bg-rose-700 transition-colors text-center"
            >
              View Invitations
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <div className="bg-slate-900 border-b border-slate-800">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center space-x-4">
            <Link
              href="/admin/users"
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
              <h1 className="text-2xl font-bold text-white">Invite User</h1>
              <p className="text-sm text-slate-400">Send an invitation to join your clinic</p>
            </div>
          </div>
        </div>
      </div>

      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Info */}
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Basic Information</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">
                  First Name <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  value={formData.first_name}
                  onChange={(e) => updateField('first_name', e.target.value)}
                  required
                  className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:border-rose-500"
                  placeholder="John"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">
                  Last Name <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  value={formData.last_name}
                  onChange={(e) => updateField('last_name', e.target.value)}
                  required
                  className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:border-rose-500"
                  placeholder="Smith"
                />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-slate-300 mb-1.5">
                  Email Address <span className="text-rose-400">*</span>
                </label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => updateField('email', e.target.value)}
                  required
                  className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:border-rose-500"
                  placeholder="john.smith@example.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">
                  Role <span className="text-rose-400">*</span>
                </label>
                <select
                  value={formData.role}
                  onChange={(e) => updateField('role', e.target.value)}
                  className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-rose-500"
                >
                  {Object.entries(ROLE_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">
                  Title
                </label>
                <select
                  value={formData.title || ''}
                  onChange={(e) => updateField('title', e.target.value || undefined)}
                  className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-rose-500"
                >
                  <option value="">None</option>
                  <option value="Dr.">Dr.</option>
                  <option value="Prof.">Prof.</option>
                  <option value="Mr.">Mr.</option>
                  <option value="Ms.">Ms.</option>
                  <option value="Mrs.">Mrs.</option>
                </select>
              </div>
            </div>
          </div>

          {/* Professional Info */}
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Professional Information</h2>
            <p className="text-sm text-slate-400 mb-4">
              Optional details for healthcare professionals
            </p>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">
                  Specialty
                </label>
                <input
                  type="text"
                  value={formData.specialty || ''}
                  onChange={(e) => updateField('specialty', e.target.value || undefined)}
                  className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:border-rose-500"
                  placeholder="e.g., Interventional Cardiology"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">
                  License Number
                </label>
                <input
                  type="text"
                  value={formData.license_number || ''}
                  onChange={(e) => updateField('license_number', e.target.value || undefined)}
                  className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:border-rose-500"
                  placeholder="Medical license number"
                />
              </div>
            </div>
          </div>

          {/* Personal Message */}
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Personal Message</h2>
            <p className="text-sm text-slate-400 mb-4">
              Optional message to include in the invitation email
            </p>
            <textarea
              value={formData.message || ''}
              onChange={(e) => updateField('message', e.target.value || undefined)}
              rows={3}
              maxLength={500}
              className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:border-rose-500 resize-none"
              placeholder="Welcome to our team! We're excited to have you..."
            />
            <p className="text-xs text-slate-500 mt-1">
              {(formData.message || '').length}/500 characters
            </p>
          </div>

          {/* Error */}
          {error && (
            <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-4">
              <p className="text-sm text-rose-400">{error}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <Link
              href="/admin/users"
              className="flex-1 py-3 bg-slate-800 text-slate-300 rounded-lg font-medium hover:bg-slate-700 transition-colors text-center"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={mutation.isPending}
              className="flex-1 py-3 bg-rose-600 text-white rounded-lg font-medium hover:bg-rose-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {mutation.isPending ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Sending...
                </span>
              ) : (
                'Send Invitation'
              )}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
