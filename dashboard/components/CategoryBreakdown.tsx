"use client";

/**
 * Category breakdown with animated horizontal bars
 */

import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { useStats } from '@/hooks/useApi';

const CATEGORY_STYLES: Record<string, { bar: string; dot: string; label: string }> = {
  fruit: { bar: 'bg-emerald-500', dot: 'bg-emerald-400', label: 'text-emerald-400' },
  snack: { bar: 'bg-orange-500', dot: 'bg-orange-400', label: 'text-orange-400' },
  drink: { bar: 'bg-blue-500', dot: 'bg-blue-400', label: 'text-blue-400' },
  hygiene: { bar: 'bg-purple-500', dot: 'bg-purple-400', label: 'text-purple-400' },
};

const DEFAULT_STYLE = { bar: 'bg-slate-500', dot: 'bg-slate-400', label: 'text-slate-400' };

export default function CategoryBreakdown() {
  const { data: stats, isLoading } = useStats();

  const categoryData = useMemo(() => {
    if (!stats) return [];
    const total = stats.total_items;
    if (total === 0) return [];
    return Object.entries(stats.by_category)
      .map(([category, count]) => ({
        category,
        count,
        percentage: (count / total) * 100,
      }))
      .sort((a, b) => b.count - a.count);
  }, [stats]);

  if (isLoading || !stats) {
    return (
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 border border-slate-700/30 h-full">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-white text-base font-semibold" style={{ fontFamily: 'var(--font-heading)' }}>Categories</h3>
        </div>
        <div className="space-y-5 animate-pulse">
          {[1, 2, 3].map((i) => (
            <div key={i}>
              <div className="h-3 bg-slate-700 rounded w-20 mb-2" />
              <div className="h-2 bg-slate-700 rounded w-full" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (categoryData.length === 0) {
    return (
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 border border-slate-700/30 h-full">
        <h3 className="text-white text-base font-semibold mb-6" style={{ fontFamily: 'var(--font-heading)' }}>Categories</h3>
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <svg className="w-10 h-10 text-slate-600 mb-3" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25a2.25 2.25 0 0 1-2.25-2.25v-2.25Z" />
          </svg>
          <p className="text-slate-500 text-sm">No donations yet</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 border border-slate-700/30 h-full">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-white text-base font-semibold" style={{ fontFamily: 'var(--font-heading)' }}>Categories</h3>
        <span className="text-slate-500 text-xs">{stats.total_items} total</span>
      </div>
      <div className="space-y-5">
        {categoryData.map(({ category, count, percentage }) => {
          const styles = CATEGORY_STYLES[category] || DEFAULT_STYLE;
          return (
            <div key={category}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${styles.dot}`} />
                  <span className="text-slate-200 capitalize text-sm font-medium">{category}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-slate-400 text-xs tabular-nums">{count}</span>
                  <span className="text-slate-600 text-xs">({percentage.toFixed(0)}%)</span>
                </div>
              </div>
              <div className="w-full bg-slate-700/50 rounded-full h-1.5 overflow-hidden">
                <motion.div
                  className={`${styles.bar} h-full rounded-full`}
                  initial={{ width: 0 }}
                  animate={{ width: `${percentage}%` }}
                  transition={{ duration: 0.8, ease: 'easeOut' }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
