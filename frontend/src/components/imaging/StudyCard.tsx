"use client";

import { useState } from "react";
import {
  Calendar,
  FileText,
  Image,
  Maximize2,
  MoreVertical,
  User,
  Activity,
  Heart,
} from "lucide-react";
import {
  type DicomStudy,
  type Modality,
  formatModality,
  formatStudyDate,
  getModalityColor,
  getStudyThumbnailUrl,
} from "@/lib/api/imaging";

interface StudyCardProps {
  study: DicomStudy;
  onView?: () => void;
  onViewMeasurements?: () => void;
  isSelected?: boolean;
  showPatientInfo?: boolean;
}

// Modality icon mapping
function getModalityIcon(modality: Modality) {
  switch (modality) {
    case "US":
      return Heart; // Echo
    case "XA":
      return Activity; // Cath
    case "ECG":
      return Activity;
    default:
      return Image;
  }
}

export function StudyCard({
  study,
  onView,
  onViewMeasurements,
  isSelected = false,
  showPatientInfo = false,
}: StudyCardProps) {
  const [thumbnailError, setThumbnailError] = useState(false);
  const [showMenu, setShowMenu] = useState(false);

  const primaryModality = study.modalities[0] || "SR";
  const ModalityIcon = getModalityIcon(primaryModality);
  const thumbnailUrl = getStudyThumbnailUrl(study.study_instance_uid);

  return (
    <div
      className={`group relative rounded-xl border transition-all ${
        isSelected
          ? "border-teal-500/50 bg-teal-500/5 ring-2 ring-teal-500/20"
          : "border-white/10 bg-slate-900/50 hover:border-white/20"
      }`}
    >
      {/* Thumbnail / Placeholder */}
      <div className="relative aspect-video overflow-hidden rounded-t-xl bg-slate-800">
        {!thumbnailError ? (
          <img
            src={thumbnailUrl}
            alt={study.study_description || "Study"}
            className="h-full w-full object-cover transition-transform group-hover:scale-105"
            onError={() => setThumbnailError(true)}
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center">
            <ModalityIcon className="h-12 w-12 text-slate-600" />
          </div>
        )}

        {/* Modality badges */}
        <div className="absolute left-2 top-2 flex flex-wrap gap-1">
          {study.modalities.map((mod) => (
            <span
              key={mod}
              className={`rounded-full border px-2 py-0.5 text-xs font-medium ${getModalityColor(
                mod
              )}`}
            >
              {mod}
            </span>
          ))}
        </div>

        {/* Quick view button (on hover) */}
        {onView && (
          <button
            onClick={onView}
            className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 transition-opacity group-hover:opacity-100"
          >
            <div className="flex items-center gap-2 rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-teal-700">
              <Maximize2 className="h-4 w-4" />
              Open Viewer
            </div>
          </button>
        )}

        {/* Menu button */}
        <div className="absolute right-2 top-2">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="rounded-lg bg-black/50 p-1.5 text-white opacity-0 transition-opacity hover:bg-black/70 group-hover:opacity-100"
          >
            <MoreVertical className="h-4 w-4" />
          </button>

          {/* Dropdown menu */}
          {showMenu && (
            <div className="absolute right-0 top-full z-10 mt-1 w-48 rounded-lg border border-white/10 bg-slate-900 py-1 shadow-xl">
              {onView && (
                <button
                  onClick={() => {
                    setShowMenu(false);
                    onView();
                  }}
                  className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-slate-300 hover:bg-white/5"
                >
                  <Maximize2 className="h-4 w-4" />
                  Open in Viewer
                </button>
              )}
              {onViewMeasurements && primaryModality === "US" && (
                <button
                  onClick={() => {
                    setShowMenu(false);
                    onViewMeasurements();
                  }}
                  className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-slate-300 hover:bg-white/5"
                >
                  <FileText className="h-4 w-4" />
                  View Measurements
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Study Info */}
      <div className="p-4">
        {/* Description */}
        <h3 className="font-medium text-white line-clamp-1">
          {study.study_description || formatModality(primaryModality)}
        </h3>

        {/* Patient info (optional) */}
        {showPatientInfo && study.patient && (
          <div className="mt-1 flex items-center gap-1.5 text-sm text-slate-400">
            <User className="h-3.5 w-3.5" />
            <span>{study.patient.patient_name}</span>
          </div>
        )}

        {/* Date and series count */}
        <div className="mt-2 flex items-center gap-4 text-xs text-slate-500">
          <span className="flex items-center gap-1">
            <Calendar className="h-3.5 w-3.5" />
            {formatStudyDate(study.study_date)}
          </span>
          <span className="flex items-center gap-1">
            <Image className="h-3.5 w-3.5" />
            {study.series_count} series
          </span>
        </div>

        {/* Accession number */}
        {study.accession_number && (
          <p className="mt-1 text-xs text-slate-600">
            ACC# {study.accession_number}
          </p>
        )}
      </div>
    </div>
  );
}

// Compact study row for lists
export function StudyRow({
  study,
  onView,
  showPatientInfo = false,
}: StudyCardProps) {
  const primaryModality = study.modalities[0] || "SR";
  const ModalityIcon = getModalityIcon(primaryModality);

  return (
    <div
      className="flex items-center gap-4 rounded-lg border border-white/10 bg-slate-900/50 p-3 transition-colors hover:border-white/20 hover:bg-slate-900/80"
      onClick={onView}
      role="button"
      tabIndex={0}
    >
      {/* Modality icon */}
      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-white/5">
        <ModalityIcon className="h-5 w-5 text-slate-400" />
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h4 className="font-medium text-white truncate">
            {study.study_description || formatModality(primaryModality)}
          </h4>
          {study.modalities.map((mod) => (
            <span
              key={mod}
              className={`shrink-0 rounded-full border px-1.5 py-0.5 text-xs ${getModalityColor(
                mod
              )}`}
            >
              {mod}
            </span>
          ))}
        </div>
        <div className="mt-0.5 flex items-center gap-3 text-xs text-slate-500">
          {showPatientInfo && study.patient && (
            <span>{study.patient.patient_name}</span>
          )}
          <span>{formatStudyDate(study.study_date)}</span>
          {study.accession_number && (
            <span>ACC# {study.accession_number}</span>
          )}
        </div>
      </div>

      {/* View button */}
      {onView && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onView();
          }}
          className="flex items-center gap-1 rounded-lg bg-white/5 px-3 py-1.5 text-sm text-slate-300 transition-colors hover:bg-white/10"
        >
          <Maximize2 className="h-3.5 w-3.5" />
          View
        </button>
      )}
    </div>
  );
}
