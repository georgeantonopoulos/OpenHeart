'use client';

import { useState } from 'react';
import { useSession } from 'next-auth/react';
import { useQuery, useMutation } from '@tanstack/react-query';
import Link from 'next/link';
import { getMFAStatus, changePassword, checkPasswordStrength } from '@/lib/api/auth';

/**
 * User Profile Page.
 *
 * Shows user information and account settings.
 */
export default function ProfilePage() {
  const { data: session } = useSession();
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState(false);

  // Fetch MFA status
  const { data: mfaStatus } = useQuery({
    queryKey: ['mfaStatus'],
    queryFn: () => getMFAStatus(session?.accessToken || ''),
    enabled: !!session?.accessToken,
  });

  // Change password mutation
  const passwordMutation = useMutation({
    mutationFn: () => changePassword(session?.accessToken || '', currentPassword, newPassword),
    onSuccess: () => {
      setPasswordSuccess(true);
      setShowPasswordForm(false);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    },
    onError: (err: Error) => {
      setPasswordError(err.message);
    },
  });

  // Password validation
  const passwordStrength = checkPasswordStrength(newPassword);
  const passwordsMatch = newPassword === confirmPassword;
  const canChangePassword =
    currentPassword.length > 0 &&
    passwordStrength.meets_requirements &&
    passwordsMatch &&
    confirmPassword.length > 0;

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError('');
    if (canChangePassword) {
      passwordMutation.mutate();
    }
  };

  if (!session) {
    return null;
  }

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <div className="bg-slate-900 border-b border-slate-800">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
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
              <h1 className="text-2xl font-bold text-white">Profile</h1>
              <p className="text-sm text-slate-400">Manage your account settings</p>
            </div>
          </div>
        </div>
      </div>

      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* User Info */}
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Account Information</h2>
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-rose-500/20 rounded-full flex items-center justify-center">
                <span className="text-2xl font-bold text-rose-400">
                  {session.user?.name?.charAt(0) || session.user?.email?.charAt(0) || '?'}
                </span>
              </div>
              <div>
                <p className="text-lg font-medium text-white">{session.user?.name || 'User'}</p>
                <p className="text-sm text-slate-400">{session.user?.email}</p>
              </div>
            </div>

            <div className="grid gap-3 pt-4 border-t border-slate-800">
              <div className="flex justify-between">
                <span className="text-sm text-slate-400">Role</span>
                <span className="text-sm text-white font-medium capitalize">
                  {session.user?.role || 'User'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-slate-400">Clinic</span>
                <span className="text-sm text-white font-medium">
                  {session.user?.clinic_name || 'N/A'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Security */}
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Security</h2>

          {/* MFA Status */}
          <div className="flex items-center justify-between py-4 border-b border-slate-800">
            <div>
              <p className="text-sm font-medium text-white">Two-Factor Authentication</p>
              <p className="text-xs text-slate-400">
                {mfaStatus?.enabled
                  ? `Enabled (${mfaStatus.backup_codes_remaining} backup codes remaining)`
                  : 'Add an extra layer of security to your account'}
              </p>
            </div>
            <Link
              href="/profile/security"
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                mfaStatus?.enabled
                  ? 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                  : 'bg-rose-600 text-white hover:bg-rose-700'
              }`}
            >
              {mfaStatus?.enabled ? 'Manage' : 'Enable'}
            </Link>
          </div>

          {/* Change Password */}
          <div className="py-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-white">Password</p>
                <p className="text-xs text-slate-400">Change your account password</p>
              </div>
              {!showPasswordForm && (
                <button
                  onClick={() => setShowPasswordForm(true)}
                  className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg text-sm font-medium hover:bg-slate-700 transition-colors"
                >
                  Change
                </button>
              )}
            </div>

            {/* Password Success */}
            {passwordSuccess && (
              <div className="mt-4 p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
                <p className="text-sm text-green-400">Password changed successfully!</p>
              </div>
            )}

            {/* Password Form */}
            {showPasswordForm && (
              <form onSubmit={handlePasswordSubmit} className="mt-4 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">
                    Current Password
                  </label>
                  <input
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:border-rose-500"
                    placeholder="Enter current password"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">
                    New Password
                  </label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:border-rose-500"
                    placeholder="Enter new password"
                  />
                  {newPassword.length > 0 && (
                    <div className="mt-2">
                      <div className="flex gap-1 mb-1">
                        {[1, 2, 3, 4, 5, 6].map((i) => (
                          <div
                            key={i}
                            className={`h-1 flex-1 rounded ${
                              i <= passwordStrength.score
                                ? passwordStrength.strength === 'weak'
                                  ? 'bg-rose-500'
                                  : passwordStrength.strength === 'moderate'
                                    ? 'bg-amber-500'
                                    : 'bg-green-500'
                                : 'bg-slate-700'
                            }`}
                          />
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">
                    Confirm New Password
                  </label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className={`w-full px-4 py-2.5 bg-slate-800 border rounded-lg text-white placeholder:text-slate-500 focus:outline-none ${
                      confirmPassword.length > 0 && !passwordsMatch
                        ? 'border-rose-500'
                        : 'border-slate-700 focus:border-rose-500'
                    }`}
                    placeholder="Confirm new password"
                  />
                  {confirmPassword.length > 0 && !passwordsMatch && (
                    <p className="text-xs text-rose-400 mt-1">Passwords do not match</p>
                  )}
                </div>

                {passwordError && (
                  <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg">
                    <p className="text-sm text-rose-400">{passwordError}</p>
                  </div>
                )}

                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => {
                      setShowPasswordForm(false);
                      setCurrentPassword('');
                      setNewPassword('');
                      setConfirmPassword('');
                      setPasswordError('');
                    }}
                    className="flex-1 py-2.5 bg-slate-800 text-slate-300 rounded-lg text-sm font-medium hover:bg-slate-700 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={!canChangePassword || passwordMutation.isPending}
                    className="flex-1 py-2.5 bg-rose-600 text-white rounded-lg text-sm font-medium hover:bg-rose-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {passwordMutation.isPending ? 'Changing...' : 'Change Password'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>

        {/* Sessions Link */}
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-white">Active Sessions</h2>
              <p className="text-sm text-slate-400">View and manage your active sessions</p>
            </div>
            <Link
              href="/profile/sessions"
              className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg text-sm font-medium hover:bg-slate-700 transition-colors"
            >
              View Sessions
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
