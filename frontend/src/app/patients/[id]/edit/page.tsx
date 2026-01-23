'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { getPatient, updatePatient, PatientUpdateInput } from '@/lib/api/patients';
import { ApiClientError } from '@/lib/api/client';

export default function EditPatientPage() {
  const { data: session } = useSession();
  const params = useParams();
  const router = useRouter();
  const patientId = Number(params.id);

  const [formData, setFormData] = useState<PatientUpdateInput>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [initialized, setInitialized] = useState(false);

  // Fetch existing patient data
  const { data: patient, isLoading } = useQuery({
    queryKey: ['patient', patientId],
    queryFn: () => getPatient(session?.accessToken || '', patientId),
    enabled: !!session?.accessToken && !!patientId,
  });

  // Pre-populate form when patient data loads
  useEffect(() => {
    if (patient && !initialized) {
      setFormData({
        first_name: patient.first_name || '',
        last_name: patient.last_name || '',
        middle_name: patient.middle_name || '',
        gender: patient.gender,
        phone: patient.phone || '',
        email: patient.email || '',
        gesy_beneficiary_id: patient.gesy_beneficiary_id || '',
        referring_physician: patient.referring_physician || '',
      });
      setInitialized(true);
    }
  }, [patient, initialized]);

  // Update mutation
  const mutation = useMutation({
    mutationFn: (data: PatientUpdateInput) =>
      updatePatient(session?.accessToken || '', patientId, data),
    onSuccess: () => {
      router.push(`/patients/${patientId}`);
    },
    onError: (error: Error) => {
      const message = error instanceof ApiClientError ? error.detail : error.message;
      setErrors({ form: message });
    },
  });

  // Validation
  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (formData.first_name !== undefined && !formData.first_name.trim()) {
      newErrors.first_name = 'First name is required';
    }
    if (formData.last_name !== undefined && !formData.last_name.trim()) {
      newErrors.last_name = 'Last name is required';
    }
    if (formData.phone && !/^\+357\d{8}$/.test(formData.phone.replace(/[\s\-()]/g, ''))) {
      newErrors.phone = 'Phone must be in Cyprus format: +357 XX XXXXXX';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validate()) {
      // Only send fields that have changed
      const updates: PatientUpdateInput = {};
      if (formData.first_name !== patient?.first_name) updates.first_name = formData.first_name;
      if (formData.last_name !== patient?.last_name) updates.last_name = formData.last_name;
      if (formData.middle_name !== (patient?.middle_name || '')) updates.middle_name = formData.middle_name;
      if (formData.gender !== patient?.gender) updates.gender = formData.gender;
      if (formData.phone !== (patient?.phone || '')) updates.phone = formData.phone;
      if (formData.email !== (patient?.email || '')) updates.email = formData.email;
      if (formData.gesy_beneficiary_id !== (patient?.gesy_beneficiary_id || '')) updates.gesy_beneficiary_id = formData.gesy_beneficiary_id;
      if (formData.referring_physician !== (patient?.referring_physician || '')) updates.referring_physician = formData.referring_physician;

      if (Object.keys(updates).length === 0) {
        router.push(`/patients/${patientId}`);
        return;
      }

      mutation.mutate(updates);
    }
  };

  const updateField = (field: keyof PatientUpdateInput, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  if (!session) return null;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-2 border-rose-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!patient) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <p className="text-white text-lg">Patient not found</p>
          <Link href="/patients" className="text-rose-400 hover:text-rose-300 mt-2 inline-block">
            Back to Patients
          </Link>
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
              <h1 className="text-2xl font-bold text-white">Edit Patient</h1>
              <p className="text-sm text-slate-400">
                {patient.first_name} {patient.last_name} &bull; {patient.mrn}
              </p>
            </div>
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
            <h2 className="text-lg font-semibold text-white mb-4">Basic Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="first_name" className="block text-sm font-medium text-slate-300 mb-1">
                  First Name *
                </label>
                <input
                  type="text"
                  id="first_name"
                  value={formData.first_name || ''}
                  onChange={(e) => updateField('first_name', e.target.value)}
                  className={`w-full px-4 py-2 bg-slate-800 border rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-rose-500 ${
                    errors.first_name ? 'border-red-500' : 'border-slate-700'
                  }`}
                />
                {errors.first_name && (
                  <p className="mt-1 text-xs text-red-400">{errors.first_name}</p>
                )}
              </div>

              <div>
                <label htmlFor="last_name" className="block text-sm font-medium text-slate-300 mb-1">
                  Last Name *
                </label>
                <input
                  type="text"
                  id="last_name"
                  value={formData.last_name || ''}
                  onChange={(e) => updateField('last_name', e.target.value)}
                  className={`w-full px-4 py-2 bg-slate-800 border rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-rose-500 ${
                    errors.last_name ? 'border-red-500' : 'border-slate-700'
                  }`}
                />
                {errors.last_name && (
                  <p className="mt-1 text-xs text-red-400">{errors.last_name}</p>
                )}
              </div>

              <div>
                <label htmlFor="middle_name" className="block text-sm font-medium text-slate-300 mb-1">
                  Middle Name
                </label>
                <input
                  type="text"
                  id="middle_name"
                  value={formData.middle_name || ''}
                  onChange={(e) => updateField('middle_name', e.target.value)}
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-rose-500"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-slate-300 mb-2">Gender</label>
                <div className="flex flex-wrap gap-4">
                  {[
                    { value: 'male', label: 'Male' },
                    { value: 'female', label: 'Female' },
                    { value: 'other', label: 'Other' },
                    { value: 'unknown', label: 'Unknown' },
                  ].map((option) => (
                    <label key={option.value} className="flex items-center space-x-2 cursor-pointer">
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

          {/* Contact Information */}
          <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Contact Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="phone" className="block text-sm font-medium text-slate-300 mb-1">
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

              <div>
                <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-1">
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
            <h2 className="text-lg font-semibold text-white mb-4">Gesy & Referral</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="gesy_beneficiary_id" className="block text-sm font-medium text-slate-300 mb-1">
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

              <div>
                <label htmlFor="referring_physician" className="block text-sm font-medium text-slate-300 mb-1">
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
              href={`/patients/${patientId}`}
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
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Saving...
                </>
              ) : (
                'Save Changes'
              )}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
