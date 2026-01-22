"use client";

import { useState, useEffect, Suspense } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Search,
  Filter,
  Loader2,
  AlertCircle,
  Image,
  Grid3X3,
  List,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
} from "lucide-react";
import {
  searchStudies,
  getViewerUrl,
  type DicomStudy,
  type Modality,
  type StudySearchParams,
  formatModality,
} from "@/lib/api/imaging";
import { StudyCard, StudyRow } from "@/components/imaging/StudyCard";

const MODALITIES: Modality[] = ["US", "XA", "CT", "MR", "NM", "ECG"];
const PER_PAGE = 20;

function ImagingBrowserContent() {
  const { data: session } = useSession();
  const router = useRouter();

  // Filter state
  const [patientSearch, setPatientSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [modalityFilter, setModalityFilter] = useState<Modality | "">("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");

  // Data state
  const [studies, setStudies] = useState<DicomStudy[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Debounce patient search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(patientSearch);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [patientSearch]);

  // Reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [modalityFilter, dateFrom, dateTo]);

  // Fetch studies
  useEffect(() => {
    if (!session?.accessToken) return;

    const fetchStudies = async () => {
      setLoading(true);
      setError(null);
      try {
        const params: StudySearchParams = {
          page,
          per_page: PER_PAGE,
        };
        if (debouncedSearch) params.patient_name = debouncedSearch;
        if (modalityFilter) params.modality = modalityFilter;
        if (dateFrom) params.study_date_from = dateFrom;
        if (dateTo) params.study_date_to = dateTo;

        const result = await searchStudies(session.accessToken, params);
        setStudies(result.studies);
        setTotal(result.total);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load studies");
      } finally {
        setLoading(false);
      }
    };

    fetchStudies();
  }, [session?.accessToken, debouncedSearch, modalityFilter, dateFrom, dateTo, page]);

  const totalPages = Math.ceil(total / PER_PAGE);

  const handleViewStudy = async (study: DicomStudy) => {
    if (!session?.accessToken) return;
    try {
      const { viewer_url } = await getViewerUrl(
        session.accessToken,
        study.study_instance_uid
      );
      window.open(viewer_url, "_blank");
    } catch {
      // Fallback: navigate to viewer page with study UID
      router.push(`/viewer?studyInstanceUid=${study.study_instance_uid}`);
    }
  };

  const handleRefresh = () => {
    setPage(1);
    // Trigger refetch by toggling a state dependency
    setDebouncedSearch((prev) => prev + "");
  };

  const hasFilters = debouncedSearch || modalityFilter || dateFrom || dateTo;

  return (
    <div className="min-h-screen bg-slate-950 p-6">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <Link
                href="/dashboard"
                className="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-white/5 hover:text-white"
              >
                <ChevronLeft className="h-5 w-5" />
              </Link>
              <div>
                <h1 className="text-2xl font-bold text-white">Imaging Browser</h1>
                <p className="text-sm text-slate-400">
                  Search DICOM studies across all patients
                </p>
              </div>
            </div>
          </div>
          <button
            onClick={handleRefresh}
            className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300 transition-colors hover:bg-white/10"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        </div>

        {/* Filters */}
        <div className="mb-6 rounded-xl border border-white/10 bg-slate-900/50 p-4">
          <div className="flex items-center gap-2 mb-3 text-sm text-slate-400">
            <Filter className="h-4 w-4" />
            <span>Filters</span>
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
            {/* Patient search */}
            <div className="relative lg:col-span-2">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                placeholder="Patient name..."
                value={patientSearch}
                onChange={(e) => setPatientSearch(e.target.value)}
                className="w-full rounded-lg border border-white/10 bg-slate-800 py-2 pl-9 pr-3 text-sm text-white placeholder-slate-500 focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
              />
            </div>

            {/* Modality filter */}
            <select
              value={modalityFilter}
              onChange={(e) => setModalityFilter(e.target.value as Modality | "")}
              className="rounded-lg border border-white/10 bg-slate-800 px-3 py-2 text-sm text-white focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
            >
              <option value="">All Modalities</option>
              {MODALITIES.map((mod) => (
                <option key={mod} value={mod}>
                  {formatModality(mod)}
                </option>
              ))}
            </select>

            {/* Date from */}
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="rounded-lg border border-white/10 bg-slate-800 px-3 py-2 text-sm text-white focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
              placeholder="From date"
            />

            {/* Date to */}
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="rounded-lg border border-white/10 bg-slate-800 px-3 py-2 text-sm text-white focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
              placeholder="To date"
            />
          </div>
        </div>

        {/* Toolbar: results count + view mode */}
        <div className="mb-4 flex items-center justify-between">
          <p className="text-sm text-slate-400">
            {loading ? "Loading..." : `${total} ${total === 1 ? "study" : "studies"} found`}
          </p>
          <div className="flex items-center gap-1 rounded-lg border border-white/10 bg-slate-900/50 p-1">
            <button
              onClick={() => setViewMode("grid")}
              className={`rounded-md p-1.5 transition-colors ${
                viewMode === "grid"
                  ? "bg-teal-600 text-white"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Grid3X3 className="h-4 w-4" />
            </button>
            <button
              onClick={() => setViewMode("list")}
              className={`rounded-md p-1.5 transition-colors ${
                viewMode === "list"
                  ? "bg-teal-600 text-white"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <List className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-teal-400" />
            <p className="mt-3 text-sm text-slate-400">Loading studies...</p>
          </div>
        ) : error ? (
          <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-6 text-center">
            <AlertCircle className="mx-auto h-8 w-8 text-red-400" />
            <p className="mt-2 text-sm text-red-300">{error}</p>
          </div>
        ) : studies.length === 0 ? (
          <div className="rounded-xl border border-white/10 bg-slate-900/50 p-12 text-center">
            <Image className="mx-auto h-12 w-12 text-slate-600" />
            <h3 className="mt-3 text-lg font-medium text-white">
              No imaging studies found
            </h3>
            <p className="mt-1 text-sm text-slate-400">
              {hasFilters
                ? "Try adjusting your search filters"
                : "No DICOM studies are available yet"}
            </p>
          </div>
        ) : viewMode === "grid" ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {studies.map((study) => (
              <StudyCard
                key={study.study_instance_uid}
                study={study}
                showPatientInfo={true}
                onView={() => handleViewStudy(study)}
              />
            ))}
          </div>
        ) : (
          <div className="space-y-2">
            {studies.map((study) => (
              <StudyRow
                key={study.study_instance_uid}
                study={study}
                showPatientInfo={true}
                onView={() => handleViewStudy(study)}
              />
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="mt-6 flex items-center justify-center gap-3">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="flex items-center gap-1 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300 transition-colors hover:bg-white/10 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </button>
            <span className="text-sm text-slate-400">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="flex items-center gap-1 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300 transition-colors hover:bg-white/10 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default function ImagingBrowserPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center bg-slate-950">
          <Loader2 className="h-12 w-12 animate-spin text-teal-400" />
        </div>
      }
    >
      <ImagingBrowserContent />
    </Suspense>
  );
}
