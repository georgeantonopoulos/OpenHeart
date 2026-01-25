'use client';

import { useState } from 'react';
import { InteractionDetail, InteractionSeverity, getSeverityColor } from '@/lib/api/prescriptions';

interface InteractionAlertProps {
  interactions: InteractionDetail[];
  onAcknowledge?: (acknowledged: boolean, reason?: string) => void;
  showAcknowledge?: boolean;
}

/**
 * Displays drug interaction warnings with severity indicators.
 * For major/contraindicated interactions, requires acknowledgment before proceeding.
 */
export default function InteractionAlert({
  interactions,
  onAcknowledge,
  showAcknowledge = false,
}: InteractionAlertProps) {
  const [acknowledgeReason, setAcknowledgeReason] = useState('');
  const [showReasonInput, setShowReasonInput] = useState(false);

  if (!interactions || interactions.length === 0) {
    return null;
  }

  const hasContraindicated = interactions.some((i) => i.severity === 'contraindicated');
  const hasMajor = interactions.some((i) => i.severity === 'major');
  const requiresAcknowledge = hasContraindicated || hasMajor;

  const severityOrder: Record<InteractionSeverity, number> = {
    contraindicated: 0,
    major: 1,
    moderate: 2,
    minor: 3,
  };

  const sortedInteractions = [...interactions].sort(
    (a, b) => severityOrder[a.severity] - severityOrder[b.severity]
  );

  const getBorderColor = () => {
    if (hasContraindicated) return 'border-red-500/50';
    if (hasMajor) return 'border-orange-500/50';
    return 'border-amber-500/50';
  };

  const getHeaderColor = () => {
    if (hasContraindicated) return 'text-red-400';
    if (hasMajor) return 'text-orange-400';
    return 'text-amber-400';
  };

  return (
    <div className={`rounded-lg border ${getBorderColor()} bg-slate-900 overflow-hidden`}>
      {/* Header */}
      <div className="px-4 py-3 bg-slate-800/50 border-b border-slate-700 flex items-center gap-2">
        <svg
          className={`w-5 h-5 ${getHeaderColor()}`}
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
        <span className={`font-medium ${getHeaderColor()}`}>
          {interactions.length} Drug Interaction{interactions.length > 1 ? 's' : ''} Detected
        </span>
      </div>

      {/* Interactions List */}
      <div className="p-4 space-y-3">
        {sortedInteractions.map((interaction, idx) => (
          <div
            key={idx}
            className={`p-3 rounded border ${getSeverityColor(interaction.severity)}`}
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="font-bold text-xs uppercase tracking-wider">
                {interaction.severity}
              </span>
              <span className="text-sm">
                Interaction with <strong>{interaction.interacting_drug}</strong>
              </span>
            </div>
            <p className="text-sm opacity-90">{interaction.description}</p>
            {interaction.management && (
              <div className="mt-2 pt-2 border-t border-current/20">
                <p className="text-xs">
                  <strong>Management:</strong> {interaction.management}
                </p>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Acknowledge Section */}
      {showAcknowledge && requiresAcknowledge && (
        <div className="px-4 py-3 bg-slate-800/30 border-t border-slate-700">
          {hasContraindicated && (
            <p className="text-red-400 text-sm mb-3">
              <strong>Warning:</strong> This combination is marked as CONTRAINDICATED. Prescribing
              requires explicit acknowledgment with justification.
            </p>
          )}

          {!showReasonInput ? (
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowReasonInput(true)}
                className="px-4 py-2 bg-amber-600 text-white text-sm rounded-lg hover:bg-amber-700 transition-colors"
              >
                I Acknowledge the Risk
              </button>
              <button
                onClick={() => onAcknowledge?.(false)}
                className="px-4 py-2 text-slate-400 text-sm hover:text-white transition-colors"
              >
                Cancel Prescription
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <div>
                <label className="block text-sm text-slate-300 mb-1">
                  Clinical justification for overriding this warning:
                </label>
                <textarea
                  value={acknowledgeReason}
                  onChange={(e) => setAcknowledgeReason(e.target.value)}
                  placeholder="Enter your clinical reasoning..."
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:border-amber-500 focus:ring-1 focus:ring-amber-500 outline-none text-sm"
                  rows={2}
                />
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => {
                    if (acknowledgeReason.length >= 10) {
                      onAcknowledge?.(true, acknowledgeReason);
                    }
                  }}
                  disabled={acknowledgeReason.length < 10}
                  className="px-4 py-2 bg-amber-600 text-white text-sm rounded-lg hover:bg-amber-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Proceed with Prescription
                </button>
                <button
                  onClick={() => {
                    setShowReasonInput(false);
                    setAcknowledgeReason('');
                  }}
                  className="px-4 py-2 text-slate-400 text-sm hover:text-white transition-colors"
                >
                  Back
                </button>
              </div>
              {acknowledgeReason.length > 0 && acknowledgeReason.length < 10 && (
                <p className="text-xs text-amber-400">
                  Justification must be at least 10 characters ({10 - acknowledgeReason.length} more
                  needed)
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
