'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import {
  ChevronLeft,
  ChevronRight,
  Plus,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import {
  listAppointments,
  checkInAppointment,
  startEncounterFromAppointment,
  type Appointment,
} from '@/lib/api/appointments';
import WeekView from '@/components/calendar/WeekView';
import DayView from '@/components/calendar/DayView';

type ViewMode = 'week' | 'day';

function AppointmentsContent() {
  const { data: session } = useSession();
  const router = useRouter();

  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [viewMode, setViewMode] = useState<ViewMode>('week');

  useEffect(() => {
    if (session?.accessToken) {
      loadAppointments();
    }
  }, [session?.accessToken, currentDate, viewMode]);

  async function loadAppointments() {
    try {
      setLoading(true);
      setError(null);

      const { from, to } = getDateRange();
      const data = await listAppointments(session!.accessToken, {
        from_date: from,
        to_date: to,
      });
      setAppointments(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load appointments');
    } finally {
      setLoading(false);
    }
  }

  function getDateRange(): { from: string; to: string } {
    if (viewMode === 'day') {
      const dateStr = currentDate.toISOString().split('T')[0];
      return { from: dateStr, to: dateStr };
    }
    // Week view: Monday to Sunday
    const start = new Date(currentDate);
    const day = start.getDay();
    const diff = start.getDate() - day + (day === 0 ? -6 : 1);
    start.setDate(diff);
    const end = new Date(start);
    end.setDate(start.getDate() + 6);
    return {
      from: start.toISOString().split('T')[0],
      to: end.toISOString().split('T')[0],
    };
  }

  function navigateDate(direction: number) {
    const next = new Date(currentDate);
    if (viewMode === 'week') {
      next.setDate(next.getDate() + direction * 7);
    } else {
      next.setDate(next.getDate() + direction);
    }
    setCurrentDate(next);
  }

  function goToToday() {
    setCurrentDate(new Date());
  }

  async function handleCheckIn(appointment: Appointment) {
    try {
      await checkInAppointment(session!.accessToken, appointment.appointment_id);
      await loadAppointments();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Check-in failed');
    }
  }

  async function handleStartEncounter(appointment: Appointment) {
    try {
      await startEncounterFromAppointment(
        session!.accessToken,
        appointment.appointment_id
      );
      router.push(`/patients/${appointment.patient_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start encounter');
    }
  }

  function handleAppointmentClick(_appointment: Appointment) {
    // Could open a detail panel or navigate
  }

  if (!session) return null;

  return (
    <div className="min-h-screen bg-slate-950 p-6">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Appointments</h1>
            <p className="mt-1 text-sm text-slate-400">
              Schedule and manage patient appointments
            </p>
          </div>
          <button
            onClick={() => router.push('/appointments/new')}
            className="flex items-center gap-2 rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-500 transition-colors"
          >
            <Plus className="h-4 w-4" />
            New Appointment
          </button>
        </div>

        {/* Calendar Controls */}
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigateDate(-1)}
              className="rounded p-1.5 text-slate-400 hover:bg-white/10 hover:text-white"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <button
              onClick={goToToday}
              className="rounded-lg border border-white/10 px-3 py-1.5 text-sm text-slate-300 hover:bg-white/5"
            >
              Today
            </button>
            <button
              onClick={() => navigateDate(1)}
              className="rounded p-1.5 text-slate-400 hover:bg-white/10 hover:text-white"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
            <h2 className="ml-2 text-lg font-medium text-white">
              {viewMode === 'week'
                ? `Week of ${currentDate.toLocaleDateString('en-CY', { month: 'short', day: 'numeric', year: 'numeric' })}`
                : currentDate.toLocaleDateString('en-CY', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
            </h2>
          </div>

          {/* View Toggle */}
          <div className="flex rounded-lg border border-white/10 overflow-hidden">
            <button
              onClick={() => setViewMode('week')}
              className={`px-3 py-1.5 text-sm ${viewMode === 'week'
                ? 'bg-teal-600 text-white'
                : 'text-slate-400 hover:text-white'
                }`}
            >
              Week
            </button>
            <button
              onClick={() => setViewMode('day')}
              className={`px-3 py-1.5 text-sm ${viewMode === 'day'
                ? 'bg-teal-600 text-white'
                : 'text-slate-400 hover:text-white'
                }`}
            >
              Day
            </button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 flex items-center gap-3 rounded-lg border border-red-500/30 bg-red-500/10 p-3">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {/* Calendar View */}
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin text-teal-400" />
            <span className="ml-3 text-slate-400">Loading appointments...</span>
          </div>
        ) : viewMode === 'week' ? (
          <WeekView
            appointments={appointments}
            currentDate={currentDate}
            onAppointmentClick={handleAppointmentClick}
            onCheckIn={handleCheckIn}
            onStartEncounter={handleStartEncounter}
          />
        ) : (
          <DayView
            appointments={appointments}
            currentDate={currentDate}
            onAppointmentClick={handleAppointmentClick}
            onCheckIn={handleCheckIn}
            onStartEncounter={handleStartEncounter}
          />
        )}
      </div>
    </div>
  );
}

export default function AppointmentsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-slate-950">
          <Loader2 className="h-8 w-8 animate-spin text-teal-400" />
        </div>
      }
    >
      <AppointmentsContent />
    </Suspense>
  );
}
