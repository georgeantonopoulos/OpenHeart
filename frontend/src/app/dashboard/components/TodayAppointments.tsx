'use client';

import Link from 'next/link';
import { useSession } from 'next-auth/react';
import { useQuery } from '@tanstack/react-query';
import { getTodayAppointments, Appointment } from '@/lib/api/appointments';

const typeLabels: Record<string, { label: string; color: string }> = {
  consultation: { label: 'Consultation', color: 'bg-purple-500/20 text-purple-300' },
  follow_up: { label: 'Follow-up', color: 'bg-blue-500/20 text-blue-300' },
  echo: { label: 'Echo', color: 'bg-teal-500/20 text-teal-300' },
  stress_test: { label: 'Stress Test', color: 'bg-amber-500/20 text-amber-300' },
  holter: { label: 'Holter', color: 'bg-rose-500/20 text-rose-300' },
  procedure: { label: 'Procedure', color: 'bg-red-500/20 text-red-300' },
  ecg: { label: 'ECG', color: 'bg-green-500/20 text-green-300' },
  pre_op: { label: 'Pre-Op', color: 'bg-orange-500/20 text-orange-300' },
};

const statusStyles: Record<string, { bg: string; dot: string }> = {
  scheduled: { bg: '', dot: 'bg-slate-400' },
  confirmed: { bg: '', dot: 'bg-blue-300' },
  checked_in: { bg: 'bg-blue-900/10', dot: 'bg-blue-400' },
  in_progress: { bg: 'bg-green-900/10', dot: 'bg-green-400 animate-pulse' },
  completed: { bg: 'bg-slate-800/50', dot: 'bg-slate-500' },
  cancelled: { bg: 'bg-slate-800/50', dot: 'bg-slate-600' },
  no_show: { bg: 'bg-red-900/10', dot: 'bg-red-400' },
};

/**
 * Today's Appointments component.
 *
 * Shows the day's schedule fetched from the appointments API.
 */
export default function TodayAppointments() {
  const { data: session } = useSession();

  const { data: appointments = [], isLoading } = useQuery({
    queryKey: ['today-appointments'],
    queryFn: () => getTodayAppointments(session!.accessToken!),
    enabled: !!session?.accessToken,
    staleTime: 30000,
  });

  const now = new Date();

  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-CY', { hour: '2-digit', minute: '2-digit', hour12: false });
  };

  const isPastAppointment = (apt: Appointment) => {
    if (apt.status === 'completed' || apt.status === 'cancelled') return true;
    return new Date(apt.end_time) < now;
  };

  return (
    <div className="bg-slate-900 rounded-lg border border-slate-800">
      <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Today&apos;s Schedule</h2>
        <Link
          href="/appointments"
          className="text-sm text-rose-400 hover:text-rose-300 transition-colors"
        >
          View All
        </Link>
      </div>

      <div className="divide-y divide-slate-800">
        {isLoading ? (
          // Loading skeleton
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="px-4 py-3 animate-pulse">
              <div className="flex items-center gap-4">
                <div className="w-14 h-4 bg-slate-700 rounded" />
                <div className="w-2 h-2 rounded-full bg-slate-700" />
                <div className="flex-1">
                  <div className="h-4 w-36 bg-slate-700 rounded mb-1" />
                  <div className="h-3 w-24 bg-slate-800 rounded" />
                </div>
                <div className="h-5 w-16 bg-slate-800 rounded" />
              </div>
            </div>
          ))
        ) : appointments.length === 0 ? (
          <div className="p-8 text-center text-slate-400">
            <svg
              className="mx-auto h-12 w-12 text-slate-500 mb-3"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <p>No appointments scheduled for today</p>
          </div>
        ) : (
          appointments.map((apt: Appointment) => {
            const typeInfo = typeLabels[apt.appointment_type] ?? { label: apt.appointment_type, color: 'bg-slate-500/20 text-slate-300' };
            const statusStyle = statusStyles[apt.status] ?? statusStyles.scheduled;
            const past = isPastAppointment(apt);

            return (
              <Link
                key={apt.appointment_id}
                href={`/patients/${apt.patient_id}`}
                className={`block px-4 py-3 hover:bg-slate-800/50 transition-colors ${statusStyle.bg} ${
                  past && apt.status !== 'in_progress' ? 'opacity-60' : ''
                }`}
              >
                <div className="flex items-center gap-4">
                  {/* Time */}
                  <div className="w-14 flex-shrink-0">
                    <span className="text-sm font-mono text-slate-300">
                      {formatTime(apt.start_time)}
                    </span>
                  </div>

                  {/* Status dot */}
                  <div className={`w-2 h-2 rounded-full ${statusStyle.dot}`} />

                  {/* Patient info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-white font-medium truncate">
                        {apt.patient_name ?? `Patient #${apt.patient_id}`}
                      </span>
                      {apt.gesy_referral_id && (
                        <span className="px-1.5 py-0.5 text-[10px] bg-teal-900/50 text-teal-300 rounded">
                          Gesy
                        </span>
                      )}
                    </div>
                    {(apt.notes || apt.reason) && (
                      <p className="text-xs text-slate-400 truncate mt-0.5">{apt.notes || apt.reason}</p>
                    )}
                  </div>

                  {/* Type badge */}
                  <span className={`px-2 py-1 text-xs rounded ${typeInfo.color}`}>
                    {typeInfo.label}
                  </span>
                </div>
              </Link>
            );
          })
        )}
      </div>

      {/* Quick add */}
      <div className="px-4 py-3 border-t border-slate-800">
        <Link
          href="/appointments/new"
          className="flex items-center justify-center gap-2 w-full py-2 text-sm text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Appointment
        </Link>
      </div>
    </div>
  );
}
