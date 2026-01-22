'use client';

import { useState } from 'react';
import { useSession } from 'next-auth/react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import {
  listInvitations,
  revokeInvitation,
  ROLE_LABELS,
  ROLE_COLORS,
  InvitationResponse,
} from '@/lib/api/auth';

/**
 * User Management Page for Admins.
 *
 * Lists pending invitations and allows management of user invites.
 */
export default function AdminUsersPage() {
  const { data: session } = useSession();
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>('pending');
  const [page, setPage] = useState(1);

  // Fetch invitations
  const { data, isLoading, error } = useQuery({
    queryKey: ['invitations', statusFilter, page],
    queryFn: () =>
      listInvitations(session?.accessToken || '', {
        status: statusFilter || undefined,
        page,
        per_page: 20,
      }),
    enabled: !!session?.accessToken,
  });

  // Revoke mutation
  const revokeMutation = useMutation({
    mutationFn: (invitationId: number) =>
      revokeInvitation(session?.accessToken || '', invitationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invitations'] });
    },
  });

  const handleRevoke = async (invitation: InvitationResponse) => {
    if (
      confirm(
        `Are you sure you want to revoke the invitation for ${invitation.first_name} ${invitation.last_name}?`
      )
    ) {
      revokeMutation.mutate(invitation.invitation_id);
    }
  };

  if (!session) {
    return null;
  }

  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString('en-CY', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-amber-500/20 text-amber-400';
      case 'accepted':
        return 'bg-green-500/20 text-green-400';
      case 'expired':
        return 'bg-slate-500/20 text-slate-400';
      case 'revoked':
        return 'bg-rose-500/20 text-rose-400';
      default:
        return 'bg-slate-500/20 text-slate-400';
    }
  };

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <div className="bg-slate-900 border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link
                href="/dashboard"
                className="text-slate-400 hover:text-slate-200 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10 19l-7-7m0 0l7-7m-7 7h18"
                  />
                </svg>
              </Link>
              <div>
                <h1 className="text-2xl font-bold text-white">User Management</h1>
                <p className="text-sm text-slate-400">Manage user invitations and access</p>
              </div>
            </div>

            <Link
              href="/admin/users/invite"
              className="inline-flex items-center gap-2 px-4 py-2 bg-rose-600 text-white rounded-lg font-medium hover:bg-rose-700 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                />
              </svg>
              Invite User
            </Link>
          </div>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Filters */}
        <div className="flex items-center gap-4 mb-6">
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-400">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:border-rose-500"
            >
              <option value="">All</option>
              <option value="pending">Pending</option>
              <option value="accepted">Accepted</option>
              <option value="expired">Expired</option>
              <option value="revoked">Revoked</option>
            </select>
          </div>

          {data && (
            <span className="text-sm text-slate-500">
              {data.total} invitation{data.total !== 1 ? 's' : ''}
            </span>
          )}
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="w-8 h-8 border-2 border-rose-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : error ? (
          <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-4 text-center">
            <p className="text-rose-400">Failed to load invitations</p>
          </div>
        ) : data?.invitations.length === 0 ? (
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-8 text-center">
            <div className="w-16 h-16 bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-slate-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">No invitations found</h3>
            <p className="text-slate-400 mb-4">
              {statusFilter ? `No ${statusFilter} invitations` : 'Start by inviting a new user'}
            </p>
            <Link
              href="/admin/users/invite"
              className="inline-flex items-center gap-2 px-4 py-2 bg-rose-600 text-white rounded-lg font-medium hover:bg-rose-700 transition-colors"
            >
              Invite User
            </Link>
          </div>
        ) : (
          <>
            {/* Table */}
            <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-800">
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                      User
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Role
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Invited By
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {data?.invitations.map((invitation) => (
                    <tr key={invitation.invitation_id} className="hover:bg-slate-800/50">
                      <td className="px-6 py-4">
                        <div>
                          <p className="text-sm font-medium text-white">
                            {invitation.first_name} {invitation.last_name}
                          </p>
                          <p className="text-sm text-slate-400">{invitation.email}</p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${ROLE_COLORS[invitation.role]?.bg || 'bg-slate-500/20'} ${ROLE_COLORS[invitation.role]?.text || 'text-slate-400'}`}
                        >
                          {ROLE_LABELS[invitation.role] || invitation.role}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${getStatusColor(invitation.status)}`}
                        >
                          {invitation.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-400">
                        {invitation.invited_by_name || '-'}
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-400">
                        {formatDate(invitation.created_at)}
                      </td>
                      <td className="px-6 py-4 text-right">
                        {invitation.status === 'pending' && (
                          <button
                            onClick={() => handleRevoke(invitation)}
                            disabled={revokeMutation.isPending}
                            className="text-rose-400 hover:text-rose-300 text-sm font-medium disabled:opacity-50"
                          >
                            Revoke
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {data && data.total > data.per_page && (
              <div className="flex items-center justify-between mt-4">
                <p className="text-sm text-slate-400">
                  Showing {(page - 1) * data.per_page + 1} to{' '}
                  {Math.min(page * data.per_page, data.total)} of {data.total}
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-3 py-1.5 bg-slate-800 text-slate-300 rounded-lg text-sm disabled:opacity-50 hover:bg-slate-700 transition-colors"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setPage((p) => p + 1)}
                    disabled={page * data.per_page >= data.total}
                    className="px-3 py-1.5 bg-slate-800 text-slate-300 rounded-lg text-sm disabled:opacity-50 hover:bg-slate-700 transition-colors"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
