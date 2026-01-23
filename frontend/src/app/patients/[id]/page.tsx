'use client';

import { useSession } from 'next-auth/react';
import { useQuery } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { getPatient, getPatientTimeline } from '@/lib/api/patients';
import PatientHeader from './components/PatientHeader';
import VitalsPanel from './components/VitalsPanel';
import Timeline from './components/Timeline';

/**
 * Patient Profile Page.
 *
 * Displays comprehensive patient information including:
 * - Header with demographics and risk badges
 * - Quick actions (new note, CDSS, imaging)
 * - Recent vitals
 * - Activity timeline
 */
export default function PatientProfilePage() {
  const { data: session } = useSession();
  const params = useParams();
  const patientId = Number(params.id);

  // Fetch patient data
  const {
    data: patient,
    isLoading: patientLoading,
    error: patientError,
  } = useQuery({
    queryKey: ['patient', patientId],
    queryFn: () => getPatient(session?.accessToken || '', patientId),
    enabled: !!session?.accessToken && !!patientId,
  });

  // Fetch timeline
  const { data: timeline, isLoading: timelineLoading } = useQuery({
    queryKey: ['patient-timeline', patientId],
    queryFn: () => getPatientTimeline(session?.accessToken || '', patientId),
    enabled: !!session?.accessToken && !!patientId,
    refetchOnMount: 'always', // Force refresh when navigating back
  });

  if (!session) {
    return null;
  }

  if (patientLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-rose-500"></div>
      </div>
    );
  }

  if (patientError || !patient) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-white mb-2">Patient Not Found</h2>
          <p className="text-slate-400 mb-4">
            The patient you're looking for doesn't exist or you don't have access.
          </p>
          <Link
            href="/patients"
            className="text-rose-400 hover:text-rose-300 transition-colors"
          >
            Back to Patients
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Sticky Navigation */}
      <nav className="sticky top-0 z-50 bg-slate-900/95 backdrop-blur border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            {/* Breadcrumb */}
            <div className="flex items-center space-x-2 text-sm">
              <Link
                href="/dashboard"
                className="text-slate-400 hover:text-slate-200 transition-colors"
              >
                Dashboard
              </Link>
              <span className="text-slate-600">/</span>
              <Link
                href="/patients"
                className="text-slate-400 hover:text-slate-200 transition-colors"
              >
                Patients
              </Link>
              <span className="text-slate-600">/</span>
              <span className="text-white font-medium">
                {patient.first_name} {patient.last_name}
              </span>
            </div>

            {/* Quick Actions */}
            <div className="flex items-center space-x-2">
              <Link
                href={`/patients/${patientId}/notes/new`}
                className="inline-flex items-center px-3 py-1.5 bg-rose-600 text-white text-sm rounded-lg hover:bg-rose-700 transition-colors"
              >
                <svg
                  className="w-4 h-4 mr-1.5"
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
                New Note
              </Link>
              <Link
                href={`/cdss?patient=${patientId}`}
                className="inline-flex items-center px-3 py-1.5 bg-slate-700 text-white text-sm rounded-lg hover:bg-slate-600 transition-colors"
              >
                <svg
                  className="w-4 h-4 mr-1.5"
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
                CDSS
              </Link>
              <Link
                href={`/patients/${patientId}/imaging`}
                className="inline-flex items-center px-3 py-1.5 bg-slate-700 text-white text-sm rounded-lg hover:bg-slate-600 transition-colors"
              >
                <svg
                  className="w-4 h-4 mr-1.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
                Imaging
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Patient Header */}
        <PatientHeader patient={patient} />

        {/* Main Content Grid */}
        <div className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Vitals & Quick Info */}
          <div className="space-y-6">
            <VitalsPanel patientId={patientId} />

            {/* Clinical Summary Card */}
            <div className="bg-slate-900 rounded-lg border border-slate-800 p-4">
              <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-3">
                Clinical Summary
              </h3>
              <div className="space-y-3">
                {/* Placeholder for conditions, medications, allergies */}
                <div className="text-center py-6 text-slate-500 text-sm">
                  <p>No clinical data available yet</p>
                  <p className="text-xs mt-1">
                    Create encounters to populate this summary
                  </p>
                </div>
              </div>
            </div>

            {/* Gesy Status Card */}
            {patient.is_gesy_beneficiary && (
              <div className="bg-teal-900/20 rounded-lg border border-teal-800 p-4">
                <div className="flex items-center space-x-2">
                  <div className="flex-shrink-0 w-8 h-8 bg-teal-600 rounded-full flex items-center justify-center">
                    <svg
                      className="w-4 h-4 text-white"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                      />
                    </svg>
                  </div>
                  <div>
                    <p className="text-teal-200 font-medium">Gesy Beneficiary</p>
                    <p className="text-teal-400 text-sm">
                      ID: {patient.gesy_beneficiary_id}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Timeline */}
          <div className="lg:col-span-2">
            <Timeline
              patientId={patientId}
              events={timeline?.events || []}
              isLoading={timelineLoading}
            />
          </div>
        </div>
      </main>
    </div>
  );
}
