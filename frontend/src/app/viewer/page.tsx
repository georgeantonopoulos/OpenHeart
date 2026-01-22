"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  X,
  Maximize2,
  Minimize2,
  ExternalLink,
  AlertTriangle,
  Loader2,
  FileText,
  Image,
} from "lucide-react";
import { getViewerUrl, type DicomStudy, getStudy } from "@/lib/api/imaging";

function ViewerContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const studyUid = searchParams.get("study");
  const returnUrl = searchParams.get("return");

  const [viewerUrl, setViewerUrl] = useState<string | null>(null);
  const [study, setStudy] = useState<DicomStudy | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);

  useEffect(() => {
    if (studyUid) {
      loadViewer(studyUid);
    } else {
      setError("No study specified");
      setLoading(false);
    }
  }, [studyUid]);

  async function loadViewer(uid: string) {
    try {
      setLoading(true);
      setError(null);

      // Get viewer URL and study details in parallel
      const [urlResponse, studyData] = await Promise.all([
        getViewerUrl(uid),
        getStudy(uid).catch(() => null), // Study details are optional
      ]);

      setViewerUrl(urlResponse.viewer_url);
      setStudy(studyData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load viewer");
    } finally {
      setLoading(false);
    }
  }

  function handleClose() {
    if (returnUrl) {
      router.push(returnUrl);
    } else {
      router.back();
    }
  }

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  }

  function handleOpenExternal() {
    if (viewerUrl) {
      window.open(viewerUrl, "_blank", "noopener,noreferrer");
    }
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950">
        <div className="text-center">
          <Loader2 className="mx-auto h-12 w-12 animate-spin text-teal-400" />
          <p className="mt-4 text-slate-400">Loading DICOM viewer...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950">
        <div className="mx-4 max-w-md text-center">
          <AlertTriangle className="mx-auto h-12 w-12 text-red-400" />
          <h2 className="mt-4 text-lg font-semibold text-white">
            Failed to Load Viewer
          </h2>
          <p className="mt-2 text-slate-400">{error}</p>
          <button
            onClick={handleClose}
            className="mt-6 rounded-lg bg-teal-600 px-6 py-2 text-white hover:bg-teal-700"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-slate-950">
      {/* Header Bar */}
      <header className="flex items-center justify-between border-b border-white/10 bg-slate-900 px-4 py-2">
        <div className="flex items-center gap-4">
          <button
            onClick={handleClose}
            className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-white hover:bg-white/10"
          >
            <X className="h-4 w-4" />
            Close
          </button>

          {study && (
            <div className="hidden md:block">
              <h1 className="font-medium text-white">
                {study.study_description || "DICOM Study"}
              </h1>
              <p className="text-xs text-slate-400">
                {study.patient?.patient_name} • {study.study_date}
              </p>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Toggle sidebar */}
          <button
            onClick={() => setShowSidebar(!showSidebar)}
            className={`rounded-lg p-2 text-slate-400 hover:bg-white/10 hover:text-white ${
              showSidebar ? "bg-white/10" : ""
            }`}
            title="Toggle study info"
          >
            <FileText className="h-5 w-5" />
          </button>

          {/* Fullscreen toggle */}
          <button
            onClick={toggleFullscreen}
            className="rounded-lg p-2 text-slate-400 hover:bg-white/10 hover:text-white"
            title={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
          >
            {isFullscreen ? (
              <Minimize2 className="h-5 w-5" />
            ) : (
              <Maximize2 className="h-5 w-5" />
            )}
          </button>

          {/* Open in new tab */}
          <button
            onClick={handleOpenExternal}
            className="rounded-lg p-2 text-slate-400 hover:bg-white/10 hover:text-white"
            title="Open in new tab"
          >
            <ExternalLink className="h-5 w-5" />
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* OHIF Viewer iframe */}
        <div className="flex-1">
          {viewerUrl ? (
            <iframe
              src={viewerUrl}
              className="h-full w-full border-0"
              title="OHIF DICOM Viewer"
              allow="fullscreen"
            />
          ) : (
            <div className="flex h-full items-center justify-center">
              <div className="text-center text-slate-500">
                <Image className="mx-auto h-16 w-16" />
                <p className="mt-4">Viewer not available</p>
              </div>
            </div>
          )}
        </div>

        {/* Study Info Sidebar */}
        {showSidebar && study && (
          <aside className="w-80 overflow-y-auto border-l border-white/10 bg-slate-900/50 p-4">
            <h2 className="text-sm font-medium uppercase tracking-wider text-slate-400">
              Study Information
            </h2>

            <div className="mt-4 space-y-4">
              {/* Patient */}
              <InfoSection title="Patient">
                <InfoRow label="Name" value={study.patient?.patient_name} />
                <InfoRow label="ID" value={study.patient?.patient_id} />
                <InfoRow label="DOB" value={study.patient?.birth_date} />
                <InfoRow label="Sex" value={study.patient?.sex} />
              </InfoSection>

              {/* Study */}
              <InfoSection title="Study">
                <InfoRow label="Date" value={study.study_date} />
                <InfoRow label="Description" value={study.study_description} />
                <InfoRow label="Accession" value={study.accession_number} />
                <InfoRow label="Institution" value={study.institution_name} />
                <InfoRow
                  label="Referring"
                  value={study.referring_physician}
                />
                <InfoRow
                  label="Modalities"
                  value={study.modalities.join(", ")}
                />
              </InfoSection>

              {/* Series */}
              <InfoSection title={`Series (${study.series_count})`}>
                {study.series.map((series, idx) => (
                  <div
                    key={series.series_instance_uid}
                    className="rounded-lg border border-white/10 bg-white/5 p-2 text-sm"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-white">
                        {series.series_description || `Series ${idx + 1}`}
                      </span>
                      <span className="rounded bg-white/10 px-1.5 py-0.5 text-xs text-slate-400">
                        {series.modality}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-slate-500">
                      {series.instance_count} images
                    </p>
                  </div>
                ))}
              </InfoSection>

              {/* Study UID (for debugging) */}
              <InfoSection title="Technical">
                <div className="rounded-lg border border-white/10 bg-white/5 p-2">
                  <p className="text-xs text-slate-500">Study Instance UID</p>
                  <p className="mt-1 break-all font-mono text-xs text-slate-400">
                    {study.study_instance_uid}
                  </p>
                </div>
              </InfoSection>
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}

// Helper components
function InfoSection({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <h3 className="text-xs font-medium uppercase tracking-wider text-slate-500">
        {title}
      </h3>
      <div className="mt-2 space-y-1">{children}</div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value?: string | null }) {
  if (!value) return null;
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-slate-500">{label}</span>
      <span className="text-white">{value}</span>
    </div>
  );
}

// Main page with Suspense boundary
export default function ViewerPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center bg-slate-950">
          <Loader2 className="h-12 w-12 animate-spin text-teal-400" />
        </div>
      }
    >
      <ViewerContent />
    </Suspense>
  );
}
