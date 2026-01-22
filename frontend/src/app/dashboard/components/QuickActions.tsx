'use client';

import Link from 'next/link';

interface QuickAction {
  label: string;
  description: string;
  href: string;
  icon: React.ReactNode;
  color: 'rose' | 'teal' | 'blue' | 'purple' | 'amber';
}

/**
 * Quick Actions grid component.
 *
 * Provides fast access to common cardiologist workflows:
 * - Find Patient
 * - CDSS Calculators
 * - New Note
 * - Imaging
 * - Referrals
 * - Claims
 */
export default function QuickActions() {
  const actions: QuickAction[] = [
    {
      label: 'Find Patient',
      description: 'Search records',
      href: '/patients',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      ),
      color: 'blue',
    },
    {
      label: 'CDSS',
      description: 'Risk calculators',
      href: '/cdss',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"
          />
        </svg>
      ),
      color: 'rose',
    },
    {
      label: 'New Note',
      description: 'Clinical documentation',
      href: '/notes/new',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
          />
        </svg>
      ),
      color: 'purple',
    },
    {
      label: 'Imaging',
      description: 'DICOM viewer',
      href: '/imaging',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
      ),
      color: 'teal',
    },
    {
      label: 'Referrals',
      description: 'Incoming from PD',
      href: '/referrals/incoming',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"
          />
        </svg>
      ),
      color: 'amber',
    },
    {
      label: 'Claims',
      description: 'Gesy submissions',
      href: '/billing/claims',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"
          />
        </svg>
      ),
      color: 'teal',
    },
  ];

  const colorClasses: Record<string, { bg: string; hover: string; icon: string }> = {
    rose: {
      bg: 'bg-slate-800/50',
      hover: 'hover:bg-rose-900/20 hover:border-rose-800',
      icon: 'text-rose-400',
    },
    teal: {
      bg: 'bg-slate-800/50',
      hover: 'hover:bg-teal-900/20 hover:border-teal-800',
      icon: 'text-teal-400',
    },
    blue: {
      bg: 'bg-slate-800/50',
      hover: 'hover:bg-blue-900/20 hover:border-blue-800',
      icon: 'text-blue-400',
    },
    purple: {
      bg: 'bg-slate-800/50',
      hover: 'hover:bg-purple-900/20 hover:border-purple-800',
      icon: 'text-purple-400',
    },
    amber: {
      bg: 'bg-slate-800/50',
      hover: 'hover:bg-amber-900/20 hover:border-amber-800',
      icon: 'text-amber-400',
    },
  };

  return (
    <div className="bg-slate-900 rounded-lg border border-slate-800 p-4">
      <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {actions.map((action) => {
          const colors = colorClasses[action.color];
          return (
            <Link
              key={action.label}
              href={action.href}
              className={`${colors.bg} ${colors.hover} rounded-lg border border-slate-700 p-4 transition-all group`}
            >
              <div className={`${colors.icon} mb-2 group-hover:scale-110 transition-transform`}>
                {action.icon}
              </div>
              <h3 className="text-sm font-medium text-white">{action.label}</h3>
              <p className="text-xs text-slate-400 mt-0.5">{action.description}</p>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
