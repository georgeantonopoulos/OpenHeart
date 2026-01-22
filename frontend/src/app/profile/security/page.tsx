'use client';

import { useState } from 'react';
import { useSession } from 'next-auth/react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import {
  getMFAStatus,
  setupMFA,
  verifyAndEnableMFA,
  disableMFA,
  regenerateBackupCodes,
  MFASetupResponse,
} from '@/lib/api/auth';

type View = 'status' | 'setup' | 'backup-codes' | 'disable';

/**
 * MFA Security Settings Page.
 *
 * Allows users to enable, disable, and manage two-factor authentication.
 */
export default function SecurityPage() {
  const { data: session } = useSession();
  const queryClient = useQueryClient();

  const [view, setView] = useState<View>('status');
  const [setupData, setSetupData] = useState<MFASetupResponse | null>(null);
  const [verificationCode, setVerificationCode] = useState('');
  const [password, setPassword] = useState('');
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [error, setError] = useState('');

  // Fetch MFA status
  const { data: mfaStatus, isLoading } = useQuery({
    queryKey: ['mfaStatus'],
    queryFn: () => getMFAStatus(session?.accessToken || ''),
    enabled: !!session?.accessToken,
  });

  // Setup MFA mutation
  const setupMutation = useMutation({
    mutationFn: () => setupMFA(session?.accessToken || ''),
    onSuccess: (data) => {
      setSetupData(data);
      setView('setup');
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  // Verify and enable mutation
  const verifyMutation = useMutation({
    mutationFn: () => verifyAndEnableMFA(session?.accessToken || '', verificationCode),
    onSuccess: (data) => {
      setBackupCodes(data.backup_codes);
      setView('backup-codes');
      queryClient.invalidateQueries({ queryKey: ['mfaStatus'] });
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  // Disable MFA mutation
  const disableMutation = useMutation({
    mutationFn: () => disableMFA(session?.accessToken || '', password),
    onSuccess: () => {
      setView('status');
      setPassword('');
      queryClient.invalidateQueries({ queryKey: ['mfaStatus'] });
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  // Regenerate backup codes mutation
  const regenerateMutation = useMutation({
    mutationFn: () => regenerateBackupCodes(session?.accessToken || '', verificationCode),
    onSuccess: (codes) => {
      setBackupCodes(codes);
      setVerificationCode('');
      queryClient.invalidateQueries({ queryKey: ['mfaStatus'] });
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  if (!session) {
    return null;
  }

  const handleStartSetup = () => {
    setError('');
    setupMutation.mutate();
  };

  const handleVerify = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    verifyMutation.mutate();
  };

  const handleDisable = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    disableMutation.mutate();
  };

  const handleRegenerate = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    regenerateMutation.mutate();
  };

  const copyBackupCodes = () => {
    navigator.clipboard.writeText(backupCodes.join('\n'));
  };

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <div className="bg-slate-900 border-b border-slate-800">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center space-x-4">
            <Link
              href="/profile"
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
              <h1 className="text-2xl font-bold text-white">Two-Factor Authentication</h1>
              <p className="text-sm text-slate-400">Secure your account with 2FA</p>
            </div>
          </div>
        </div>
      </div>

      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="w-8 h-8 border-2 border-rose-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : view === 'status' ? (
          /* Status View */
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
            {mfaStatus?.enabled ? (
              <>
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center">
                    <svg
                      className="w-6 h-6 text-green-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                      />
                    </svg>
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-white">2FA is Enabled</h2>
                    <p className="text-sm text-slate-400">
                      Your account is protected with two-factor authentication
                    </p>
                  </div>
                </div>

                {/* Backup Codes */}
                <div className="p-4 bg-slate-800/50 rounded-lg mb-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-white">Backup Codes</p>
                      <p className="text-xs text-slate-400">
                        {mfaStatus.backup_codes_remaining} codes remaining
                      </p>
                    </div>
                    <button
                      onClick={() => {
                        setView('backup-codes');
                        setVerificationCode('');
                        setBackupCodes([]);
                      }}
                      className="text-sm text-rose-400 hover:text-rose-300"
                    >
                      Regenerate
                    </button>
                  </div>
                </div>

                {/* Disable */}
                <button
                  onClick={() => setView('disable')}
                  className="text-sm text-slate-400 hover:text-rose-400 transition-colors"
                >
                  Disable Two-Factor Authentication
                </button>
              </>
            ) : (
              <>
                <div className="text-center py-8">
                  <div className="w-16 h-16 bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg
                      className="w-8 h-8 text-slate-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                      />
                    </svg>
                  </div>
                  <h2 className="text-lg font-semibold text-white mb-2">
                    Two-Factor Authentication is Off
                  </h2>
                  <p className="text-sm text-slate-400 mb-6 max-w-sm mx-auto">
                    Add an extra layer of security to your account by enabling two-factor
                    authentication with an authenticator app.
                  </p>
                  <button
                    onClick={handleStartSetup}
                    disabled={setupMutation.isPending}
                    className="px-6 py-3 bg-rose-600 text-white rounded-lg font-medium hover:bg-rose-700 disabled:opacity-50 transition-colors"
                  >
                    {setupMutation.isPending ? 'Setting up...' : 'Enable 2FA'}
                  </button>
                </div>
              </>
            )}

            {error && (
              <div className="mt-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg">
                <p className="text-sm text-rose-400">{error}</p>
              </div>
            )}
          </div>
        ) : view === 'setup' && setupData ? (
          /* Setup View */
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Set Up 2FA</h2>
            <p className="text-sm text-slate-400 mb-6">
              Scan the QR code with your authenticator app (Google Authenticator, Authy, etc.)
            </p>

            <div className="flex flex-col items-center mb-6">
              {/* QR Code would be rendered here - using placeholder */}
              <div className="w-48 h-48 bg-white p-4 rounded-lg mb-4">
                <img
                  src={`https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=${encodeURIComponent(setupData.provisioning_uri)}`}
                  alt="QR Code"
                  className="w-full h-full"
                />
              </div>

              <p className="text-xs text-slate-500 mb-2">Or enter this code manually:</p>
              <code className="px-3 py-2 bg-slate-800 rounded text-sm text-slate-300 font-mono">
                {setupData.secret}
              </code>
            </div>

            <form onSubmit={handleVerify} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">
                  Verification Code
                </label>
                <input
                  type="text"
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ''))}
                  maxLength={6}
                  className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white text-center text-2xl tracking-[0.5em] font-mono placeholder:text-slate-500 focus:outline-none focus:border-rose-500"
                  placeholder="000000"
                />
              </div>

              {error && (
                <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg">
                  <p className="text-sm text-rose-400">{error}</p>
                </div>
              )}

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setView('status');
                    setSetupData(null);
                    setVerificationCode('');
                    setError('');
                  }}
                  className="flex-1 py-3 bg-slate-800 text-slate-300 rounded-lg font-medium hover:bg-slate-700 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={verificationCode.length !== 6 || verifyMutation.isPending}
                  className="flex-1 py-3 bg-rose-600 text-white rounded-lg font-medium hover:bg-rose-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {verifyMutation.isPending ? 'Verifying...' : 'Verify & Enable'}
                </button>
              </div>
            </form>
          </div>
        ) : view === 'backup-codes' ? (
          /* Backup Codes View */
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
            {backupCodes.length > 0 ? (
              <>
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center">
                    <svg
                      className="w-6 h-6 text-green-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-white">
                      {mfaStatus?.enabled ? 'New Backup Codes' : '2FA Enabled!'}
                    </h2>
                    <p className="text-sm text-slate-400">Save these codes in a safe place</p>
                  </div>
                </div>

                <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4 mb-6">
                  <p className="text-sm text-amber-200">
                    <strong>Important:</strong> These codes will only be shown once. Each code can
                    only be used once to sign in if you lose access to your authenticator app.
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-2 mb-6">
                  {backupCodes.map((code, i) => (
                    <div
                      key={i}
                      className="px-3 py-2 bg-slate-800 rounded text-center font-mono text-sm text-slate-300"
                    >
                      {code}
                    </div>
                  ))}
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={copyBackupCodes}
                    className="flex-1 py-3 bg-slate-800 text-slate-300 rounded-lg font-medium hover:bg-slate-700 transition-colors flex items-center justify-center gap-2"
                  >
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"
                      />
                    </svg>
                    Copy Codes
                  </button>
                  <button
                    onClick={() => {
                      setView('status');
                      setBackupCodes([]);
                    }}
                    className="flex-1 py-3 bg-rose-600 text-white rounded-lg font-medium hover:bg-rose-700 transition-colors"
                  >
                    Done
                  </button>
                </div>
              </>
            ) : (
              /* Regenerate form */
              <form onSubmit={handleRegenerate} className="space-y-4">
                <h2 className="text-lg font-semibold text-white mb-2">Regenerate Backup Codes</h2>
                <p className="text-sm text-slate-400 mb-4">
                  Enter your current 2FA code to generate new backup codes. This will invalidate
                  your existing backup codes.
                </p>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">
                    Current 2FA Code
                  </label>
                  <input
                    type="text"
                    value={verificationCode}
                    onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ''))}
                    maxLength={6}
                    className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white text-center text-2xl tracking-[0.5em] font-mono placeholder:text-slate-500 focus:outline-none focus:border-rose-500"
                    placeholder="000000"
                  />
                </div>

                {error && (
                  <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg">
                    <p className="text-sm text-rose-400">{error}</p>
                  </div>
                )}

                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => {
                      setView('status');
                      setVerificationCode('');
                      setError('');
                    }}
                    className="flex-1 py-3 bg-slate-800 text-slate-300 rounded-lg font-medium hover:bg-slate-700 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={verificationCode.length !== 6 || regenerateMutation.isPending}
                    className="flex-1 py-3 bg-rose-600 text-white rounded-lg font-medium hover:bg-rose-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {regenerateMutation.isPending ? 'Generating...' : 'Generate New Codes'}
                  </button>
                </div>
              </form>
            )}
          </div>
        ) : view === 'disable' ? (
          /* Disable View */
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-12 h-12 bg-rose-500/20 rounded-full flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-rose-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">Disable 2FA</h2>
                <p className="text-sm text-slate-400">
                  This will reduce the security of your account
                </p>
              </div>
            </div>

            <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-4 mb-6">
              <p className="text-sm text-rose-200">
                <strong>Warning:</strong> Disabling two-factor authentication will make your account
                less secure. You will only need your password to sign in.
              </p>
            </div>

            <form onSubmit={handleDisable} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">
                  Confirm Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:border-rose-500"
                  placeholder="Enter your password"
                />
              </div>

              {error && (
                <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg">
                  <p className="text-sm text-rose-400">{error}</p>
                </div>
              )}

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setView('status');
                    setPassword('');
                    setError('');
                  }}
                  className="flex-1 py-3 bg-slate-800 text-slate-300 rounded-lg font-medium hover:bg-slate-700 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={password.length === 0 || disableMutation.isPending}
                  className="flex-1 py-3 bg-rose-600 text-white rounded-lg font-medium hover:bg-rose-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {disableMutation.isPending ? 'Disabling...' : 'Disable 2FA'}
                </button>
              </div>
            </form>
          </div>
        ) : null}
      </main>
    </div>
  );
}
