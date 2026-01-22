'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import {
  FileText,
  Clock,
  AlertCircle,
  Loader2,
  ChevronRight,
  Search,
  Filter,
} from 'lucide-react';
import {
  listReferrals,
  type GesyReferral,
  type ReferralStatus,
  getReferralStatusColor,
  formatReferralStatus,
} from '@/lib/api/gesy';

function IncomingReferralsContent() {
  const { data: session } = useSession();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [referrals, setReferrals] = useState<GesyReferral[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<ReferralStatus | ''>('');
  const [beneficiarySearch, setBeneficiarySearch] = useState('');

  // Default beneficiary for demo (would come from patient context)
  const defaultBeneficiaryId = searchParams.get('beneficiary_id') || 'GHS100001';

  useEffect(() => {
    if (session?.accessToken) {
      loadReferrals();
    }
  }, [session?.accessToken, statusFilter]);

  async function loadReferrals() {
    try {
      setLoading(true);
      setError(null);
      const params: { beneficiary_id: string; status?: ReferralStatus } = {
        beneficiary_id: beneficiarySearch || defaultBeneficiaryId,
      };
      if (statusFilter) {
        params.status = statusFilter;
      }
      const data = await listReferrals(session!.accessToken, params);
      setReferrals(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load referrals');
    } finally {
      setLoading(false);
    }
  }

  if (!session) return null;

  return (
    <div className="min-h-screen bg-slate-950 p-6">
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Incoming Referrals</h1>
            <p className="mt-1 text-sm text-slate-400">
              Referrals received from personal doctors via Gesy
            </p>
          </div>
        </div>

        {/* Filters */}
        <div className="mb-6 flex flex-wrap items-center gap-4">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Beneficiary ID (e.g., GHS100001)"
              value={beneficiarySearch}
              onChange={(e) => setBeneficiarySearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && loadReferrals()}
              className="w-full rounded-lg border border-white/10 bg-white/5 py-2 pl-10 pr-4 text-white placeholder-slate-500 focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-slate-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as ReferralStatus | '')}
              className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white focus:border-teal-500 focus:outline-none"
            >
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="used">Used</option>
              <option value="expired">Expired</option>
            </select>
          </div>
          <button
            onClick={loadReferrals}
            className="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-500 transition-colors"
          >
            Search
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 flex items-center gap-3 rounded-lg border border-red-500/30 bg-red-500/10 p-4">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {/* Loading */}
        {loading && referrals.length === 0 ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin text-teal-400" />
            <span className="ml-3 text-slate-400">Loading referrals...</span>
          </div>
        ) : referrals.length === 0 ? (
          /* Empty State */
          <div className="rounded-lg border border-white/10 bg-slate-900 p-12 text-center">
            <FileText className="mx-auto h-12 w-12 text-slate-500" />
            <h3 className="mt-4 text-lg font-medium text-white">No referrals found</h3>
            <p className="mt-2 text-slate-400">
              No referrals match the current filters. Try adjusting your search.
            </p>
          </div>
        ) : (
          /* Referrals List */
          <div className="space-y-3">
            {referrals.map((referral) => (
              <Link
                key={referral.referral_id}
                href={`/referrals/${referral.referral_id}`}
                className="block rounded-lg border border-white/10 bg-slate-900 p-4 transition-all hover:border-white/20 hover:bg-slate-800"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-mono text-slate-300">
                        {referral.referral_id}
                      </span>
                      <span
                        className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${getReferralStatusColor(referral.status)}`}
                      >
                        {formatReferralStatus(referral.status)}
                      </span>
                      {referral.urgency === 'urgent' && (
                        <span className="inline-flex items-center rounded-full border border-red-500/30 bg-red-500/20 px-2.5 py-0.5 text-xs font-medium text-red-400">
                          Urgent
                        </span>
                      )}
                    </div>
                    <p className="mt-1 text-white">
                      {referral.diagnosis_description}
                    </p>
                    <div className="mt-2 flex items-center gap-4 text-sm text-slate-400">
                      <span>ICD-10: {referral.diagnosis_code}</span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        Valid until {new Date(referral.valid_until).toLocaleDateString('en-GB')}
                      </span>
                      <span>From: Dr. {referral.referring_doctor_id}</span>
                    </div>
                  </div>
                  <ChevronRight className="h-5 w-5 text-slate-500" />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function IncomingReferralsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-slate-950">
          <Loader2 className="h-8 w-8 animate-spin text-teal-400" />
        </div>
      }
    >
      <IncomingReferralsContent />
    </Suspense>
  );
}
