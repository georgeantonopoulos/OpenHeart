'use client';

import { useCallback } from 'react';
import { useSession } from 'next-auth/react';
import CodeSearchModal from './CodeSearchModal';
import { searchMedications, type GesyMedication } from '@/lib/api/coding';

interface MedicationPickerProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (medication: GesyMedication) => void;
}

export default function MedicationPicker({
  isOpen,
  onClose,
  onSelect,
}: MedicationPickerProps) {
  const { data: session } = useSession();

  const searchFn = useCallback(
    async (query: string) => {
      if (!session?.accessToken) return [];
      return searchMedications(session.accessToken, query);
    },
    [session?.accessToken]
  );

  return (
    <CodeSearchModal<GesyMedication>
      isOpen={isOpen}
      onClose={onClose}
      onSelect={onSelect}
      title="Search Gesy Medications"
      placeholder="Search by brand name, generic name, or ATC code..."
      searchFn={searchFn}
      getKey={(item) => item.hio_product_id}
      renderItem={(item) => (
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0">
            <span className="block rounded border border-purple-500/30 bg-purple-500/10 px-2 py-0.5 text-xs font-mono text-purple-400">
              {item.atc_code}
            </span>
            {item.requires_pre_auth && (
              <span className="mt-1 block rounded bg-amber-500/20 px-1.5 py-0.5 text-center text-[10px] text-amber-400">
                Pre-Auth
              </span>
            )}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white">{item.brand_name}</p>
            {item.generic_name && (
              <p className="text-xs text-slate-400">{item.generic_name}</p>
            )}
            <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
              {item.strength && <span>{item.strength}</span>}
              {item.form && <span>• {item.form}</span>}
              {item.pack_size && <span>• x{item.pack_size}</span>}
              {item.manufacturer && <span>• {item.manufacturer}</span>}
            </div>
          </div>
          {item.price_eur != null && (
            <span className="text-sm font-medium text-green-400">
              &euro;{item.price_eur.toFixed(2)}
            </span>
          )}
        </div>
      )}
    />
  );
}
