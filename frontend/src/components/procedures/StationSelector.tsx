"use client";

import { useState, useEffect } from "react";
import {
  Monitor,
  HeartPulse,
  Crosshair,
  Scan,
  AlertCircle,
  Loader2,
  MapPin,
  CheckCircle2,
} from "lucide-react";
import {
  listStations,
  type WorklistStation,
  type ImagingModality,
} from "@/lib/api/procedures";

interface StationSelectorProps {
  accessToken: string;
  modality?: ImagingModality;
  selectedAeTitle?: string;
  onSelect: (station: WorklistStation) => void;
  disabled?: boolean;
}

const modalityIcons: Record<ImagingModality, typeof HeartPulse> = {
  US: HeartPulse,
  XA: Crosshair,
  CT: Scan,
  MR: Monitor,
  NM: Monitor,
};

const modalityLabels: Record<ImagingModality, string> = {
  US: "Echo",
  XA: "Cath Lab",
  CT: "CT Scanner",
  MR: "MRI",
  NM: "Nuclear",
};

export function StationSelector({
  accessToken,
  modality,
  selectedAeTitle,
  onSelect,
  disabled = false,
}: StationSelectorProps) {
  const [stations, setStations] = useState<WorklistStation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStations();
  }, [accessToken]);

  async function loadStations() {
    try {
      setLoading(true);
      setError(null);
      const data = await listStations(accessToken);
      setStations(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load stations");
    } finally {
      setLoading(false);
    }
  }

  // Filter stations by modality if specified
  const filteredStations = modality
    ? stations.filter((s) => s.modality === modality)
    : stations;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-teal-400" />
        <span className="ml-2 text-slate-400">Loading stations...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center gap-2 py-8 text-red-400">
        <AlertCircle className="h-5 w-5" />
        <span>{error}</span>
      </div>
    );
  }

  if (filteredStations.length === 0) {
    return (
      <div className="rounded-lg border border-white/10 bg-white/5 p-6 text-center">
        <Monitor className="mx-auto h-10 w-10 text-slate-500" />
        <p className="mt-2 text-slate-400">
          {modality
            ? `No ${modalityLabels[modality]} stations configured`
            : "No imaging stations configured"}
        </p>
        <p className="mt-1 text-sm text-slate-500">
          Contact your clinic admin to add equipment
        </p>
      </div>
    );
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {filteredStations.map((station) => {
        const Icon = modalityIcons[station.modality] || Monitor;
        const isSelected = selectedAeTitle === station.ae_title;

        return (
          <button
            key={station.id}
            type="button"
            onClick={() => onSelect(station)}
            disabled={disabled || !station.is_active}
            className={`
              relative flex items-start gap-3 rounded-lg border p-4 text-left
              transition-all duration-200
              ${
                isSelected
                  ? "border-teal-500 bg-teal-500/10"
                  : station.is_active
                    ? "border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/10"
                    : "border-white/5 bg-white/[0.02] opacity-50 cursor-not-allowed"
              }
              ${disabled ? "cursor-not-allowed opacity-50" : ""}
            `}
          >
            {/* Selection indicator */}
            {isSelected && (
              <div className="absolute right-3 top-3">
                <CheckCircle2 className="h-5 w-5 text-teal-400" />
              </div>
            )}

            {/* Icon */}
            <div
              className={`
              rounded-lg p-2
              ${isSelected ? "bg-teal-500/20" : "bg-white/10"}
            `}
            >
              <Icon
                className={`h-5 w-5 ${isSelected ? "text-teal-400" : "text-slate-400"}`}
              />
            </div>

            {/* Station info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span
                  className={`font-medium ${isSelected ? "text-white" : "text-slate-200"}`}
                >
                  {station.station_name}
                </span>
                <span className="rounded bg-white/10 px-1.5 py-0.5 text-xs text-slate-400">
                  {modalityLabels[station.modality]}
                </span>
              </div>

              <div className="mt-1 space-y-0.5">
                <p className="text-sm text-slate-500 font-mono">
                  AE: {station.ae_title}
                </p>
                {station.location && (
                  <p className="flex items-center gap-1 text-sm text-slate-500">
                    <MapPin className="h-3 w-3" />
                    {station.location}
                  </p>
                )}
                {station.manufacturer && (
                  <p className="text-xs text-slate-600">
                    {station.manufacturer}
                    {station.model && ` ${station.model}`}
                  </p>
                )}
              </div>

              {/* Status indicator */}
              {!station.is_active && (
                <p className="mt-2 text-xs text-amber-500">Offline</p>
              )}
              {station.last_query_at && station.is_active && (
                <p className="mt-2 text-xs text-slate-600">
                  Last query: {formatRelativeTime(station.last_query_at)}
                </p>
              )}
            </div>
          </button>
        );
      })}
    </div>
  );
}

function formatRelativeTime(dateStr: string): string {
  try {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  } catch {
    return "Unknown";
  }
}

// Compact version for forms
export function StationDropdown({
  accessToken,
  modality,
  value,
  onChange,
  disabled = false,
}: {
  accessToken: string;
  modality?: ImagingModality;
  value?: string;
  onChange: (aeTitle: string) => void;
  disabled?: boolean;
}) {
  const [stations, setStations] = useState<WorklistStation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await listStations(accessToken);
        setStations(data);
      } catch {
        // Ignore errors for dropdown
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [accessToken]);

  const filteredStations = modality
    ? stations.filter((s) => s.modality === modality && s.is_active)
    : stations.filter((s) => s.is_active);

  return (
    <select
      value={value || ""}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled || loading}
      className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5
                 text-white focus:border-teal-500 focus:outline-none focus:ring-1
                 focus:ring-teal-500 disabled:cursor-not-allowed disabled:opacity-50"
    >
      <option value="" className="bg-slate-900">
        {loading ? "Loading..." : "Select station..."}
      </option>
      {filteredStations.map((station) => (
        <option key={station.id} value={station.ae_title} className="bg-slate-900">
          {station.station_name} ({station.ae_title})
        </option>
      ))}
    </select>
  );
}
