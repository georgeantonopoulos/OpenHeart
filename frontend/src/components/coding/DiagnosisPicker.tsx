'use client';

import { useSession } from 'next-auth/react';
import { useCallback } from 'react';
import CodeSearchModal from './CodeSearchModal';
import { searchICD10, type ICD10Code } from '@/lib/api/coding';

interface DiagnosisPickerProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (code: ICD10Code) => void;
}

export default function DiagnosisPicker({
  isOpen,
  onClose,
  onSelect,
}: DiagnosisPickerProps) {
  const { data: session } = useSession();

  const searchFn = useCallback(
    async (query: string) => {
      if (!session?.accessToken) return [];
      return searchICD10(session.accessToken, query);
    },
    [session?.accessToken]
  );

  return (
    <CodeSearchModal<ICD10Code>
      isOpen={isOpen}
      onClose={onClose}
      onSelect={onSelect}
      title="Search Diagnosis (ICD-10)"
      placeholder="Search by code or description (EN/EL)..."
      searchFn={searchFn}
      getKey={(item) => item.code}
      renderItem={(item) => (
        <div className="flex items-start gap-3">
          <span className="mt-0.5 rounded border border-teal-500/30 bg-teal-500/10 px-2 py-0.5 text-xs font-mono text-teal-400">
            {item.code}
          </span>
          <div className="flex-1 min-w-0">
            <p className="text-sm text-white truncate">{item.description_en}</p>
            {item.description_el && (
              <p className="text-xs text-slate-400 truncate">{item.description_el}</p>
            )}
            <p className="mt-0.5 text-xs text-slate-500">{item.category}</p>
          </div>
          {item.is_billable && (
            <span className="text-xs text-green-400">Billable</span>
          )}
        </div>
      )}
    />
  );
}
