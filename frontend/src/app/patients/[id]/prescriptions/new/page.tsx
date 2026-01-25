'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { getPatient } from '@/lib/api/patients';
import {
  createPrescription,
  searchFormulary,
  checkInteractions,
  DrugTemplate,
  InteractionDetail,
  PrescriptionCreateInput,
  FREQUENCY_LABELS,
  ROUTE_LABELS,
  getSeverityColor,
} from '@/lib/api/prescriptions';

export default function NewPrescriptionPage() {
  const { data: session } = useSession();
  const params = useParams();
  const router = useRouter();
  const patientId = Number(params.id);

  // Form state
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDrug, setSelectedDrug] = useState<DrugTemplate | null>(null);
  const [formData, setFormData] = useState({
    drug_name: '',
    atc_code: '',
    generic_name: '',
    form: 'tablet',
    strength: '',
    dosage: '1 tablet',
    quantity: 30,
    frequency: 'OD',
    frequency_custom: '',
    route: 'oral',
    duration_days: undefined as number | undefined,
    is_chronic: true,
    indication: '',
    prescriber_notes: '',
  });
  const [interactions, setInteractions] = useState<InteractionDetail[]>([]);
  const [interactionsChecked, setInteractionsChecked] = useState(false);
  const [showInteractionWarning, setShowInteractionWarning] = useState(false);

  // Fetch patient
  const { data: patient } = useQuery({
    queryKey: ['patient', patientId],
    queryFn: () => getPatient(session?.accessToken || '', patientId),
    enabled: !!session?.accessToken && !!patientId,
  });

  // Search formulary
  const { data: searchResults, isLoading: searchLoading } = useQuery({
    queryKey: ['formulary-search', searchQuery],
    queryFn: () => searchFormulary(session?.accessToken || '', searchQuery),
    enabled: !!session?.accessToken && searchQuery.length >= 2,
  });

  // Check interactions when drug is selected
  const interactionMutation = useMutation({
    mutationFn: () =>
      checkInteractions(session?.accessToken || '', {
        patient_id: patientId,
        drug_name: formData.drug_name,
        atc_code: formData.atc_code || undefined,
      }),
    onSuccess: (data) => {
      setInteractions(data.interactions);
      setInteractionsChecked(true);
      if (data.has_interactions) {
        setShowInteractionWarning(true);
      }
    },
  });

  // Create prescription
  const createMutation = useMutation({
    mutationFn: (data: PrescriptionCreateInput) =>
      createPrescription(session?.accessToken || '', patientId, data),
    onSuccess: () => {
      router.push(`/patients/${patientId}/prescriptions`);
    },
  });

  // Select drug from search results
  const handleSelectDrug = (drug: DrugTemplate) => {
    setSelectedDrug(drug);
    setFormData({
      ...formData,
      drug_name: drug.generic_name,
      atc_code: drug.atc_code,
      generic_name: drug.generic_name,
      form: drug.default_form,
      strength: drug.default_strength,
      frequency: drug.default_frequency,
      route: drug.default_route,
      is_chronic: drug.is_chronic,
    });
    setSearchQuery('');
    setInteractionsChecked(false);
    setInteractions([]);
  };

  // Check interactions when drug is set
  useEffect(() => {
    if (formData.drug_name && formData.atc_code && !interactionsChecked) {
      interactionMutation.mutate();
    }
  }, [formData.drug_name, formData.atc_code]);

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Check for contraindicated interactions
    const hasContraindicated = interactions.some((i) => i.severity === 'contraindicated');
    if (hasContraindicated && !window.confirm('There are CONTRAINDICATED drug interactions. Are you sure you want to proceed?')) {
      return;
    }

    const payload: PrescriptionCreateInput = {
      patient_id: patientId,
      drug_name: formData.drug_name,
      atc_code: formData.atc_code || undefined,
      generic_name: formData.generic_name || undefined,
      form: formData.form || undefined,
      strength: formData.strength || undefined,
      dosage: formData.dosage || undefined,
      quantity: formData.quantity || undefined,
      frequency: formData.frequency,
      frequency_custom: formData.frequency === 'custom' ? formData.frequency_custom : undefined,
      route: formData.route,
      duration_days: formData.is_chronic ? undefined : formData.duration_days,
      is_chronic: formData.is_chronic,
      indication: formData.indication || undefined,
      prescriber_notes: formData.prescriber_notes || undefined,
    };

    createMutation.mutate(payload);
  };

  if (!session) return null;

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 bg-slate-900/95 backdrop-blur border-b border-slate-800">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <div className="flex items-center space-x-2 text-sm">
              <Link href={`/patients/${patientId}`} className="text-slate-400 hover:text-slate-200">
                {patient?.first_name} {patient?.last_name}
              </Link>
              <span className="text-slate-600">/</span>
              <Link
                href={`/patients/${patientId}/prescriptions`}
                className="text-slate-400 hover:text-slate-200"
              >
                Medications
              </Link>
              <span className="text-slate-600">/</span>
              <span className="text-white font-medium">New Prescription</span>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <h1 className="text-2xl font-bold text-white mb-6">New Prescription</h1>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Drug Search */}
          <div className="bg-slate-900 rounded-lg border border-slate-800 p-4">
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Search Drug (Formulary)
            </label>
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Type drug name or indication..."
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:border-rose-500 focus:ring-1 focus:ring-rose-500 outline-none"
              />
              {searchLoading && (
                <div className="absolute right-3 top-2.5">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-rose-500" />
                </div>
              )}
            </div>

            {/* Search Results */}
            {searchResults && searchResults.length > 0 && searchQuery.length >= 2 && (
              <div className="mt-2 bg-slate-800 rounded-lg border border-slate-700 max-h-60 overflow-y-auto">
                {searchResults.map((drug) => (
                  <button
                    key={drug.atc_code}
                    type="button"
                    onClick={() => handleSelectDrug(drug)}
                    className="w-full text-left px-4 py-3 hover:bg-slate-700 border-b border-slate-700 last:border-b-0"
                  >
                    <div className="font-medium text-white">{drug.generic_name}</div>
                    <div className="text-sm text-slate-400">
                      {drug.default_strength} | {drug.category} | ATC: {drug.atc_code}
                    </div>
                    {drug.common_indications.length > 0 && (
                      <div className="text-xs text-slate-500 mt-1">
                        {drug.common_indications.slice(0, 2).join(', ')}
                      </div>
                    )}
                  </button>
                ))}
              </div>
            )}

            {/* Selected Drug Display */}
            {selectedDrug && (
              <div className="mt-3 bg-slate-800/50 rounded-lg px-4 py-3 border border-green-500/30">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-medium text-green-400">{selectedDrug.generic_name}</span>
                    <span className="text-slate-400 ml-2">({selectedDrug.atc_code})</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedDrug(null);
                      setFormData({
                        ...formData,
                        drug_name: '',
                        atc_code: '',
                        generic_name: '',
                      });
                      setInteractions([]);
                      setInteractionsChecked(false);
                    }}
                    className="text-slate-400 hover:text-white"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
            )}

            {/* Manual Entry */}
            {!selectedDrug && (
              <div className="mt-4">
                <label className="block text-sm text-slate-400 mb-1">Or enter drug name manually:</label>
                <input
                  type="text"
                  value={formData.drug_name}
                  onChange={(e) => setFormData({ ...formData, drug_name: e.target.value })}
                  placeholder="Drug name"
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:border-rose-500 focus:ring-1 focus:ring-rose-500 outline-none"
                />
              </div>
            )}
          </div>

          {/* Interaction Warnings */}
          {interactions.length > 0 && (
            <div className="bg-slate-900 rounded-lg border border-amber-500/30 p-4">
              <h3 className="text-amber-400 font-medium mb-3 flex items-center">
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
                Drug Interactions Detected
              </h3>
              <div className="space-y-2">
                {interactions.map((interaction, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded border ${getSeverityColor(interaction.severity)}`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-sm uppercase">{interaction.severity}</span>
                      <span className="text-sm">with {interaction.interacting_drug}</span>
                    </div>
                    <p className="text-sm opacity-90">{interaction.description}</p>
                    {interaction.management && (
                      <p className="text-xs mt-2 opacity-75">
                        <strong>Management:</strong> {interaction.management}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Prescription Details */}
          <div className="bg-slate-900 rounded-lg border border-slate-800 p-4 space-y-4">
            <h3 className="text-lg font-medium text-white mb-4">Prescription Details</h3>

            <div className="grid grid-cols-2 gap-4">
              {/* Strength */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Strength</label>
                {selectedDrug ? (
                  <select
                    value={formData.strength}
                    onChange={(e) => setFormData({ ...formData, strength: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-rose-500 focus:ring-1 focus:ring-rose-500 outline-none"
                  >
                    {selectedDrug.available_strengths.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="text"
                    value={formData.strength}
                    onChange={(e) => setFormData({ ...formData, strength: e.target.value })}
                    placeholder="e.g., 10mg"
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:border-rose-500 outline-none"
                  />
                )}
              </div>

              {/* Form */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Form</label>
                <select
                  value={formData.form}
                  onChange={(e) => setFormData({ ...formData, form: e.target.value })}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-rose-500 outline-none"
                >
                  <option value="tablet">Tablet</option>
                  <option value="capsule">Capsule</option>
                  <option value="injection">Injection</option>
                  <option value="syrup">Syrup</option>
                  <option value="patch">Patch</option>
                  <option value="spray">Spray</option>
                </select>
              </div>

              {/* Dosage */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Dosage</label>
                <input
                  type="text"
                  value={formData.dosage}
                  onChange={(e) => setFormData({ ...formData, dosage: e.target.value })}
                  placeholder="e.g., 1 tablet"
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:border-rose-500 outline-none"
                />
              </div>

              {/* Quantity */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Quantity</label>
                <input
                  type="number"
                  value={formData.quantity}
                  onChange={(e) => setFormData({ ...formData, quantity: parseInt(e.target.value) || 0 })}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-rose-500 outline-none"
                />
              </div>

              {/* Frequency */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Frequency</label>
                <select
                  value={formData.frequency}
                  onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-rose-500 outline-none"
                >
                  {Object.entries(FREQUENCY_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Route */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Route</label>
                <select
                  value={formData.route}
                  onChange={(e) => setFormData({ ...formData, route: e.target.value })}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-rose-500 outline-none"
                >
                  {Object.entries(ROUTE_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Chronic toggle */}
            <div className="flex items-center gap-3 pt-2">
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_chronic}
                  onChange={(e) => setFormData({ ...formData, is_chronic: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-slate-700 peer-focus:ring-2 peer-focus:ring-rose-500 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-rose-600" />
              </label>
              <span className="text-slate-300">Chronic medication (ongoing)</span>
            </div>

            {/* Duration (if not chronic) */}
            {!formData.is_chronic && (
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Duration (days)
                </label>
                <input
                  type="number"
                  value={formData.duration_days || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      duration_days: e.target.value ? parseInt(e.target.value) : undefined,
                    })
                  }
                  placeholder="Number of days"
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:border-rose-500 outline-none"
                />
              </div>
            )}

            {/* Indication */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Indication</label>
              <input
                type="text"
                value={formData.indication}
                onChange={(e) => setFormData({ ...formData, indication: e.target.value })}
                placeholder="Clinical indication for this medication"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:border-rose-500 outline-none"
              />
            </div>

            {/* Notes */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Prescriber Notes (optional)
              </label>
              <textarea
                value={formData.prescriber_notes}
                onChange={(e) => setFormData({ ...formData, prescriber_notes: e.target.value })}
                placeholder="Additional instructions or notes..."
                rows={2}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:border-rose-500 outline-none resize-none"
              />
            </div>
          </div>

          {/* Submit */}
          <div className="flex justify-end gap-3">
            <Link
              href={`/patients/${patientId}/prescriptions`}
              className="px-4 py-2 text-slate-400 hover:text-white transition-colors"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={!formData.drug_name || createMutation.isPending}
              className="px-6 py-2 bg-rose-600 text-white rounded-lg hover:bg-rose-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {createMutation.isPending ? 'Creating...' : 'Create Prescription'}
            </button>
          </div>

          {createMutation.isError && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400 text-sm">
              Failed to create prescription. Please check the form and try again.
            </div>
          )}
        </form>
      </main>
    </div>
  );
}
