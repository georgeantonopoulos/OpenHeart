import { redirect } from 'next/navigation';

export default function Home() {
  // Redirect to login or dashboard based on auth status
  // For now, redirect to login
  redirect('/login');
}
