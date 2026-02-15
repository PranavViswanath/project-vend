"use client";

/**
 * Scrollable feed of recent donations
 */

import { motion } from 'framer-motion';
import { useRecentDonations } from '@/hooks/useApi';

const CATEGORY_BADGES: Record<string, string> = {
  fruit: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/25',
  snack: 'bg-orange-500/15 text-orange-400 border-orange-500/25',
  drink: 'bg-blue-500/15 text-blue-400 border-blue-500/25',
  hygiene: 'bg-purple-500/15 text-purple-400 border-purple-500/25',
};

const DEFAULT_BADGE = 'bg-slate-500/15 text-slate-400 border-slate-500/25';

function timeAgo(timestamp: string): string {
  const now = new Date();
  const then = new Date(timestamp);
  const seconds = Math.floor((now.getTime() - then.getTime()) / 1000);

  if (seconds < 60) return 'just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return then.toLocaleDateString();
}

export default function DonationFeed() {
  const { data: donations, isLoading } = useRecentDonations(10);

  if (isLoading || !donations) {
    return (
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 border border-slate-700/30">
        <h3 className="text-white text-base font-semibold mb-4" style={{ fontFamily: 'var(--font-heading)' }}>Recent Donations</h3>
        <div className="space-y-3 animate-pulse">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-slate-700/30 rounded-xl p-4 h-16" />
          ))}
        </div>
      </div>
    );
  }

  if (donations.length === 0) {
    return (
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 border border-slate-700/30">
        <h3 className="text-white text-base font-semibold mb-4" style={{ fontFamily: 'var(--font-heading)' }}>Recent Donations</h3>
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <svg className="w-10 h-10 text-slate-600 mb-3" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 11.25v8.25a1.5 1.5 0 0 1-1.5 1.5H5.25a1.5 1.5 0 0 1-1.5-1.5v-8.25M12 4.875A2.625 2.625 0 1 0 9.375 7.5H12m0-2.625V7.5m0-2.625A2.625 2.625 0 1 1 14.625 7.5H12m0 0V21m-8.625-9.75h18c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125h-18c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125Z" />
          </svg>
          <p className="text-slate-500 text-sm">Waiting for donations...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 border border-slate-700/30">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-white text-base font-semibold" style={{ fontFamily: 'var(--font-heading)' }}>Recent Donations</h3>
        <span className="text-slate-500 text-xs">{donations.length} items</span>
      </div>
      <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
        {[...donations].reverse().map((donation, index) => (
          <motion.div
            key={donation.id}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.03, duration: 0.3 }}
            className="flex items-center justify-between gap-4 bg-slate-700/20 hover:bg-slate-700/40 rounded-xl px-4 py-3 transition-colors duration-150 cursor-default group"
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <p className="text-white text-sm font-medium truncate">{donation.item_name}</p>
                {donation.estimated_weight_lbs && (
                  <span className="text-slate-500 text-xs flex-shrink-0">{donation.estimated_weight_lbs} lbs</span>
                )}
              </div>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-slate-500 text-xs">{timeAgo(donation.timestamp)}</span>
                {donation.estimated_expiry && (
                  <>
                    <span className="text-slate-700 text-xs">|</span>
                    <span className="text-slate-500 text-xs">
                      Exp {new Date(donation.estimated_expiry).toLocaleDateString()}
                    </span>
                  </>
                )}
              </div>
            </div>
            <span
              className={`px-2.5 py-0.5 rounded-full text-[11px] font-medium border capitalize flex-shrink-0 ${
                CATEGORY_BADGES[donation.category] || DEFAULT_BADGE
              }`}
            >
              {donation.category}
            </span>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
