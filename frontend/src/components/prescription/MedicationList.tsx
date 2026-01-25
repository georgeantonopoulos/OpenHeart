'use client';

import { useSession } from 'next-auth/react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import {
  getActiveMedications,
  Prescription,
  getStatusColor,
  formatPrescriptionLine,
} from '@/lib/api/prescriptions';

interface MedicationListProps {
  patientId: number;
  compact?: boolean;
  maxItems?: number;
}

/**
 * Compact medication list for patient sidebar or summary views.
 */
export default function MedicationList({
  patientId,
  compact = false,
  maxItems = 5,
}: MedicationListProps) {
  const { data: session } = useSession();

  const {
    data: medications,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['active-medications', patientId],
    queryFn: () => getActiveMedications(session?.accessToken || '', patientId),
    enabled: !!session?.accessToken && !!patientId,
    staleTime: 30000,
  });

  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="h-4 bg-slate-700 rounded w-3/4 mb-2" />
        <div className="h-4 bg-slate-700 rounded w-2/3 mb-2" />
        <div className="h-4 bg-slate-700 rounded w-1/2" />
      </div>
    );
  }

  if (error) {
    return <div className="text-sm text-red-400">Failed to load medications</div>;
  }

  if (!medications || medications.length === 0) {
    return <div className="text-sm text-slate-500">No active medications</div>;
  }

  const displayMeds = medications.slice(0, maxItems);
  const remaining = medications.length - maxItems;

  if (compact) {
    return (
      <div className="space-y-1">
        {displayMeds.map((rx: Prescription) => (
          <div key={rx.id} className="flex items-center gap-2 text-sm">
            <span className="w-2 h-2 rounded-full bg-green-500 flex-shrink-0" />
            <span className="text-slate-300 truncate">
              {rx.drug_name} {rx.strength}
            </span>
            {rx.is_chronic && (
              <span className="text-xs text-blue-400 flex-shrink-0">chronic</span>
            )}
          </div>
        ))}
        {remaining > 0 && (
          <Link
            href={`/patients/${patientId}/prescriptions`}
            className="text-xs text-rose-400 hover:text-rose-300"
          >
            +{remaining} more medications
          </Link>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {displayMeds.map((rx: Prescription) => (
        <div
          key={rx.id}
          className="bg-slate-800/50 rounded-lg px-3 py-2 border border-slate-700/50"
        >
          <div className="flex items-center justify-between">
            <span className="font-medium text-white text-sm">{rx.drug_name}</span>
            <span
              className={`px-1.5 py-0.5 text-xs rounded border ${getStatusColor(rx.status)}`}
            >
              {rx.status}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">{formatPrescriptionLine(rx)}</p>
          {rx.interactions && rx.interactions.length > 0 && (
            <div className="mt-1 flex items-center gap-1">
              <svg
                className="w-3 h-3 text-amber-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01"
                />
              </svg>
              <span className="text-xs text-amber-400">
                {rx.interactions.length} interaction{rx.interactions.length > 1 ? 's' : ''}
              </span>
            </div>
          )}
        </div>
      ))}

      <Link
        href={`/patients/${patientId}/prescriptions`}
        className="block text-center text-sm text-rose-400 hover:text-rose-300 py-2"
      >
        View all medications {medications.length > 0 && `(${medications.length})`}
      </Link>
    </div>
  );
}
