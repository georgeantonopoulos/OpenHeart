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
import { LanguageSwitcher } from '@/components/LanguageSwitcher';
import { useTranslation } from 'react-i18next';

interface DashboardContentProps {
  session: Session;
}

/**
 * Dashboard content component (client-side).
 */
export default function DashboardContent({ session }: DashboardContentProps) {
  const { t, i18n } = useTranslation('common');
  const { user } = session;

  const [commandOpen, setCommandOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Format role for display
  const formatRole = (role: string) => {
    return role.charAt(0).toUpperCase() + role.slice(1).replace('_', ' ');
  };

  // Get current time greeting
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return t('dashboard.greeting.morning');
    if (hour < 17) return t('dashboard.greeting.afternoon');
    return t('dashboard.greeting.evening');
  };

  // Format current date
  const formatDate = () => {
    const currentLang = i18n.language || 'en';
    return new Date().toLocaleDateString(currentLang === 'el' ? 'el-GR' : 'en-CY', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

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

  const greeting = getGreeting();
  // Ensure we don't duplicate "Dr." if it's already in the name
  let userName = user.name?.split(' ')[0] || '';
  if (user.name && user.name.toLowerCase().startsWith('dr.')) {
    userName = user.name.split(' ')[1] || '';
  }

  const displayGreeting =
    i18n.language === 'el' ? `${greeting}, Δρ. ${userName}` : `${greeting}, Dr. ${userName}`;

  const navItems = [
    { href: '/patients', label: t('nav.patients') },
    { href: '/appointments', label: t('nav.encounters') },
    { href: '/cdss', label: t('nav.cdss') },
    { href: '/imaging', label: t('nav.imaging') },
    { href: '/procedures', label: 'Worklist' },
    { href: '/referrals/incoming', label: 'Referrals' },
    { href: '/billing/claims', label: 'Claims' },
  ];

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">
      {/* Navigation Bar */}
      <nav className="bg-slate-900 border-b border-slate-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Left - Logo */}
            <div className="flex items-center flex-shrink-0">
              <Link href="/dashboard" className="flex items-center space-x-2 mr-4">
                <div className="w-8 h-8 bg-gradient-to-br from-rose-500 to-rose-600 rounded-lg flex items-center justify-center flex-shrink-0">
                  <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
                  </svg>
                </div>
                <span className="text-xl font-bold text-white hidden sm:block">OpenHeart</span>
              </Link>
            </div>

            {/* Center - Desktop Navigation */}
            <div className="hidden xl:flex flex-1 items-center justify-center overflow-hidden mx-4">
              <div className="flex space-x-1 overflow-x-auto no-scrollbar py-1">
                {navItems.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="px-3 py-2 text-sm text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors whitespace-nowrap"
                  >
                    {item.label}
                  </Link>
                ))}
              </div>
            </div>

            {/* Right Group */}
            <div className="flex items-center space-x-2 sm:space-x-3 flex-shrink-0">
              {/* Search */}
              <button
                className="flex items-center p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors lg:bg-slate-800 lg:border lg:border-slate-700 lg:px-3 lg:py-1.5"
                onClick={() => setCommandOpen(true)}
              >
                <svg className="w-5 h-5 lg:w-4 lg:h-4 lg:mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <span className="hidden xl:inline text-sm">Search...</span>
                <kbd className="hidden 2xl:inline ml-4 px-1.5 py-0.5 text-xs bg-slate-700 rounded text-slate-400">⌘K</kbd>
              </button>

              <LanguageSwitcher />

              {/* Profile */}
              <div className="relative group flex-shrink-0">
                <button className="w-9 h-9 rounded-full bg-gradient-to-br from-rose-500 to-pink-600 flex items-center justify-center text-white font-medium text-sm">
                  {user.name?.charAt(0) || 'U'}
                </button>
                <div className="absolute right-0 mt-2 w-48 bg-slate-900 border border-slate-800 rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-[60]">
                  <div className="py-1">
                    <div className="px-4 py-2 border-b border-slate-800 lg:hidden">
                      <p className="text-sm font-medium text-white truncate">{user.name}</p>
                      <p className="text-xs text-slate-400 truncate">{formatRole(user.role)}</p>
                    </div>
                    <Link href="/profile" className="block px-4 py-2 text-sm text-slate-300 hover:text-white hover:bg-slate-800">
                      My Profile
                    </Link>
                    <Link href="/profile/security" className="block px-4 py-2 text-sm text-slate-300 hover:text-white hover:bg-slate-800">
                      Security
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

              {/* Mobile Menu Toggle */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="xl:hidden p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                aria-label="Toggle menu"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={mobileMenuOpen ? "M6 18L18 6M6 6l12 12" : "M4 6h16M4 12h16M4 18h16"} />
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Dropdown */}
        {mobileMenuOpen && (
          <div className="xl:hidden bg-slate-900 border-t border-slate-800 animate-in slide-in-from-top duration-200">
            <div className="px-4 pt-2 pb-6 space-y-1">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="block px-3 py-3 text-base font-medium text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {item.label}
                </Link>
              ))}
            </div>
          </div>
        )}
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex-1 w-full">
        {/* Welcome Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white">{displayGreeting}</h1>
          <p className="text-slate-400 mt-1 uppercase tracking-wider text-xs font-semibold">
            {formatDate()}
          </p>
        </div>

        {/* Quick Stats */}
        <div className="mb-6">
          <QuickStats />
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <TodayAppointments />
          </div>
          <div className="space-y-6">
            <RecentPatients />
            <QuickActions />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-900/50">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-xs text-slate-500">
            OpenHeart Cyprus v0.1.0 • GDPR & Law 125(I)/2018 Compliant • Gesy Compatible
          </p>
        </div>
      </footer>

      {/* Command Palette */}
      <CommandPalette open={commandOpen} onOpenChange={setCommandOpen} />
    </div>
  );
}
