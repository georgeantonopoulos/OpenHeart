'use client';

import { useState } from 'react';
import { useSession } from 'next-auth/react';
import { useMutation } from '@tanstack/react-query';
import Link from 'next/link';
import {
  calculateGRACE,
  GRACEInput,
  GRACEResult,
  KillipClass,
  KILLIP_DESCRIPTIONS,
  getRiskCategoryColor,
} from '@/lib/api/cdss';

/**
 * GRACE Score Calculator Page.
 *
 * Calculates in-hospital mortality risk for ACS patients.
 */
export default function GRACECalculatorPage() {
  const { data: session } = useSession();

  // Form state
  const [formData, setFormData] = useState<GRACEInput>({
    age: 65,
    heart_rate: 80,
    systolic_bp: 120,
    creatinine_mg_dl: 1.0,
    killip_class: 'I',
    cardiac_arrest_at_admission: false,
    st_segment_deviation: false,
    elevated_cardiac_enzymes: false,
  });

  const [result, setResult] = useState<GRACEResult | null>(null);

  // Calculate mutation
  const mutation = useMutation({
    mutationFn: () => calculateGRACE(session?.accessToken || '', formData),
    onSuccess: (data) => {
      setResult(data);
    },
  });

  // Update numeric field
  const updateNumeric = (field: keyof GRACEInput, value: string) => {
    const numValue = field === 'creatinine_mg_dl' ? parseFloat(value) : parseInt(value);
    if (!isNaN(numValue)) {
      setFormData((prev) => ({ ...prev, [field]: numValue }));
    }
  };

  // Update boolean field
  const updateBoolean = (field: keyof GRACEInput, value: boolean) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  // Handle submit
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setResult(null);
    mutation.mutate();
  };

  // Reset form
  const resetForm = () => {
    setFormData({
      age: 65,
      heart_rate: 80,
      systolic_bp: 120,
      creatinine_mg_dl: 1.0,
      killip_class: 'I',
      cardiac_arrest_at_admission: false,
      st_segment_deviation: false,
      elevated_cardiac_enzymes: false,
    });
    setResult(null);
  };

  if (!session) {
    return null;
  }

  const riskColors = result ? getRiskCategoryColor(result.risk_category) : null;

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <div className="bg-slate-900 border-b border-slate-800">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center space-x-4">
            <Link
              href="/cdss"
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
              <h1 className="text-2xl font-bold text-white">GRACE Score</h1>
              <p className="text-sm text-slate-400">
                In-hospital mortality risk in Acute Coronary Syndrome
              </p>
            </div>
          </div>
        </div>
      </div>

      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Input Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Vitals */}
            <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Patient Vitals</h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Age (years)
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={120}
                    value={formData.age}
                    onChange={(e) => updateNumeric('age', e.target.value)}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-rose-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Heart Rate (bpm)
                  </label>
                  <input
                    type="number"
                    min={20}
                    max={300}
                    value={formData.heart_rate}
                    onChange={(e) => updateNumeric('heart_rate', e.target.value)}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-rose-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Systolic BP (mmHg)
                  </label>
                  <input
                    type="number"
                    min={40}
                    max={300}
                    value={formData.systolic_bp}
                    onChange={(e) => updateNumeric('systolic_bp', e.target.value)}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-rose-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Creatinine (mg/dL)
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={20}
                    step={0.1}
                    value={formData.creatinine_mg_dl}
                    onChange={(e) => updateNumeric('creatinine_mg_dl', e.target.value)}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-rose-500"
                  />
                </div>
              </div>
            </div>

            {/* Killip Class */}
            <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Killip Classification</h2>
              <div className="space-y-2">
                {(['I', 'II', 'III', 'IV'] as KillipClass[]).map((killip) => (
                  <label
                    key={killip}
                    className={`flex items-center p-3 rounded-lg cursor-pointer transition-colors ${
                      formData.killip_class === killip
                        ? 'bg-rose-900/30 border border-rose-700'
                        : 'bg-slate-800/50 border border-transparent hover:bg-slate-800'
                    }`}
                  >
                    <input
                      type="radio"
                      name="killip_class"
                      value={killip}
                      checked={formData.killip_class === killip}
                      onChange={() => setFormData((prev) => ({ ...prev, killip_class: killip }))}
                      className="sr-only"
                    />
                    <span className="font-mono font-bold text-rose-400 w-8">{killip}</span>
                    <span className="text-sm text-slate-300">{KILLIP_DESCRIPTIONS[killip]}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Risk Factors */}
            <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Risk Factors</h2>
              <div className="space-y-3">
                {[
                  { key: 'cardiac_arrest_at_admission', label: 'Cardiac arrest at admission' },
                  { key: 'st_segment_deviation', label: 'ST-segment deviation on ECG' },
                  { key: 'elevated_cardiac_enzymes', label: 'Elevated cardiac enzymes (troponin)' },
                ].map(({ key, label }) => (
                  <label
                    key={key}
                    className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg cursor-pointer hover:bg-slate-800 transition-colors"
                  >
                    <span className="text-sm text-slate-300">{label}</span>
                    <input
                      type="checkbox"
                      checked={formData[key as keyof GRACEInput] as boolean}
                      onChange={(e) =>
                        updateBoolean(key as keyof GRACEInput, e.target.checked)
                      }
                      className="w-5 h-5 rounded bg-slate-700 border-slate-600 text-rose-600 focus:ring-rose-500"
                    />
                  </label>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <button
                type="submit"
                disabled={mutation.isPending}
                className="flex-1 py-3 bg-rose-600 text-white rounded-lg font-medium hover:bg-rose-700 disabled:opacity-50 transition-colors"
              >
                {mutation.isPending ? 'Calculating...' : 'Calculate GRACE Score'}
              </button>
              <button
                type="button"
                onClick={resetForm}
                className="px-4 py-3 bg-slate-800 text-slate-300 rounded-lg hover:bg-slate-700 transition-colors"
              >
                Reset
              </button>
            </div>
          </form>

          {/* Result Panel */}
          <div className="space-y-6">
            {result && riskColors && (
              <>
                {/* Score Display */}
                <div
                  className={`${riskColors.bg} rounded-lg border ${riskColors.border} p-6 text-center`}
                >
                  <p className="text-sm text-slate-400 mb-2">GRACE Score</p>
                  <p className={`text-6xl font-bold ${riskColors.text}`}>
                    {result.total_score}
                  </p>
                  <p className={`mt-2 text-xl font-semibold ${riskColors.text}`}>
                    {result.risk_category} Risk
                  </p>
                  <p className="mt-1 text-sm text-slate-400">
                    {result.in_hospital_mortality_estimate}
                  </p>
                </div>

                {/* Recommendation */}
                <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
                  <h3 className="text-sm font-medium text-slate-400 mb-2">
                    Recommendation
                  </h3>
                  <p className="text-white">{result.recommendation}</p>
                </div>

                {/* Score Breakdown */}
                <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
                  <h3 className="text-sm font-medium text-slate-400 mb-3">
                    Score Breakdown
                  </h3>
                  <div className="space-y-2">
                    {Object.entries(result.score_breakdown).map(([factor, points]) => (
                      <div
                        key={factor}
                        className="flex items-center justify-between py-2 border-b border-slate-800 last:border-0"
                      >
                        <span className="text-sm text-slate-300 capitalize">
                          {factor.replace(/_/g, ' ')}
                        </span>
                        <span
                          className={`font-mono font-medium ${
                            points > 0 ? 'text-rose-400' : 'text-slate-500'
                          }`}
                        >
                          +{points}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* Reference */}
            {!result && (
              <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
                <h3 className="text-sm font-medium text-white mb-3">Risk Categories</h3>
                <div className="space-y-3 text-sm">
                  <div className="flex items-center gap-3">
                    <span className="w-3 h-3 rounded-full bg-green-500"></span>
                    <span className="text-slate-300">
                      <strong className="text-green-400">Low (≤108):</strong> &lt;1% mortality
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="w-3 h-3 rounded-full bg-amber-500"></span>
                    <span className="text-slate-300">
                      <strong className="text-amber-400">Intermediate (109-140):</strong> 1-3%
                      mortality
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="w-3 h-3 rounded-full bg-rose-500"></span>
                    <span className="text-slate-300">
                      <strong className="text-rose-400">High (&gt;140):</strong> &gt;3% mortality
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
