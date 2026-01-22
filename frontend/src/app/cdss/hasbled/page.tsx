'use client';

import { useState } from 'react';
import { useSession } from 'next-auth/react';
import { useMutation } from '@tanstack/react-query';
import Link from 'next/link';
import {
  calculateHASBLED,
  HASBLEDInput,
  HASBLEDResult,
  getRiskCategoryColor,
} from '@/lib/api/cdss';

/**
 * HAS-BLED Score Calculator Page.
 *
 * Calculates major bleeding risk in patients on anticoagulation.
 */
export default function HASBLEDCalculatorPage() {
  const { data: session } = useSession();

  // Form state
  const [formData, setFormData] = useState<HASBLEDInput>({
    hypertension_uncontrolled: false,
    abnormal_renal_function: false,
    abnormal_liver_function: false,
    stroke_history: false,
    bleeding_history: false,
    labile_inr: false,
    elderly: false,
    antiplatelet_or_nsaid: false,
    alcohol_abuse: false,
  });

  const [result, setResult] = useState<HASBLEDResult | null>(null);

  // Calculate mutation
  const mutation = useMutation({
    mutationFn: () => calculateHASBLED(session?.accessToken || '', formData),
    onSuccess: (data) => {
      setResult(data);
    },
  });

  // Update boolean field
  const updateBoolean = (field: keyof HASBLEDInput, value: boolean) => {
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
      hypertension_uncontrolled: false,
      abnormal_renal_function: false,
      abnormal_liver_function: false,
      stroke_history: false,
      bleeding_history: false,
      labile_inr: false,
      elderly: false,
      antiplatelet_or_nsaid: false,
      alcohol_abuse: false,
    });
    setResult(null);
  };

  if (!session) {
    return null;
  }

  const riskColors = result ? getRiskCategoryColor(result.risk_level) : null;

  // Risk factor definitions following HAS-BLED mnemonic
  const riskFactors = [
    {
      key: 'hypertension_uncontrolled',
      letter: 'H',
      label: 'Hypertension (uncontrolled)',
      description: 'Systolic BP >160 mmHg',
      modifiable: true,
    },
    {
      key: 'abnormal_renal_function',
      letter: 'A',
      label: 'Abnormal Renal function',
      description: 'Dialysis, transplant, Cr >2.3 mg/dL, or eGFR <30',
      modifiable: true,
    },
    {
      key: 'abnormal_liver_function',
      letter: 'A',
      label: 'Abnormal Liver function',
      description: 'Cirrhosis, bilirubin >2x normal, or AST/ALT/ALP >3x normal',
      modifiable: true,
    },
    {
      key: 'stroke_history',
      letter: 'S',
      label: 'Stroke history',
      description: 'Previous stroke',
      modifiable: false,
    },
    {
      key: 'bleeding_history',
      letter: 'B',
      label: 'Bleeding history/predisposition',
      description: 'Major bleeding or bleeding predisposition',
      modifiable: false,
    },
    {
      key: 'labile_inr',
      letter: 'L',
      label: 'Labile INR',
      description: 'Time in therapeutic range <60% (if on warfarin)',
      modifiable: true,
    },
    {
      key: 'elderly',
      letter: 'E',
      label: 'Elderly (>65)',
      description: 'Age greater than 65 years',
      modifiable: false,
    },
    {
      key: 'antiplatelet_or_nsaid',
      letter: 'D',
      label: 'Drugs (antiplatelet/NSAID)',
      description: 'Concomitant antiplatelet or NSAID use',
      modifiable: true,
    },
    {
      key: 'alcohol_abuse',
      letter: 'D',
      label: 'Drugs (alcohol abuse)',
      description: 'Alcohol abuse (≥8 drinks/week)',
      modifiable: true,
    },
  ];

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
              <h1 className="text-2xl font-bold text-white">HAS-BLED Score</h1>
              <p className="text-sm text-slate-400">
                Major bleeding risk assessment for anticoagulation
              </p>
            </div>
          </div>
        </div>
      </div>

      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Input Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Risk Factors */}
            <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Risk Factors</h2>
              <div className="space-y-3">
                {riskFactors.map(({ key, letter, label, description, modifiable }) => (
                  <label
                    key={key}
                    className={`block p-3 rounded-lg cursor-pointer transition-colors ${
                      formData[key as keyof HASBLEDInput]
                        ? 'bg-amber-900/30 border border-amber-700'
                        : 'bg-slate-800/50 border border-transparent hover:bg-slate-800'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="w-6 h-6 flex items-center justify-center bg-amber-500/20 text-amber-400 font-bold text-sm rounded">
                            {letter}
                          </span>
                          <span className="text-sm font-medium text-white">{label}</span>
                          {modifiable && (
                            <span className="px-1.5 py-0.5 text-[10px] bg-teal-500/20 text-teal-300 rounded">
                              Modifiable
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-400 mt-0.5 ml-8">{description}</p>
                      </div>
                      <input
                        type="checkbox"
                        checked={formData[key as keyof HASBLEDInput]}
                        onChange={(e) => updateBoolean(key as keyof HASBLEDInput, e.target.checked)}
                        className="w-5 h-5 rounded bg-slate-700 border-slate-600 text-amber-600 focus:ring-amber-500"
                      />
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <button
                type="submit"
                disabled={mutation.isPending}
                className="flex-1 py-3 bg-amber-600 text-white rounded-lg font-medium hover:bg-amber-700 disabled:opacity-50 transition-colors"
              >
                {mutation.isPending ? 'Calculating...' : 'Calculate HAS-BLED Score'}
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
                  <p className="text-sm text-slate-400 mb-2">HAS-BLED Score</p>
                  <p className={`text-6xl font-bold ${riskColors.text}`}>{result.total_score}</p>
                  <p className={`mt-2 text-xl font-semibold ${riskColors.text}`}>
                    {result.risk_level} Risk
                  </p>
                  <p className="mt-1 text-sm text-slate-400">{result.annual_bleeding_rate}</p>
                </div>

                {/* Recommendation */}
                <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
                  <h3 className="text-sm font-medium text-slate-400 mb-2">Recommendation</h3>
                  <p className="text-white">{result.recommendation}</p>
                </div>

                {/* Modifiable Factors */}
                {result.modifiable_factors.length > 0 && (
                  <div className="bg-teal-900/20 rounded-lg border border-teal-800 p-6">
                    <h3 className="text-sm font-medium text-teal-400 mb-3">
                      Modifiable Risk Factors to Address
                    </h3>
                    <ul className="space-y-2">
                      {result.modifiable_factors.map((factor, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                          <svg
                            className="w-4 h-4 text-teal-400 mt-0.5 flex-shrink-0"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                          </svg>
                          {factor}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Score Breakdown */}
                <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
                  <h3 className="text-sm font-medium text-slate-400 mb-3">Score Breakdown</h3>
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
                            points > 0 ? 'text-amber-400' : 'text-slate-500'
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
              <>
                <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
                  <h3 className="text-sm font-medium text-white mb-3">Risk Levels</h3>
                  <div className="space-y-3 text-sm">
                    <div className="flex items-center gap-3">
                      <span className="w-3 h-3 rounded-full bg-green-500"></span>
                      <span className="text-slate-300">
                        <strong className="text-green-400">Low (0-1):</strong> ~1%/year major bleeding
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="w-3 h-3 rounded-full bg-amber-500"></span>
                      <span className="text-slate-300">
                        <strong className="text-amber-400">Moderate (2):</strong> ~2%/year major
                        bleeding
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="w-3 h-3 rounded-full bg-rose-500"></span>
                      <span className="text-slate-300">
                        <strong className="text-rose-400">High (≥3):</strong> ≥3.7%/year major
                        bleeding
                      </span>
                    </div>
                  </div>
                </div>

                <div className="bg-amber-900/10 rounded-lg border border-amber-800/50 p-4">
                  <div className="flex items-start gap-3">
                    <svg
                      className="w-5 h-5 text-amber-400 flex-shrink-0"
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
                    <p className="text-sm text-amber-200">
                      <strong>Important:</strong> High HAS-BLED does NOT contraindicate
                      anticoagulation. It identifies modifiable risk factors requiring attention.
                    </p>
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
