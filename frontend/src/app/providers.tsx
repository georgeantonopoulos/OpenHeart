'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SessionProvider } from 'next-auth/react';
import { useState } from 'react';
import ActiveEncounterOverlay from '@/components/ActiveEncounterOverlay';
import '@/lib/i18n';

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 5 * 1000, // 5 seconds (sensible default for an EMR)
            refetchOnWindowFocus: true, // Auto-refresh when switching back to tab
          },
        },
      })
  );

  return (
    <SessionProvider>
      <QueryClientProvider client={queryClient}>
        {children}
        <ActiveEncounterOverlay />
      </QueryClientProvider>
    </SessionProvider>
  );
}
