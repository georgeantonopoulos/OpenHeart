'use client';

import { useMemo } from 'react';
import {
  type Appointment,
  getAppointmentStatusColor,
  formatAppointmentType,
} from '@/lib/api/appointments';

interface WeekViewProps {
  appointments: Appointment[];
  currentDate: Date;
  onAppointmentClick: (appointment: Appointment) => void;
  onSlotClick?: (date: Date, hour: number) => void;
  onCheckIn?: (appointment: Appointment) => void;
  onStartEncounter?: (appointment: Appointment) => void;
}

const HOURS = Array.from({ length: 15 }, (_, i) => i + 7); // 07:00 - 21:00

function getWeekDays(date: Date): Date[] {
  const start = new Date(date);
  const day = start.getDay();
  const diff = start.getDate() - day + (day === 0 ? -6 : 1); // Monday start
  start.setDate(diff);

  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(start);
    d.setDate(start.getDate() + i);
    return d;
  });
}

function isSameDay(d1: Date, d2: Date): boolean {
  return (
    d1.getFullYear() === d2.getFullYear() &&
    d1.getMonth() === d2.getMonth() &&
    d1.getDate() === d2.getDate()
  );
}

export default function WeekView({
  appointments,
  currentDate,
  onAppointmentClick,
  onSlotClick,
  onCheckIn,
  onStartEncounter,
}: WeekViewProps) {
  const weekDays = useMemo(() => getWeekDays(currentDate), [currentDate]);
  const today = new Date();

  const getAppointmentsForDay = (day: Date) => {
    return appointments.filter((a) => {
      const start = new Date(a.start_time);
      return isSameDay(start, day);
    });
  };

  return (
    <div className="overflow-x-auto rounded-lg border border-white/10 bg-slate-900">
      {/* Header */}
      <div className="grid grid-cols-[60px_repeat(7,1fr)] border-b border-white/10">
        <div className="p-2" />
        {weekDays.map((day) => {
          const isToday = isSameDay(day, today);
          return (
            <div
              key={day.toISOString()}
              className={`border-l border-white/10 p-2 text-center ${isToday ? 'bg-teal-500/10' : ''
                }`}
            >
              <p className="text-xs text-slate-500">
                {day.toLocaleDateString('en-US', { weekday: 'short' })}
              </p>
              <p
                className={`text-lg font-semibold ${isToday ? 'text-teal-400' : 'text-white'
                  }`}
              >
                {day.getDate()}
              </p>
            </div>
          );
        })}
      </div>

      {/* Time grid */}
      <div className="grid grid-cols-[60px_repeat(7,1fr)]">
        {HOURS.map((hour) => (
          <div key={hour} className="contents">
            {/* Time label */}
            <div className="border-t border-white/5 p-1 text-right">
              <span className="text-xs text-slate-500">
                {hour.toString().padStart(2, '0')}:00
              </span>
            </div>

            {/* Day cells */}
            {weekDays.map((day) => {
              const dayAppointments = getAppointmentsForDay(day).filter((a) => {
                const start = new Date(a.start_time);
                return start.getHours() === hour;
              });

              return (
                <div
                  key={`${day.toISOString()}-${hour}`}
                  className="relative min-h-[48px] border-l border-t border-white/5 p-0.5"
                  onClick={() => onSlotClick?.(day, hour)}
                >
                  {dayAppointments.map((appt) => (
                    <div
                      key={appt.appointment_id}
                      className={`group relative w-full rounded px-1.5 py-0.5 mt-0.5 text-left text-[10px] transition-all hover:ring-1 hover:ring-white/20 ${getAppointmentStatusColor(appt.status)}`}
                      style={{
                        minHeight: `${Math.max(24, (appt.duration_minutes / 60) * 48)}px`,
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        onAppointmentClick(appt);
                      }}
                    >
                      <div className="flex flex-col h-full justify-between">
                        <div>
                          <p className="truncate font-bold text-[11px] leading-tight">
                            {new Date(appt.start_time).toLocaleTimeString('en-US', {
                              hour: '2-digit',
                              minute: '2-digit',
                              hour12: false,
                            })}
                          </p>
                          <p className="truncate opacity-90 font-medium">
                            {formatAppointmentType(appt.appointment_type)}
                          </p>
                        </div>

                        {/* Quick Actions (only visible if there's enough height or on hover) */}
                        <div className="hidden group-hover:flex gap-1 mt-1 pb-1">
                          {(appt.status === 'scheduled' || appt.status === 'confirmed') && onCheckIn && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                onCheckIn(appt);
                              }}
                              className="px-1.5 py-0.5 rounded bg-amber-500/30 text-white hover:bg-amber-500 transition-colors font-bold text-[9px] uppercase"
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
                                className="px-1.5 py-0.5 rounded bg-teal-500/30 text-white hover:bg-teal-500 transition-colors font-bold text-[9px] uppercase"
                              >
                                Start
                              </button>
                            )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
