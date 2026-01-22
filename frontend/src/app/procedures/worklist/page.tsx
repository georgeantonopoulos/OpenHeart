"use client";

import { useState, useEffect, Suspense } from "react";
import { useSession } from "next-auth/react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Plus,
  Calendar,
  Clock,
  Filter,
  Search,
  HeartPulse,
  Crosshair,
  Scan,
  Monitor,
  AlertCircle,
  Loader2,
  RefreshCw,
  ChevronRight,
  User,
  XCircle,
  CheckCircle,
  PlayCircle,
  PauseCircle,
} from "lucide-react";
import {
  listScheduledProcedures,
  cancelProcedure,
  type ScheduledProcedure,
  type ImagingModality,
  type ProcedureStatus,
  formatModality,
  getModalityColor,
  getStatusColor,
  getPriorityColor,
  formatScheduledTime,
  formatTimeOnly,
} from "@/lib/api/procedures";

const modalityIcons: Record<ImagingModality, typeof HeartPulse> = {
  US: HeartPulse,
  XA: Crosshair,
  CT: Scan,
  MR: Monitor,
  NM: Monitor,
};

const statusIcons: Record<ProcedureStatus, typeof Clock> = {
  SCHEDULED: Clock,
  IN_PROGRESS: PlayCircle,
  COMPLETED: CheckCircle,
  CANCELLED: XCircle,
};

function WorklistContent() {
  const { data: session } = useSession();
  const router = useRouter();
  const searchParams = useSearchParams();

  const highlightAccession = searchParams.get("highlight");

  // State
  const [procedures, setProcedures] = useState<ScheduledProcedure[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split("T")[0]
  );
  const [selectedModality, setSelectedModality] = useState<ImagingModality | "">("");
  const [selectedStation, setSelectedStation] = useState<string>("");
  const [includeCompleted, setIncludeCompleted] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  // Cancel modal
  const [cancellingId, setCancellingId] = useState<string | null>(null);
  const [cancelReason, setCancelReason] = useState("");
  const [cancelLoading, setCancelLoading] = useState(false);

  useEffect(() => {
    if (session?.accessToken) {
      loadWorklist();
    }
  }, [
    session?.accessToken,
    selectedDate,
    selectedModality,
    selectedStation,
    includeCompleted,
  ]);

  async function loadWorklist() {
    try {
      setLoading(true);
      setError(null);
      const data = await listScheduledProcedures(session?.accessToken || "", {
        scheduled_date: selectedDate,
        modality: selectedModality || undefined,
        station_ae_title: selectedStation || undefined,
        include_completed: includeCompleted,
      });
      setProcedures(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load worklist");
    } finally {
      setLoading(false);
    }
  }

  async function handleCancel() {
    if (!cancellingId || !cancelReason.trim()) return;

    try {
      setCancelLoading(true);
      await cancelProcedure(session?.accessToken || "", cancellingId, {
        cancellation_reason: cancelReason,
      });
      setCancellingId(null);
      setCancelReason("");
      loadWorklist();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to cancel procedure");
    } finally {
      setCancelLoading(false);
    }
  }

  // Filter procedures by search query
  const filteredProcedures = searchQuery
    ? procedures.filter(
        (p) =>
          p.accession_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
          p.procedure_description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          p.station_ae_title.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : procedures;

  // Group by status
  const inProgress = filteredProcedures.filter((p) => p.status === "IN_PROGRESS");
  const scheduled = filteredProcedures.filter((p) => p.status === "SCHEDULED");
  const completed = filteredProcedures.filter((p) => p.status === "COMPLETED");
  const cancelled = filteredProcedures.filter((p) => p.status === "CANCELLED");

  if (!session) {
    return null;
  }

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <div className="border-b border-white/10 bg-slate-900">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">Modality Worklist</h1>
              <p className="text-sm text-slate-400">
                Scheduled imaging procedures for your clinic
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={loadWorklist}
                disabled={loading}
                className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-white hover:bg-white/10 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                Refresh
              </button>
              <Link
                href="/procedures/schedule"
                className="flex items-center gap-2 rounded-lg bg-teal-600 px-4 py-2 text-white hover:bg-teal-700"
              >
                <Plus className="h-4 w-4" />
                Schedule Procedure
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="border-b border-white/10 bg-slate-900/50">
        <div className="mx-auto max-w-7xl px-4 py-3 sm:px-6 lg:px-8">
          <div className="flex flex-wrap items-center gap-4">
            {/* Date Filter */}
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-slate-400" />
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>

            {/* Modality Filter */}
            <select
              value={selectedModality}
              onChange={(e) =>
                setSelectedModality(e.target.value as ImagingModality | "")
              }
              className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-teal-500"
            >
              <option value="" className="bg-slate-900">
                All Modalities
              </option>
              <option value="US" className="bg-slate-900">
                Echo (US)
              </option>
              <option value="XA" className="bg-slate-900">
                Cath (XA)
              </option>
              <option value="CT" className="bg-slate-900">
                CT
              </option>
              <option value="MR" className="bg-slate-900">
                MRI
              </option>
              <option value="NM" className="bg-slate-900">
                Nuclear
              </option>
            </select>

            {/* Station Filter */}
            <input
              type="text"
              value={selectedStation}
              onChange={(e) => setSelectedStation(e.target.value)}
              placeholder="Station AE..."
              className="w-32 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500"
            />

            {/* Include Completed */}
            <label className="flex items-center gap-2 text-sm text-slate-400">
              <input
                type="checkbox"
                checked={includeCompleted}
                onChange={(e) => setIncludeCompleted(e.target.checked)}
                className="rounded border-white/20 bg-white/5 text-teal-500 focus:ring-teal-500"
              />
              Show completed
            </label>

            {/* Search */}
            <div className="relative ml-auto">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search accession..."
                className="w-48 rounded-lg border border-white/10 bg-white/5 py-1.5 pl-9 pr-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>
          </div>
        </div>
      </div>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {/* Error State */}
        {error && (
          <div className="mb-6 flex items-center gap-3 rounded-lg border border-red-500/30 bg-red-500/10 p-4">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {/* Loading State */}
        {loading && procedures.length === 0 ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin text-teal-400" />
            <span className="ml-3 text-slate-400">Loading worklist...</span>
          </div>
        ) : filteredProcedures.length === 0 ? (
          <div className="rounded-lg border border-white/10 bg-slate-900 p-12 text-center">
            <Calendar className="mx-auto h-12 w-12 text-slate-500" />
            <h3 className="mt-4 text-lg font-medium text-white">
              No procedures scheduled
            </h3>
            <p className="mt-2 text-slate-400">
              {searchQuery
                ? "No procedures match your search."
                : `No procedures found for ${new Date(selectedDate).toLocaleDateString("en-GB")}`}
            </p>
            <Link
              href="/procedures/schedule"
              className="mt-6 inline-flex items-center gap-2 rounded-lg bg-teal-600 px-4 py-2 text-white hover:bg-teal-700"
            >
              <Plus className="h-4 w-4" />
              Schedule Procedure
            </Link>
          </div>
        ) : (
          <div className="space-y-8">
            {/* In Progress Section */}
            {inProgress.length > 0 && (
              <ProcedureSection
                title="In Progress"
                icon={PlayCircle}
                iconColor="text-amber-400"
                procedures={inProgress}
                highlightAccession={highlightAccession}
                onCancel={setCancellingId}
              />
            )}

            {/* Scheduled Section */}
            {scheduled.length > 0 && (
              <ProcedureSection
                title="Scheduled"
                icon={Clock}
                iconColor="text-teal-400"
                procedures={scheduled}
                highlightAccession={highlightAccession}
                onCancel={setCancellingId}
              />
            )}

            {/* Completed Section */}
            {completed.length > 0 && includeCompleted && (
              <ProcedureSection
                title="Completed"
                icon={CheckCircle}
                iconColor="text-green-400"
                procedures={completed}
                highlightAccession={highlightAccession}
              />
            )}

            {/* Cancelled Section */}
            {cancelled.length > 0 && includeCompleted && (
              <ProcedureSection
                title="Cancelled"
                icon={XCircle}
                iconColor="text-slate-400"
                procedures={cancelled}
                highlightAccession={highlightAccession}
              />
            )}
          </div>
        )}
      </main>

      {/* Cancel Modal */}
      {cancellingId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="mx-4 w-full max-w-md rounded-lg border border-white/10 bg-slate-900 p-6">
            <h3 className="text-lg font-semibold text-white">Cancel Procedure</h3>
            <p className="mt-2 text-sm text-slate-400">
              Please provide a reason for cancellation.
            </p>
            <textarea
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              placeholder="Reason for cancellation..."
              rows={3}
              className="mt-4 w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-red-500"
            />
            <div className="mt-4 flex justify-end gap-3">
              <button
                onClick={() => {
                  setCancellingId(null);
                  setCancelReason("");
                }}
                className="rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-white hover:bg-white/10"
              >
                Keep Scheduled
              </button>
              <button
                onClick={handleCancel}
                disabled={!cancelReason.trim() || cancelLoading}
                className="flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-white hover:bg-red-700 disabled:opacity-50"
              >
                {cancelLoading && <Loader2 className="h-4 w-4 animate-spin" />}
                Cancel Procedure
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Procedure section component
function ProcedureSection({
  title,
  icon: Icon,
  iconColor,
  procedures,
  highlightAccession,
  onCancel,
}: {
  title: string;
  icon: typeof Clock;
  iconColor: string;
  procedures: ScheduledProcedure[];
  highlightAccession?: string | null;
  onCancel?: (id: string) => void;
}) {
  return (
    <div>
      <div className="mb-4 flex items-center gap-2">
        <Icon className={`h-5 w-5 ${iconColor}`} />
        <h2 className="text-lg font-semibold text-white">
          {title} ({procedures.length})
        </h2>
      </div>
      <div className="space-y-3">
        {procedures.map((procedure) => (
          <ProcedureCard
            key={procedure.id}
            procedure={procedure}
            isHighlighted={highlightAccession === procedure.accession_number}
            onCancel={onCancel}
          />
        ))}
      </div>
    </div>
  );
}

// Procedure card component
function ProcedureCard({
  procedure,
  isHighlighted,
  onCancel,
}: {
  procedure: ScheduledProcedure;
  isHighlighted?: boolean;
  onCancel?: (id: string) => void;
}) {
  const ModalityIcon = modalityIcons[procedure.modality] || Monitor;
  const StatusIcon = statusIcons[procedure.status] || Clock;

  return (
    <div
      className={`group rounded-lg border transition-all ${
        isHighlighted
          ? "border-teal-500 bg-teal-500/10 ring-2 ring-teal-500/50"
          : "border-white/10 bg-slate-900 hover:border-white/20"
      }`}
    >
      <div className="flex items-center gap-4 p-4">
        {/* Modality Icon */}
        <div
          className={`rounded-lg p-3 ${
            isHighlighted ? "bg-teal-500/20" : "bg-white/5"
          }`}
        >
          <ModalityIcon
            className={`h-6 w-6 ${
              isHighlighted ? "text-teal-400" : "text-slate-400"
            }`}
          />
        </div>

        {/* Main Info */}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-3">
            <span className="font-mono text-sm font-medium text-white">
              {procedure.accession_number}
            </span>
            <span className={`rounded px-2 py-0.5 text-xs ${getModalityColor(procedure.modality)}`}>
              {formatModality(procedure.modality)}
            </span>
            <span className={`rounded px-2 py-0.5 text-xs ${getStatusColor(procedure.status)}`}>
              {procedure.status}
            </span>
            {procedure.priority !== "ROUTINE" && (
              <span className={`rounded px-2 py-0.5 text-xs ${getPriorityColor(procedure.priority)}`}>
                {procedure.priority}
              </span>
            )}
          </div>

          <div className="mt-1 flex items-center gap-4 text-sm text-slate-400">
            <span className="flex items-center gap-1">
              <User className="h-3.5 w-3.5" />
              Patient #{procedure.patient_id}
            </span>
            <span className="flex items-center gap-1">
              <Monitor className="h-3.5 w-3.5" />
              {procedure.station_ae_title}
              {procedure.station_name && ` (${procedure.station_name})`}
            </span>
          </div>

          {procedure.procedure_description && (
            <p className="mt-1 truncate text-sm text-slate-500">
              {procedure.procedure_description}
            </p>
          )}
        </div>

        {/* Time */}
        <div className="text-right">
          <p className="font-medium text-white">
            {formatTimeOnly(procedure.scheduled_datetime)}
          </p>
          <p className="text-sm text-slate-500">
            {new Date(procedure.scheduled_datetime).toLocaleDateString("en-GB", {
              day: "2-digit",
              month: "short",
            })}
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 opacity-0 transition-opacity group-hover:opacity-100">
          {onCancel && procedure.status === "SCHEDULED" && (
            <button
              onClick={() => onCancel(procedure.id)}
              className="rounded-lg p-2 text-slate-400 hover:bg-red-500/10 hover:text-red-400"
              title="Cancel procedure"
            >
              <XCircle className="h-5 w-5" />
            </button>
          )}
          <Link
            href={`/patients/${procedure.patient_id}`}
            className="rounded-lg p-2 text-slate-400 hover:bg-white/10 hover:text-white"
            title="View patient"
          >
            <ChevronRight className="h-5 w-5" />
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function WorklistPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center bg-slate-950">
          <Loader2 className="h-12 w-12 animate-spin text-teal-400" />
        </div>
      }
    >
      <WorklistContent />
    </Suspense>
  );
}
