export default function RootLoading() {
  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <div className="flex flex-col items-center">
        <div className="w-12 h-12 bg-gradient-to-br from-rose-500 to-rose-600 rounded-xl flex items-center justify-center animate-pulse">
          <svg className="w-7 h-7 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
          </svg>
        </div>
        <p className="mt-4 text-slate-400 text-sm">Loading...</p>
      </div>
    </div>
  );
}
