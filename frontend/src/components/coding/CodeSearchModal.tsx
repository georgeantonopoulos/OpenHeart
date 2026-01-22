'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { X, Search, Loader2 } from 'lucide-react';

interface CodeSearchModalProps<T> {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (item: T) => void;
  title: string;
  placeholder?: string;
  searchFn: (query: string) => Promise<T[]>;
  renderItem: (item: T) => React.ReactNode;
  getKey: (item: T) => string;
  minQueryLength?: number;
}

export default function CodeSearchModal<T>({
  isOpen,
  onClose,
  onSelect,
  title,
  placeholder = 'Search...',
  searchFn,
  renderItem,
  getKey,
  minQueryLength = 2,
}: CodeSearchModalProps<T>) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<T[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setResults([]);
      setError(null);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  const doSearch = useCallback(
    async (q: string) => {
      if (q.length < minQueryLength) {
        setResults([]);
        return;
      }
      try {
        setLoading(true);
        setError(null);
        const data = await searchFn(q);
        setResults(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Search failed');
      } finally {
        setLoading(false);
      }
    },
    [searchFn, minQueryLength]
  );

  const handleQueryChange = (value: string) => {
    setQuery(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => doSearch(value), 300);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[10vh]">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative z-10 w-full max-w-xl rounded-xl border border-white/10 bg-slate-900 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
          <h2 className="text-lg font-semibold text-white">{title}</h2>
          <button
            onClick={onClose}
            className="rounded p-1 text-slate-400 hover:bg-white/10 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Search Input */}
        <div className="border-b border-white/10 px-4 py-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => handleQueryChange(e.target.value)}
              placeholder={placeholder}
              className="w-full rounded-lg border border-white/10 bg-white/5 py-2 pl-10 pr-4 text-white placeholder-slate-500 focus:border-teal-500 focus:outline-none"
            />
            {loading && (
              <Loader2 className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-teal-400" />
            )}
          </div>
        </div>

        {/* Results */}
        <div className="max-h-[50vh] overflow-y-auto p-2">
          {error && (
            <p className="px-4 py-3 text-sm text-red-400">{error}</p>
          )}

          {!loading && query.length >= minQueryLength && results.length === 0 && !error && (
            <p className="px-4 py-6 text-center text-sm text-slate-500">
              No results found for &ldquo;{query}&rdquo;
            </p>
          )}

          {query.length < minQueryLength && (
            <p className="px-4 py-6 text-center text-sm text-slate-500">
              Type at least {minQueryLength} characters to search
            </p>
          )}

          {results.map((item) => (
            <button
              key={getKey(item)}
              onClick={() => {
                onSelect(item);
                onClose();
              }}
              className="w-full rounded-lg px-3 py-2 text-left transition-colors hover:bg-white/5"
            >
              {renderItem(item)}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
