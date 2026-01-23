'use client';

import { useState, useEffect, useRef, Suspense } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import {
  ArrowLeft,
  Calendar,
  Clock,
  AlertTriangle,
  Loader2,
  CheckCircle,
  Search,
  X,
} from 'lucide-react';
import {
  createAppointment,
  EXPECTED_DURATIONS,
  type AppointmentType,
  type AppointmentCreateInput,
} from '@/lib/api/appointments';
import { searchPatients, type Patient } from '@/lib/api/patients';

const APPOINTMENT_TYPES: { value: AppointmentType; label: string }[] = [
  { value: 'consultation', label: 'Consultation' },
  { value: 'follow_up', label: 'Follow-up' },
  { value: 'echo', label: 'Echocardiogram' },
  { value: 'stress_test', label: 'Stress Test' },
  { value: 'holter', label: 'Holter Monitor' },
  { value: 'ecg', label: 'ECG' },
  { value: 'procedure', label: 'Procedure' },
  { value: 'pre_op', label: 'Pre-Op Assessment' },
];

function NewAppointmentContent() {
  const { data: session } = useSession();
  const router = useRouter();

  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Patient search state
  const [patientId, setPatientId] = useState('');
  const [patientSearch, setPatientSearch] = useState('');
  const [patientResults, setPatientResults] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Form state
  const [appointmentType, setAppointmentType] = useState<AppointmentType>('consultation');
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');
  const [duration, setDuration] = useState(20);
  const [reason, setReason] = useState('');
  const [location, setLocation] = useState('');
  const [notes, setNotes] = useState('');
  const [referralId, setReferralId] = useState('');

  // Duration warning
  const expectedDuration = EXPECTED_DURATIONS[appointmentType] || 30;
  const showDurationWarning = duration < Math.floor(expectedDuration * 0.75);

  // Debounced patient search
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (!patientSearch.trim() || !session?.accessToken) {
      setPatientResults([]);
      setShowResults(false);
      return;
    }

    searchTimeoutRef.current = setTimeout(async () => {
      try {
        setSearchLoading(true);
        const result = await searchPatients(session.accessToken, {
          q: patientSearch.trim(),
          page_size: 5,
        });
        setPatientResults(result.items);
        setShowResults(true);
      } catch {
        setPatientResults([]);
      } finally {
        setSearchLoading(false);
      }
    }, 300);

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [patientSearch, session?.accessToken]);

  function selectPatient(patient: Patient) {
    setSelectedPatient(patient);
    setPatientId(String(patient.patient_id));
    setPatientSearch('');
    setShowResults(false);
    setPatientResults([]);
  }

  function clearPatient() {
    setSelectedPatient(null);
    setPatientId('');
    setPatientSearch('');
  }

  function handleTypeChange(type: AppointmentType) {
    setAppointmentType(type);
    setDuration(EXPECTED_DURATIONS[type] || 30);
  }

  async function handleSubmit() {
    if (!session?.accessToken || !patientId || !date || !time) return;

    try {
      setSubmitting(true);
      setError(null);

      const startTime = new Date(`${date}T${time}:00`).toISOString();

      const data: AppointmentCreateInput = {
        patient_id: parseInt(patientId, 10),
        provider_id: parseInt(session.user.id, 10),
        start_time: startTime,
        duration_minutes: duration,
        appointment_type: appointmentType,
        reason: reason || undefined,
        notes: notes || undefined,
        location: location || undefined,
        gesy_referral_id: referralId || undefined,
      };

      await createAppointment(session.accessToken, data);
      setSuccess(true);
      setTimeout(() => router.push('/appointments'), 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create appointment');
    } finally {
      setSubmitting(false);
    }
  }

  if (!session) return null;

  if (success) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950">
        <div className="text-center">
          <CheckCircle className="mx-auto h-12 w-12 text-green-400" />
          <h2 className="mt-4 text-lg font-medium text-white">Appointment Created</h2>
          <p className="mt-1 text-slate-400">Redirecting to calendar...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 p-6">
      <div className="mx-auto max-w-2xl">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => router.back()}
            className="mb-4 flex items-center gap-2 text-sm text-slate-400 hover:text-white"
          >
            <ArrowLeft className="h-4 w-4" />
            Back
          </button>
          <h1 className="text-2xl font-bold text-white">New Appointment</h1>
          <p className="mt-1 text-sm text-slate-400">
            Schedule a new patient appointment
          </p>
        </div>

        {/* Step indicators */}
        <div className="mb-8 flex items-center gap-4">
          {[1, 2, 3].map((s) => (
            <div key={s} className="flex items-center gap-2">
              <div
                className={`h-8 w-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step === s
                    ? 'bg-teal-600 text-white'
                    : step > s
                      ? 'bg-teal-600/30 text-teal-400'
                      : 'bg-slate-800 text-slate-500'
                }`}
              >
                {step > s ? <CheckCircle className="h-4 w-4" /> : s}
              </div>
              <span className={`text-sm ${step >= s ? 'text-white' : 'text-slate-500'}`}>
                {s === 1 ? 'Type & Patient' : s === 2 ? 'Date & Time' : 'Details'}
              </span>
              {s < 3 && <div className="mx-2 h-px w-8 bg-slate-700" />}
            </div>
          ))}
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 flex items-center gap-3 rounded-lg border border-red-500/30 bg-red-500/10 p-4">
            <AlertTriangle className="h-5 w-5 text-red-400" />
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {/* Step 1: Type & Patient */}
        {step === 1 && (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Appointment Type
              </label>
              <div className="grid grid-cols-2 gap-2">
                {APPOINTMENT_TYPES.map((type) => (
                  <button
                    key={type.value}
                    onClick={() => handleTypeChange(type.value)}
                    className={`rounded-lg border p-3 text-left transition-colors ${
                      appointmentType === type.value
                        ? 'border-teal-500 bg-teal-500/10 text-white'
                        : 'border-white/10 bg-white/5 text-slate-300 hover:border-white/20'
                    }`}
                  >
                    <p className="text-sm font-medium">{type.label}</p>
                    <p className="text-xs text-slate-500">
                      ~{EXPECTED_DURATIONS[type.value]} min
                    </p>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Patient
              </label>
              {selectedPatient ? (
                <div className="flex items-center justify-between rounded-lg border border-teal-500/50 bg-teal-500/10 px-3 py-2">
                  <div>
                    <p className="text-sm font-medium text-white">
                      {selectedPatient.first_name} {selectedPatient.last_name}
                    </p>
                    <p className="text-xs text-slate-400">
                      MRN: {selectedPatient.mrn}
                      {selectedPatient.birth_date && ` • DOB: ${new Date(selectedPatient.birth_date).toLocaleDateString('en-GB')}`}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={clearPatient}
                    className="p-1 text-slate-400 hover:text-white"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ) : (
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    value={patientSearch}
                    onChange={(e) => setPatientSearch(e.target.value)}
                    placeholder="Search by name or MRN..."
                    className="w-full rounded-lg border border-white/10 bg-white/5 py-2 pl-9 pr-3 text-white placeholder-slate-500 focus:border-teal-500 focus:outline-none"
                  />
                  {searchLoading && (
                    <Loader2 className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-slate-400" />
                  )}
                  {showResults && patientResults.length > 0 && (
                    <div className="absolute z-10 mt-1 w-full rounded-lg border border-white/10 bg-slate-900 shadow-lg">
                      {patientResults.map((p) => (
                        <button
                          key={p.patient_id}
                          type="button"
                          onClick={() => selectPatient(p)}
                          className="w-full px-3 py-2 text-left hover:bg-white/5 first:rounded-t-lg last:rounded-b-lg"
                        >
                          <p className="text-sm font-medium text-white">
                            {p.first_name} {p.last_name}
                          </p>
                          <p className="text-xs text-slate-400">
                            MRN: {p.mrn}
                            {p.birth_date && ` • DOB: ${new Date(p.birth_date).toLocaleDateString('en-GB')}`}
                          </p>
                        </button>
                      ))}
                    </div>
                  )}
                  {showResults && patientResults.length === 0 && patientSearch.trim() && !searchLoading && (
                    <div className="absolute z-10 mt-1 w-full rounded-lg border border-white/10 bg-slate-900 p-3 text-center">
                      <p className="text-sm text-slate-400">No patients found</p>
                    </div>
                  )}
                </div>
              )}
            </div>

            <button
              onClick={() => setStep(2)}
              disabled={!patientId}
              className="w-full rounded-lg bg-teal-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-teal-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Next: Date & Time
            </button>
          </div>
        )}

        {/* Step 2: Date & Time */}
        {step === 2 && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  <Calendar className="inline h-4 w-4 mr-1" />
                  Date
                </label>
                <input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white focus:border-teal-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  <Clock className="inline h-4 w-4 mr-1" />
                  Time
                </label>
                <input
                  type="time"
                  value={time}
                  onChange={(e) => setTime(e.target.value)}
                  min="08:00"
                  max="17:00"
                  className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white focus:border-teal-500 focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Duration (minutes)
              </label>
              <input
                type="number"
                value={duration}
                onChange={(e) => setDuration(parseInt(e.target.value, 10) || 15)}
                min={5}
                max={480}
                className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white focus:border-teal-500 focus:outline-none"
              />

              {/* Duration warning */}
              {showDurationWarning && (
                <div className="mt-2 flex items-start gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3">
                  <AlertTriangle className="h-4 w-4 text-amber-400 mt-0.5 flex-shrink-0" />
                  <p className="text-sm text-amber-300">
                    {appointmentType.replace('_', ' ')} appointments typically require{' '}
                    <strong>{expectedDuration} minutes</strong>, but you&apos;ve scheduled{' '}
                    <strong>{duration} minutes</strong>. You can proceed, but consider
                    allowing more time.
                  </p>
                </div>
              )}
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setStep(1)}
                className="flex-1 rounded-lg border border-white/10 px-4 py-2.5 text-sm text-slate-300 hover:bg-white/5"
              >
                Back
              </button>
              <button
                onClick={() => setStep(3)}
                disabled={!date || !time}
                className="flex-1 rounded-lg bg-teal-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-teal-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Next: Details
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Details */}
        {step === 3 && (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Reason for Visit
              </label>
              <input
                type="text"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="e.g., Chest pain evaluation"
                className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white placeholder-slate-500 focus:border-teal-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Location
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g., Consultation Room 1"
                className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white placeholder-slate-500 focus:border-teal-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Gesy Referral ID (optional)
              </label>
              <input
                type="text"
                value={referralId}
                onChange={(e) => setReferralId(e.target.value)}
                placeholder="e.g., REF-CARD-001"
                className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white placeholder-slate-500 focus:border-teal-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Notes
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Additional notes..."
                rows={3}
                className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white placeholder-slate-500 focus:border-teal-500 focus:outline-none resize-none"
              />
            </div>

            {/* Summary */}
            <div className="rounded-lg border border-white/10 bg-white/5 p-4">
              <h3 className="text-sm font-medium text-slate-300 mb-2">Summary</h3>
              <div className="space-y-1 text-sm text-slate-400">
                <p>
                  <span className="text-slate-500">Type:</span>{' '}
                  {APPOINTMENT_TYPES.find((t) => t.value === appointmentType)?.label}
                </p>
                <p>
                  <span className="text-slate-500">Date:</span>{' '}
                  {date && new Date(date).toLocaleDateString('en-CY')} at {time}
                </p>
                <p>
                  <span className="text-slate-500">Duration:</span> {duration} minutes
                </p>
                {reason && (
                  <p>
                    <span className="text-slate-500">Reason:</span> {reason}
                  </p>
                )}
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setStep(2)}
                className="flex-1 rounded-lg border border-white/10 px-4 py-2.5 text-sm text-slate-300 hover:bg-white/5"
              >
                Back
              </button>
              <button
                onClick={handleSubmit}
                disabled={submitting}
                className="flex-1 rounded-lg bg-teal-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-teal-500 disabled:opacity-50 transition-colors"
              >
                {submitting ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Creating...
                  </span>
                ) : (
                  'Create Appointment'
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function NewAppointmentPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-slate-950">
          <Loader2 className="h-8 w-8 animate-spin text-teal-400" />
        </div>
      }
    >
      <NewAppointmentContent />
    </Suspense>
  );
}
