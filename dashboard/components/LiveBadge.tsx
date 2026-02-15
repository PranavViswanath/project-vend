"use client";

/**
 * Live status badge - shows pipeline connection status
 */

import { usePipelineState } from '@/hooks/useApi';

export default function LiveBadge() {
  const { data: state, error } = usePipelineState();

  const isLive = state && !error;
  const isActive = state?.camera_active;

  return (
    <div className="flex items-center gap-2">
      {isLive ? (
        <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-full">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
          <span className="text-emerald-400 text-xs font-medium">
            {isActive ? 'LIVE' : 'CONNECTED'}
          </span>
        </div>
      ) : (
        <div className="flex items-center gap-2 bg-slate-700/50 border border-slate-600/20 px-3 py-1.5 rounded-full">
          <span className="h-2 w-2 rounded-full bg-slate-500" />
          <span className="text-slate-400 text-xs font-medium">OFFLINE</span>
        </div>
      )}
    </div>
  );
}
