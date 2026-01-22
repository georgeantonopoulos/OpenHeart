'use client';

import { useState } from 'react';
import { useSession } from 'next-auth/react';
import { useMutation } from '@tanstack/react-query';
import Link from 'next/link';
import {
  calculateEuroSCOREII,
  EuroSCOREIIInput,
  EuroSCOREIIResult,
  getRiskCategoryColor,
  Sex,
  LVFunction,
  PulmonaryHypertension,
  OperationUrgency,
  OperationWeight,
  LV_FUNCTION_DESCRIPTIONS,
  PULMONARY_HTN_DESCRIPTIONS,
  URGENCY_DESCRIPTIONS,
  OPERATION_WEIGHT_DESCRIPTIONS,
  NYHA_DESCRIPTIONS,
} from '@/lib/api/cdss';

/**
 * EuroSCORE II Calculator Page.
 *
 * Cardiac surgery mortality risk prediction for Heart Team decisions.
 */
export default function EuroSCOREIICalculatorPage() {
  const { data: session } = useSession();

  // Form state
  const [formData, setFormData] = useState<EuroSCOREIIInput>({
    // Patient factors
    age: 70,
    sex: 'male',
    creatinine_clearance: 85,
    on_dialysis: false,
    extracardiac_arteriopathy: false,
    poor_mobility: false,
    previous_cardiac_surgery: false,
    chronic_lung_disease: false,
    active_endocarditis: false,
    critical_preoperative_state: false,
    diabetes_on_insulin: false,
    // Cardiac factors
    nyha_class: 1,
    ccs_class_4_angina: false,
    lv_function: 'good',
    recent_mi: false,
    pulmonary_hypertension: 'no',
    // Operation factors
    urgency: 'elective',
    operation_weight: 'isolated_cabg',
    surgery_on_thoracic_aorta: false,
  });

  const [activeTab, setActiveTab] = useState<'patient' | 'cardiac' | 'operation'>('patient');
  const [result, setResult] = useState<EuroSCOREIIResult | null>(null);

  // Calculate mutation
  const mutation = useMutation({
    mutationFn: () => calculateEuroSCOREII(session?.accessToken || '', formData),
    onSuccess: (data) => {
      setResult(data);
    },
  });

  // Update numeric field
  const updateNumber = (field: keyof EuroSCOREIIInput, value: number) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  // Update boolean field
  const updateBoolean = (field: keyof EuroSCOREIIInput, value: boolean) => {
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
      age: 70,
      sex: 'male',
      creatinine_clearance: 85,
      on_dialysis: false,
      extracardiac_arteriopathy: false,
      poor_mobility: false,
      previous_cardiac_surgery: false,
      chronic_lung_disease: false,
      active_endocarditis: false,
      critical_preoperative_state: false,
      diabetes_on_insulin: false,
      nyha_class: 1,
      ccs_class_4_angina: false,
      lv_function: 'good',
      recent_mi: false,
      pulmonary_hypertension: 'no',
      urgency: 'elective',
      operation_weight: 'isolated_cabg',
      surgery_on_thoracic_aorta: false,
    });
    setResult(null);
  };

  if (!session) {
    return null;
  }

  const riskColors = result ? getRiskCategoryColor(result.risk_category) : null;

  const tabs = [
    { id: 'patient', label: 'Patient Factors', icon: '👤' },
    { id: 'cardiac', label: 'Cardiac Factors', icon: '❤️' },
    { id: 'operation', label: 'Operation', icon: '🔧' },
  ] as const;

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
              <h1 className="text-2xl font-bold text-white">EuroSCORE II</h1>
              <p className="text-sm text-slate-400">
                Cardiac surgery mortality risk for Heart Team decisions
              </p>
            </div>
          </div>
        </div>
      </div>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid gap-6 lg:grid-cols-5">
          {/* Input Form - 3 columns */}
          <form onSubmit={handleSubmit} className="lg:col-span-3 space-y-6">
            {/* Tab Navigation */}
            <div className="flex bg-slate-900 rounded-lg border border-slate-800 p-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === tab.id
                      ? 'bg-purple-600 text-white'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`}
                >
                  <span>{tab.icon}</span>
                  <span className="hidden sm:inline">{tab.label}</span>
                </button>
              ))}
            </div>

            {/* Patient Factors */}
            {activeTab === 'patient' && (
              <div className="bg-slate-900 rounded-lg border border-slate-800 p-6 space-y-6">
                <h2 className="text-lg font-semibold text-white">Patient Factors</h2>

                {/* Demographics */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">Age</label>
                    <input
                      type="number"
                      min={18}
                      max={100}
                      value={formData.age}
                      onChange={(e) => updateNumber('age', parseInt(e.target.value) || 70)}
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">Sex</label>
                    <div className="flex gap-2">
                      {(['male', 'female'] as Sex[]).map((sex) => (
                        <label
                          key={sex}
                          className={`flex-1 flex items-center justify-center px-3 py-2 rounded-lg cursor-pointer transition-colors text-sm ${
                            formData.sex === sex
                              ? 'bg-purple-600 text-white'
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

                {/* Renal */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Creatinine Clearance (mL/min)
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={200}
                    value={formData.creatinine_clearance}
                    onChange={(e) => updateNumber('creatinine_clearance', parseInt(e.target.value) || 85)}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                  <p className="text-xs text-slate-500 mt-1">Cockcroft-Gault formula</p>
                </div>

                {/* Comorbidities */}
                <div className="space-y-3">
                  <p className="text-sm font-medium text-slate-400">Comorbidities</p>
                  {[
                    { key: 'on_dialysis', label: 'On Dialysis', desc: 'Chronic dialysis' },
                    { key: 'extracardiac_arteriopathy', label: 'Extracardiac Arteriopathy', desc: 'Claudication, carotid >50%, prior aortic surgery' },
                    { key: 'poor_mobility', label: 'Poor Mobility', desc: 'Musculoskeletal/neurological dysfunction' },
                    { key: 'previous_cardiac_surgery', label: 'Previous Cardiac Surgery', desc: 'Redo sternotomy' },
                    { key: 'chronic_lung_disease', label: 'Chronic Lung Disease', desc: 'Bronchodilator/steroid use' },
                    { key: 'active_endocarditis', label: 'Active Endocarditis', desc: 'Still on antibiotics at surgery' },
                    { key: 'critical_preoperative_state', label: 'Critical Preoperative State', desc: 'VT/VF, IABP, ventilated, inotropes' },
                    { key: 'diabetes_on_insulin', label: 'Diabetes on Insulin', desc: 'Insulin-dependent DM' },
                  ].map(({ key, label, desc }) => (
                    <label
                      key={key}
                      className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors ${
                        formData[key as keyof EuroSCOREIIInput]
                          ? 'bg-purple-900/30 border border-purple-700'
                          : 'bg-slate-800/50 border border-transparent hover:bg-slate-800'
                      }`}
                    >
                      <div>
                        <span className="text-sm text-white">{label}</span>
                        <p className="text-xs text-slate-500">{desc}</p>
                      </div>
                      <input
                        type="checkbox"
                        checked={formData[key as keyof EuroSCOREIIInput] as boolean}
                        onChange={(e) => updateBoolean(key as keyof EuroSCOREIIInput, e.target.checked)}
                        className="w-5 h-5 rounded bg-slate-700 border-slate-600 text-purple-600 focus:ring-purple-500"
                      />
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* Cardiac Factors */}
            {activeTab === 'cardiac' && (
              <div className="bg-slate-900 rounded-lg border border-slate-800 p-6 space-y-6">
                <h2 className="text-lg font-semibold text-white">Cardiac Factors</h2>

                {/* NYHA Class */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">NYHA Class</label>
                  <div className="grid grid-cols-2 gap-2">
                    {([1, 2, 3, 4] as const).map((cls) => (
                      <label
                        key={cls}
                        className={`flex items-center p-3 rounded-lg cursor-pointer transition-colors ${
                          formData.nyha_class === cls
                            ? 'bg-purple-600 text-white'
                            : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                        }`}
                      >
                        <input
                          type="radio"
                          name="nyha_class"
                          value={cls}
                          checked={formData.nyha_class === cls}
                          onChange={() => setFormData((prev) => ({ ...prev, nyha_class: cls }))}
                          className="sr-only"
                        />
                        <span className="text-sm">{NYHA_DESCRIPTIONS[cls]}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* LV Function */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">LV Function</label>
                  <div className="grid grid-cols-2 gap-2">
                    {(['good', 'moderate', 'poor', 'very_poor'] as LVFunction[]).map((lv) => (
                      <label
                        key={lv}
                        className={`flex items-center p-3 rounded-lg cursor-pointer transition-colors ${
                          formData.lv_function === lv
                            ? 'bg-purple-600 text-white'
                            : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                        }`}
                      >
                        <input
                          type="radio"
                          name="lv_function"
                          value={lv}
                          checked={formData.lv_function === lv}
                          onChange={() => setFormData((prev) => ({ ...prev, lv_function: lv }))}
                          className="sr-only"
                        />
                        <span className="text-sm">{LV_FUNCTION_DESCRIPTIONS[lv]}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Pulmonary Hypertension */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Pulmonary Hypertension (PA systolic)
                  </label>
                  <div className="space-y-2">
                    {(['no', 'moderate', 'severe'] as PulmonaryHypertension[]).map((ph) => (
                      <label
                        key={ph}
                        className={`flex items-center p-3 rounded-lg cursor-pointer transition-colors ${
                          formData.pulmonary_hypertension === ph
                            ? 'bg-purple-600 text-white'
                            : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                        }`}
                      >
                        <input
                          type="radio"
                          name="pulmonary_hypertension"
                          value={ph}
                          checked={formData.pulmonary_hypertension === ph}
                          onChange={() => setFormData((prev) => ({ ...prev, pulmonary_hypertension: ph }))}
                          className="sr-only"
                        />
                        <span className="text-sm">{PULMONARY_HTN_DESCRIPTIONS[ph]}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Other Cardiac */}
                <div className="space-y-3">
                  {[
                    { key: 'ccs_class_4_angina', label: 'CCS Class 4 Angina', desc: 'Angina at rest' },
                    { key: 'recent_mi', label: 'Recent MI', desc: 'MI within 90 days' },
                  ].map(({ key, label, desc }) => (
                    <label
                      key={key}
                      className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors ${
                        formData[key as keyof EuroSCOREIIInput]
                          ? 'bg-purple-900/30 border border-purple-700'
                          : 'bg-slate-800/50 border border-transparent hover:bg-slate-800'
                      }`}
                    >
                      <div>
                        <span className="text-sm text-white">{label}</span>
                        <p className="text-xs text-slate-500">{desc}</p>
                      </div>
                      <input
                        type="checkbox"
                        checked={formData[key as keyof EuroSCOREIIInput] as boolean}
                        onChange={(e) => updateBoolean(key as keyof EuroSCOREIIInput, e.target.checked)}
                        className="w-5 h-5 rounded bg-slate-700 border-slate-600 text-purple-600 focus:ring-purple-500"
                      />
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* Operation Factors */}
            {activeTab === 'operation' && (
              <div className="bg-slate-900 rounded-lg border border-slate-800 p-6 space-y-6">
                <h2 className="text-lg font-semibold text-white">Operation Factors</h2>

                {/* Urgency */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Urgency</label>
                  <div className="space-y-2">
                    {(['elective', 'urgent', 'emergency', 'salvage'] as OperationUrgency[]).map((urg) => (
                      <label
                        key={urg}
                        className={`flex items-center p-3 rounded-lg cursor-pointer transition-colors ${
                          formData.urgency === urg
                            ? 'bg-purple-600 text-white'
                            : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                        }`}
                      >
                        <input
                          type="radio"
                          name="urgency"
                          value={urg}
                          checked={formData.urgency === urg}
                          onChange={() => setFormData((prev) => ({ ...prev, urgency: urg }))}
                          className="sr-only"
                        />
                        <span className="text-sm">{URGENCY_DESCRIPTIONS[urg]}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Procedure Weight */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Type of Procedure
                  </label>
                  <div className="space-y-2">
                    {(['isolated_cabg', 'single_non_cabg', 'two_procedures', 'three_or_more'] as OperationWeight[]).map((weight) => (
                      <label
                        key={weight}
                        className={`flex items-center p-3 rounded-lg cursor-pointer transition-colors ${
                          formData.operation_weight === weight
                            ? 'bg-purple-600 text-white'
                            : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                        }`}
                      >
                        <input
                          type="radio"
                          name="operation_weight"
                          value={weight}
                          checked={formData.operation_weight === weight}
                          onChange={() => setFormData((prev) => ({ ...prev, operation_weight: weight }))}
                          className="sr-only"
                        />
                        <span className="text-sm">{OPERATION_WEIGHT_DESCRIPTIONS[weight]}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Thoracic Aorta */}
                <label
                  className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors ${
                    formData.surgery_on_thoracic_aorta
                      ? 'bg-purple-900/30 border border-purple-700'
                      : 'bg-slate-800/50 border border-transparent hover:bg-slate-800'
                  }`}
                >
                  <div>
                    <span className="text-sm text-white">Surgery on Thoracic Aorta</span>
                    <p className="text-xs text-slate-500">Ascending, arch, or descending aortic surgery</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={formData.surgery_on_thoracic_aorta}
                    onChange={(e) => updateBoolean('surgery_on_thoracic_aorta', e.target.checked)}
                    className="w-5 h-5 rounded bg-slate-700 border-slate-600 text-purple-600 focus:ring-purple-500"
                  />
                </label>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3">
              <button
                type="submit"
                disabled={mutation.isPending}
                className="flex-1 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 disabled:opacity-50 transition-colors"
              >
                {mutation.isPending ? 'Calculating...' : 'Calculate EuroSCORE II'}
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

          {/* Result Panel - 2 columns */}
          <div className="lg:col-span-2 space-y-6">
            {result && riskColors && (
              <>
                {/* Main Risk Display */}
                <div className={`${riskColors.bg} rounded-lg border ${riskColors.border} p-6 text-center`}>
                  <p className="text-sm text-slate-400 mb-2">Predicted Operative Mortality</p>
                  <p className={`text-5xl font-bold ${riskColors.text}`}>
                    {result.predicted_mortality}%
                  </p>
                  <p className={`mt-2 text-lg font-semibold ${riskColors.text}`}>
                    {result.risk_category} Risk
                  </p>
                </div>

                {/* Surgical Suitability */}
                <div className="bg-slate-900 rounded-lg border border-slate-800 p-4">
                  <h3 className="text-sm font-medium text-slate-400 mb-2">Surgical Candidacy</h3>
                  <p className="text-white font-medium">{result.suitability_for_surgery}</p>
                </div>

                {/* Recommendation */}
                <div className="bg-slate-900 rounded-lg border border-slate-800 p-4">
                  <h3 className="text-sm font-medium text-slate-400 mb-2">Heart Team Considerations</h3>
                  <p className="text-white text-sm leading-relaxed">{result.recommendation}</p>
                </div>

                {/* Risk Factors Present */}
                {result.risk_factors_present.length > 0 && (
                  <div className="bg-slate-900 rounded-lg border border-slate-800 p-4">
                    <h3 className="text-sm font-medium text-slate-400 mb-3">
                      Contributing Risk Factors ({result.risk_factors_present.length})
                    </h3>
                    <div className="space-y-2">
                      {result.risk_factors_present.map((factor, i) => (
                        <div key={i} className="flex items-center gap-2 text-sm text-slate-300">
                          <span className="w-1.5 h-1.5 bg-purple-400 rounded-full"></span>
                          {factor}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Reference when no result */}
            {!result && (
              <>
                <div className="bg-slate-900 rounded-lg border border-slate-800 p-4">
                  <h3 className="text-sm font-medium text-white mb-3">Risk Thresholds</h3>
                  <div className="space-y-3 text-sm">
                    <div className="flex items-center gap-3">
                      <span className="w-3 h-3 rounded-full bg-green-500"></span>
                      <span className="text-slate-300">
                        <strong className="text-green-400">Low (&lt;2%):</strong> Good candidate
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="w-3 h-3 rounded-full bg-amber-500"></span>
                      <span className="text-slate-300">
                        <strong className="text-amber-400">Intermediate (2-5%):</strong> Heart Team review
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="w-3 h-3 rounded-full bg-rose-500"></span>
                      <span className="text-slate-300">
                        <strong className="text-rose-400">High (5-10%):</strong> Consider alternatives
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="w-3 h-3 rounded-full bg-red-700"></span>
                      <span className="text-slate-300">
                        <strong className="text-red-400">Very High (&gt;10%):</strong> Prohibitive risk
                      </span>
                    </div>
                  </div>
                </div>

                <div className="bg-purple-900/10 rounded-lg border border-purple-800/50 p-4">
                  <div className="flex items-start gap-3">
                    <svg
                      className="w-5 h-5 text-purple-400 flex-shrink-0"
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
                    <div className="text-sm text-purple-200">
                      <p className="font-medium">Clinical Use</p>
                      <p className="text-purple-300/80 mt-1">
                        EuroSCORE II guides Heart Team decisions between surgical and
                        percutaneous approaches (e.g., CABG vs PCI, SAVR vs TAVI).
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
