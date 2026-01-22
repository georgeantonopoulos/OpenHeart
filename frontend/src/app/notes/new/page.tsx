"use client";

import { useState, useEffect, Suspense } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Search,
  Loader2,
  ChevronLeft,
  ChevronRight,
  FileText,
  User,
  Calendar,
} from "lucide-react";
import {
  searchPatients,
  listPatients,
  type Patient,
} from "@/lib/api/patients";

function NewNoteContent() {
  const { data: session } = useSession();
  const router = useRouter();

  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [patients, setPatients] = useState<Patient[]>([]);
  const [recentPatients, setRecentPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(false);
  const [recentLoading, setRecentLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Debounce search query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Load recent patients on mount
  useEffect(() => {
    if (!session?.accessToken) return;

    const fetchRecent = async () => {
      try {
        const result = await listPatients(session.accessToken, {
          page: 1,
          page_size: 5,
          status: "active",
        });
        setRecentPatients(result.items);
      } catch {
        // Non-critical, just don't show recent patients
      } finally {
        setRecentLoading(false);
      }
    };

    fetchRecent();
  }, [session?.accessToken]);

  // Search patients when query changes
  useEffect(() => {
    if (!session?.accessToken || !debouncedQuery) {
      setPatients([]);
      return;
    }

    const fetchPatients = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await searchPatients(session.accessToken, {
          q: debouncedQuery,
          page: 1,
          page_size: 10,
        });
        setPatients(result.items);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Search failed");
      } finally {
        setLoading(false);
      }
    };

    fetchPatients();
  }, [session?.accessToken, debouncedQuery]);

  const handleSelectPatient = (patient: Patient) => {
    router.push(`/patients/${patient.patient_id}/notes/new`);
  };

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      });
    } catch {
      return dateStr;
    }
  };

  const PatientCard = ({ patient }: { patient: Patient }) => (
    <button
      onClick={() => handleSelectPatient(patient)}
      className="flex w-full items-center gap-4 rounded-lg border border-white/10 bg-slate-900/50 p-4 text-left transition-all hover:border-teal-500/30 hover:bg-slate-800/80"
    >
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-teal-500/10">
        <User className="h-5 w-5 text-teal-400" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-medium text-white truncate">
          {patient.first_name} {patient.last_name}
        </p>
        <div className="mt-0.5 flex items-center gap-3 text-xs text-slate-400">
          <span className="font-mono">MRN: {patient.mrn}</span>
          {patient.birth_date && (
            <span className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {formatDate(patient.birth_date)}
            </span>
          )}
          <span className="capitalize">{patient.gender}</span>
        </div>
      </div>
      <ChevronRight className="h-5 w-5 shrink-0 text-slate-600" />
    </button>
  );

  const showSearchResults = debouncedQuery.length > 0;

  return (
    <div className="min-h-screen bg-slate-950 p-6">
      <div className="mx-auto max-w-2xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3">
            <Link
              href="/dashboard"
              className="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-white/5 hover:text-white"
            >
              <ChevronLeft className="h-5 w-5" />
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-white">New Clinical Note</h1>
              <p className="text-sm text-slate-400">
                Select a patient to begin documentation
              </p>
            </div>
          </div>
        </div>

        {/* Search */}
        <div className="mb-6">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Search by name, MRN, or Cyprus ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              autoFocus
              className="w-full rounded-xl border border-white/10 bg-slate-900/50 py-3.5 pl-12 pr-4 text-white placeholder-slate-500 focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
            />
          </div>
        </div>

        {/* Search Results */}
        {showSearchResults && (
          <div className="mb-6">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-teal-400" />
              </div>
            ) : error ? (
              <div className="rounded-lg border border-red-500/30 bg-red-500/5 p-4 text-center text-sm text-red-300">
                {error}
              </div>
            ) : patients.length === 0 ? (
              <div className="rounded-xl border border-white/10 bg-slate-900/50 p-8 text-center">
                <User className="mx-auto h-8 w-8 text-slate-600" />
                <p className="mt-2 text-sm text-slate-400">
                  No patients match &ldquo;{debouncedQuery}&rdquo;
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  Try a different name, MRN, or ID number
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                <p className="mb-2 text-xs font-medium uppercase tracking-wider text-slate-500">
                  Search Results
                </p>
                {patients.map((patient) => (
                  <PatientCard key={patient.patient_id} patient={patient} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Recent Patients (shown when no search) */}
        {!showSearchResults && (
          <div>
            <p className="mb-3 text-xs font-medium uppercase tracking-wider text-slate-500">
              Recent Patients
            </p>
            {recentLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-teal-400" />
              </div>
            ) : recentPatients.length === 0 ? (
              <div className="rounded-xl border border-white/10 bg-slate-900/50 p-8 text-center">
                <FileText className="mx-auto h-8 w-8 text-slate-600" />
                <p className="mt-2 text-sm text-slate-400">
                  No recent patients
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  Use the search above to find a patient
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {recentPatients.map((patient) => (
                  <PatientCard key={patient.patient_id} patient={patient} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function NewNotePage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center bg-slate-950">
          <Loader2 className="h-12 w-12 animate-spin text-teal-400" />
        </div>
      }
    >
      <NewNoteContent />
    </Suspense>
  );
}
