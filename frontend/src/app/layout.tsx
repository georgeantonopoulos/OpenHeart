import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';

const inter = Inter({
  subsets: ['latin', 'greek'],
  variable: '--font-inter',
});

// TODO: No favicon exists in public/ directory. The browser requests /favicon.ico on every page load
// and receives a 404. Add an appropriate favicon (heart/cardiology themed) to public/favicon.ico.
export const metadata: Metadata = {
  title: {
    default: 'OpenHeart Cyprus',
    template: '%s | OpenHeart Cyprus',
  },
  description: 'Open-source Cardiology EMR for Cypriot cardiologists. GDPR-compliant with Gesy integration.',
  keywords: ['EMR', 'Cardiology', 'Cyprus', 'Gesy', 'Healthcare', 'FHIR'],
  authors: [{ name: 'OpenHeart Cyprus' }],
  viewport: 'width=device-width, initial-scale=1',
  robots: 'noindex, nofollow', // Medical data - no indexing
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
