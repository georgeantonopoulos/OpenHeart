"use client";

import { useState, useEffect, Suspense } from "react";
import { useSession } from "next-auth/react";
import { useMutation } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Calendar,
  Clock,
  HeartPulse,
  Crosshair,
  Scan,
  Monitor,
  AlertCircle,
  Loader2,
  CheckCircle,
  User,
  FileText,
} from "lucide-react";
import {
  scheduleProcedure,
  type ScheduleProcedureInput,
  type ImagingModality,
  type ProcedurePriority,
  formatModality,
  getModalityColor,
} from "@/lib/api/procedures";
import { getPatient, type Patient } from "@/lib/api/patients";
import { StationSelector } from "@/components/procedures/StationSelector";

const MODALITIES: { value: ImagingModality; label: string; icon: typeof HeartPulse }[] = [
  { value: "US", label: "Echocardiogram", icon: HeartPulse },
  { value: "XA", label: "Catheterization", icon: Crosshair },
  { value: "CT", label: "CT Angiography", icon: Scan },
  { value: "MR", label: "Cardiac MRI", icon: Monitor },
  { value: "NM", label: "Nuclear Imaging", icon: Monitor },
];

const PRIORITIES: { value: ProcedurePriority; label: string; description: string }[] = [
  { value: "ROUTINE", label: "Routine", description: "Standard scheduling" },
  { value: "URGENT", label: "Urgent", description: "Same day if possible" },
  { value: "STAT", label: "STAT", description: "Immediate priority" },
];

function ScheduleProcedureContent() {
  const { data: session } = useSession();
  const router = useRouter();
  const searchParams = useSearchParams();

  // Get patient_id from URL if provided
  const patientIdParam = searchParams.get("patient_id");
  const returnUrl = searchParams.get("return");

  // Patient state
  const [patient, setPatient] = useState<Patient | null>(null);
  const [patientLoading, setPatientLoading] = useState(!!patientIdParam);
  const [patientError, setPatientError] = useState<string | null>(null);

  // Form state
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState<Partial<ScheduleProcedureInput>>({
    patient_id: patientIdParam ? parseInt(patientIdParam) : undefined,
    priority: "ROUTINE",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Load patient if ID provided
  useEffect(() => {
    if (patientIdParam && session?.accessToken) {
      loadPatient(parseInt(patientIdParam));
    }
  }, [patientIdParam, session?.accessToken]);

  async function loadPatient(id: number) {
    try {
      setPatientLoading(true);
      setPatientError(null);
      const data = await getPatient(session?.accessToken || "", id);
      setPatient(data);
      setFormData((prev) => ({ ...prev, patient_id: data.patient_id }));
    } catch (err) {
      setPatientError(err instanceof Error ? err.message : "Failed to load patient");
    } finally {
      setPatientLoading(false);
    }
  }

  // Schedule mutation
  const mutation = useMutation({
    mutationFn: (data: ScheduleProcedureInput) =>
      scheduleProcedure(session?.accessToken || "", data),
    onSuccess: (procedure) => {
      // Navigate to worklist or patient page
      if (returnUrl) {
        router.push(returnUrl);
      } else {
        router.push(`/procedures/worklist?highlight=${procedure.accession_number}`);
      }
    },
    onError: (error: Error) => {
      setErrors({ form: error.message });
    },
  });

  // Validation
  const validateStep = (currentStep: number): boolean => {
    const newErrors: Record<string, string> = {};

    if (currentStep === 1) {
      if (!formData.patient_id) {
        newErrors.patient_id = "Patient is required";
      }
    }

    if (currentStep === 2) {
      if (!formData.modality) {
        newErrors.modality = "Modality is required";
      }
      if (!formData.station_ae_title) {
        newErrors.station_ae_title = "Station is required";
      }
    }

    if (currentStep === 3) {
      if (!formData.scheduled_datetime) {
        newErrors.scheduled_datetime = "Date and time is required";
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submit
  const handleSubmit = () => {
    if (validateStep(3)) {
      mutation.mutate(formData as ScheduleProcedureInput);
    }
  };

  // Next step
  const handleNext = () => {
    if (validateStep(step)) {
      setStep(step + 1);
    }
  };

  // Update form field
  const updateField = <K extends keyof ScheduleProcedureInput>(
    field: K,
    value: ScheduleProcedureInput[K]
  ) => {
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
      <div className="border-b border-white/10 bg-slate-900">
        <div className="mx-auto max-w-3xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-4">
            <Link
              href={returnUrl || "/procedures/worklist"}
              className="text-slate-400 transition-colors hover:text-white"
            >
              <ArrowLeft className="h-5 w-5" />
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-white">Schedule Procedure</h1>
              <p className="text-sm text-slate-400">
                Add to Modality Worklist for imaging equipment
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Progress Steps */}
      <div className="border-b border-white/10 bg-slate-900/50">
        <div className="mx-auto max-w-3xl px-4 py-3 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            {[
              { num: 1, label: "Patient" },
              { num: 2, label: "Equipment" },
              { num: 3, label: "Schedule" },
            ].map((s, idx) => (
              <div key={s.num} className="flex items-center">
                <button
                  onClick={() => step > s.num && setStep(s.num)}
                  disabled={step < s.num}
                  className={`flex items-center gap-2 ${
                    step < s.num ? "cursor-not-allowed opacity-50" : ""
                  }`}
                >
                  <div
                    className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium ${
                      step > s.num
                        ? "bg-teal-500 text-white"
                        : step === s.num
                          ? "bg-teal-500/20 text-teal-400 ring-2 ring-teal-500"
                          : "bg-white/10 text-slate-400"
                    }`}
                  >
                    {step > s.num ? (
                      <CheckCircle className="h-4 w-4" />
                    ) : (
                      s.num
                    )}
                  </div>
                  <span
                    className={`hidden sm:block ${
                      step === s.num ? "text-white" : "text-slate-400"
                    }`}
                  >
                    {s.label}
                  </span>
                </button>
                {idx < 2 && (
                  <div
                    className={`mx-4 h-px w-12 sm:w-24 ${
                      step > s.num ? "bg-teal-500" : "bg-white/10"
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      <main className="mx-auto max-w-3xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Error Alert */}
        {errors.form && (
          <div className="mb-6 flex items-center gap-3 rounded-lg border border-red-500/30 bg-red-500/10 p-4">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <p className="text-red-400">{errors.form}</p>
          </div>
        )}

        {/* Step 1: Patient Selection */}
        {step === 1 && (
          <div className="space-y-6">
            <div className="rounded-lg border border-white/10 bg-slate-900 p-6">
              <h2 className="mb-4 text-lg font-semibold text-white">
                Select Patient
              </h2>

              {patientLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-teal-400" />
                  <span className="ml-2 text-slate-400">Loading patient...</span>
                </div>
              ) : patientError ? (
                <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-red-400">
                  {patientError}
                </div>
              ) : patient ? (
                <div className="rounded-lg border border-teal-500/30 bg-teal-500/10 p-4">
                  <div className="flex items-center gap-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-full bg-teal-500/20">
                      <User className="h-6 w-6 text-teal-400" />
                    </div>
                    <div>
                      <p className="font-medium text-white">
                        {patient.first_name} {patient.last_name}
                      </p>
                      <p className="text-sm text-slate-400">
                        MRN: {patient.mrn} • DOB: {patient.birth_date}
                      </p>
                    </div>
                    <button
                      onClick={() => {
                        setPatient(null);
                        setFormData((prev) => ({ ...prev, patient_id: undefined }));
                      }}
                      className="ml-auto text-sm text-slate-400 hover:text-white"
                    >
                      Change
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <p className="text-slate-400">
                    Enter the patient ID to schedule a procedure:
                  </p>
                  <div className="flex gap-4">
                    <input
                      type="number"
                      value={formData.patient_id || ""}
                      onChange={(e) =>
                        updateField("patient_id", parseInt(e.target.value) || 0)
                      }
                      placeholder="Patient ID"
                      className={`flex-1 rounded-lg border bg-white/5 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500 ${
                        errors.patient_id
                          ? "border-red-500"
                          : "border-white/10"
                      }`}
                    />
                    <button
                      onClick={() =>
                        formData.patient_id && loadPatient(formData.patient_id)
                      }
                      disabled={!formData.patient_id}
                      className="rounded-lg bg-teal-600 px-4 py-2.5 text-white hover:bg-teal-700 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      Load
                    </button>
                  </div>
                  {errors.patient_id && (
                    <p className="text-sm text-red-400">{errors.patient_id}</p>
                  )}
                  <p className="text-sm text-slate-500">
                    Or{" "}
                    <Link
                      href="/patients"
                      className="text-teal-400 hover:text-teal-300"
                    >
                      search patients
                    </Link>{" "}
                    and schedule from their profile.
                  </p>
                </div>
              )}
            </div>

            <div className="flex justify-end">
              <button
                onClick={handleNext}
                disabled={!patient}
                className="rounded-lg bg-teal-600 px-6 py-2.5 text-white hover:bg-teal-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Continue
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Modality & Station */}
        {step === 2 && (
          <div className="space-y-6">
            {/* Modality Selection */}
            <div className="rounded-lg border border-white/10 bg-slate-900 p-6">
              <h2 className="mb-4 text-lg font-semibold text-white">
                Select Modality
              </h2>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {MODALITIES.map((mod) => {
                  const Icon = mod.icon;
                  const isSelected = formData.modality === mod.value;
                  return (
                    <button
                      key={mod.value}
                      type="button"
                      onClick={() => {
                        updateField("modality", mod.value);
                        // Clear station when modality changes
                        updateField("station_ae_title", undefined as unknown as string);
                      }}
                      className={`flex items-center gap-3 rounded-lg border p-4 text-left transition-all ${
                        isSelected
                          ? "border-teal-500 bg-teal-500/10"
                          : "border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/10"
                      }`}
                    >
                      <div
                        className={`rounded-lg p-2 ${
                          isSelected ? "bg-teal-500/20" : "bg-white/10"
                        }`}
                      >
                        <Icon
                          className={`h-5 w-5 ${
                            isSelected ? "text-teal-400" : "text-slate-400"
                          }`}
                        />
                      </div>
                      <div>
                        <span
                          className={`font-medium ${
                            isSelected ? "text-white" : "text-slate-200"
                          }`}
                        >
                          {mod.label}
                        </span>
                        <span
                          className={`ml-2 rounded px-1.5 py-0.5 text-xs ${getModalityColor(mod.value)}`}
                        >
                          {mod.value}
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>
              {errors.modality && (
                <p className="mt-2 text-sm text-red-400">{errors.modality}</p>
              )}
            </div>

            {/* Station Selection */}
            {formData.modality && (
              <div className="rounded-lg border border-white/10 bg-slate-900 p-6">
                <h2 className="mb-4 text-lg font-semibold text-white">
                  Select Equipment
                </h2>
                <StationSelector
                  accessToken={session?.accessToken || ""}
                  modality={formData.modality}
                  selectedAeTitle={formData.station_ae_title}
                  onSelect={(station) =>
                    updateField("station_ae_title", station.ae_title)
                  }
                />
                {errors.station_ae_title && (
                  <p className="mt-2 text-sm text-red-400">
                    {errors.station_ae_title}
                  </p>
                )}
              </div>
            )}

            <div className="flex justify-between">
              <button
                onClick={() => setStep(1)}
                className="rounded-lg border border-white/10 bg-white/5 px-6 py-2.5 text-white hover:bg-white/10"
              >
                Back
              </button>
              <button
                onClick={handleNext}
                disabled={!formData.modality || !formData.station_ae_title}
                className="rounded-lg bg-teal-600 px-6 py-2.5 text-white hover:bg-teal-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Continue
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Schedule & Details */}
        {step === 3 && (
          <div className="space-y-6">
            {/* Date/Time */}
            <div className="rounded-lg border border-white/10 bg-slate-900 p-6">
              <h2 className="mb-4 text-lg font-semibold text-white">
                Schedule Date & Time
              </h2>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-300">
                    Date & Time *
                  </label>
                  <div className="relative">
                    <Calendar className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
                    <input
                      type="datetime-local"
                      value={formData.scheduled_datetime || ""}
                      onChange={(e) =>
                        updateField("scheduled_datetime", e.target.value)
                      }
                      className={`w-full rounded-lg border bg-white/5 py-2.5 pl-10 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-teal-500 ${
                        errors.scheduled_datetime
                          ? "border-red-500"
                          : "border-white/10"
                      }`}
                    />
                  </div>
                  {errors.scheduled_datetime && (
                    <p className="mt-1 text-sm text-red-400">
                      {errors.scheduled_datetime}
                    </p>
                  )}
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-300">
                    Expected Duration
                  </label>
                  <div className="relative">
                    <Clock className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
                    <select
                      value={formData.expected_duration_minutes || ""}
                      onChange={(e) =>
                        updateField(
                          "expected_duration_minutes",
                          parseInt(e.target.value) || undefined
                        )
                      }
                      className="w-full appearance-none rounded-lg border border-white/10 bg-white/5 py-2.5 pl-10 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                    >
                      <option value="" className="bg-slate-900">
                        Select duration...
                      </option>
                      <option value="15" className="bg-slate-900">
                        15 minutes
                      </option>
                      <option value="30" className="bg-slate-900">
                        30 minutes
                      </option>
                      <option value="45" className="bg-slate-900">
                        45 minutes
                      </option>
                      <option value="60" className="bg-slate-900">
                        1 hour
                      </option>
                      <option value="90" className="bg-slate-900">
                        1.5 hours
                      </option>
                      <option value="120" className="bg-slate-900">
                        2 hours
                      </option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            {/* Priority */}
            <div className="rounded-lg border border-white/10 bg-slate-900 p-6">
              <h2 className="mb-4 text-lg font-semibold text-white">Priority</h2>
              <div className="flex flex-wrap gap-3">
                {PRIORITIES.map((p) => {
                  const isSelected = formData.priority === p.value;
                  return (
                    <button
                      key={p.value}
                      type="button"
                      onClick={() => updateField("priority", p.value)}
                      className={`rounded-lg border px-4 py-2 text-left transition-all ${
                        isSelected
                          ? p.value === "STAT"
                            ? "border-red-500 bg-red-500/10"
                            : p.value === "URGENT"
                              ? "border-amber-500 bg-amber-500/10"
                              : "border-teal-500 bg-teal-500/10"
                          : "border-white/10 bg-white/5 hover:border-white/20"
                      }`}
                    >
                      <span
                        className={`font-medium ${
                          isSelected
                            ? p.value === "STAT"
                              ? "text-red-400"
                              : p.value === "URGENT"
                                ? "text-amber-400"
                                : "text-teal-400"
                            : "text-slate-200"
                        }`}
                      >
                        {p.label}
                      </span>
                      <span className="ml-2 text-sm text-slate-500">
                        {p.description}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Clinical Details */}
            <div className="rounded-lg border border-white/10 bg-slate-900 p-6">
              <h2 className="mb-4 text-lg font-semibold text-white">
                Clinical Details
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-300">
                    Procedure Description
                  </label>
                  <input
                    type="text"
                    value={formData.procedure_description || ""}
                    onChange={(e) =>
                      updateField("procedure_description", e.target.value)
                    }
                    placeholder={
                      formData.modality === "US"
                        ? "e.g., TTE with Doppler"
                        : formData.modality === "XA"
                          ? "e.g., Diagnostic Angiogram"
                          : "Procedure description"
                    }
                    className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-300">
                    Reason for Exam
                  </label>
                  <textarea
                    value={formData.reason_for_exam || ""}
                    onChange={(e) =>
                      updateField("reason_for_exam", e.target.value)
                    }
                    placeholder="Clinical indication..."
                    rows={2}
                    className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-300">
                    Referring Physician
                  </label>
                  <input
                    type="text"
                    value={formData.referring_physician_name || ""}
                    onChange={(e) =>
                      updateField("referring_physician_name", e.target.value)
                    }
                    placeholder="Dr. Name"
                    className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-300">
                    Internal Notes
                  </label>
                  <textarea
                    value={formData.notes || ""}
                    onChange={(e) => updateField("notes", e.target.value)}
                    placeholder="Notes visible only to staff..."
                    rows={2}
                    className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>
              </div>
            </div>

            {/* Summary */}
            <div className="rounded-lg border border-teal-500/30 bg-teal-500/5 p-6">
              <h3 className="mb-3 text-sm font-medium uppercase tracking-wider text-teal-400">
                Summary
              </h3>
              <div className="grid gap-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-400">Patient</span>
                  <span className="text-white">
                    {patient?.first_name} {patient?.last_name}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Modality</span>
                  <span className="text-white">
                    {formData.modality && formatModality(formData.modality)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Station</span>
                  <span className="font-mono text-white">
                    {formData.station_ae_title}
                  </span>
                </div>
                {formData.scheduled_datetime && (
                  <div className="flex justify-between">
                    <span className="text-slate-400">Scheduled</span>
                    <span className="text-white">
                      {new Date(formData.scheduled_datetime).toLocaleString(
                        "en-GB"
                      )}
                    </span>
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-between">
              <button
                onClick={() => setStep(2)}
                className="rounded-lg border border-white/10 bg-white/5 px-6 py-2.5 text-white hover:bg-white/10"
              >
                Back
              </button>
              <button
                onClick={handleSubmit}
                disabled={mutation.isPending}
                className="flex items-center gap-2 rounded-lg bg-teal-600 px-6 py-2.5 text-white hover:bg-teal-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {mutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Scheduling...
                  </>
                ) : (
                  <>
                    <Calendar className="h-4 w-4" />
                    Schedule Procedure
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default function ScheduleProcedurePage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center bg-slate-950">
          <Loader2 className="h-12 w-12 animate-spin text-teal-400" />
        </div>
      }
    >
      <ScheduleProcedureContent />
    </Suspense>
  );
}
