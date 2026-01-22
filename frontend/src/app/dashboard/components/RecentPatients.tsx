'use client';

import Link from 'next/link';

interface RecentPatient {
  patientId: string;
  firstName: string;
  lastName: string;
  mrn: string;
  age: number;
  lastVisit: string;
  primaryDiagnosis?: string;
  riskLevel?: 'low' | 'moderate' | 'high';
  hasUnreadResults?: boolean;
}

/**
 * Recent Patients component.
 *
 * Shows the last 5 patients the user viewed for quick access.
 */
export default function RecentPatients() {
  // TODO: Replace with real data from localStorage or API
  const recentPatients: RecentPatient[] = [
    {
      patientId: '101',
      firstName: 'Μαρία',
      lastName: 'Παπαδοπούλου',
      mrn: 'OH-2025-00101',
      age: 67,
      lastVisit: '2025-01-22',
      primaryDiagnosis: 'CHF (NYHA II)',
      riskLevel: 'moderate',
    },
    {
      patientId: '102',
      firstName: 'Ανδρέας',
      lastName: 'Χριστοδούλου',
      mrn: 'OH-2025-00102',
      age: 54,
      lastVisit: '2025-01-22',
      primaryDiagnosis: 'Post-STEMI',
      riskLevel: 'high',
      hasUnreadResults: true,
    },
    {
      patientId: '103',
      firstName: 'Elena',
      lastName: 'Georgiou',
      mrn: 'OH-2025-00103',
      age: 45,
      lastVisit: '2025-01-21',
      primaryDiagnosis: 'Hypertension',
      riskLevel: 'low',
    },
    {
      patientId: '104',
      firstName: 'Κώστας',
      lastName: 'Νικολάου',
      mrn: 'OH-2025-00104',
      age: 72,
      lastVisit: '2025-01-20',
      primaryDiagnosis: 'ICD (Brugada)',
      riskLevel: 'moderate',
    },
    {
      patientId: '105',
      firstName: 'Sophia',
      lastName: 'Antoniou',
      mrn: 'OH-2025-00105',
      age: 58,
      lastVisit: '2025-01-19',
      primaryDiagnosis: 'Atrial Fibrillation',
      riskLevel: 'moderate',
    },
  ];

  const riskColors: Record<string, string> = {
    low: 'bg-green-500',
    moderate: 'bg-amber-500',
    high: 'bg-rose-500',
  };

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
        {recentPatients.map((patient) => (
          <Link
            key={patient.patientId}
            href={`/patients/${patient.patientId}`}
            className="block px-4 py-3 hover:bg-slate-800/50 transition-colors"
          >
            <div className="flex items-center gap-3">
              {/* Avatar with risk indicator */}
              <div className="relative flex-shrink-0">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-rose-500 to-pink-600 flex items-center justify-center text-white font-medium text-sm">
                  {patient.firstName[0]}
                  {patient.lastName[0]}
                </div>
                {patient.riskLevel && (
                  <div
                    className={`absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-slate-900 ${riskColors[patient.riskLevel]}`}
                  />
                )}
              </div>

              {/* Patient info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-white font-medium truncate">
                    {patient.firstName} {patient.lastName}
                  </span>
                  {patient.hasUnreadResults && (
                    <span className="flex-shrink-0 w-2 h-2 bg-blue-500 rounded-full" />
                  )}
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <span className="font-mono">{patient.mrn}</span>
                  <span>•</span>
                  <span>{patient.age}y</span>
                </div>
              </div>

              {/* Last visit & diagnosis */}
              <div className="text-right flex-shrink-0">
                <p className="text-xs text-slate-400">{formatDate(patient.lastVisit)}</p>
                {patient.primaryDiagnosis && (
                  <p className="text-xs text-slate-500 truncate max-w-24">{patient.primaryDiagnosis}</p>
                )}
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Search link */}
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
