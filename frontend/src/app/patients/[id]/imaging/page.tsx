"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Calendar,
  Filter,
  Grid3X3,
  Image,
  List,
  Loader2,
  Search,
  Activity,
  Heart,
  AlertTriangle,
} from "lucide-react";
import { StudyCard, StudyRow } from "@/components/imaging/StudyCard";
import {
  type DicomStudy,
  type Modality,
  getPatientStudies,
  getViewerUrl,
  searchStudies,
} from "@/lib/api/imaging";

type ViewMode = "grid" | "list";

export default function PatientImagingPage() {
  const params = useParams();
  const router = useRouter();
  const patientId = Number(params.id);

  const [studies, setStudies] = useState<DicomStudy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [searchTerm, setSearchTerm] = useState("");
  const [modalityFilter, setModalityFilter] = useState<Modality | "all">("all");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const perPage = 12;

  useEffect(() => {
    loadStudies();
  }, [patientId, page, modalityFilter]);

  async function loadStudies() {
    try {
      setLoading(true);
      setError(null);

      // In production, this would use the patient's DICOM Patient ID
      // For now, we search by linked_patient_id
      const params = {
        linked_patient_id: patientId,
        page,
        per_page: perPage,
        ...(modalityFilter !== "all" && { modality: modalityFilter }),
      };

      const result = await searchStudies(params);
      setStudies(result.studies);
      setTotal(result.total);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load imaging studies"
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleOpenViewer(study: DicomStudy) {
    try {
      const { viewer_url } = await getViewerUrl(study.study_instance_uid);
      // Open in new tab for full-screen viewer experience
      window.open(viewer_url, "_blank", "noopener,noreferrer");
    } catch (err) {
      console.error("Failed to get viewer URL:", err);
    }
  }

  function handleViewMeasurements(study: DicomStudy) {
    // Navigate to measurements view
    router.push(
      `/patients/${patientId}/imaging/${study.study_instance_uid}/measurements`
    );
  }

  // Filter studies by search term
  const filteredStudies = studies.filter((study) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      study.study_description?.toLowerCase().includes(term) ||
      study.accession_number?.toLowerCase().includes(term) ||
      study.modalities.some((m) => m.toLowerCase().includes(term))
    );
  });

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <header className="sticky top-0 z-10 border-b border-white/10 bg-slate-900/80 backdrop-blur-xl">
        <div className="mx-auto max-w-7xl px-6 py-4">
          <div className="flex items-center gap-4">
            <Link
              href={`/patients/${patientId}`}
              className="flex items-center gap-2 text-slate-400 hover:text-white"
            >
              <ArrowLeft className="h-5 w-5" />
              <span className="hidden sm:inline">Back to Patient</span>
            </Link>

            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/20">
                <Image className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-white">
                  Imaging Studies
                </h1>
                <p className="text-sm text-slate-400">
                  {total} {total === 1 ? "study" : "studies"} found
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Filters */}
      <div className="border-b border-white/10 bg-slate-900/30">
        <div className="mx-auto max-w-7xl px-6 py-4">
          <div className="flex flex-wrap items-center gap-4">
            {/* Search */}
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                placeholder="Search studies..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full rounded-lg border border-white/10 bg-white/5 py-2 pl-10 pr-4 text-white placeholder-slate-500 focus:border-teal-500/50 focus:outline-none focus:ring-1 focus:ring-teal-500/50"
              />
            </div>

            {/* Modality filter */}
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-slate-500" />
              <select
                value={modalityFilter}
                onChange={(e) =>
                  setModalityFilter(e.target.value as Modality | "all")
                }
                className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white focus:border-teal-500/50 focus:outline-none"
              >
                <option value="all">All Modalities</option>
                <option value="US">Echo (US)</option>
                <option value="XA">Cath Lab (XA)</option>
                <option value="CT">CT Scan</option>
                <option value="MR">MRI</option>
                <option value="NM">Nuclear</option>
                <option value="ECG">ECG</option>
              </select>
            </div>

            {/* View mode toggle */}
            <div className="flex rounded-lg border border-white/10 bg-white/5 p-1">
              <button
                onClick={() => setViewMode("grid")}
                className={`rounded-md p-2 transition-colors ${
                  viewMode === "grid"
                    ? "bg-white/10 text-white"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                <Grid3X3 className="h-4 w-4" />
              </button>
              <button
                onClick={() => setViewMode("list")}
                className={`rounded-md p-2 transition-colors ${
                  viewMode === "list"
                    ? "bg-white/10 text-white"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                <List className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <main className="mx-auto max-w-7xl px-6 py-8">
        {error && (
          <div className="mb-6 flex items-center gap-3 rounded-lg border border-red-500/30 bg-red-500/10 p-4">
            <AlertTriangle className="h-5 w-5 text-red-400" />
            <p className="text-sm text-red-300">{error}</p>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-teal-400" />
          </div>
        ) : filteredStudies.length === 0 ? (
          <EmptyState searchTerm={searchTerm} modalityFilter={modalityFilter} />
        ) : viewMode === "grid" ? (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {filteredStudies.map((study) => (
              <StudyCard
                key={study.study_instance_uid}
                study={study}
                onView={() => handleOpenViewer(study)}
                onViewMeasurements={() => handleViewMeasurements(study)}
              />
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {filteredStudies.map((study) => (
              <StudyRow
                key={study.study_instance_uid}
                study={study}
                onView={() => handleOpenViewer(study)}
              />
            ))}
          </div>
        )}

        {/* Pagination */}
        {total > perPage && (
          <div className="mt-8 flex items-center justify-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm text-white disabled:opacity-50"
            >
              Previous
            </button>
            <span className="px-4 text-sm text-slate-400">
              Page {page} of {Math.ceil(total / perPage)}
            </span>
            <button
              onClick={() =>
                setPage((p) => Math.min(Math.ceil(total / perPage), p + 1))
              }
              disabled={page >= Math.ceil(total / perPage)}
              className="rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm text-white disabled:opacity-50"
            >
              Next
            </button>
          </div>
        )}
      </main>

      {/* Quick Stats */}
      <aside className="fixed bottom-4 right-4">
        <div className="rounded-xl border border-white/10 bg-slate-900/90 p-4 backdrop-blur-xl">
          <div className="flex items-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <Heart className="h-4 w-4 text-blue-400" />
              <span className="text-slate-400">Echo:</span>
              <span className="font-medium text-white">
                {
                  studies.filter((s) => s.modalities.includes("US" as Modality))
                    .length
                }
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-red-400" />
              <span className="text-slate-400">Cath:</span>
              <span className="font-medium text-white">
                {
                  studies.filter((s) => s.modalities.includes("XA" as Modality))
                    .length
                }
              </span>
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
}

// Empty state component
function EmptyState({
  searchTerm,
  modalityFilter,
}: {
  searchTerm: string;
  modalityFilter: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-white/10 bg-slate-900/50 py-16">
      <Image className="h-16 w-16 text-slate-600" />
      <h3 className="mt-4 text-lg font-medium text-white">No imaging studies</h3>
      <p className="mt-2 text-center text-slate-400">
        {searchTerm || modalityFilter !== "all"
          ? "No studies match your current filters."
          : "This patient has no imaging studies linked yet."}
      </p>
      {(searchTerm || modalityFilter !== "all") && (
        <button
          onClick={() => {
            // Reset filters
          }}
          className="mt-4 text-teal-400 hover:text-teal-300"
        >
          Clear filters
        </button>
      )}
    </div>
  );
}
