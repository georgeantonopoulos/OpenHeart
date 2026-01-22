'use client';

import { useState } from 'react';
import { useSession } from 'next-auth/react';
import { useMutation } from '@tanstack/react-query';
import Link from 'next/link';
import {
  calculatePREVENT,
  PREVENTInput,
  PREVENTResult,
  getRiskCategoryColor,
  Sex,
} from '@/lib/api/cdss';

/**
 * PREVENT Equations Calculator Page.
 *
 * Modern race-agnostic ASCVD and Heart Failure risk prediction (AHA 2023).
 */
export default function PREVENTCalculatorPage() {
  const { data: session } = useSession();

  // Form state
  const [formData, setFormData] = useState<PREVENTInput>({
    age: 55,
    sex: 'male',
    systolic_bp: 130,
    total_cholesterol: 200,
    hdl_cholesterol: 50,
    egfr: 90,
    diabetes: false,
    current_smoker: false,
    on_bp_treatment: false,
    on_statin: false,
    hba1c: undefined,
    uacr: undefined,
  });

  const [showAdvanced, setShowAdvanced] = useState(false);
  const [result, setResult] = useState<PREVENTResult | null>(null);

  // Calculate mutation
  const mutation = useMutation({
    mutationFn: () => calculatePREVENT(session?.accessToken || '', formData),
    onSuccess: (data) => {
      setResult(data);
    },
  });

  // Update numeric field
  const updateNumber = (field: keyof PREVENTInput, value: number) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  // Update boolean field
  const updateBoolean = (field: keyof PREVENTInput, value: boolean) => {
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
      age: 55,
      sex: 'male',
      systolic_bp: 130,
      total_cholesterol: 200,
      hdl_cholesterol: 50,
      egfr: 90,
      diabetes: false,
      current_smoker: false,
      on_bp_treatment: false,
      on_statin: false,
      hba1c: undefined,
      uacr: undefined,
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
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
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
              <h1 className="text-2xl font-bold text-white">PREVENT Equations</h1>
              <p className="text-sm text-slate-400">
                AHA 2023 - ASCVD and Heart Failure risk prediction
              </p>
            </div>
          </div>
        </div>
      </div>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Input Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Demographics */}
            <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Demographics</h2>
              <div className="space-y-4">
                {/* Age */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Age (30-79 years)
                  </label>
                  <input
                    type="number"
                    min={30}
                    max={79}
                    value={formData.age}
                    onChange={(e) => updateNumber('age', parseInt(e.target.value) || 30)}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>

                {/* Sex */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Sex</label>
                  <div className="flex gap-4">
                    {(['male', 'female'] as Sex[]).map((sex) => (
                      <label
                        key={sex}
                        className={`flex-1 flex items-center justify-center px-4 py-2 rounded-lg cursor-pointer transition-colors ${
                          formData.sex === sex
                            ? 'bg-teal-600 text-white'
                            : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                        }`}
                      >
                        <input
                          type="radio"
                          name="sex"
                          value={sex}
                          checked={formData.sex === sex}
                          onChange={(e) =>
                            setFormData((prev) => ({ ...prev, sex: e.target.value as Sex }))
                          }
                          className="sr-only"
                        />
                        <span className="capitalize">{sex}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Clinical Values */}
            <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Clinical Values</h2>
              <div className="grid grid-cols-2 gap-4">
                {/* Systolic BP */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Systolic BP (mmHg)
                  </label>
                  <input
                    type="number"
                    min={80}
                    max={250}
                    value={formData.systolic_bp}
                    onChange={(e) => updateNumber('systolic_bp', parseInt(e.target.value) || 120)}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>

                {/* eGFR - Required for PREVENT */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    eGFR (mL/min/1.73m²) *
                  </label>
                  <input
                    type="number"
                    min={5}
                    max={200}
                    value={formData.egfr}
                    onChange={(e) => updateNumber('egfr', parseInt(e.target.value) || 90)}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>

                {/* Total Cholesterol */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Total Cholesterol (mg/dL)
                  </label>
                  <input
                    type="number"
                    min={100}
                    max={400}
                    value={formData.total_cholesterol}
                    onChange={(e) => updateNumber('total_cholesterol', parseInt(e.target.value) || 200)}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>

                {/* HDL Cholesterol */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    HDL Cholesterol (mg/dL)
                  </label>
                  <input
                    type="number"
                    min={20}
                    max={150}
                    value={formData.hdl_cholesterol}
                    onChange={(e) => updateNumber('hdl_cholesterol', parseInt(e.target.value) || 50)}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>
              </div>
            </div>

            {/* Risk Factors */}
            <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Risk Factors</h2>
              <div className="space-y-3">
                {[
                  { key: 'diabetes', label: 'Diabetes Mellitus' },
                  { key: 'current_smoker', label: 'Current Smoker' },
                  { key: 'on_bp_treatment', label: 'On Antihypertensive Medication' },
                  { key: 'on_statin', label: 'On Statin Therapy' },
                ].map(({ key, label }) => (
                  <label
                    key={key}
                    className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors ${
                      formData[key as keyof PREVENTInput]
                        ? 'bg-teal-900/30 border border-teal-700'
                        : 'bg-slate-800/50 border border-transparent hover:bg-slate-800'
                    }`}
                  >
                    <span className="text-sm text-white">{label}</span>
                    <input
                      type="checkbox"
                      checked={formData[key as keyof PREVENTInput] as boolean}
                      onChange={(e) => updateBoolean(key as keyof PREVENTInput, e.target.checked)}
                      className="w-5 h-5 rounded bg-slate-700 border-slate-600 text-teal-600 focus:ring-teal-500"
                    />
                  </label>
                ))}
              </div>
            </div>

            {/* Advanced Options */}
            <div className="bg-slate-900 rounded-lg border border-slate-800">
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="w-full flex items-center justify-between p-4 text-left"
              >
                <span className="text-sm font-medium text-slate-300">
                  Advanced Options (Optional)
                </span>
                <svg
                  className={`w-5 h-5 text-slate-400 transition-transform ${
                    showAdvanced ? 'rotate-180' : ''
                  }`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {showAdvanced && (
                <div className="px-4 pb-4 space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">
                      HbA1c (%) - if diabetic
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min={4}
                      max={20}
                      value={formData.hba1c || ''}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          hba1c: e.target.value ? parseFloat(e.target.value) : undefined,
                        }))
                      }
                      placeholder="Optional"
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">
                      UACR (mg/g) - Urine Albumin-to-Creatinine Ratio
                    </label>
                    <input
                      type="number"
                      min={0}
                      max={10000}
                      value={formData.uacr || ''}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          uacr: e.target.value ? parseFloat(e.target.value) : undefined,
                        }))
                      }
                      placeholder="Optional"
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <button
                type="submit"
                disabled={mutation.isPending}
                className="flex-1 py-3 bg-teal-600 text-white rounded-lg font-medium hover:bg-teal-700 disabled:opacity-50 transition-colors"
              >
                {mutation.isPending ? 'Calculating...' : 'Calculate PREVENT Risk'}
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
                {/* Main Risk Display */}
                <div className={`${riskColors.bg} rounded-lg border ${riskColors.border} p-6 text-center`}>
                  <p className="text-sm text-slate-400 mb-2">10-Year ASCVD Risk</p>
                  <p className={`text-6xl font-bold ${riskColors.text}`}>
                    {result.ten_year_ascvd_risk}%
                  </p>
                  <p className={`mt-2 text-xl font-semibold ${riskColors.text}`}>
                    {result.risk_category} Risk
                  </p>
                </div>

                {/* Heart Failure Risk */}
                <div className="bg-purple-900/20 rounded-lg border border-purple-800 p-6 text-center">
                  <p className="text-sm text-slate-400 mb-2">10-Year Heart Failure Risk</p>
                  <p className="text-4xl font-bold text-purple-400">{result.ten_year_hf_risk}%</p>
                  <p className="text-sm text-slate-400 mt-1">
                    Total CVD Risk: {result.ten_year_total_cvd_risk}%
                  </p>
                </div>

                {/* Statin Benefit */}
                <div
                  className={`rounded-lg border p-4 ${
                    result.statin_benefit_group
                      ? 'bg-green-900/20 border-green-800'
                      : 'bg-slate-900 border-slate-800'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`p-2 rounded-full ${
                        result.statin_benefit_group ? 'bg-green-500/20 text-green-400' : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {result.statin_benefit_group ? (
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                        </svg>
                      )}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-white">Statin Benefit Group</p>
                      <p className="text-xs text-slate-400">
                        {result.statin_benefit_group
                          ? 'Patient likely to benefit from statin therapy'
                          : 'Below threshold for routine statin recommendation'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Recommendation */}
                <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
                  <h3 className="text-sm font-medium text-slate-400 mb-2">Recommendation</h3>
                  <p className="text-white text-sm leading-relaxed">{result.recommendation}</p>
                </div>

                {/* Risk Enhancers */}
                {result.risk_enhancers.length > 0 && (
                  <div className="bg-amber-900/20 rounded-lg border border-amber-800 p-6">
                    <h3 className="text-sm font-medium text-amber-400 mb-3">
                      Risk-Enhancing Factors Present
                    </h3>
                    <ul className="space-y-2">
                      {result.risk_enhancers.map((enhancer, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                          <svg
                            className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                            />
                          </svg>
                          {enhancer}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            )}

            {/* Reference when no result */}
            {!result && (
              <>
                <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
                  <h3 className="text-sm font-medium text-white mb-3">Risk Categories</h3>
                  <div className="space-y-3 text-sm">
                    <div className="flex items-center gap-3">
                      <span className="w-3 h-3 rounded-full bg-green-500"></span>
                      <span className="text-slate-300">
                        <strong className="text-green-400">Low (&lt;5%):</strong> Lifestyle modifications
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="w-3 h-3 rounded-full bg-blue-500"></span>
                      <span className="text-slate-300">
                        <strong className="text-blue-400">Borderline (5-7.5%):</strong> Consider risk enhancers
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="w-3 h-3 rounded-full bg-amber-500"></span>
                      <span className="text-slate-300">
                        <strong className="text-amber-400">Intermediate (7.5-20%):</strong> Statin reasonable
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="w-3 h-3 rounded-full bg-rose-500"></span>
                      <span className="text-slate-300">
                        <strong className="text-rose-400">High (≥20%):</strong> High-intensity statin
                      </span>
                    </div>
                  </div>
                </div>

                <div className="bg-teal-900/10 rounded-lg border border-teal-800/50 p-4">
                  <div className="flex items-start gap-3">
                    <svg
                      className="w-5 h-5 text-teal-400 flex-shrink-0"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    <div className="text-sm text-teal-200">
                      <p className="font-medium">Why PREVENT?</p>
                      <p className="text-teal-300/80 mt-1">
                        PREVENT (2023) replaces Pooled Cohort Equations. It is race-agnostic,
                        includes kidney function (eGFR), and predicts both ASCVD and Heart Failure risk.
                      </p>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
