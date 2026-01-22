'use client';

import Link from 'next/link';

interface Appointment {
  id: string;
  time: string;
  patientId: string;
  patientName: string;
  type: 'follow_up' | 'new_patient' | 'echo' | 'stress_test' | 'device_check';
  status: 'scheduled' | 'checked_in' | 'in_progress' | 'completed' | 'no_show';
  isGesy: boolean;
  notes?: string;
}

/**
 * Today's Appointments component.
 *
 * Shows the day's schedule with patient links and appointment status.
 */
export default function TodayAppointments() {
  // TODO: Replace with real data from appointments API
  const appointments: Appointment[] = [
    {
      id: '1',
      time: '09:00',
      patientId: '101',
      patientName: 'Μαρία Παπαδοπούλου',
      type: 'follow_up',
      status: 'completed',
      isGesy: true,
    },
    {
      id: '2',
      time: '09:30',
      patientId: '102',
      patientName: 'Ανδρέας Χριστοδούλου',
      type: 'echo',
      status: 'completed',
      isGesy: true,
    },
    {
      id: '3',
      time: '10:15',
      patientId: '103',
      patientName: 'Elena Georgiou',
      type: 'new_patient',
      status: 'in_progress',
      isGesy: false,
      notes: 'Referral from Dr. Stavrou',
    },
    {
      id: '4',
      time: '11:00',
      patientId: '104',
      patientName: 'Κώστας Νικολάου',
      type: 'device_check',
      status: 'checked_in',
      isGesy: true,
      notes: 'ICD check - 6 month',
    },
    {
      id: '5',
      time: '11:45',
      patientId: '105',
      patientName: 'Sophia Antoniou',
      type: 'stress_test',
      status: 'scheduled',
      isGesy: true,
    },
    {
      id: '6',
      time: '14:00',
      patientId: '106',
      patientName: 'Γιώργος Ιωάννου',
      type: 'follow_up',
      status: 'scheduled',
      isGesy: true,
      notes: 'Post-MI 3 month',
    },
  ];

  const typeLabels: Record<string, { label: string; color: string }> = {
    follow_up: { label: 'Follow-up', color: 'bg-blue-500/20 text-blue-300' },
    new_patient: { label: 'New Patient', color: 'bg-purple-500/20 text-purple-300' },
    echo: { label: 'Echo', color: 'bg-teal-500/20 text-teal-300' },
    stress_test: { label: 'Stress Test', color: 'bg-amber-500/20 text-amber-300' },
    device_check: { label: 'Device Check', color: 'bg-rose-500/20 text-rose-300' },
  };

  const statusStyles: Record<string, { bg: string; dot: string }> = {
    scheduled: { bg: '', dot: 'bg-slate-400' },
    checked_in: { bg: 'bg-blue-900/10', dot: 'bg-blue-400' },
    in_progress: { bg: 'bg-green-900/10', dot: 'bg-green-400 animate-pulse' },
    completed: { bg: 'bg-slate-800/50', dot: 'bg-slate-500' },
    no_show: { bg: 'bg-red-900/10', dot: 'bg-red-400' },
  };

  const currentTime = new Date();
  const currentHour = currentTime.getHours();
  const currentMinute = currentTime.getMinutes();

  return (
    <div className="bg-slate-900 rounded-lg border border-slate-800">
      <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Today's Schedule</h2>
        <Link
          href="/appointments"
          className="text-sm text-rose-400 hover:text-rose-300 transition-colors"
        >
          View All
        </Link>
      </div>

      <div className="divide-y divide-slate-800">
        {appointments.length === 0 ? (
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
          appointments.map((apt) => {
            const typeInfo = typeLabels[apt.type];
            const statusStyle = statusStyles[apt.status];
            const [hours, minutes] = apt.time.split(':').map(Number);
            const isPast =
              apt.status === 'completed' ||
              hours < currentHour ||
              (hours === currentHour && minutes < currentMinute);

            return (
              <Link
                key={apt.id}
                href={`/patients/${apt.patientId}`}
                className={`block px-4 py-3 hover:bg-slate-800/50 transition-colors ${statusStyle.bg} ${
                  isPast && apt.status !== 'in_progress' ? 'opacity-60' : ''
                }`}
              >
                <div className="flex items-center gap-4">
                  {/* Time */}
                  <div className="w-14 flex-shrink-0">
                    <span className="text-sm font-mono text-slate-300">{apt.time}</span>
                  </div>

                  {/* Status dot */}
                  <div className={`w-2 h-2 rounded-full ${statusStyle.dot}`} />

                  {/* Patient info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-white font-medium truncate">{apt.patientName}</span>
                      {apt.isGesy && (
                        <span className="px-1.5 py-0.5 text-[10px] bg-teal-900/50 text-teal-300 rounded">
                          Gesy
                        </span>
                      )}
                    </div>
                    {apt.notes && (
                      <p className="text-xs text-slate-400 truncate mt-0.5">{apt.notes}</p>
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
