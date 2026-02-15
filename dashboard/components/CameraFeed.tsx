"use client";

/**
 * Live MJPEG camera feed with pipeline state overlay
 */

import { usePipelineState } from '@/hooks/useApi';
import { endpoints } from '@/lib/api';

const STATE_COLORS: Record<string, string> = {
  IDLE: 'bg-slate-500',
  WARMUP: 'bg-amber-500',
  WATCHING: 'bg-emerald-500',
  SETTLING: 'bg-orange-500',
  CLASSIFYING: 'bg-blue-500',
  COOLDOWN: 'bg-purple-500',
};

const STATE_LABELS: Record<string, string> = {
  IDLE: 'Idle',
  WARMUP: 'Warming Up',
  WATCHING: 'Watching',
  SETTLING: 'Settling',
  CLASSIFYING: 'Classifying',
  COOLDOWN: 'Cooldown',
};

const CATEGORY_COLORS: Record<string, string> = {
  fruit: 'bg-emerald-500',
  snack: 'bg-orange-500',
  drink: 'bg-blue-500',
  hygiene: 'bg-purple-500',
};

export default function CameraFeed() {
  const { data: state } = usePipelineState();

  return (
    <div className="relative w-full aspect-video bg-slate-900 rounded-2xl overflow-hidden border border-slate-700/30">
      {/* MJPEG Stream */}
      <img
        src={endpoints.videoFeed}
        alt="Live camera feed"
        className="w-full h-full object-contain"
      />

      {/* State Indicator Overlay */}
      {state && (
        <>
          <div className="absolute top-3 left-3 flex items-center gap-2 bg-black/50 backdrop-blur-md px-3 py-1.5 rounded-lg">
            <div className={`w-2 h-2 rounded-full ${STATE_COLORS[state.state] || 'bg-slate-500'} ${state.state === 'WATCHING' ? 'animate-pulse' : ''}`} />
            <span className="text-white font-medium text-xs">
              {STATE_LABELS[state.state] || state.state}
            </span>
          </div>

          {/* Motion Area Indicator */}
          {state.motion_area > 0 && (
            <div className="absolute top-3 right-3 bg-black/50 backdrop-blur-md px-3 py-1.5 rounded-lg">
              <span className="text-slate-300 text-xs tabular-nums">
                {Math.round(state.motion_area).toLocaleString()} px²
              </span>
            </div>
          )}

          {/* Cooldown Timer */}
          {state.state === 'COOLDOWN' && state.cooldown_remaining > 0 && (
            <div className="absolute top-12 right-3 bg-purple-500/80 backdrop-blur-md px-3 py-1.5 rounded-lg">
              <span className="text-white font-medium text-xs tabular-nums">
                {state.cooldown_remaining.toFixed(1)}s
              </span>
            </div>
          )}

          {/* Last Detected Item */}
          {state.last_item && (
            <div className="absolute bottom-3 left-3 right-3 bg-black/60 backdrop-blur-md px-4 py-3 rounded-xl">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-[10px] uppercase tracking-wider font-medium">Last Detected</p>
                  <p className="text-white font-semibold text-sm mt-0.5">{state.last_item}</p>
                </div>
                {state.last_category && (
                  <span className={`${CATEGORY_COLORS[state.last_category] || 'bg-slate-500'} text-white px-2.5 py-1 rounded-lg text-xs font-medium capitalize`}>
                    {state.last_category}
                  </span>
                )}
              </div>
            </div>
          )}
        </>
      )}

      {/* Offline Indicator */}
      {state && !state.camera_active && (
        <div className="absolute inset-0 bg-slate-900/90 flex items-center justify-center">
          <div className="text-center">
            <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-slate-800 flex items-center justify-center border border-slate-700/50">
              <svg className="w-6 h-6 text-slate-500" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z" />
              </svg>
            </div>
            <p className="text-slate-400 font-medium text-sm">Camera Offline</p>
            <p className="text-slate-600 text-xs mt-1">Run main.py to start the pipeline</p>
          </div>
        </div>
      )}
    </div>
  );
}
