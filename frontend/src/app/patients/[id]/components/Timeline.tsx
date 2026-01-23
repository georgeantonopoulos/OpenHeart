'use client';

import Link from 'next/link';
import { TimelineEvent } from '@/lib/api/patients';

interface TimelineProps {
  patientId: number;
  events: TimelineEvent[];
  isLoading: boolean;
}

/**
 * Patient Timeline Component.
 *
 * Displays chronological activity including:
 * - Encounters
 * - Clinical notes
 * - Observations
 * - CDSS calculations
 * - DICOM studies
 */
export default function Timeline({ patientId, events, isLoading }: TimelineProps) {
  // Event type icons and colors
  // Event type icons and colors
  const getEventStyle = (type: string) => {
    switch (type) {
      case 'encounter':
        return {
          bg: 'bg-sky-500/5',
          border: 'border-sky-500/20',
          accent: 'bg-sky-500',
          text: 'text-sky-400',
          icon: (
            <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          ),
        };
      case 'note':
        return {
          bg: 'bg-indigo-500/5',
          border: 'border-indigo-500/20',
          accent: 'bg-indigo-500',
          text: 'text-indigo-400',
          icon: (
            <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          ),
        };
      case 'observation':
        return {
          bg: 'bg-emerald-500/5',
          border: 'border-emerald-500/20',
          accent: 'bg-emerald-500',
          text: 'text-emerald-400',
          icon: (
            <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          ),
        };
      case 'cdss':
        return {
          bg: 'bg-amber-500/5',
          border: 'border-amber-500/20',
          accent: 'bg-amber-500',
          text: 'text-amber-400',
          icon: (
            <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
          ),
        };
      case 'dicom':
        return {
          bg: 'bg-violet-500/5',
          border: 'border-violet-500/20',
          accent: 'bg-violet-500',
          text: 'text-violet-400',
          icon: (
            <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          ),
        };
      default:
        return {
          bg: 'bg-slate-800/50',
          border: 'border-slate-700/50',
          accent: 'bg-slate-600',
          text: 'text-slate-400',
          icon: (
            <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          ),
        };
    }
  };

  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) {
      return `Today at ${date.toLocaleTimeString('en-CY', {
        hour: '2-digit',
        minute: '2-digit',
      })}`;
    } else if (days === 1) {
      return 'Yesterday';
    } else if (days < 7) {
      return `${days} days ago`;
    } else {
      return date.toLocaleDateString('en-CY', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      });
    }
  };

  return (
    <div className="bg-slate-900 rounded-lg border border-slate-800">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
        <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wider">
          Activity Timeline
        </h3>
        <div className="flex items-center space-x-2">
          {/* Filter chips (future implementation) */}
          <span className="text-xs text-slate-500">All Activity</span>
        </div>
      </div>

      {/* Timeline Content */}
      <div className="p-4">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-rose-500"></div>
          </div>
        ) : events.length === 0 ? (
          /* Empty State */
          <div className="text-center py-12">
            <svg
              className="mx-auto h-12 w-12 text-slate-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <h4 className="mt-4 text-lg font-medium text-slate-300">
              No Activity Yet
            </h4>
            <p className="mt-2 text-sm text-slate-500 max-w-sm mx-auto">
              This patient has no recorded encounters, notes, or studies.
              Start by creating a new encounter or clinical note.
            </p>
            <div className="mt-6 flex items-center justify-center space-x-3">
              <Link
                href={`/patients/${patientId}/notes/new`}
                className="inline-flex items-center px-4 py-2 bg-rose-600 text-white text-sm rounded-lg hover:bg-rose-700 transition-colors"
              >
                <svg
                  className="w-4 h-4 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                  />
                </svg>
                Create Note
              </Link>
              <Link
                href={`/cdss?patient=${patientId}`}
                className="inline-flex items-center px-4 py-2 bg-slate-700 text-white text-sm rounded-lg hover:bg-slate-600 transition-colors"
              >
                <svg
                  className="w-4 h-4 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                  />
                </svg>
                Run CDSS
              </Link>
            </div>
          </div>
        ) : (
          /* Events List */
          <div className="relative">
            {/* Timeline line */}
            <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-slate-700"></div>

            <div className="space-y-6">
              {events.map((event, index) => {
                const style = getEventStyle(event.type);
                return (
                  <div key={event.id || index} className="relative pl-12">
                    {/* Timeline dot */}
                    <div
                      className={`absolute left-1.5 w-6 h-6 rounded-full ${style.accent} border-4 border-slate-900 flex items-center justify-center z-10 shadow-lg shadow-black/50`}
                    >
                      {style.icon}
                    </div>

                    {/* Event card */}
                    <div
                      className={`group relative ${style.bg} ${style.border} border rounded-xl p-4 transition-all duration-300 hover:translate-x-1 hover:shadow-xl hover:shadow-black/20 overflow-hidden`}
                    >
                      {/* Sidebar accent */}
                      <div className={`absolute left-0 top-0 bottom-0 w-1 ${style.accent} opacity-40 group-hover:opacity-100 transition-opacity`}></div>

                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-grow">
                          <h4 className={`font-semibold text-base ${style.text} tracking-tight`}>
                            {event.title}
                          </h4>
                          {event.description && (
                            <p className="mt-1 text-sm text-slate-300/80 leading-relaxed font-normal">
                              {event.description}
                            </p>
                          )}

                          <div className="mt-3 flex items-center space-x-4">
                            {event.user_name && (
                              <div className="flex items-center text-xs text-slate-500 font-medium">
                                <svg className="w-3.5 h-3.5 mr-1.5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                </svg>
                                {event.user_name}
                              </div>
                            )}
                            <div className="flex items-center text-xs text-slate-500 font-medium italic">
                              <svg className="w-3.5 h-3.5 mr-1.5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                              {formatTimestamp(event.timestamp)}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
