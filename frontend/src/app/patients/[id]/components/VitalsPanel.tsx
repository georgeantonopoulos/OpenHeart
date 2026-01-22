'use client';

interface VitalsPanelProps {
  patientId: number;
}

/**
 * Vitals Panel Component.
 *
 * Displays recent vital signs with trend indicators.
 * Placeholder until Observation/Vitals module is implemented.
 */
export default function VitalsPanel({ patientId }: VitalsPanelProps) {
  // Placeholder vitals - will be fetched from API when observations module is ready
  const vitals = [
    {
      name: 'Blood Pressure',
      value: '--/-- mmHg',
      trend: null,
      icon: (
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
            d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
          />
        </svg>
      ),
    },
    {
      name: 'Heart Rate',
      value: '-- bpm',
      trend: null,
      icon: (
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
            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
          />
        </svg>
      ),
    },
    {
      name: 'SpO2',
      value: '--%',
      trend: null,
      icon: (
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
            d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"
          />
        </svg>
      ),
    },
    {
      name: 'Weight',
      value: '-- kg',
      trend: null,
      icon: (
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
            d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3"
          />
        </svg>
      ),
    },
  ];

  return (
    <div className="bg-slate-900 rounded-lg border border-slate-800 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wider">
          Recent Vitals
        </h3>
        <button
          className="text-xs text-rose-400 hover:text-rose-300 transition-colors"
          title="Record new vitals"
        >
          + Record
        </button>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {vitals.map((vital, index) => (
          <div
            key={index}
            className="bg-slate-800/50 rounded-lg p-3 border border-slate-700"
          >
            <div className="flex items-center space-x-2 text-slate-400 mb-1">
              {vital.icon}
              <span className="text-xs">{vital.name}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-lg font-semibold text-white">
                {vital.value}
              </span>
              {vital.trend && (
                <span
                  className={`text-xs ${
                    vital.trend === 'up'
                      ? 'text-red-400'
                      : vital.trend === 'down'
                      ? 'text-green-400'
                      : 'text-slate-400'
                  }`}
                >
                  {vital.trend === 'up' ? '↑' : vital.trend === 'down' ? '↓' : '→'}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* No data message */}
      <p className="mt-3 text-center text-xs text-slate-500">
        No recent measurements recorded
      </p>
    </div>
  );
}
