'use client';

import { useState } from 'react';
import { useSession } from 'next-auth/react';
import { useMutation } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { createPatient, PatientCreateInput } from '@/lib/api/patients';

/**
 * New Patient Form Page.
 *
 * Multi-step form for registering a new patient with:
 * - Basic demographics
 * - Cyprus identifiers (ID/ARC)
 * - Contact information
 * - Optional Gesy details
 */
export default function NewPatientPage() {
  const { data: session } = useSession();
  const router = useRouter();

  // Form state
  const [formData, setFormData] = useState<PatientCreateInput>({
    first_name: '',
    last_name: '',
    birth_date: '',
    gender: 'unknown',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Create mutation
  const mutation = useMutation({
    mutationFn: (data: PatientCreateInput) =>
      createPatient(session?.accessToken || '', data),
    onSuccess: (patient) => {
      router.push(`/patients/${patient.patient_id}`);
    },
    onError: (error: Error) => {
      setErrors({ form: error.message });
    },
  });

  // Form validation
  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.first_name.trim()) {
      newErrors.first_name = 'First name is required';
    }
    if (!formData.last_name.trim()) {
      newErrors.last_name = 'Last name is required';
    }
    if (!formData.birth_date) {
      newErrors.birth_date = 'Date of birth is required';
    }

    // Phone validation (Cyprus format)
    if (formData.phone && !/^\+357\d{8}$/.test(formData.phone.replace(/[\s\-()]/g, ''))) {
      newErrors.phone = 'Phone must be in Cyprus format: +357 XX XXXXXX';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submit
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validate()) {
      mutation.mutate(formData);
    }
  };

  // Update form field
  const updateField = (field: keyof PatientCreateInput, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  if (!session) {
    return null;
  }

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <div className="bg-slate-900 border-b border-slate-800">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center space-x-4">
            <Link
              href="/patients"
              className="text-slate-400 hover:text-slate-200 transition-colors"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10 19l-7-7m0 0l7-7m-7 7h18"
                />
              </svg>
            </Link>
            <h1 className="text-2xl font-bold text-white">New Patient</h1>
          </div>
        </div>
      </div>

      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Error Alert */}
          {errors.form && (
            <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
              <p className="text-red-400">{errors.form}</p>
            </div>
          )}

          {/* Basic Information */}
          <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
            <h2 className="text-lg font-semibold text-white mb-4">
              Basic Information
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* First Name */}
              <div>
                <label
                  htmlFor="first_name"
                  className="block text-sm font-medium text-slate-300 mb-1"
                >
                  First Name *
                </label>
                <input
                  type="text"
                  id="first_name"
                  value={formData.first_name}
                  onChange={(e) => updateField('first_name', e.target.value)}
                  className={`w-full px-4 py-2 bg-slate-800 border rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-rose-500 ${
                    errors.first_name ? 'border-red-500' : 'border-slate-700'
                  }`}
                  placeholder="Γιώργος / George"
                />
                {errors.first_name && (
                  <p className="mt-1 text-xs text-red-400">{errors.first_name}</p>
                )}
              </div>

              {/* Last Name */}
              <div>
                <label
                  htmlFor="last_name"
                  className="block text-sm font-medium text-slate-300 mb-1"
                >
                  Last Name *
                </label>
                <input
                  type="text"
                  id="last_name"
                  value={formData.last_name}
                  onChange={(e) => updateField('last_name', e.target.value)}
                  className={`w-full px-4 py-2 bg-slate-800 border rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-rose-500 ${
                    errors.last_name ? 'border-red-500' : 'border-slate-700'
                  }`}
                  placeholder="Παπαδόπουλος / Papadopoulos"
                />
                {errors.last_name && (
                  <p className="mt-1 text-xs text-red-400">{errors.last_name}</p>
                )}
              </div>

              {/* Middle Name (optional) */}
              <div>
                <label
                  htmlFor="middle_name"
                  className="block text-sm font-medium text-slate-300 mb-1"
                >
                  Middle Name
                </label>
                <input
                  type="text"
                  id="middle_name"
                  value={formData.middle_name || ''}
                  onChange={(e) => updateField('middle_name', e.target.value)}
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-rose-500"
                  placeholder="Optional"
                />
              </div>

              {/* Date of Birth */}
              <div>
                <label
                  htmlFor="birth_date"
                  className="block text-sm font-medium text-slate-300 mb-1"
                >
                  Date of Birth *
                </label>
                <input
                  type="date"
                  id="birth_date"
                  value={formData.birth_date}
                  onChange={(e) => updateField('birth_date', e.target.value)}
                  className={`w-full px-4 py-2 bg-slate-800 border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-rose-500 ${
                    errors.birth_date ? 'border-red-500' : 'border-slate-700'
                  }`}
                />
                {errors.birth_date && (
                  <p className="mt-1 text-xs text-red-400">{errors.birth_date}</p>
                )}
              </div>

              {/* Gender */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Gender
                </label>
                <div className="flex flex-wrap gap-4">
                  {[
                    { value: 'male', label: 'Male' },
                    { value: 'female', label: 'Female' },
                    { value: 'other', label: 'Other' },
                    { value: 'unknown', label: 'Unknown' },
                  ].map((option) => (
                    <label
                      key={option.value}
                      className="flex items-center space-x-2 cursor-pointer"
                    >
                      <input
                        type="radio"
                        name="gender"
                        value={option.value}
                        checked={formData.gender === option.value}
                        onChange={(e) => updateField('gender', e.target.value)}
                        className="w-4 h-4 text-rose-600 bg-slate-800 border-slate-600 focus:ring-rose-500"
                      />
                      <span className="text-slate-300">{option.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Cyprus Identifiers */}
          <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
            <h2 className="text-lg font-semibold text-white mb-4">
              Cyprus Identifiers
            </h2>
            <p className="text-sm text-slate-400 mb-4">
              Provide at least one identifier (Cyprus ID or ARC)
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Cyprus ID */}
              <div>
                <label
                  htmlFor="cyprus_id"
                  className="block text-sm font-medium text-slate-300 mb-1"
                >
                  Cyprus ID Card
                </label>
                <input
                  type="text"
                  id="cyprus_id"
                  value={formData.cyprus_id || ''}
                  onChange={(e) => updateField('cyprus_id', e.target.value.toUpperCase())}
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-rose-500 font-mono"
                  placeholder="1234567"
                  maxLength={10}
                />
              </div>

              {/* ARC Number */}
              <div>
                <label
                  htmlFor="arc_number"
                  className="block text-sm font-medium text-slate-300 mb-1"
                >
                  ARC Number (Non-citizens)
                </label>
                <input
                  type="text"
                  id="arc_number"
                  value={formData.arc_number || ''}
                  onChange={(e) => updateField('arc_number', e.target.value.toUpperCase())}
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-rose-500 font-mono"
                  placeholder="ARC number"
                />
              </div>
            </div>
          </div>

          {/* Contact Information */}
          <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
            <h2 className="text-lg font-semibold text-white mb-4">
              Contact Information
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Phone */}
              <div>
                <label
                  htmlFor="phone"
                  className="block text-sm font-medium text-slate-300 mb-1"
                >
                  Mobile Phone
                </label>
                <input
                  type="tel"
                  id="phone"
                  value={formData.phone || ''}
                  onChange={(e) => updateField('phone', e.target.value)}
                  className={`w-full px-4 py-2 bg-slate-800 border rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-rose-500 ${
                    errors.phone ? 'border-red-500' : 'border-slate-700'
                  }`}
                  placeholder="+357 99 123456"
                />
                {errors.phone && (
                  <p className="mt-1 text-xs text-red-400">{errors.phone}</p>
                )}
              </div>

              {/* Email */}
              <div>
                <label
                  htmlFor="email"
                  className="block text-sm font-medium text-slate-300 mb-1"
                >
                  Email
                </label>
                <input
                  type="email"
                  id="email"
                  value={formData.email || ''}
                  onChange={(e) => updateField('email', e.target.value)}
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-rose-500"
                  placeholder="patient@example.com"
                />
              </div>
            </div>
          </div>

          {/* Gesy & Referral */}
          <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
            <h2 className="text-lg font-semibold text-white mb-4">
              Gesy & Referral
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Gesy Beneficiary ID */}
              <div>
                <label
                  htmlFor="gesy_beneficiary_id"
                  className="block text-sm font-medium text-slate-300 mb-1"
                >
                  Gesy Beneficiary ID
                </label>
                <input
                  type="text"
                  id="gesy_beneficiary_id"
                  value={formData.gesy_beneficiary_id || ''}
                  onChange={(e) => updateField('gesy_beneficiary_id', e.target.value)}
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-rose-500 font-mono"
                  placeholder="GHS number"
                />
              </div>

              {/* Referring Physician */}
              <div>
                <label
                  htmlFor="referring_physician"
                  className="block text-sm font-medium text-slate-300 mb-1"
                >
                  Referring Physician
                </label>
                <input
                  type="text"
                  id="referring_physician"
                  value={formData.referring_physician || ''}
                  onChange={(e) => updateField('referring_physician', e.target.value)}
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-rose-500"
                  placeholder="Dr. Name / Personal Doctor"
                />
              </div>
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex items-center justify-end space-x-4">
            <Link
              href="/patients"
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
                  Creating...
                </>
              ) : (
                'Create Patient'
              )}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
