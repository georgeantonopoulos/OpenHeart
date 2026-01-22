'use client';

import { useState } from 'react';
import { useSession } from 'next-auth/react';
import { useMutation } from '@tanstack/react-query';
import Link from 'next/link';
import {
  calculateCHA2DS2VASc,
  CHA2DS2VAScInput,
  CHA2DS2VAScResult,
  Sex,
} from '@/lib/api/cdss';

/**
 * CHA₂DS₂-VASc Score Calculator Page.
 *
 * Calculates stroke risk in patients with atrial fibrillation.
 */
export default function CHA2DS2VAScCalculatorPage() {
  const { data: session } = useSession();

  // Form state
  const [formData, setFormData] = useState<CHA2DS2VAScInput>({
    age: 65,
    sex: 'male',
    congestive_heart_failure: false,
    hypertension: false,
    diabetes: false,
    stroke_tia_thromboembolism: false,
    vascular_disease: false,
  });

  const [result, setResult] = useState<CHA2DS2VAScResult | null>(null);

  // Calculate mutation
  const mutation = useMutation({
    mutationFn: () => calculateCHA2DS2VASc(session?.accessToken || '', formData),
    onSuccess: (data) => {
      setResult(data);
    },
  });

  // Update boolean field
  const updateBoolean = (field: keyof CHA2DS2VAScInput, value: boolean) => {
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
      sex: 'male',
      congestive_heart_failure: false,
      hypertension: false,
      diabetes: false,
      stroke_tia_thromboembolism: false,
      vascular_disease: false,
    });
    setResult(null);
  };

  // Get recommendation color
  const getRecommendationColor = (score: number) => {
    if (score === 0) return { bg: 'bg-green-500/20', text: 'text-green-400', border: 'border-green-500' };
    if (score === 1) return { bg: 'bg-amber-500/20', text: 'text-amber-400', border: 'border-amber-500' };
    return { bg: 'bg-rose-500/20', text: 'text-rose-400', border: 'border-rose-500' };
  };

  if (!session) {
    return null;
  }

  const colors = result ? getRecommendationColor(result.adjusted_score) : null;

  // Risk factor definitions
  const riskFactors = [
    {
      key: 'congestive_heart_failure',
      label: 'Congestive Heart Failure',
      description: 'History of CHF or LV dysfunction (LVEF ≤40%)',
      points: 1,
    },
    {
      key: 'hypertension',
      label: 'Hypertension',
      description: 'History of hypertension or on antihypertensive therapy',
      points: 1,
    },
    {
      key: 'diabetes',
      label: 'Diabetes Mellitus',
      description: 'History of diabetes mellitus',
      points: 1,
    },
    {
      key: 'stroke_tia_thromboembolism',
      label: 'Stroke / TIA / Thromboembolism',
      description: 'Prior stroke, TIA, or systemic thromboembolism',
      points: 2,
    },
    {
      key: 'vascular_disease',
      label: 'Vascular Disease',
      description: 'Prior MI, peripheral artery disease, or aortic plaque',
      points: 1,
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
              <h1 className="text-2xl font-bold text-white">
                CHA<sub>2</sub>DS<sub>2</sub>-VASc Score
              </h1>
              <p className="text-sm text-slate-400">
                Stroke risk in atrial fibrillation
              </p>
            </div>
          </div>
        </div>
      </div>

      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Input Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Demographics */}
            <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Demographics</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Age (years)
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={120}
                    value={formData.age}
                    onChange={(e) =>
                      setFormData((prev) => ({ ...prev, age: parseInt(e.target.value) || 0 }))
                    }
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="mt-1 text-xs text-slate-500">
                    65-74: +1 point | ≥75: +2 points
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Sex</label>
                  <div className="grid grid-cols-2 gap-3">
                    {(['male', 'female'] as Sex[]).map((sex) => (
                      <button
                        key={sex}
                        type="button"
                        onClick={() => setFormData((prev) => ({ ...prev, sex }))}
                        className={`py-2 px-4 rounded-lg border font-medium transition-colors ${
                          formData.sex === sex
                            ? 'bg-blue-900/30 border-blue-700 text-blue-300'
                            : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'
                        }`}
                      >
                        {sex === 'male' ? 'Male' : 'Female (+1)'}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Risk Factors */}
            <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Risk Factors</h2>
              <div className="space-y-3">
                {riskFactors.map(({ key, label, description, points }) => (
                  <label
                    key={key}
                    className={`block p-3 rounded-lg cursor-pointer transition-colors ${
                      formData[key as keyof CHA2DS2VAScInput]
                        ? 'bg-blue-900/30 border border-blue-700'
                        : 'bg-slate-800/50 border border-transparent hover:bg-slate-800'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-white">{label}</span>
                          <span className="px-1.5 py-0.5 text-xs bg-slate-700 text-slate-300 rounded">
                            +{points}
                          </span>
                        </div>
                        <p className="text-xs text-slate-400 mt-0.5">{description}</p>
                      </div>
                      <input
                        type="checkbox"
                        checked={formData[key as keyof CHA2DS2VAScInput] as boolean}
                        onChange={(e) => updateBoolean(key as keyof CHA2DS2VAScInput, e.target.checked)}
                        className="w-5 h-5 rounded bg-slate-700 border-slate-600 text-blue-600 focus:ring-blue-500"
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
                className="flex-1 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {mutation.isPending ? 'Calculating...' : 'Calculate Score'}
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
            {result && colors && (
              <>
                {/* Score Display */}
                <div className={`${colors.bg} rounded-lg border ${colors.border} p-6 text-center`}>
                  <p className="text-sm text-slate-400 mb-2">CHA₂DS₂-VASc Score</p>
                  <p className={`text-6xl font-bold ${colors.text}`}>{result.total_score}</p>
                  <p className="mt-1 text-sm text-slate-400">
                    Sex-adjusted: {result.adjusted_score}
                  </p>
                  <p className={`mt-2 text-lg font-semibold ${colors.text}`}>
                    {result.annual_stroke_risk}
                  </p>
                </div>

                {/* Recommendation */}
                <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
                  <h3 className="text-sm font-medium text-slate-400 mb-2">Recommendation</h3>
                  <p className="text-white">{result.recommendation}</p>
                </div>

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
                            points > 0 ? 'text-blue-400' : 'text-slate-500'
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
                <h3 className="text-sm font-medium text-white mb-3">Treatment Thresholds</h3>
                <div className="space-y-3 text-sm">
                  <div className="flex items-start gap-3">
                    <span className="w-3 h-3 rounded-full bg-green-500 mt-1.5"></span>
                    <div>
                      <strong className="text-green-400">Score 0:</strong>
                      <span className="text-slate-300 ml-1">
                        No anticoagulation needed
                      </span>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <span className="w-3 h-3 rounded-full bg-amber-500 mt-1.5"></span>
                    <div>
                      <strong className="text-amber-400">Score 1:</strong>
                      <span className="text-slate-300 ml-1">
                        Consider anticoagulation
                      </span>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <span className="w-3 h-3 rounded-full bg-rose-500 mt-1.5"></span>
                    <div>
                      <strong className="text-rose-400">Score ≥2:</strong>
                      <span className="text-slate-300 ml-1">
                        Oral anticoagulation recommended
                      </span>
                    </div>
                  </div>
                </div>
                <p className="mt-4 text-xs text-slate-500">
                  Note: Female sex alone (score 1) does not warrant anticoagulation.
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
