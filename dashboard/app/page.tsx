/**
 * Project Lend - Main Dashboard Page
 * Real-time monitoring of autonomous food bank system
 */

import CameraFeed from '@/components/CameraFeed';
import StatsCards from '@/components/StatsCards';
import CategoryBreakdown from '@/components/CategoryBreakdown';
import DonationFeed from '@/components/DonationFeed';
import LiveBadge from '@/components/LiveBadge';

export default function Home() {
  return (
    <main className="min-h-screen bg-[#0F172A] p-4 md:p-6 lg:p-8">
      {/* Subtle gradient overlay */}
      <div className="fixed inset-0 bg-gradient-to-br from-emerald-950/20 via-transparent to-blue-950/20 pointer-events-none" />

      <div className="relative max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <header className="flex items-center justify-between py-4">
          <div className="flex items-center gap-4">
            {/* Logo mark */}
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center shadow-lg shadow-emerald-500/20">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 11.25v8.25a1.5 1.5 0 0 1-1.5 1.5H5.25a1.5 1.5 0 0 1-1.5-1.5v-8.25M12 4.875A2.625 2.625 0 1 0 9.375 7.5H12m0-2.625V7.5m0-2.625A2.625 2.625 0 1 1 14.625 7.5H12m0 0V21m-8.625-9.75h18c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125h-18c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125Z" />
              </svg>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white" style={{ fontFamily: 'var(--font-heading)' }}>
                Project Lend
              </h1>
              <p className="text-slate-400 text-sm">
                Autonomous Food Bank System
              </p>
            </div>
          </div>

          <LiveBadge />
        </header>

        {/* Stats Cards */}
        <StatsCards />

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Camera Feed - Spans 2 columns */}
          <div className="lg:col-span-2">
            <CameraFeed />
          </div>

          {/* Category Breakdown */}
          <div>
            <CategoryBreakdown />
          </div>
        </div>

        {/* Donation Feed - Full Width */}
        <DonationFeed />

        {/* Footer */}
        <footer className="text-center pt-6 pb-4">
          <p className="text-slate-500 text-xs">
            Built for TreeHacks 2026 with Next.js, Claude Vision, and xArm 1S
          </p>
        </footer>
      </div>
    </main>
  );
}
