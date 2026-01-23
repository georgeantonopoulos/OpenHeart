'use client';

import { useState, useEffect } from 'react';
import { signOut } from 'next-auth/react';
import { Session } from 'next-auth';
import Link from 'next/link';
import QuickStats from './components/QuickStats';
import TodayAppointments from './components/TodayAppointments';
import RecentPatients from './components/RecentPatients';
import QuickActions from './components/QuickActions';
import { CommandPalette } from '@/components/CommandPalette';

interface DashboardContentProps {
  session: Session;
}

/**
 * Dashboard content component (client-side).
 *
 * Main workspace for cardiologists featuring:
 * - Quick stats overview
 * - Today's appointments
 * - Recent patients
 * - Quick action grid
 */
export default function DashboardContent({ session }: DashboardContentProps) {
  const { user } = session;

  // Format role for display
  const formatRole = (role: string) => {
    return role.charAt(0).toUpperCase() + role.slice(1).replace('_', ' ');
  };

  // Get current time greeting
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  // Format current date
  const formatDate = () => {
    return new Date().toLocaleDateString('en-CY', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  // Command palette state
  const [commandOpen, setCommandOpen] = useState(false);

  // CMD+K / Ctrl+K keyboard shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCommandOpen((prev) => !prev);
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Navigation Bar */}
      <nav className="bg-slate-900 border-b border-slate-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            {/* Left - Logo & Nav */}
            <div className="flex items-center space-x-8">
              <Link href="/dashboard" className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gradient-to-br from-rose-500 to-rose-600 rounded-lg flex items-center justify-center">
                  <svg
                    className="w-5 h-5 text-white"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
                  </svg>
                </div>
                <span className="text-xl font-bold text-white">OpenHeart</span>
              </Link>

              {/* Main Navigation */}
              <nav className="hidden md:flex space-x-1">
                <Link
                  href="/patients"
                  className="px-3 py-2 text-sm text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                >
                  Patients
                </Link>
                <Link
                  href="/appointments"
                  className="px-3 py-2 text-sm text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                >
                  Appointments
                </Link>
                <Link
                  href="/cdss"
                  className="px-3 py-2 text-sm text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                >
                  CDSS
                </Link>
                <Link
                  href="/imaging"
                  className="px-3 py-2 text-sm text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                >
                  Imaging
                </Link>
                <Link
                  href="/procedures"
                  className="px-3 py-2 text-sm text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                >
                  Worklist
                </Link>
                <Link
                  href="/referrals/incoming"
                  className="px-3 py-2 text-sm text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                >
                  Referrals
                </Link>
                <Link
                  href="/billing/claims"
                  className="px-3 py-2 text-sm text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                >
                  Claims
                </Link>
              </nav>
            </div>

            {/* Right - Search, Notifications, User */}
            <div className="flex items-center space-x-4">
              {/* Global Search */}
              <button
                className="hidden sm:flex items-center px-3 py-1.5 text-sm text-slate-400 bg-slate-800 border border-slate-700 rounded-lg hover:border-slate-600 transition-colors"
                onClick={() => setCommandOpen(true)}
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
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
                <span>Search...</span>
                <kbd className="ml-4 px-1.5 py-0.5 text-xs bg-slate-700 rounded">⌘K</kbd>
              </button>

              {/* Notifications */}
              <button className="relative p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                  />
                </svg>
              </button>

              {/* User Menu */}
              <div className="flex items-center space-x-3">
                <div className="text-right hidden sm:block">
                  <p className="text-sm font-medium text-white">{user.name}</p>
                  <p className="text-xs text-slate-400">
                    {formatRole(user.role)} • {user.clinicName}
                  </p>
                </div>
                <div className="relative group">
                  <button className="w-9 h-9 rounded-full bg-gradient-to-br from-rose-500 to-pink-600 flex items-center justify-center text-white font-medium text-sm">
                    {user.name?.charAt(0) || 'U'}
                  </button>
                  {/* Dropdown */}
                  <div className="absolute right-0 mt-2 w-48 bg-slate-900 border border-slate-800 rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all">
                    <div className="py-1">
                      <Link
                        href="/profile"
                        className="block px-4 py-2 text-sm text-slate-300 hover:text-white hover:bg-slate-800"
                      >
                        My Profile
                      </Link>
                      <Link
                        href="/profile/security"
                        className="block px-4 py-2 text-sm text-slate-300 hover:text-white hover:bg-slate-800"
                      >
                        Security Settings
                      </Link>
                      <hr className="my-1 border-slate-800" />
                      <button
                        onClick={() => signOut({ callbackUrl: '/login' })}
                        className="block w-full text-left px-4 py-2 text-sm text-rose-400 hover:text-rose-300 hover:bg-slate-800"
                      >
                        Sign Out
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Welcome Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white">
            {getGreeting()}, {user.name?.split(' ')[0]}
          </h1>
          <p className="text-slate-400 mt-1">{formatDate()}</p>
        </div>

        {/* Quick Stats */}
        <div className="mb-6">
          <QuickStats />
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Appointments */}
          <div className="lg:col-span-2">
            <TodayAppointments />
          </div>

          {/* Right Column - Recent & Actions */}
          <div className="space-y-6">
            <RecentPatients />
            <QuickActions />
          </div>
        </div>

        {/* Debug Info (Development Only) */}
        {process.env.NODE_ENV === 'development' && (
          <details className="mt-8">
            <summary className="text-slate-500 text-sm cursor-pointer hover:text-slate-400">
              Debug Info (Development Only)
            </summary>
            <div className="mt-2 bg-slate-900 rounded-lg border border-slate-800 p-4 text-xs">
              <pre className="text-green-400 overflow-auto">
                {JSON.stringify(
                  {
                    user: {
                      id: user.id,
                      email: user.email,
                      name: user.name,
                      role: user.role,
                      clinicId: user.clinicId,
                      clinicName: user.clinicName,
                    },
                    hasAccessToken: !!session.accessToken,
                    tokenPreview: session.accessToken
                      ? `${session.accessToken.substring(0, 20)}...`
                      : null,
                  },
                  null,
                  2
                )}
              </pre>
            </div>
          </details>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 mt-auto">
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
          <p className="text-center text-xs text-slate-500">
            OpenHeart Cyprus v0.1.0 • GDPR & Law 125(I)/2018 Compliant • Gesy Compatible
          </p>
        </div>
      </footer>

      {/* Command Palette */}
      <CommandPalette open={commandOpen} onOpenChange={setCommandOpen} />
    </div>
  );
}
