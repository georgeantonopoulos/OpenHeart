'use client';

import { useState, useCallback } from 'react';
import { useSession } from 'next-auth/react';
import CodeSearchModal from './CodeSearchModal';
import { searchCPT, searchHIO, type CPTCode, type HIOServiceCode } from '@/lib/api/coding';

type ProcedureCodeType = 'cpt' | 'hio';

interface ProcedurePickerProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectCPT?: (code: CPTCode) => void;
  onSelectHIO?: (code: HIOServiceCode) => void;
  defaultCodeType?: ProcedureCodeType;
}

export default function ProcedurePicker({
  isOpen,
  onClose,
  onSelectCPT,
  onSelectHIO,
  defaultCodeType = 'hio',
}: ProcedurePickerProps) {
  const { data: session } = useSession();
  const [codeType, setCodeType] = useState<ProcedureCodeType>(defaultCodeType);

  const searchCPTFn = useCallback(
    async (query: string) => {
      if (!session?.accessToken) return [];
      return searchCPT(session.accessToken, query);
    },
    [session?.accessToken]
  );

  const searchHIOFn = useCallback(
    async (query: string) => {
      if (!session?.accessToken) return [];
      return searchHIO(session.accessToken, query);
    },
    [session?.accessToken]
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[10vh]">
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      <div className="relative z-10 w-full max-w-xl">
        {/* Code type tabs */}
        <div className="mb-2 flex justify-center gap-2">
          <button
            onClick={() => setCodeType('hio')}
            className={`rounded-lg px-4 py-1.5 text-sm font-medium transition-colors ${
              codeType === 'hio'
                ? 'bg-teal-600 text-white'
                : 'bg-slate-800 text-slate-300 hover:text-white'
            }`}
          >
            HIO (Cyprus)
          </button>
          <button
            onClick={() => setCodeType('cpt')}
            className={`rounded-lg px-4 py-1.5 text-sm font-medium transition-colors ${
              codeType === 'cpt'
                ? 'bg-teal-600 text-white'
                : 'bg-slate-800 text-slate-300 hover:text-white'
            }`}
          >
            CPT
          </button>
        </div>

        {codeType === 'cpt' ? (
          <CodeSearchModal<CPTCode>
            isOpen={true}
            onClose={onClose}
            onSelect={(item) => {
              onSelectCPT?.(item);
              onClose();
            }}
            title="Search Procedure (CPT)"
            placeholder="Search by code or description..."
            searchFn={searchCPTFn}
            getKey={(item) => item.code}
            renderItem={(item) => (
              <div className="flex items-start gap-3">
                <span className="mt-0.5 rounded border border-blue-500/30 bg-blue-500/10 px-2 py-0.5 text-xs font-mono text-blue-400">
                  {item.code}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white truncate">{item.description}</p>
                  <p className="text-xs text-slate-500">{item.category}</p>
                </div>
                {item.relative_value != null && (
                  <span className="text-xs text-slate-400">RV: {item.relative_value}</span>
                )}
              </div>
            )}
          />
        ) : (
          <CodeSearchModal<HIOServiceCode>
            isOpen={true}
            onClose={onClose}
            onSelect={(item) => {
              onSelectHIO?.(item);
              onClose();
            }}
            title="Search Procedure (HIO)"
            placeholder="Search by code or description (EN/EL)..."
            searchFn={searchHIOFn}
            getKey={(item) => item.code}
            renderItem={(item) => (
              <div className="flex items-start gap-3">
                <span className="mt-0.5 rounded border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-xs font-mono text-amber-400">
                  {item.code}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white truncate">{item.description_en}</p>
                  {item.description_el && (
                    <p className="text-xs text-slate-400 truncate">{item.description_el}</p>
                  )}
                  <p className="text-xs text-slate-500">{item.service_type}</p>
                </div>
                {item.base_price_eur != null && (
                  <span className="text-xs text-green-400">&euro;{item.base_price_eur.toFixed(2)}</span>
                )}
              </div>
            )}
          />
        )}
      </div>
    </div>
  );
}
