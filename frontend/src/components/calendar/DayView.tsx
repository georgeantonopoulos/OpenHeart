'use client';

import {
  type Appointment,
  getAppointmentStatusColor,
  formatAppointmentType,
  formatAppointmentStatus,
} from '@/lib/api/appointments';
import { Clock, MapPin, FileText } from 'lucide-react';

interface DayViewProps {
  appointments: Appointment[];
  currentDate: Date;
  onAppointmentClick: (appointment: Appointment) => void;
  onCheckIn?: (appointment: Appointment) => void;
  onStartEncounter?: (appointment: Appointment) => void;
}

const HOURS = Array.from({ length: 15 }, (_, i) => i + 7); // 07:00 - 21:00

export default function DayView({
  appointments,
  currentDate,
  onAppointmentClick,
  onCheckIn,
  onStartEncounter,
}: DayViewProps) {
  const getAppointmentsForHour = (hour: number) => {
    return appointments.filter((a) => {
      const start = new Date(a.start_time);
      return start.getHours() === hour;
    });
  };

  return (
    <div className="rounded-lg border border-white/10 bg-slate-900">
      {/* Header */}
      <div className="border-b border-white/10 px-4 py-3">
        <h2 className="text-lg font-semibold text-white">
          {currentDate.toLocaleDateString('en-CY', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
          })}
        </h2>
        <p className="text-sm text-slate-400">
          {appointments.length} appointment{appointments.length !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Time slots */}
      <div className="divide-y divide-white/5">
        {HOURS.map((hour) => {
          const hourAppointments = getAppointmentsForHour(hour);

          return (
            <div key={hour} className="flex min-h-[64px]">
              {/* Time label */}
              <div className="w-16 flex-shrink-0 p-2 text-right">
                <span className="text-sm text-slate-500">
                  {hour.toString().padStart(2, '0')}:00
                </span>
              </div>

              {/* Appointments */}
              <div className="flex-1 p-1 space-y-1">
                {hourAppointments.map((appt) => (
                  <div
                    key={appt.appointment_id}
                    onClick={() => onAppointmentClick(appt)}
                    className="cursor-pointer rounded-lg border border-white/10 bg-slate-800 p-3 hover:bg-slate-700/50 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <Clock className="h-3.5 w-3.5 text-slate-400" />
                          <span className="text-sm text-white">
                            {new Date(appt.start_time).toLocaleTimeString('en-US', {
                              hour: '2-digit',
                              minute: '2-digit',
                              hour12: false,
                            })}
                            {' - '}
                            {new Date(appt.end_time).toLocaleTimeString('en-US', {
                              hour: '2-digit',
                              minute: '2-digit',
                              hour12: false,
                            })}
                          </span>
                          <span className="text-xs text-slate-500">
                            ({appt.duration_minutes} min)
                          </span>
                        </div>

                        <p className="mt-1 text-sm font-medium text-white">
                          {formatAppointmentType(appt.appointment_type)}
                        </p>

                        {appt.reason && (
                          <p className="mt-0.5 text-xs text-slate-400 flex items-center gap-1">
                            <FileText className="h-3 w-3" />
                            {appt.reason}
                          </p>
                        )}

                        {appt.location && (
                          <p className="mt-0.5 text-xs text-slate-500 flex items-center gap-1">
                            <MapPin className="h-3 w-3" />
                            {appt.location}
                          </p>
                        )}

                        {appt.duration_warning && (
                          <p className="mt-1 text-xs text-amber-400">
                            {appt.duration_warning}
                          </p>
                        )}
                      </div>

                      <div className="flex flex-col items-end gap-2">
                        <span
                          className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${getAppointmentStatusColor(appt.status)}`}
                        >
                          {formatAppointmentStatus(appt.status)}
                        </span>

                        {/* Action buttons */}
                        <div className="flex gap-1.5">
                          {(appt.status === 'scheduled' || appt.status === 'confirmed') && onCheckIn && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                onCheckIn(appt);
                              }}
                              className="rounded bg-amber-600/20 px-2 py-1 text-xs text-amber-400 hover:bg-amber-600/30"
                            >
                              Check In
                            </button>
                          )}
                          {(appt.status === 'checked_in' || appt.status === 'scheduled' || appt.status === 'confirmed') &&
                            !appt.encounter_id &&
                            onStartEncounter && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onStartEncounter(appt);
                                }}
                                className="rounded bg-teal-600/20 px-2 py-1 text-xs text-teal-400 hover:bg-teal-600/30"
                              >
                                Start Session
                              </button>
                            )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
