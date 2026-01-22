'use client';

import { useState, useEffect } from 'react';
import { signIn, useSession } from 'next-auth/react';
import { useRouter, useSearchParams } from 'next/navigation';

/**
 * Login page for OpenHeart Cyprus.
 *
 * Authenticates users via NextAuth credentials provider which calls
 * the FastAPI backend /api/auth/login endpoint.
 *
 * In development mode, displays test account credentials.
 */
export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { status } = useSession();

  // Get callback URL from query params or default to dashboard
  const callbackUrl = searchParams.get('callbackUrl') || '/dashboard';

  // Form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Redirect if already authenticated
  useEffect(() => {
    if (status === 'authenticated') {
      router.push(callbackUrl);
    }
  }, [status, router, callbackUrl]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const result = await signIn('credentials', {
        email,
        password,
        redirect: false,
      });

      if (result?.error) {
        // Generic error message - don't reveal if email exists
        setError('Invalid email or password');
      } else if (result?.ok) {
        // Successful login - redirect to callback URL
        router.push(callbackUrl);
      }
    } catch (err) {
      setError('An error occurred. Please try again.');
      console.error('Login error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Fill in test credentials (dev mode only)
  const fillTestCredentials = (testEmail: string, testPassword: string) => {
    setEmail(testEmail);
    setPassword(testPassword);
    setError('');
  };

  // Check if we're in development mode
  const isDev = process.env.NODE_ENV === 'development';

  // Show loading while checking session
  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-gray-600">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow-lg">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-red-600">OpenHeart Cyprus</h1>
          <p className="mt-2 text-gray-600">Cardiology EMR System</p>
        </div>

        {/* Login Form */}
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {/* Error Message */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Email Field */}
          <div className="space-y-4">
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700"
              >
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-red-500 focus:border-red-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                placeholder="doctor@clinic.cy"
                disabled={isLoading}
              />
            </div>

            {/* Password Field */}
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700"
              >
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-red-500 focus:border-red-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                disabled={isLoading}
              />
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <span className="flex items-center">
                <svg
                  className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Signing in...
              </span>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        {/* Development Test Accounts */}
        {isDev && (
          <div className="mt-4 p-4 bg-blue-50 rounded-md border border-blue-200">
            <p className="text-sm font-medium text-blue-800 mb-3">
              Development Test Accounts
            </p>
            <div className="space-y-2 text-xs">
              <button
                type="button"
                onClick={() => fillTestCredentials('admin@openheart.example.com', 'DevAdmin123!')}
                className="w-full text-left p-2 bg-white rounded border border-blue-200 hover:bg-blue-50 transition-colors"
              >
                <span className="font-medium text-blue-900">System Admin</span>
                <span className="text-blue-600 ml-2">admin@openheart.example.com</span>
              </button>
              <button
                type="button"
                onClick={() => fillTestCredentials('cardiologist@openheart.example.com', 'TestUser123!')}
                className="w-full text-left p-2 bg-white rounded border border-blue-200 hover:bg-blue-50 transition-colors"
              >
                <span className="font-medium text-blue-900">Cardiologist</span>
                <span className="text-blue-600 ml-2">cardiologist@openheart.example.com</span>
              </button>
              <button
                type="button"
                onClick={() => fillTestCredentials('nurse@openheart.example.com', 'TestUser123!')}
                className="w-full text-left p-2 bg-white rounded border border-blue-200 hover:bg-blue-50 transition-colors"
              >
                <span className="font-medium text-blue-900">Nurse</span>
                <span className="text-blue-600 ml-2">nurse@openheart.example.com</span>
              </button>
              <button
                type="button"
                onClick={() => fillTestCredentials('reception@openheart.example.com', 'TestUser123!')}
                className="w-full text-left p-2 bg-white rounded border border-blue-200 hover:bg-blue-50 transition-colors"
              >
                <span className="font-medium text-blue-900">Receptionist</span>
                <span className="text-blue-600 ml-2">reception@openheart.example.com</span>
              </button>
            </div>
            <p className="mt-3 text-xs text-blue-600">
              Click an account to auto-fill credentials
            </p>
          </div>
        )}

        {/* Footer */}
        <div className="text-center text-xs text-gray-500 space-y-1">
          <p>GDPR & Law 125(I)/2018 Compliant</p>
          <p>Gesy Compatible</p>
        </div>
      </div>
    </div>
  );
}
