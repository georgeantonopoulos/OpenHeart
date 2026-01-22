'use client';

import { useSession } from 'next-auth/react';
import Link from 'next/link';

interface Calculator {
  id: string;
  name: string;
  fullName: string;
  description: string;
  useCase: string;
  href: string;
  color: 'rose' | 'blue' | 'amber' | 'teal' | 'purple';
  badge: string;
}

/**
 * CDSS Calculator Selection Page.
 *
 * Hub for all clinical decision support tools.
 */
export default function CDSSPage() {
  const { data: session } = useSession();

  const calculators: Calculator[] = [
    {
      id: 'grace',
      name: 'GRACE',
      fullName: 'Global Registry of Acute Coronary Events',
      description: 'Estimates in-hospital mortality risk for patients with Acute Coronary Syndrome.',
      useCase: 'Use for STEMI/NSTEMI risk stratification to guide invasive strategy timing.',
      href: '/cdss/grace',
      color: 'rose',
      badge: 'ACS',
    },
    {
      id: 'cha2ds2vasc',
      name: 'CHA₂DS₂-VASc',
      fullName: 'Stroke Risk in Atrial Fibrillation',
      description: 'Assesses stroke risk in patients with non-valvular atrial fibrillation.',
      useCase: 'Use to determine anticoagulation need in AF patients.',
      href: '/cdss/cha2ds2vasc',
      color: 'blue',
      badge: 'AF',
    },
    {
      id: 'hasbled',
      name: 'HAS-BLED',
      fullName: 'Bleeding Risk Assessment',
      description: 'Evaluates major bleeding risk in patients on anticoagulation.',
      useCase: 'Use alongside CHA₂DS₂-VASc to identify modifiable bleeding risk factors.',
      href: '/cdss/hasbled',
      color: 'amber',
      badge: 'Bleeding',
    },
    {
      id: 'prevent',
      name: 'PREVENT',
      fullName: 'AHA PREVENT Equations (2023)',
      description: 'Modern race-agnostic ASCVD and Heart Failure risk prediction with kidney function.',
      useCase: 'Use for primary prevention statin decisions and HF risk stratification.',
      href: '/cdss/prevent',
      color: 'teal',
      badge: 'Prevention',
    },
    {
      id: 'euroscore',
      name: 'EuroSCORE II',
      fullName: 'European System for Cardiac Operative Risk',
      description: 'Predicts 30-day mortality for cardiac surgery. Essential for Heart Team decisions.',
      useCase: 'Use for CABG vs PCI and TAVI vs SAVR decision-making.',
      href: '/cdss/euroscore',
      color: 'purple',
      badge: 'Surgery',
    },
  ];

  const colorClasses = {
    rose: {
      bg: 'bg-rose-900/20',
      border: 'border-rose-800 hover:border-rose-600',
      icon: 'text-rose-400',
      badge: 'bg-rose-500/20 text-rose-300',
    },
    blue: {
      bg: 'bg-blue-900/20',
      border: 'border-blue-800 hover:border-blue-600',
      icon: 'text-blue-400',
      badge: 'bg-blue-500/20 text-blue-300',
    },
    amber: {
      bg: 'bg-amber-900/20',
      border: 'border-amber-800 hover:border-amber-600',
      icon: 'text-amber-400',
      badge: 'bg-amber-500/20 text-amber-300',
    },
    teal: {
      bg: 'bg-teal-900/20',
      border: 'border-teal-800 hover:border-teal-600',
      icon: 'text-teal-400',
      badge: 'bg-teal-500/20 text-teal-300',
    },
    purple: {
      bg: 'bg-purple-900/20',
      border: 'border-purple-800 hover:border-purple-600',
      icon: 'text-purple-400',
      badge: 'bg-purple-500/20 text-purple-300',
    },
  };

  if (!session) {
    return null;
  }

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <div className="bg-slate-900 border-b border-slate-800">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center space-x-4">
            <Link
              href="/dashboard"
              className="text-slate-400 hover:text-slate-200 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10 19l-7-7m0 0l7-7m-7 7h18"
                />
              </svg>
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-white">Clinical Decision Support</h1>
              <p className="text-slate-400 mt-1">
                Evidence-based risk calculators for cardiology
              </p>
            </div>
          </div>
        </div>
      </div>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Calculator Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {calculators.map((calc) => {
            const colors = colorClasses[calc.color];
            return (
              <Link
                key={calc.id}
                href={calc.href}
                className={`block ${colors.bg} rounded-lg border ${colors.border} p-6 transition-all hover:shadow-lg hover:shadow-${calc.color}-500/10`}
              >
                {/* Icon */}
                <div className="flex items-start justify-between mb-4">
                  <div className={`p-3 rounded-lg bg-slate-800/50 ${colors.icon}`}>
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                      />
                    </svg>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded ${colors.badge}`}>
                    {calc.badge}
                  </span>
                </div>

                {/* Title */}
                <h2 className="text-xl font-bold text-white mb-1">{calc.name}</h2>
                <p className="text-xs text-slate-500 mb-3">{calc.fullName}</p>

                {/* Description */}
                <p className="text-sm text-slate-300 mb-4">{calc.description}</p>

                {/* Use Case */}
                <div className="pt-4 border-t border-slate-700/50">
                  <p className="text-xs text-slate-400">
                    <span className="font-medium text-slate-300">When to use: </span>
                    {calc.useCase}
                  </p>
                </div>

                {/* Arrow */}
                <div className="mt-4 flex items-center text-sm font-medium text-slate-400 group-hover:text-white">
                  <span>Calculate</span>
                  <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </div>
              </Link>
            );
          })}
        </div>

        {/* Info Card */}
        <div className="mt-8 bg-slate-900 rounded-lg border border-slate-800 p-6">
          <div className="flex items-start gap-4">
            <div className="p-2 rounded-lg bg-teal-500/20 text-teal-400">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <div>
              <h3 className="font-medium text-white mb-1">About CDSS Calculators</h3>
              <p className="text-sm text-slate-400">
                All calculations are logged for clinical audit and GDPR compliance.
                Results are evidence-based but should be interpreted in the clinical context.
                These tools support, but do not replace, clinical judgment.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
