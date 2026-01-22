'use client';

import Link from 'next/link';
import { useSession } from 'next-auth/react';
import { useQuery } from '@tanstack/react-query';
import { listPatients, Patient } from '@/lib/api/patients';

/**
 * Recent Patients component.
 *
 * Shows the most recently updated patients for quick access.
 * Fetches real data from the patients API.
 */
export default function RecentPatients() {
  const { data: session } = useSession();

  const { data: patientList, isLoading } = useQuery({
    queryKey: ['recent-patients'],
    queryFn: () => listPatients(session!.accessToken!, { page: 1, page_size: 5 }),
    enabled: !!session?.accessToken,
    staleTime: 30000,
  });

  const patients = patientList?.items ?? [];

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    }
    if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    }
    return date.toLocaleDateString('en-CY', { day: '2-digit', month: 'short' });
  };

  return (
    <div className="bg-slate-900 rounded-lg border border-slate-800">
      <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Recent Patients</h2>
        <Link
          href="/patients"
          className="text-sm text-rose-400 hover:text-rose-300 transition-colors"
        >
          View All
        </Link>
      </div>

      <div className="divide-y divide-slate-800">
        {isLoading ? (
          // Loading skeleton
          Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="px-4 py-3 animate-pulse">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-slate-700" />
                <div className="flex-1">
                  <div className="h-4 w-32 bg-slate-700 rounded mb-1" />
                  <div className="h-3 w-24 bg-slate-800 rounded" />
                </div>
                <div className="h-3 w-16 bg-slate-800 rounded" />
              </div>
            </div>
          ))
        ) : patients.length === 0 ? (
          // Empty state
          <div className="px-4 py-8 text-center">
            <svg className="w-10 h-10 mx-auto text-slate-600 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <p className="text-sm text-slate-400">No patients yet</p>
            <p className="text-xs text-slate-500 mt-1">Add your first patient to get started</p>
          </div>
        ) : (
          patients.map((patient: Patient) => (
            <Link
              key={patient.patient_id}
              href={`/patients/${patient.patient_id}`}
              className="block px-4 py-3 hover:bg-slate-800/50 transition-colors"
            >
              <div className="flex items-center gap-3">
                {/* Avatar */}
                <div className="relative flex-shrink-0">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-rose-500 to-pink-600 flex items-center justify-center text-white font-medium text-sm">
                    {(patient.first_name?.[0] ?? '').toUpperCase()}
                    {(patient.last_name?.[0] ?? '').toUpperCase()}
                  </div>
                  {patient.is_gesy_beneficiary && (
                    <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-slate-900 bg-teal-500" />
                  )}
                </div>

                {/* Patient info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-white font-medium truncate">
                      {patient.first_name} {patient.last_name}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-400">
                    <span className="font-mono">{patient.mrn}</span>
                    {patient.age != null && (
                      <>
                        <span>•</span>
                        <span>{patient.age}y</span>
                      </>
                    )}
                  </div>
                </div>

                {/* Last updated */}
                <div className="text-right flex-shrink-0">
                  <p className="text-xs text-slate-400">
                    {patient.updated_at ? formatDate(patient.updated_at) : ''}
                  </p>
                  {patient.status && patient.status !== 'active' && (
                    <p className="text-xs text-slate-500 capitalize">{patient.status}</p>
                  )}
                </div>
              </div>
            </Link>
          ))
        )}
      </div>

      {/* Add patient link */}
      <div className="px-4 py-3 border-t border-slate-800">
        <Link
          href="/patients/new"
          className="flex items-center justify-center gap-2 w-full py-2 text-sm text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
            />
          </svg>
          Add New Patient
        </Link>
      </div>
    </div>
  );
}
