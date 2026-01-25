'use client';

import { useState } from 'react';
import { useSession } from 'next-auth/react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { getPatient } from '@/lib/api/patients';
import {
  listPrescriptions,
  discontinuePrescription,
  renewPrescription,
  holdPrescription,
  resumePrescription,
  Prescription,
  getStatusColor,
  formatPrescriptionLine,
  getSeverityColor,
} from '@/lib/api/prescriptions';

export default function PrescriptionsPage() {
  const { data: session } = useSession();
  const params = useParams();
  const patientId = Number(params.id);
  const queryClient = useQueryClient();

  const [statusFilter, setStatusFilter] = useState<string>('active');
  const [showDiscontinueModal, setShowDiscontinueModal] = useState<string | null>(null);
  const [discontinueReason, setDiscontinueReason] = useState('');

  // Fetch patient data
  const { data: patient } = useQuery({
    queryKey: ['patient', patientId],
    queryFn: () => getPatient(session?.accessToken || '', patientId),
    enabled: !!session?.accessToken && !!patientId,
  });

  // Fetch prescriptions
  const {
    data: prescriptions,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['prescriptions', patientId, statusFilter],
    queryFn: () =>
      listPrescriptions(session?.accessToken || '', patientId, {
        status: statusFilter === 'all' ? undefined : statusFilter,
        include_inactive: statusFilter === 'all',
      }),
    enabled: !!session?.accessToken && !!patientId,
  });

  // Mutations
  const discontinueMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      discontinuePrescription(session?.accessToken || '', id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prescriptions', patientId] });
      setShowDiscontinueModal(null);
      setDiscontinueReason('');
    },
  });

  const renewMutation = useMutation({
    mutationFn: (id: string) => renewPrescription(session?.accessToken || '', id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prescriptions', patientId] });
    },
  });

  const holdMutation = useMutation({
    mutationFn: (id: string) => holdPrescription(session?.accessToken || '', id, 'Temporarily held'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prescriptions', patientId] });
    },
  });

  const resumeMutation = useMutation({
    mutationFn: (id: string) => resumePrescription(session?.accessToken || '', id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prescriptions', patientId] });
    },
  });

  if (!session) return null;

  const handleDiscontinue = () => {
    if (showDiscontinueModal && discontinueReason.length >= 3) {
      discontinueMutation.mutate({ id: showDiscontinueModal, reason: discontinueReason });
    }
  };

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 bg-slate-900/95 backdrop-blur border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <div className="flex items-center space-x-2 text-sm">
              <Link href="/patients" className="text-slate-400 hover:text-slate-200">
                Patients
              </Link>
              <span className="text-slate-600">/</span>
              <Link href={`/patients/${patientId}`} className="text-slate-400 hover:text-slate-200">
                {patient?.first_name} {patient?.last_name}
              </Link>
              <span className="text-slate-600">/</span>
              <span className="text-white font-medium">Medications</span>
            </div>

            <Link
              href={`/patients/${patientId}/prescriptions/new`}
              className="inline-flex items-center px-3 py-1.5 bg-rose-600 text-white text-sm rounded-lg hover:bg-rose-700 transition-colors"
            >
              <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              New Prescription
            </Link>
          </div>
        </div>
      </nav>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white">Medications</h1>
          <p className="text-slate-400 mt-1">
            {patient?.first_name} {patient?.last_name}
          </p>
        </div>

        {/* Filter Tabs */}
        <div className="flex space-x-1 mb-6 bg-slate-800/50 rounded-lg p-1 w-fit">
          {['active', 'on_hold', 'discontinued', 'all'].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                statusFilter === status
                  ? 'bg-slate-700 text-white'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {status === 'on_hold' ? 'On Hold' : status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-rose-500" />
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400">
            Failed to load prescriptions. Please try again.
          </div>
        )}

        {/* Prescription List */}
        {prescriptions && prescriptions.items.length === 0 && (
          <div className="text-center py-12">
            <svg
              className="mx-auto h-12 w-12 text-slate-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-slate-300">No medications</h3>
            <p className="mt-1 text-sm text-slate-500">
              {statusFilter === 'active'
                ? 'No active medications for this patient.'
                : `No ${statusFilter} medications found.`}
            </p>
          </div>
        )}

        {prescriptions && prescriptions.items.length > 0 && (
          <div className="space-y-3">
            {prescriptions.items.map((rx: Prescription) => (
              <div
                key={rx.id}
                className="bg-slate-900 rounded-lg border border-slate-800 p-4 hover:border-slate-700 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    {/* Drug name and status */}
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-semibold text-white">{rx.drug_name}</h3>
                      <span
                        className={`px-2 py-0.5 text-xs rounded-full border ${getStatusColor(
                          rx.status
                        )}`}
                      >
                        {rx.status}
                      </span>
                      {rx.is_chronic && (
                        <span className="px-2 py-0.5 text-xs rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30">
                          Chronic
                        </span>
                      )}
                    </div>

                    {/* Dosage line */}
                    <p className="text-slate-300 mt-1">{formatPrescriptionLine(rx)}</p>

                    {/* Indication */}
                    {rx.indication && (
                      <p className="text-slate-500 text-sm mt-1">Indication: {rx.indication}</p>
                    )}

                    {/* Interactions */}
                    {rx.interactions && rx.interactions.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-2">
                        {rx.interactions.map((interaction) => (
                          <span
                            key={interaction.id}
                            className={`px-2 py-1 text-xs rounded border ${getSeverityColor(
                              interaction.severity
                            )}`}
                            title={interaction.description}
                          >
                            {interaction.severity.toUpperCase()}: {interaction.interacting_drug_name}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Meta info */}
                    <div className="flex items-center gap-4 mt-3 text-xs text-slate-500">
                      <span>Started: {new Date(rx.start_date).toLocaleDateString('en-CY')}</span>
                      {rx.end_date && (
                        <span>Ends: {new Date(rx.end_date).toLocaleDateString('en-CY')}</span>
                      )}
                      {rx.days_remaining !== null && rx.days_remaining !== undefined && (
                        <span>{rx.days_remaining} days remaining</span>
                      )}
                      {rx.atc_code && <span className="font-mono">{rx.atc_code}</span>}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 ml-4">
                    {rx.status === 'active' && rx.can_renew && (
                      <button
                        onClick={() => renewMutation.mutate(rx.id)}
                        disabled={renewMutation.isPending}
                        className="px-3 py-1.5 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors disabled:opacity-50"
                      >
                        Renew
                      </button>
                    )}
                    {rx.status === 'active' && (
                      <button
                        onClick={() => holdMutation.mutate(rx.id)}
                        disabled={holdMutation.isPending}
                        className="px-3 py-1.5 text-xs bg-amber-600 text-white rounded hover:bg-amber-700 transition-colors disabled:opacity-50"
                      >
                        Hold
                      </button>
                    )}
                    {rx.status === 'on_hold' && (
                      <button
                        onClick={() => resumeMutation.mutate(rx.id)}
                        disabled={resumeMutation.isPending}
                        className="px-3 py-1.5 text-xs bg-green-600 text-white rounded hover:bg-green-700 transition-colors disabled:opacity-50"
                      >
                        Resume
                      </button>
                    )}
                    {(rx.status === 'active' || rx.status === 'on_hold') && (
                      <button
                        onClick={() => setShowDiscontinueModal(rx.id)}
                        className="px-3 py-1.5 text-xs bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                      >
                        Discontinue
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Discontinue Modal */}
      {showDiscontinueModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-slate-900 rounded-lg border border-slate-700 p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-semibold text-white mb-4">Discontinue Medication</h3>
            <p className="text-slate-400 text-sm mb-4">
              Please provide a reason for discontinuing this medication.
            </p>
            <textarea
              value={discontinueReason}
              onChange={(e) => setDiscontinueReason(e.target.value)}
              placeholder="Enter reason (minimum 3 characters)"
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:border-rose-500 focus:ring-1 focus:ring-rose-500 outline-none"
              rows={3}
            />
            <div className="flex justify-end gap-3 mt-4">
              <button
                onClick={() => {
                  setShowDiscontinueModal(null);
                  setDiscontinueReason('');
                }}
                className="px-4 py-2 text-sm text-slate-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleDiscontinue}
                disabled={discontinueReason.length < 3 || discontinueMutation.isPending}
                className="px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {discontinueMutation.isPending ? 'Discontinuing...' : 'Discontinue'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
