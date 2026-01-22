"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Monitor,
  Smartphone,
  Tablet,
  Globe,
  Clock,
  MapPin,
  Trash2,
  AlertTriangle,
  Shield,
  CheckCircle,
  Loader2,
} from "lucide-react";
import { authApi, type ActiveSession } from "@/lib/api/auth";

// Device icon mapping
function getDeviceIcon(deviceName: string) {
  const name = deviceName.toLowerCase();
  if (name.includes("iphone") || name.includes("android phone")) {
    return Smartphone;
  }
  if (name.includes("ipad") || name.includes("tablet")) {
    return Tablet;
  }
  return Monitor;
}

// Format relative time
function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins} min ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;

  return date.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

// Format full date
function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function SessionsPage() {
  const router = useRouter();
  const [sessions, setSessions] = useState<ActiveSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [revokingId, setRevokingId] = useState<string | null>(null);
  const [revokingAll, setRevokingAll] = useState(false);
  const [showConfirmAll, setShowConfirmAll] = useState(false);

  useEffect(() => {
    loadSessions();
  }, []);

  async function loadSessions() {
    try {
      setLoading(true);
      setError(null);
      const data = await authApi.getSessions();
      setSessions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load sessions");
    } finally {
      setLoading(false);
    }
  }

  async function handleRevoke(sessionId: string) {
    try {
      setRevokingId(sessionId);
      await authApi.revokeSession(sessionId);
      setSessions(sessions.filter((s) => s.id !== sessionId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to revoke session");
    } finally {
      setRevokingId(null);
    }
  }

  async function handleRevokeAll() {
    try {
      setRevokingAll(true);
      const result = await authApi.revokeAllSessions();
      // Reload sessions to show only current
      await loadSessions();
      setShowConfirmAll(false);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to revoke sessions"
      );
    } finally {
      setRevokingAll(false);
    }
  }

  const currentSession = sessions.find((s) => s.is_current);
  const otherSessions = sessions.filter((s) => !s.is_current);

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <header className="border-b border-white/10 bg-slate-900/50 backdrop-blur-xl">
        <div className="mx-auto max-w-4xl px-6 py-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-500/20">
              <Shield className="h-5 w-5 text-teal-400" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-white">
                Active Sessions
              </h1>
              <p className="text-sm text-slate-400">
                Manage your logged-in devices
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-6 py-8">
        {/* Error Banner */}
        {error && (
          <div className="mb-6 flex items-center gap-3 rounded-lg border border-red-500/30 bg-red-500/10 p-4">
            <AlertTriangle className="h-5 w-5 text-red-400" />
            <p className="text-sm text-red-300">{error}</p>
            <button
              onClick={() => setError(null)}
              className="ml-auto text-red-400 hover:text-red-300"
            >
              ×
            </button>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-teal-400" />
          </div>
        ) : (
          <>
            {/* Current Session */}
            {currentSession && (
              <section className="mb-8">
                <h2 className="mb-4 text-sm font-medium uppercase tracking-wider text-slate-400">
                  Current Session
                </h2>
                <SessionCard session={currentSession} isCurrent />
              </section>
            )}

            {/* Other Sessions */}
            <section>
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-sm font-medium uppercase tracking-wider text-slate-400">
                  Other Sessions ({otherSessions.length})
                </h2>
                {otherSessions.length > 0 && (
                  <button
                    onClick={() => setShowConfirmAll(true)}
                    className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-1.5 text-sm text-red-400 transition-colors hover:bg-red-500/20"
                  >
                    <Trash2 className="h-4 w-4" />
                    Revoke All
                  </button>
                )}
              </div>

              {otherSessions.length === 0 ? (
                <div className="rounded-xl border border-white/10 bg-slate-900/50 p-8 text-center">
                  <Globe className="mx-auto h-12 w-12 text-slate-600" />
                  <p className="mt-3 text-slate-400">
                    No other active sessions
                  </p>
                  <p className="text-sm text-slate-500">
                    You&apos;re only logged in from this device
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {otherSessions.map((session) => (
                    <SessionCard
                      key={session.id}
                      session={session}
                      onRevoke={() => handleRevoke(session.id)}
                      isRevoking={revokingId === session.id}
                    />
                  ))}
                </div>
              )}
            </section>

            {/* Security Tip */}
            <div className="mt-8 rounded-xl border border-teal-500/20 bg-teal-500/5 p-4">
              <div className="flex items-start gap-3">
                <Shield className="mt-0.5 h-5 w-5 text-teal-400" />
                <div>
                  <p className="font-medium text-teal-300">Security Tip</p>
                  <p className="mt-1 text-sm text-slate-400">
                    If you see any sessions you don&apos;t recognize, revoke
                    them immediately and change your password. Enable MFA for
                    additional security.
                  </p>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Confirm Revoke All Modal */}
        {showConfirmAll && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div className="mx-4 max-w-md rounded-xl border border-white/10 bg-slate-900 p-6 shadow-xl">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-500/20">
                  <AlertTriangle className="h-5 w-5 text-red-400" />
                </div>
                <h3 className="text-lg font-semibold text-white">
                  Revoke All Sessions?
                </h3>
              </div>

              <p className="mt-4 text-slate-400">
                This will log you out from all devices except your current
                session. You&apos;ll need to log in again on those devices.
              </p>

              <div className="mt-6 flex gap-3">
                <button
                  onClick={() => setShowConfirmAll(false)}
                  className="flex-1 rounded-lg border border-white/10 bg-white/5 py-2 text-white transition-colors hover:bg-white/10"
                  disabled={revokingAll}
                >
                  Cancel
                </button>
                <button
                  onClick={handleRevokeAll}
                  disabled={revokingAll}
                  className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-red-600 py-2 text-white transition-colors hover:bg-red-700 disabled:opacity-50"
                >
                  {revokingAll ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Revoking...
                    </>
                  ) : (
                    "Revoke All"
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

// Session Card Component
function SessionCard({
  session,
  isCurrent = false,
  onRevoke,
  isRevoking = false,
}: {
  session: ActiveSession;
  isCurrent?: boolean;
  onRevoke?: () => void;
  isRevoking?: boolean;
}) {
  const DeviceIcon = getDeviceIcon(session.device_name);

  return (
    <div
      className={`rounded-xl border p-4 transition-colors ${
        isCurrent
          ? "border-teal-500/30 bg-teal-500/5"
          : "border-white/10 bg-slate-900/50 hover:border-white/20"
      }`}
    >
      <div className="flex items-start gap-4">
        {/* Device Icon */}
        <div
          className={`flex h-12 w-12 items-center justify-center rounded-lg ${
            isCurrent ? "bg-teal-500/20" : "bg-white/5"
          }`}
        >
          <DeviceIcon
            className={`h-6 w-6 ${isCurrent ? "text-teal-400" : "text-slate-400"}`}
          />
        </div>

        {/* Session Details */}
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="font-medium text-white">{session.device_name}</h3>
            {isCurrent && (
              <span className="flex items-center gap-1 rounded-full bg-teal-500/20 px-2 py-0.5 text-xs text-teal-400">
                <CheckCircle className="h-3 w-3" />
                Current
              </span>
            )}
          </div>

          <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-400">
            <span className="flex items-center gap-1">
              <MapPin className="h-3.5 w-3.5" />
              {session.ip_address}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="h-3.5 w-3.5" />
              Active {formatRelativeTime(session.last_activity)}
            </span>
          </div>

          <p className="mt-1 text-xs text-slate-500">
            First login: {formatDate(session.created_at)}
          </p>
        </div>

        {/* Revoke Button */}
        {!isCurrent && onRevoke && (
          <button
            onClick={onRevoke}
            disabled={isRevoking}
            className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-400 transition-colors hover:bg-red-500/20 disabled:opacity-50"
          >
            {isRevoking ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Trash2 className="h-4 w-4" />
            )}
            {isRevoking ? "Revoking..." : "Revoke"}
          </button>
        )}
      </div>
    </div>
  );
}
