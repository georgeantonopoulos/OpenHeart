/**
 * Next.js Middleware for OpenHeart Cyprus.
 *
 * Protects routes that require authentication using NextAuth.
 * Unauthenticated requests are redirected to /login with the
 * original URL as a callback parameter.
 */

import { withAuth } from 'next-auth/middleware';

/**
 * NextAuth middleware configuration.
 *
 * Automatically redirects unauthenticated users to the sign-in page.
 * The callback URL is preserved so users return to their intended
 * destination after logging in.
 */
export default withAuth({
  pages: {
    signIn: '/login',
  },
});

/**
 * Middleware matcher configuration.
 *
 * Specifies which routes should be protected by authentication.
 * Routes not matching these patterns are publicly accessible.
 */
export const config = {
  matcher: [
    // Protected application routes
    '/dashboard/:path*',
    '/patients/:path*',
    '/encounters/:path*',
    '/notes/:path*',
    '/imaging/:path*',
    '/cdss/:path*',
    '/reports/:path*',
    '/appointments/:path*',
    '/procedures/:path*',
    '/referrals/:path*',
    '/billing/:path*',

    // Admin routes
    '/admin/:path*',

    // Profile and settings
    '/profile/:path*',
    '/settings/:path*',
  ],
};
