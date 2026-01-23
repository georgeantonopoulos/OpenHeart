export default function DashboardLoading() {
  return (
    <div className="min-h-screen bg-slate-950">
      {/* Skeleton Nav Bar */}
      <nav className="bg-slate-900 border-b border-slate-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center space-x-8">
              <div className="w-8 h-8 bg-slate-800 rounded-lg animate-pulse" />
              <div className="w-24 h-5 bg-slate-800 rounded animate-pulse" />
              <div className="hidden md:flex space-x-3">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="w-16 h-5 bg-slate-800 rounded animate-pulse" />
                ))}
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="w-32 h-8 bg-slate-800 rounded-lg animate-pulse" />
              <div className="w-9 h-9 bg-slate-800 rounded-full animate-pulse" />
            </div>
          </div>
        </div>
      </nav>

      {/* Skeleton Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Welcome header */}
        <div className="mb-6">
          <div className="w-64 h-8 bg-slate-800 rounded animate-pulse" />
          <div className="w-48 h-5 bg-slate-800 rounded animate-pulse mt-2" />
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <div className="w-20 h-4 bg-slate-800 rounded animate-pulse" />
              <div className="w-12 h-8 bg-slate-800 rounded animate-pulse mt-2" />
            </div>
          ))}
        </div>

        {/* Main grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Appointments column */}
          <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6">
            <div className="w-40 h-6 bg-slate-800 rounded animate-pulse mb-4" />
            <div className="space-y-3">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="flex items-center space-x-3">
                  <div className="w-16 h-5 bg-slate-800 rounded animate-pulse" />
                  <div className="flex-1 h-12 bg-slate-800/50 rounded-lg animate-pulse" />
                </div>
              ))}
            </div>
          </div>

          {/* Right column */}
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <div className="w-32 h-5 bg-slate-800 rounded animate-pulse mb-3" />
              <div className="space-y-2">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="h-10 bg-slate-800/50 rounded-lg animate-pulse" />
                ))}
              </div>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <div className="w-28 h-5 bg-slate-800 rounded animate-pulse mb-3" />
              <div className="grid grid-cols-2 gap-2">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="h-16 bg-slate-800/50 rounded-lg animate-pulse" />
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
