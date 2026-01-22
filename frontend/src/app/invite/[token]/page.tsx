'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useMutation, useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import {
  validateInvitation,
  acceptInvitation,
  checkPasswordStrength,
  InvitationDetails,
  ROLE_LABELS,
} from '@/lib/api/auth';

type Step = 'welcome' | 'security' | 'legal' | 'complete';

/**
 * Invitation acceptance wizard.
 *
 * Public page for new users to complete registration via invitation link.
 */
export default function InviteAcceptPage() {
  const router = useRouter();
  const params = useParams();
  const token = params.token as string;

  const [step, setStep] = useState<Step>('welcome');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [gdprConsent, setGdprConsent] = useState(false);
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [error, setError] = useState('');

  // Validate invitation token
  const {
    data: invitation,
    isLoading,
    error: validationError,
  } = useQuery({
    queryKey: ['invitation', token],
    queryFn: () => validateInvitation(token),
    retry: false,
  });

  // Accept invitation mutation
  const acceptMutation = useMutation({
    mutationFn: () =>
      acceptInvitation(token, {
        password,
        confirm_password: confirmPassword,
        gdpr_consent: gdprConsent,
        terms_accepted: termsAccepted,
      }),
    onSuccess: () => {
      setStep('complete');
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  // Password strength
  const passwordStrength = checkPasswordStrength(password);

  // Validation
  const passwordsMatch = password === confirmPassword;
  const canProceedToLegal =
    passwordStrength.meets_requirements && passwordsMatch && confirmPassword.length > 0;
  const canSubmit = gdprConsent && termsAccepted;

  // Handle step navigation
  const goToSecurity = () => setStep('security');
  const goToLegal = () => {
    if (canProceedToLegal) {
      setStep('legal');
    }
  };
  const handleSubmit = () => {
    if (canSubmit) {
      setError('');
      acceptMutation.mutate();
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-rose-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-400">Validating invitation...</p>
        </div>
      </div>
    );
  }

  // Invalid/expired invitation
  if (validationError || !invitation) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-slate-900 rounded-xl border border-slate-800 p-8 text-center">
          <div className="w-16 h-16 bg-rose-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg
              className="w-8 h-8 text-rose-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">Invalid Invitation</h1>
          <p className="text-slate-400 mb-6">
            This invitation link is invalid or has expired. Please contact your administrator for a
            new invitation.
          </p>
          <Link
            href="/login"
            className="inline-flex items-center justify-center px-6 py-3 bg-slate-800 text-white rounded-lg hover:bg-slate-700 transition-colors"
          >
            Go to Login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="max-w-lg w-full">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 text-2xl font-bold text-white">
            <svg className="w-8 h-8 text-rose-500" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
            </svg>
            OpenHeart Cyprus
          </div>
        </div>

        {/* Step Indicator */}
        <div className="flex items-center justify-center gap-2 mb-8">
          {(['welcome', 'security', 'legal', 'complete'] as Step[]).map((s, i) => (
            <div key={s} className="flex items-center">
              <div
                className={`w-3 h-3 rounded-full ${
                  step === s
                    ? 'bg-rose-500'
                    : i < ['welcome', 'security', 'legal', 'complete'].indexOf(step)
                      ? 'bg-rose-500/50'
                      : 'bg-slate-700'
                }`}
              />
              {i < 3 && <div className="w-8 h-0.5 bg-slate-700" />}
            </div>
          ))}
        </div>

        {/* Card */}
        <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
          {/* Welcome Step */}
          {step === 'welcome' && (
            <div className="p-8">
              <h1 className="text-2xl font-bold text-white mb-2">Welcome to OpenHeart</h1>
              <p className="text-slate-400 mb-6">
                You&apos;ve been invited to join {invitation.clinic_name} as a{' '}
                {ROLE_LABELS[invitation.role] || invitation.role}.
              </p>

              <div className="bg-slate-800/50 rounded-lg p-4 mb-6">
                <div className="grid gap-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Name</span>
                    <span className="text-white font-medium">
                      {invitation.title ? `${invitation.title} ` : ''}
                      {invitation.first_name} {invitation.last_name}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Email</span>
                    <span className="text-white font-medium">{invitation.email}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Role</span>
                    <span className="text-white font-medium">
                      {ROLE_LABELS[invitation.role] || invitation.role}
                    </span>
                  </div>
                  {invitation.specialty && (
                    <div className="flex justify-between">
                      <span className="text-slate-400">Specialty</span>
                      <span className="text-white font-medium">{invitation.specialty}</span>
                    </div>
                  )}
                </div>
              </div>

              {invitation.message && (
                <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 mb-6">
                  <p className="text-sm text-blue-200">{invitation.message}</p>
                </div>
              )}

              <button
                onClick={goToSecurity}
                className="w-full py-3 bg-rose-600 text-white rounded-lg font-medium hover:bg-rose-700 transition-colors"
              >
                Continue
              </button>
            </div>
          )}

          {/* Security Step */}
          {step === 'security' && (
            <div className="p-8">
              <h1 className="text-2xl font-bold text-white mb-2">Create Your Password</h1>
              <p className="text-slate-400 mb-6">Choose a strong password to secure your account.</p>

              <div className="space-y-4">
                {/* Password */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">
                    Password
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:border-rose-500"
                      placeholder="Enter password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
                    >
                      {showPassword ? (
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"
                          />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                          />
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                          />
                        </svg>
                      )}
                    </button>
                  </div>

                  {/* Strength Meter */}
                  {password.length > 0 && (
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
                      <p
                        className={`text-xs ${
                          passwordStrength.strength === 'weak'
                            ? 'text-rose-400'
                            : passwordStrength.strength === 'moderate'
                              ? 'text-amber-400'
                              : 'text-green-400'
                        }`}
                      >
                        {passwordStrength.strength.charAt(0).toUpperCase() +
                          passwordStrength.strength.slice(1)}{' '}
                        password
                      </p>
                    </div>
                  )}
                </div>

                {/* Confirm Password */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">
                    Confirm Password
                  </label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className={`w-full px-4 py-3 bg-slate-800 border rounded-lg text-white placeholder:text-slate-500 focus:outline-none ${
                      confirmPassword.length > 0 && !passwordsMatch
                        ? 'border-rose-500'
                        : 'border-slate-700 focus:border-rose-500'
                    }`}
                    placeholder="Confirm password"
                  />
                  {confirmPassword.length > 0 && !passwordsMatch && (
                    <p className="text-xs text-rose-400 mt-1">Passwords do not match</p>
                  )}
                </div>

                {/* Requirements */}
                <div className="bg-slate-800/50 rounded-lg p-4">
                  <p className="text-sm font-medium text-slate-300 mb-2">Password Requirements</p>
                  <ul className="space-y-1 text-sm">
                    {[
                      { text: 'At least 12 characters', met: password.length >= 12 },
                      { text: 'One uppercase letter', met: /[A-Z]/.test(password) },
                      { text: 'One lowercase letter', met: /[a-z]/.test(password) },
                      { text: 'One number', met: /[0-9]/.test(password) },
                      {
                        text: 'One special character',
                        met: /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?/~`]/.test(password),
                      },
                    ].map(({ text, met }) => (
                      <li
                        key={text}
                        className={`flex items-center gap-2 ${met ? 'text-green-400' : 'text-slate-500'}`}
                      >
                        {met ? (
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path
                              fillRule="evenodd"
                              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                              clipRule="evenodd"
                            />
                          </svg>
                        ) : (
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path
                              fillRule="evenodd"
                              d="M10 18a8 8 0 100-16 8 8 0 000 16zm0-2a6 6 0 100-12 6 6 0 000 12z"
                              clipRule="evenodd"
                            />
                          </svg>
                        )}
                        {text}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setStep('welcome')}
                  className="flex-1 py-3 bg-slate-800 text-slate-300 rounded-lg font-medium hover:bg-slate-700 transition-colors"
                >
                  Back
                </button>
                <button
                  onClick={goToLegal}
                  disabled={!canProceedToLegal}
                  className="flex-1 py-3 bg-rose-600 text-white rounded-lg font-medium hover:bg-rose-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Continue
                </button>
              </div>
            </div>
          )}

          {/* Legal Step */}
          {step === 'legal' && (
            <div className="p-8">
              <h1 className="text-2xl font-bold text-white mb-2">Terms & Consent</h1>
              <p className="text-slate-400 mb-6">
                Please review and accept the following to complete your registration.
              </p>

              <div className="space-y-4">
                {/* GDPR Consent */}
                <label className="flex items-start gap-3 p-4 bg-slate-800/50 rounded-lg cursor-pointer hover:bg-slate-800 transition-colors">
                  <input
                    type="checkbox"
                    checked={gdprConsent}
                    onChange={(e) => setGdprConsent(e.target.checked)}
                    className="mt-1 w-5 h-5 rounded bg-slate-700 border-slate-600 text-rose-600 focus:ring-rose-500"
                  />
                  <div>
                    <p className="text-sm font-medium text-white">GDPR Data Processing Consent</p>
                    <p className="text-xs text-slate-400 mt-1">
                      I consent to the processing of my personal data in accordance with EU GDPR and
                      Cyprus Law 125(I)/2018. I understand that my data will be stored securely and
                      used only for healthcare purposes.
                    </p>
                  </div>
                </label>

                {/* Terms */}
                <label className="flex items-start gap-3 p-4 bg-slate-800/50 rounded-lg cursor-pointer hover:bg-slate-800 transition-colors">
                  <input
                    type="checkbox"
                    checked={termsAccepted}
                    onChange={(e) => setTermsAccepted(e.target.checked)}
                    className="mt-1 w-5 h-5 rounded bg-slate-700 border-slate-600 text-rose-600 focus:ring-rose-500"
                  />
                  <div>
                    <p className="text-sm font-medium text-white">Terms of Service</p>
                    <p className="text-xs text-slate-400 mt-1">
                      I have read and agree to the Terms of Service and Privacy Policy. I understand
                      my responsibilities as a healthcare professional using this system.
                    </p>
                  </div>
                </label>
              </div>

              {error && (
                <div className="mt-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg">
                  <p className="text-sm text-rose-400">{error}</p>
                </div>
              )}

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setStep('security')}
                  className="flex-1 py-3 bg-slate-800 text-slate-300 rounded-lg font-medium hover:bg-slate-700 transition-colors"
                >
                  Back
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={!canSubmit || acceptMutation.isPending}
                  className="flex-1 py-3 bg-rose-600 text-white rounded-lg font-medium hover:bg-rose-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {acceptMutation.isPending ? (
                    <span className="flex items-center justify-center gap-2">
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Creating Account...
                    </span>
                  ) : (
                    'Create Account'
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Complete Step */}
          {step === 'complete' && (
            <div className="p-8 text-center">
              <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                <svg
                  className="w-8 h-8 text-green-400"
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
              <h1 className="text-2xl font-bold text-white mb-2">Account Created!</h1>
              <p className="text-slate-400 mb-6">
                Your account has been created successfully. You can now log in to OpenHeart.
              </p>
              <Link
                href="/login"
                className="inline-flex items-center justify-center px-6 py-3 bg-rose-600 text-white rounded-lg font-medium hover:bg-rose-700 transition-colors"
              >
                Go to Login
              </Link>
            </div>
          )}
        </div>

        {/* Footer */}
        <p className="text-center text-sm text-slate-500 mt-6">
          Having trouble?{' '}
          <a href="mailto:support@openheart.cy" className="text-rose-400 hover:underline">
            Contact support
          </a>
        </p>
      </div>
    </div>
  );
}
