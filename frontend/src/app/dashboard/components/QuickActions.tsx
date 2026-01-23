'use client';

import Link from 'next/link';
import { useTranslation } from 'react-i18next';

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
  const { t } = useTranslation('common');

  const actions: QuickAction[] = [
    {
      label: t('actions.find_patient'),
      description: t('actions.find_patient_desc'),
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
      description: t('actions.cdss_desc'),
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
      label: t('notes.new_note'),
      description: t('actions.new_note_desc'),
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
      label: t('nav.imaging'),
      description: t('actions.imaging_desc'),
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
      label: t('dashboard.schedule'),
      description: t('actions.schedule_desc'),
      href: '/procedures/schedule',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
      ),
      color: 'amber',
    },
    {
      label: t('actions.referrals'),
      description: t('actions.referrals_desc'),
      href: '/referrals/incoming',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"
          />
        </svg>
      ),
      color: 'amber',
    },
    {
      label: t('actions.claims'),
      description: t('actions.claims_desc'),
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
      <h2 className="text-lg font-semibold text-white mb-4">{t('dashboard.quick_actions')}</h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {actions.map((action) => {
          const colors = colorClasses[action.color];
          return (
            <Link
              key={action.href}
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
