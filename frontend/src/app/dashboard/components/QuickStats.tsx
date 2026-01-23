'use client';

import Link from 'next/link';
import { useSession } from 'next-auth/react';
import { useQuery } from '@tanstack/react-query';
import { getTodayAppointments } from '@/lib/api/appointments';
import { listPatients } from '@/lib/api/patients';
import { useTranslation } from 'react-i18next';

interface StatItem {
  label: string;
  value: number | string;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  href?: string;
  icon: React.ReactNode;
  color: 'rose' | 'teal' | 'amber' | 'blue' | 'purple';
}

/**
 * Quick Stats component for dashboard.
 *
 * Displays key metrics derived from real API data:
 * - Appointments today (from appointments API)
 * - Total patients (from patients API)
 * - Pending notes (coming soon)
 * - Pending claims (coming soon)
 */
export default function QuickStats() {
  const { t } = useTranslation('common');
  const { data: session } = useSession();

  const { data: todayAppointments = [] } = useQuery({
    queryKey: ['today-appointments'],
    queryFn: () => getTodayAppointments(session!.accessToken!),
    enabled: !!session?.accessToken,
    staleTime: 30000,
  });

  const { data: patientList } = useQuery({
    queryKey: ['patient-count'],
    queryFn: () => listPatients(session!.accessToken!, { page: 1, page_size: 1 }),
    enabled: !!session?.accessToken,
    staleTime: 60000,
  });

  const stats: StatItem[] = [
    {
      label: t('stats.appointments_today'),
      value: todayAppointments.length,
      change: todayAppointments.length > 0
        ? `${todayAppointments.filter(a => a.status === 'completed').length} ${t('stats.completed')}`
        : undefined,
      changeType: 'neutral',
      href: '/appointments',
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
      color: 'blue',
    },
    {
      label: t('stats.total_patients'),
      value: patientList?.total ?? '—',
      change: patientList?.total != null ? t('stats.active_records') : undefined,
      changeType: 'neutral',
      href: '/patients',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
          />
        </svg>
      ),
      color: 'teal',
    },
    {
      label: t('stats.pending_notes'),
      value: '—',
      change: t('dashboard.coming_soon'),
      changeType: 'neutral',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
      ),
      color: 'amber',
    },
    {
      label: t('stats.pending_claims'),
      value: '—',
      change: t('dashboard.coming_soon'),
      changeType: 'neutral',
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
      color: 'rose',
    },
  ];

  const colorClasses: Record<string, { bg: string; text: string; icon: string }> = {
    rose: {
      bg: 'bg-rose-900/20',
      text: 'text-rose-400',
      icon: 'bg-rose-500/20 text-rose-400',
    },
    teal: {
      bg: 'bg-teal-900/20',
      text: 'text-teal-400',
      icon: 'bg-teal-500/20 text-teal-400',
    },
    amber: {
      bg: 'bg-amber-900/20',
      text: 'text-amber-400',
      icon: 'bg-amber-500/20 text-amber-400',
    },
    blue: {
      bg: 'bg-blue-900/20',
      text: 'text-blue-400',
      icon: 'bg-blue-500/20 text-blue-400',
    },
    purple: {
      bg: 'bg-purple-900/20',
      text: 'text-purple-400',
      icon: 'bg-purple-500/20 text-purple-400',
    },
  };

  const changeTypeClasses: Record<string, string> = {
    positive: 'text-green-400',
    negative: 'text-amber-400',
    neutral: 'text-slate-400',
  };

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat) => {
        const colors = colorClasses[stat.color];
        const content = (
          <div
            className={`${colors.bg} rounded-lg border border-slate-800 p-4 hover:border-slate-700 transition-colors`}
          >
            <div className="flex items-start justify-between">
              <div className={`p-2 rounded-lg ${colors.icon}`}>{stat.icon}</div>
              <span className={`text-2xl font-bold ${colors.text}`}>{stat.value}</span>
            </div>
            <h3 className="mt-3 text-sm font-medium text-white">{stat.label}</h3>
            {stat.change && (
              <p className={`mt-1 text-xs ${changeTypeClasses[stat.changeType || 'neutral']}`}>
                {stat.change}
              </p>
            )}
          </div>
        );

        if (stat.href) {
          return (
            <Link key={stat.label} href={stat.href} className="block">
              {content}
            </Link>
          );
        }

        return <div key={stat.label}>{content}</div>;
      })}
    </div>
  );
}
