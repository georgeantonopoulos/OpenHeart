'use client';

import { signOut } from 'next-auth/react';
import { Session } from 'next-auth';

interface DashboardContentProps {
  session: Session;
}

/**
 * Dashboard content component (client-side).
 *
 * Displays user information, role, and clinic assignment.
 * Provides sign out functionality.
 */
export default function DashboardContent({ session }: DashboardContentProps) {
  const { user } = session;

  // Role-specific dashboard messages
  const roleMessages: Record<string, string> = {
    admin: 'You have full system access. Use the admin panel to manage users and clinics.',
    cardiologist: 'Access patient records, clinical notes, and CDSS calculators.',
    nurse: 'View patient information and record vitals.',
    receptionist: 'Manage appointments and patient demographics.',
    auditor: 'View audit logs and compliance reports.',
  };

  const roleMessage = roleMessages[user.role] || 'Welcome to OpenHeart Cyprus.';

  // Format role for display
  const formatRole = (role: string) => {
    return role.charAt(0).toUpperCase() + role.slice(1).replace('_', ' ');
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Navigation Bar */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            {/* Left - Logo */}
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-red-600">OpenHeart Cyprus</h1>
            </div>

            {/* Right - User Info & Sign Out */}
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">{user.name}</p>
                <p className="text-xs text-gray-500">
                  {formatRole(user.role)} at {user.clinicName}
                </p>
              </div>
              <button
                onClick={() => signOut({ callbackUrl: '/login' })}
                className="px-3 py-2 text-sm text-red-600 hover:text-red-800 hover:bg-red-50 rounded-md transition-colors"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Welcome Card */}
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Welcome, {user.name}
            </h2>
            <p className="text-gray-600">{roleMessage}</p>
          </div>

          {/* User Info Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
              <h3 className="text-sm font-medium text-blue-900 mb-1">Role</h3>
              <p className="text-lg font-semibold text-blue-700">
                {formatRole(user.role)}
              </p>
            </div>

            <div className="bg-green-50 rounded-lg p-4 border border-green-200">
              <h3 className="text-sm font-medium text-green-900 mb-1">Clinic</h3>
              <p className="text-lg font-semibold text-green-700">
                {user.clinicName}
              </p>
            </div>

            <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
              <h3 className="text-sm font-medium text-purple-900 mb-1">Email</h3>
              <p className="text-lg font-semibold text-purple-700 truncate">
                {user.email}
              </p>
            </div>
          </div>

          {/* Phase 1 Status Card */}
          <div className="bg-yellow-50 rounded-lg shadow p-6 border border-yellow-200">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg
                  className="h-6 w-6 text-yellow-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-lg font-medium text-yellow-900">
                  Phase 1 Complete - Authentication Working
                </h3>
                <p className="mt-2 text-sm text-yellow-700">
                  You are now authenticated. The following features will be added in subsequent phases:
                </p>
                <ul className="mt-3 text-sm text-yellow-700 list-disc list-inside space-y-1">
                  <li>Patient listing and management</li>
                  <li>Clinical notes integration</li>
                  <li>CDSS calculators (GRACE, CHA2DS2-VASc, HAS-BLED)</li>
                  <li>DICOM viewer integration</li>
                  <li>User management (Phase 2)</li>
                  <li>MFA setup (Phase 3)</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Debug Info (Development Only) */}
          {process.env.NODE_ENV === 'development' && (
            <div className="mt-6 bg-gray-800 rounded-lg p-4 text-xs">
              <h3 className="text-gray-400 font-medium mb-2">
                Session Debug Info (Development Only)
              </h3>
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
                    accessTokenPreview: session.accessToken
                      ? `${session.accessToken.substring(0, 20)}...`
                      : null,
                  },
                  null,
                  2
                )}
              </pre>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-auto">
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
          <p className="text-center text-xs text-gray-500">
            OpenHeart Cyprus - GDPR & Law 125(I)/2018 Compliant | Gesy Compatible
          </p>
        </div>
      </footer>
    </div>
  );
}
