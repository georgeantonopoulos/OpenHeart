/**
 * Dashboard page for OpenHeart Cyprus.
 *
 * This is a server component that verifies the user session and
 * renders the DashboardContent client component.
 *
 * Protected route - unauthenticated users are redirected to /login.
 */

import { getServerSession } from 'next-auth';
import { redirect } from 'next/navigation';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';
import DashboardContent from './DashboardContent';

export default async function DashboardPage() {
  // Get session from server
  const session = await getServerSession(authOptions);

  // Redirect to login if not authenticated
  if (!session) {
    redirect('/login');
  }

  // Check for token refresh error
  if (session.error === 'RefreshAccessTokenError') {
    // Redirect to login with error message
    redirect('/login?error=SessionExpired');
  }

  return <DashboardContent session={session} />;
}
