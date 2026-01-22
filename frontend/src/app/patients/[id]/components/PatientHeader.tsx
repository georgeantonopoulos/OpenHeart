'use client';

import { Patient } from '@/lib/api/patients';
import Link from 'next/link';

interface PatientHeaderProps {
  patient: Patient;
}

/**
 * Patient Header Component.
 *
 * Displays patient demographics, identifiers, and risk badges.
 */
export default function PatientHeader({ patient }: PatientHeaderProps) {
  // Format date for display (DD/MM/YYYY - Cyprus format)
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-CY', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  };

  // Gender icon
  const GenderIcon = () => {
    if (patient.gender === 'male') {
      return (
        <span className="text-blue-400" title="Male">
          ♂
        </span>
      );
    }
    if (patient.gender === 'female') {
      return (
        <span className="text-pink-400" title="Female">
          ♀
        </span>
      );
    }
    return null;
  };

  // Status badge color
  const getStatusStyle = () => {
    switch (patient.status) {
      case 'active':
        return 'bg-green-900/50 text-green-300 border-green-700';
      case 'inactive':
        return 'bg-slate-700 text-slate-300 border-slate-600';
      case 'deceased':
        return 'bg-red-900/50 text-red-300 border-red-700';
      default:
        return 'bg-slate-700 text-slate-300 border-slate-600';
    }
  };

  return (
    <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
      <div className="flex items-start justify-between">
        {/* Left - Patient Info */}
        <div className="flex items-start space-x-4">
          {/* Avatar */}
          <div className="flex-shrink-0 w-20 h-20 rounded-full bg-gradient-to-br from-rose-500 to-pink-600 flex items-center justify-center text-white text-2xl font-medium shadow-lg">
            {patient.first_name?.[0] || '?'}
            {patient.last_name?.[0] || ''}
          </div>

          {/* Details */}
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-bold text-white">
                {patient.first_name} {patient.middle_name ? `${patient.middle_name} ` : ''}
                {patient.last_name}
              </h1>
              <GenderIcon />
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusStyle()}`}
              >
                {patient.status.charAt(0).toUpperCase() + patient.status.slice(1)}
              </span>
            </div>

            <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
              {/* MRN */}
              <span className="text-slate-400">
                MRN:{' '}
                <span className="text-white font-mono">{patient.mrn}</span>
              </span>

              {/* Age & DOB */}
              <span className="text-slate-400">
                {patient.age} y/o • Born {formatDate(patient.birth_date)}
              </span>

              {/* Cyprus ID (masked) */}
              {patient.cyprus_id_masked && (
                <span className="text-slate-400">
                  ID:{' '}
                  <span className="text-white font-mono">
                    {patient.cyprus_id_masked}
                  </span>
                </span>
              )}

              {/* ARC indicator */}
              {patient.has_arc && (
                <span className="text-amber-400 text-xs">ARC Holder</span>
              )}
            </div>

            {/* Contact Info */}
            <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
              {patient.phone && (
                <span className="flex items-center text-slate-300">
                  <svg
                    className="w-4 h-4 mr-1 text-slate-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                    />
                  </svg>
                  {patient.phone}
                </span>
              )}
              {patient.email && (
                <span className="flex items-center text-slate-300">
                  <svg
                    className="w-4 h-4 mr-1 text-slate-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                    />
                  </svg>
                  {patient.email}
                </span>
              )}
              {patient.referring_physician && (
                <span className="flex items-center text-slate-400">
                  <svg
                    className="w-4 h-4 mr-1 text-slate-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                    />
                  </svg>
                  Ref: {patient.referring_physician}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Right - Risk Badges & Edit */}
        <div className="flex flex-col items-end space-y-3">
          {/* Edit Button */}
          <Link
            href={`/patients/${patient.patient_id}/edit`}
            className="inline-flex items-center px-3 py-1.5 text-sm text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
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
                d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
              />
            </svg>
            Edit
          </Link>

          {/* Risk Badges Placeholder */}
          <div className="flex flex-wrap justify-end gap-2">
            {/* These will be populated by CDSS calculations */}
            <div
              className="px-2 py-1 bg-slate-800 rounded text-xs text-slate-400 border border-slate-700"
              title="Run CDSS to calculate risk scores"
            >
              No risk scores
            </div>
          </div>

          {/* Address Summary */}
          {patient.address && (
            <div className="text-right text-xs text-slate-500 max-w-[200px]">
              {patient.address.street}, {patient.address.city}
              {patient.address.postal_code && ` ${patient.address.postal_code}`}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
