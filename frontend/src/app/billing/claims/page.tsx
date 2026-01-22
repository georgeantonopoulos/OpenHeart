'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSession } from 'next-auth/react';
import { useSearchParams } from 'next/navigation';
import {
  DollarSign,
  AlertCircle,
  Loader2,
  Filter,
  FileText,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  ChevronRight,
  X,
  ArrowRight,
} from 'lucide-react';
import {
  listClaims,
  getClaim,
  type GesyClaim,
  type ClaimStatus,
  getClaimStatusColor,
  formatClaimStatus,
} from '@/lib/api/gesy';

function ClaimsContent() {
  const { data: session } = useSession();
  const searchParams = useSearchParams();

  const [claims, setClaims] = useState<GesyClaim[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<ClaimStatus | ''>('');
  const [selectedClaim, setSelectedClaim] = useState<GesyClaim | null>(null);
  const [showResolutionPanel, setShowResolutionPanel] = useState(false);

  useEffect(() => {
    if (session?.accessToken) {
      loadClaims();
    }
  }, [session?.accessToken, statusFilter]);

  async function loadClaims() {
    try {
      setLoading(true);
      setError(null);
      const params: { status?: ClaimStatus } = {};
      if (statusFilter) params.status = statusFilter;
      const data = await listClaims(session!.accessToken, params);
      setClaims(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load claims');
    } finally {
      setLoading(false);
    }
  }

  function handleClaimClick(claim: GesyClaim) {
    setSelectedClaim(claim);
    if (claim.status === 'rejected' || claim.status === 'partially_approved') {
      setShowResolutionPanel(true);
    }
  }

  if (!session) return null;

  // Calculate statistics
  const stats = {
    total: claims.length,
    totalClaimed: claims.reduce((sum, c) => sum + c.total_claimed, 0),
    totalApproved: claims.reduce((sum, c) => sum + (c.total_approved || 0), 0),
    pending: claims.filter((c) => c.status === 'submitted' || c.status === 'under_review').length,
    rejected: claims.filter((c) => c.status === 'rejected').length,
    paid: claims.filter((c) => c.status === 'paid').length,
  };

  return (
    <div className="min-h-screen bg-slate-950 p-6">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white">Claims Console</h1>
          <p className="mt-1 text-sm text-slate-400">
            Manage Gesy claims for reimbursement
          </p>
        </div>

        {/* Statistics */}
        <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-lg border border-white/10 bg-slate-900 p-4">
            <div className="flex items-center gap-3">
              <DollarSign className="h-8 w-8 text-teal-400" />
              <div>
                <p className="text-sm text-slate-400">Total Claimed</p>
                <p className="text-xl font-bold text-white">
                  &euro;{stats.totalClaimed.toFixed(2)}
                </p>
              </div>
            </div>
          </div>
          <div className="rounded-lg border border-white/10 bg-slate-900 p-4">
            <div className="flex items-center gap-3">
              <TrendingUp className="h-8 w-8 text-green-400" />
              <div>
                <p className="text-sm text-slate-400">Total Approved</p>
                <p className="text-xl font-bold text-white">
                  &euro;{stats.totalApproved.toFixed(2)}
                </p>
              </div>
            </div>
          </div>
          <div className="rounded-lg border border-white/10 bg-slate-900 p-4">
            <div className="flex items-center gap-3">
              <Clock className="h-8 w-8 text-amber-400" />
              <div>
                <p className="text-sm text-slate-400">Pending Review</p>
                <p className="text-xl font-bold text-white">{stats.pending}</p>
              </div>
            </div>
          </div>
          <div className="rounded-lg border border-white/10 bg-slate-900 p-4">
            <div className="flex items-center gap-3">
              <XCircle className="h-8 w-8 text-red-400" />
              <div>
                <p className="text-sm text-slate-400">Rejected</p>
                <p className="text-xl font-bold text-white">{stats.rejected}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="mb-6 flex items-center gap-4">
          <Filter className="h-4 w-4 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as ClaimStatus | '')}
            className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white focus:border-teal-500 focus:outline-none"
          >
            <option value="">All Statuses</option>
            <option value="draft">Draft</option>
            <option value="submitted">Submitted</option>
            <option value="under_review">Under Review</option>
            <option value="approved">Approved</option>
            <option value="partially_approved">Partially Approved</option>
            <option value="rejected">Rejected</option>
            <option value="paid">Paid</option>
          </select>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 flex items-center gap-3 rounded-lg border border-red-500/30 bg-red-500/10 p-4">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <p className="text-red-400">{error}</p>
          </div>
        )}

        <div className="flex gap-6">
          {/* Claims List */}
          <div className={`flex-1 ${showResolutionPanel ? 'max-w-[60%]' : ''}`}>
            {loading && claims.length === 0 ? (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="h-8 w-8 animate-spin text-teal-400" />
                <span className="ml-3 text-slate-400">Loading claims...</span>
              </div>
            ) : claims.length === 0 ? (
              <div className="rounded-lg border border-white/10 bg-slate-900 p-12 text-center">
                <FileText className="mx-auto h-12 w-12 text-slate-500" />
                <h3 className="mt-4 text-lg font-medium text-white">No claims found</h3>
                <p className="mt-2 text-slate-400">
                  Submit a claim after closing a referral to see it here.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {claims.map((claim) => (
                  <button
                    key={claim.claim_id}
                    onClick={() => handleClaimClick(claim)}
                    className={`w-full text-left rounded-lg border p-4 transition-all hover:border-white/20 ${
                      selectedClaim?.claim_id === claim.claim_id
                        ? 'border-teal-500/50 bg-slate-800'
                        : 'border-white/10 bg-slate-900'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <span className="text-sm font-mono text-slate-300">
                            {claim.claim_id}
                          </span>
                          <span
                            className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${getClaimStatusColor(claim.status)}`}
                          >
                            {formatClaimStatus(claim.status)}
                          </span>
                        </div>
                        <div className="mt-2 flex items-center gap-4 text-sm text-slate-400">
                          <span>
                            Service: {new Date(claim.service_date).toLocaleDateString('en-GB')}
                          </span>
                          <span>Ref: {claim.referral_id}</span>
                          <span className="font-medium text-white">
                            &euro;{claim.total_claimed.toFixed(2)}
                          </span>
                          {claim.total_approved != null && (
                            <span className="text-green-400">
                              Approved: &euro;{claim.total_approved.toFixed(2)}
                            </span>
                          )}
                        </div>
                        {claim.rejection_reason && (
                          <p className="mt-1 text-sm text-red-400">
                            {claim.rejection_reason}
                          </p>
                        )}
                      </div>
                      <ChevronRight className="h-5 w-5 text-slate-500" />
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Rejection Resolution Side-Panel */}
          {showResolutionPanel && selectedClaim && (
            <div className="w-[40%] min-w-[320px] rounded-lg border border-white/10 bg-slate-900 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white">
                  {selectedClaim.status === 'rejected'
                    ? 'Rejection Resolution'
                    : 'Claim Details'}
                </h2>
                <button
                  onClick={() => {
                    setShowResolutionPanel(false);
                    setSelectedClaim(null);
                  }}
                  className="rounded p-1 text-slate-400 hover:bg-white/10 hover:text-white"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {selectedClaim.rejection_reason && (
                <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 p-3">
                  <p className="text-sm font-medium text-red-400">Rejection Reason:</p>
                  <p className="mt-1 text-sm text-red-300">{selectedClaim.rejection_reason}</p>
                </div>
              )}

              {selectedClaim.reviewer_notes && (
                <div className="mb-4 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3">
                  <p className="text-sm font-medium text-amber-400">Reviewer Notes:</p>
                  <p className="mt-1 text-sm text-amber-300">{selectedClaim.reviewer_notes}</p>
                </div>
              )}

              {/* Line Items with Issues */}
              <div className="mb-4">
                <h3 className="text-sm font-medium text-slate-400 mb-2">Line Items</h3>
                <div className="space-y-2">
                  {selectedClaim.line_items.map((item) => (
                    <div
                      key={item.line_number}
                      className={`rounded-lg border p-3 ${
                        item.approved === false
                          ? 'border-red-500/30 bg-red-500/5'
                          : item.approved === true
                            ? 'border-green-500/30 bg-green-500/5'
                            : 'border-white/10 bg-white/5'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="text-sm text-white">
                            <span className="font-mono text-slate-300">
                              {item.procedure_code}
                            </span>{' '}
                            - {item.procedure_description}
                          </p>
                          <p className="mt-1 text-xs text-slate-400">
                            Qty: {item.quantity} x &euro;{item.unit_price.toFixed(2)} ={' '}
                            &euro;{item.total_price.toFixed(2)}
                          </p>
                        </div>
                        {item.approved === false && (
                          <XCircle className="h-5 w-5 text-red-400 flex-shrink-0" />
                        )}
                        {item.approved === true && (
                          <CheckCircle className="h-5 w-5 text-green-400 flex-shrink-0" />
                        )}
                      </div>
                      {item.rejection_reason && (
                        <p className="mt-2 text-xs text-red-400 border-t border-red-500/20 pt-2">
                          {item.rejection_reason}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Diagnosis Codes */}
              <div className="mb-4">
                <h3 className="text-sm font-medium text-slate-400 mb-2">Diagnosis Codes</h3>
                <div className="flex flex-wrap gap-2">
                  {selectedClaim.diagnosis_codes.map((code) => (
                    <span
                      key={code}
                      className={`inline-flex items-center rounded border px-2 py-1 text-xs font-mono ${
                        code === selectedClaim.primary_diagnosis_code
                          ? 'border-teal-500/30 bg-teal-500/10 text-teal-400'
                          : 'border-white/10 bg-white/5 text-slate-300'
                      }`}
                    >
                      {code}
                      {code === selectedClaim.primary_diagnosis_code && ' (Primary)'}
                    </span>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              {selectedClaim.status === 'rejected' && (
                <div className="mt-6 space-y-3">
                  <button className="w-full flex items-center justify-center gap-2 rounded-lg bg-teal-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-teal-500 transition-colors">
                    <ArrowRight className="h-4 w-4" />
                    Fix &amp; Resubmit
                  </button>
                  <p className="text-xs text-center text-slate-500">
                    Correct invalid codes and resubmit for review
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ClaimsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-slate-950">
          <Loader2 className="h-8 w-8 animate-spin text-teal-400" />
        </div>
      }
    >
      <ClaimsContent />
    </Suspense>
  );
}
