'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSession } from 'next-auth/react';
import Link from 'next/link';
import { getTodayEncounters, completeEncounter, Encounter } from '@/lib/api/encounters';
import { useState, useEffect } from 'react';

/**
 * Active Encounter Overlay.
 * 
 * A globally visible component that shows if there is an ongoing clinical encounter.
 * Allows quick navigation back to the patient profile or completing the session.
 */
export default function ActiveEncounterOverlay() {
    const { data: session } = useSession();
    const queryClient = useQueryClient();
    const [isCompleting, setIsCompleting] = useState<number | null>(null);
    const [now, setNow] = useState(new Date());

    // Update 'now' every second for the timer
    useEffect(() => {
        const timer = setInterval(() => setNow(new Date()), 1000);
        return () => clearInterval(timer);
    }, []);

    // Use the same refresh interval we set for global queries
    const { data: encounters = [] } = useQuery({
        queryKey: ['today-encounters-active'],
        queryFn: () => getTodayEncounters(session?.accessToken || ''),
        enabled: !!session?.accessToken,
        refetchInterval: 10000, // Poll every 10 seconds to detect check-ins
    });

    // Filter for in-progress encounters
    const activeEncounters = encounters.filter(e => e.status === 'in_progress');

    // Mutation to complete encounter
    const completeMutation = useMutation({
        mutationFn: (id: number) => completeEncounter(session?.accessToken || '', id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['today-encounters-active'] });
            queryClient.invalidateQueries({ queryKey: ['patient-timeline'] });
            queryClient.invalidateQueries({ queryKey: ['today-appointments'] });
            setIsCompleting(null);
        },
    });

    if (activeEncounters.length === 0) return null;

    return (
        <div className="fixed bottom-6 right-6 z-[60] flex flex-col gap-3 max-w-sm w-full pointer-events-none">
            {activeEncounters.map((encounter) => {
                const startTime = new Date(encounter.start_time);
                const elapsedMs = now.getTime() - startTime.getTime();
                const elapsedMin = Math.floor(elapsedMs / 60000);
                const elapsedSec = Math.floor((elapsedMs % 60000) / 1000);

                return (
                    <div
                        key={encounter.encounter_id}
                        className="pointer-events-auto bg-slate-900/95 border border-emerald-500/30 rounded-2xl shadow-2xl shadow-emerald-500/10 p-4 backdrop-blur-xl animate-in fade-in slide-in-from-bottom-4 duration-500"
                    >
                        <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center space-x-3">
                                <div className="relative">
                                    <div className="w-10 h-10 bg-emerald-500/10 rounded-xl flex items-center justify-center text-emerald-400 border border-emerald-500/20">
                                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                        </svg>
                                    </div>
                                    <div className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-500 rounded-full border-2 border-slate-900 animate-pulse"></div>
                                </div>
                                <div>
                                    <div className="flex items-center gap-2">
                                        <p className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest">Live Encounter</p>
                                        <span className="text-[10px] font-mono text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded">
                                            {elapsedMin}:{elapsedSec.toString().padStart(2, '0')}
                                        </span>
                                    </div>
                                    <h4 className="text-sm font-bold text-white leading-tight">
                                        {encounter.patient_name || `Patient #${encounter.patient_id}`}
                                    </h4>
                                    <p className="text-[10px] text-slate-500 font-mono mt-0.5">{encounter.patient_mrn || 'No MRN'}</p>
                                </div>
                            </div>

                            <button
                                onClick={() => setIsCompleting(encounter.encounter_id)}
                                className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                                title="Complete Encounter"
                            >
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>

                        <div className="grid grid-cols-2 gap-2">
                            <Link
                                href={`/patients/${encounter.patient_id}`}
                                className="flex items-center justify-center px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold rounded-lg transition-all border border-slate-700"
                            >
                                Resume Patient
                            </Link>
                            <button
                                onClick={() => setIsCompleting(encounter.encounter_id)}
                                className="flex items-center justify-center px-3 py-2 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 text-xs font-bold rounded-lg transition-all border border-emerald-500/30 shadow-lg shadow-emerald-500/5"
                            >
                                End Session
                            </button>
                        </div>

                        {isCompleting === encounter.encounter_id && (
                            <div className="mt-4 pt-4 border-t border-slate-800 animate-in fade-in slide-in-from-top-2">
                                <p className="text-[10px] text-slate-400 mb-3 leading-relaxed">
                                    Finalize this encounter? Ensure all findings are documented in the patient timeline.
                                </p>
                                <div className="flex space-x-2">
                                    <button
                                        onClick={() => setIsCompleting(null)}
                                        className="flex-1 py-1.5 text-[10px] text-slate-500 hover:text-white font-bold transition-colors"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        onClick={() => completeMutation.mutate(encounter.encounter_id)}
                                        disabled={completeMutation.isPending}
                                        className="flex-[2] py-1.5 bg-rose-500 text-white text-[10px] font-bold rounded-lg hover:bg-rose-600 disabled:opacity-50 transition-all shadow-lg shadow-rose-500/20"
                                    >
                                        {completeMutation.isPending ? 'Processing...' : 'Yes, Complete Session'}
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                );
            })}
        </div>
    );
}
