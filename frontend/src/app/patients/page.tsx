'use client';

import { useState } from 'react';
import { useSession } from 'next-auth/react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { searchPatients, Patient } from '@/lib/api/patients';

/**
 * Patient List Page.
 *
 * Displays searchable, paginated list of patients.
 * Supports filtering by status and Gesy beneficiary status.
 */
export default function PatientsPage() {
  const { data: session } = useSession();
  const router = useRouter();
  const searchParams = useSearchParams();

  // Search and filter state
  const [searchQuery, setSearchQuery] = useState(searchParams.get('q') || '');
  const [statusFilter, setStatusFilter] = useState<string>(
    searchParams.get('status') || 'active'
  );
  const [gesyOnly, setGesyOnly] = useState(searchParams.get('gesy_only') === 'true');
  const [page, setPage] = useState(Number(searchParams.get('page')) || 1);

  // Fetch patients
  const { data, isLoading, error } = useQuery({
    queryKey: ['patients', searchQuery, statusFilter, gesyOnly, page],
    queryFn: () =>
      searchPatients(session?.accessToken || '', {
        q: searchQuery || undefined,
        status: statusFilter as 'active' | 'inactive' | 'deceased',
        gesy_only: gesyOnly || undefined,
        page,
        page_size: 20,
      }),
    enabled: !!session?.accessToken,
    staleTime: 30000, // 30 seconds
  });

  // Handle search
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
  };

  // Calculate age display
  const formatAge = (age: number) => {
    return `${age} y/o`;
  };

  // Format date for display
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-CY', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  };

  // Status badge styles
  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      active: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      inactive: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
      deceased: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    };
    return styles[status] || styles.active;
  };

  if (!session) {
    return null;
  }

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
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10 19l-7-7m0 0l7-7m-7 7h18"
                  />
                </svg>
              </Link>
              <h1 className="text-2xl font-bold text-white">Patients</h1>
            </div>
            <Link
              href="/patients/new"
              className="inline-flex items-center px-4 py-2 bg-rose-600 text-white rounded-lg hover:bg-rose-700 transition-colors"
            >
              <svg
                className="w-5 h-5 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4v16m8-8H4"
                />
              </svg>
              Add Patient
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Search and Filters */}
        <div className="bg-slate-900 rounded-lg border border-slate-800 p-4 mb-6">
          <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-4">
            {/* Search Input */}
            <div className="flex-1">
              <div className="relative">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search by name or MRN..."
                  className="w-full px-4 py-2 pl-10 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-rose-500 focus:border-transparent"
                />
                <svg
                  className="absolute left-3 top-2.5 w-5 h-5 text-slate-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
              </div>
            </div>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-rose-500"
            >
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="deceased">Deceased</option>
            </select>

            {/* Gesy Filter */}
            <label className="flex items-center space-x-2 text-slate-300">
              <input
                type="checkbox"
                checked={gesyOnly}
                onChange={(e) => {
                  setGesyOnly(e.target.checked);
                  setPage(1);
                }}
                className="w-4 h-4 text-rose-600 bg-slate-800 border-slate-700 rounded focus:ring-rose-500"
              />
              <span className="text-sm">Gesy Only</span>
            </label>

            <button
              type="submit"
              className="px-4 py-2 bg-rose-600 text-white rounded-lg hover:bg-rose-700 transition-colors"
            >
              Search
            </button>
          </form>
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-red-900/20 border border-red-800 rounded-lg p-4 mb-6">
            <p className="text-red-400">Failed to load patients. Please try again.</p>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-rose-500"></div>
          </div>
        )}

        {/* Patient List */}
        {!isLoading && data && (
          <>
            <div className="bg-slate-900 rounded-lg border border-slate-800 overflow-hidden">
              {/* Table Header */}
              <div className="grid grid-cols-12 gap-4 px-4 py-3 bg-slate-800/50 text-xs font-medium text-slate-400 uppercase tracking-wider">
                <div className="col-span-3">Patient</div>
                <div className="col-span-2">MRN</div>
                <div className="col-span-1">Age</div>
                <div className="col-span-2">DOB</div>
                <div className="col-span-2">Status</div>
                <div className="col-span-2">Actions</div>
              </div>

              {/* Table Body */}
              {data.items.length === 0 ? (
                <div className="px-4 py-12 text-center text-slate-400">
                  <svg
                    className="mx-auto h-12 w-12 text-slate-500"
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
                  <p className="mt-2">No patients found</p>
                  <p className="text-sm text-slate-500">
                    Try adjusting your search or filters
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-slate-800">
                  {data.items.map((patient: Patient) => (
                    <div
                      key={patient.patient_id}
                      className="grid grid-cols-12 gap-4 px-4 py-4 hover:bg-slate-800/50 transition-colors cursor-pointer"
                      onClick={() => router.push(`/patients/${patient.patient_id}`)}
                    >
                      {/* Patient Name */}
                      <div className="col-span-3 flex items-center space-x-3">
                        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-rose-500 to-pink-600 flex items-center justify-center text-white font-medium">
                          {patient.first_name?.[0] || '?'}
                          {patient.last_name?.[0] || ''}
                        </div>
                        <div>
                          <p className="text-white font-medium">
                            {patient.first_name} {patient.last_name}
                          </p>
                          {patient.is_gesy_beneficiary && (
                            <span className="inline-flex items-center px-1.5 py-0.5 text-xs bg-teal-900/50 text-teal-300 rounded">
                              Gesy
                            </span>
                          )}
                        </div>
                      </div>

                      {/* MRN */}
                      <div className="col-span-2 flex items-center">
                        <span className="text-slate-300 font-mono text-sm">
                          {patient.mrn}
                        </span>
                      </div>

                      {/* Age */}
                      <div className="col-span-1 flex items-center text-slate-300">
                        {formatAge(patient.age)}
                      </div>

                      {/* DOB */}
                      <div className="col-span-2 flex items-center text-slate-400 text-sm">
                        {formatDate(patient.birth_date)}
                      </div>

                      {/* Status */}
                      <div className="col-span-2 flex items-center">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadge(
                            patient.status
                          )}`}
                        >
                          {patient.status.charAt(0).toUpperCase() +
                            patient.status.slice(1)}
                        </span>
                      </div>

                      {/* Actions */}
                      <div className="col-span-2 flex items-center space-x-2">
                        <Link
                          href={`/patients/${patient.patient_id}`}
                          className="px-3 py-1 text-sm text-rose-400 hover:text-rose-300 hover:bg-rose-900/20 rounded transition-colors"
                          onClick={(e) => e.stopPropagation()}
                        >
                          View
                        </Link>
                        <Link
                          href={`/patients/${patient.patient_id}/notes/new`}
                          className="px-3 py-1 text-sm text-slate-400 hover:text-slate-300 hover:bg-slate-700 rounded transition-colors"
                          onClick={(e) => e.stopPropagation()}
                        >
                          + Note
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Pagination */}
            {data.total_pages > 1 && (
              <div className="flex items-center justify-between mt-4">
                <p className="text-sm text-slate-400">
                  Showing {(page - 1) * 20 + 1} to{' '}
                  {Math.min(page * 20, data.total)} of {data.total} patients
                </p>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-3 py-1 bg-slate-800 text-slate-300 rounded hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Previous
                  </button>
                  <span className="px-3 py-1 text-slate-400">
                    Page {page} of {data.total_pages}
                  </span>
                  <button
                    onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                    disabled={page === data.total_pages}
                    className="px-3 py-1 bg-slate-800 text-slate-300 rounded hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
