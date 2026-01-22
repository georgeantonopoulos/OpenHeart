'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  FileText,
  AlertCircle,
  Loader2,
  Calendar,
  User,
  Stethoscope,
  CheckCircle,
  ClipboardList,
} from 'lucide-react';
import {
  getReferral,
  closeReferral,
  type GesyReferral,
  getReferralStatusColor,
  formatReferralStatus,
} from '@/lib/api/gesy';

export default function ReferralDetailsPage() {
  const { data: session } = useSession();
  const router = useRouter();
  const params = useParams();
  const referralId = params.id as string;

  const [referral, setReferral] = useState<GesyReferral | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [closing, setClosing] = useState(false);
  const [showCloseModal, setShowCloseModal] = useState(false);
  const [summaryNotes, setSummaryNotes] = useState('');

  useEffect(() => {
    if (session?.accessToken && referralId) {
      loadReferral();
    }
  }, [session?.accessToken, referralId]);

  async function loadReferral() {
    try {
      setLoading(true);
      setError(null);
      const data = await getReferral(session!.accessToken, referralId);
      setReferral(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load referral');
    } finally {
      setLoading(false);
    }
  }

  async function handleCloseReferral() {
    if (!referral) return;
    try {
      setClosing(true);
      const updated = await closeReferral(
        session!.accessToken,
        referral.referral_id,
        summaryNotes || undefined
      );
      setReferral(updated);
      setShowCloseModal(false);
      setSummaryNotes('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to close referral');
    } finally {
      setClosing(false);
    }
  }

  if (!session) return null;

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950">
        <Loader2 className="h-8 w-8 animate-spin text-teal-400" />
        <span className="ml-3 text-slate-400">Loading referral...</span>
      </div>
    );
  }

  if (error || !referral) {
    return (
      <div className="min-h-screen bg-slate-950 p-6">
        <div className="mx-auto max-w-4xl">
          <div className="flex items-center gap-3 rounded-lg border border-red-500/30 bg-red-500/10 p-4">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <p className="text-red-400">{error || 'Referral not found'}</p>
          </div>
          <Link
            href="/referrals/incoming"
            className="mt-4 inline-flex items-center gap-2 text-sm text-teal-400 hover:text-teal-300"
          >
            <ArrowLeft className="h-4 w-4" /> Back to referrals
          </Link>
        </div>
      </div>
    );
  }

  const isActive = referral.status === 'approved' || referral.status === 'pending';
  const isExpired = new Date(referral.valid_until) < new Date();

  return (
    <div className="min-h-screen bg-slate-950 p-6">
      <div className="mx-auto max-w-4xl">
        {/* Back link */}
        <Link
          href="/referrals/incoming"
          className="mb-4 inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="h-4 w-4" /> Back to referrals
        </Link>

        {/* Header */}
        <div className="mb-6 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-white">
                Referral {referral.referral_id}
              </h1>
              <span
                className={`inline-flex items-center rounded-full border px-3 py-1 text-sm font-medium ${getReferralStatusColor(referral.status)}`}
              >
                {formatReferralStatus(referral.status)}
              </span>
            </div>
            <p className="mt-1 text-slate-400">
              Issued {new Date(referral.issued_date).toLocaleDateString('en-GB')}
            </p>
          </div>
          <div className="flex gap-3">
            {isActive && !isExpired && (
              <>
                <button
                  onClick={() => setShowCloseModal(true)}
                  className="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-500 transition-colors"
                >
                  Close Referral
                </button>
                <Link
                  href={`/billing/claims?referral_id=${referral.referral_id}`}
                  className="rounded-lg border border-white/20 px-4 py-2 text-sm font-medium text-white hover:bg-white/10 transition-colors"
                >
                  Create Claim
                </Link>
              </>
            )}
          </div>
        </div>

        {/* Details Grid */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Clinical Info */}
          <div className="rounded-lg border border-white/10 bg-slate-900 p-6">
            <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-white">
              <Stethoscope className="h-5 w-5 text-teal-400" />
              Clinical Information
            </h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm text-slate-400">Diagnosis</dt>
                <dd className="mt-1 text-white">{referral.diagnosis_description}</dd>
              </div>
              <div>
                <dt className="text-sm text-slate-400">ICD-10 Code</dt>
                <dd className="mt-1 font-mono text-white">{referral.diagnosis_code}</dd>
              </div>
              <div>
                <dt className="text-sm text-slate-400">Specialty</dt>
                <dd className="mt-1 text-white">{referral.specialty_code}</dd>
              </div>
              <div>
                <dt className="text-sm text-slate-400">Urgency</dt>
                <dd className="mt-1 capitalize text-white">{referral.urgency}</dd>
              </div>
              {referral.clinical_notes && (
                <div>
                  <dt className="text-sm text-slate-400">Clinical Notes</dt>
                  <dd className="mt-1 text-white">{referral.clinical_notes}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* Referral Details */}
          <div className="rounded-lg border border-white/10 bg-slate-900 p-6">
            <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-white">
              <FileText className="h-5 w-5 text-teal-400" />
              Referral Details
            </h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm text-slate-400">Beneficiary ID</dt>
                <dd className="mt-1 font-mono text-white">{referral.beneficiary_id}</dd>
              </div>
              <div className="flex items-center gap-2">
                <User className="h-4 w-4 text-slate-400" />
                <div>
                  <dt className="text-sm text-slate-400">Referring Doctor</dt>
                  <dd className="mt-1 text-white">{referral.referring_doctor_id}</dd>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-slate-400" />
                <div>
                  <dt className="text-sm text-slate-400">Validity Period</dt>
                  <dd className="mt-1 text-white">
                    {new Date(referral.valid_from).toLocaleDateString('en-GB')} -{' '}
                    {new Date(referral.valid_until).toLocaleDateString('en-GB')}
                    {isExpired && (
                      <span className="ml-2 text-sm text-red-400">(Expired)</span>
                    )}
                  </dd>
                </div>
              </div>
              {referral.used_date && (
                <div>
                  <dt className="text-sm text-slate-400">Used Date</dt>
                  <dd className="mt-1 text-white">
                    {new Date(referral.used_date).toLocaleDateString('en-GB')}
                  </dd>
                </div>
              )}
            </dl>
          </div>

          {/* Procedures */}
          {(referral.requested_procedures?.length || referral.approved_procedures?.length) && (
            <div className="rounded-lg border border-white/10 bg-slate-900 p-6 lg:col-span-2">
              <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-white">
                <ClipboardList className="h-5 w-5 text-teal-400" />
                Procedures
              </h2>
              <div className="grid gap-4 sm:grid-cols-2">
                {referral.requested_procedures && referral.requested_procedures.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-slate-400">Requested</h3>
                    <ul className="mt-2 space-y-1">
                      {referral.requested_procedures.map((proc) => (
                        <li key={proc} className="flex items-center gap-2 text-white">
                          <span className="font-mono text-sm text-slate-300">{proc}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {referral.approved_procedures && referral.approved_procedures.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-slate-400">Approved</h3>
                    <ul className="mt-2 space-y-1">
                      {referral.approved_procedures.map((proc) => (
                        <li key={proc} className="flex items-center gap-2 text-white">
                          <CheckCircle className="h-4 w-4 text-green-400" />
                          <span className="font-mono text-sm">{proc}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Close Referral Modal */}
        {showCloseModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div className="mx-4 w-full max-w-md rounded-lg border border-white/10 bg-slate-900 p-6">
              <h3 className="text-lg font-semibold text-white">Close Referral</h3>
              <p className="mt-2 text-sm text-slate-400">
                Add a clinical summary before closing this referral. This will be sent
                back to the referring doctor.
              </p>
              <textarea
                value={summaryNotes}
                onChange={(e) => setSummaryNotes(e.target.value)}
                placeholder="Clinical summary (findings, treatment provided, recommendations)..."
                rows={4}
                className="mt-4 w-full rounded-lg border border-white/10 bg-white/5 p-3 text-white placeholder-slate-500 focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
              />
              <div className="mt-4 flex justify-end gap-3">
                <button
                  onClick={() => setShowCloseModal(false)}
                  className="rounded-lg border border-white/20 px-4 py-2 text-sm text-white hover:bg-white/10 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCloseReferral}
                  disabled={closing}
                  className="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-500 disabled:opacity-50 transition-colors"
                >
                  {closing ? 'Closing...' : 'Close Referral'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
