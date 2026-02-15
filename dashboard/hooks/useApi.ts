/**
 * SWR hooks for Project Lend API with automatic deduplication
 * Implements Vercel best practice: client-swr-dedup
 */

import useSWR from 'swr';
import type { Donation, Stats, PipelineState } from '@/lib/types';
import { endpoints, fetcher } from '@/lib/api';

/**
 * Hook for fetching donation statistics
 * Refreshes every 2 seconds, deduplicates requests within 1 second
 */
export function useStats() {
  return useSWR<Stats>(endpoints.stats, fetcher, {
    refreshInterval: 2000,
    dedupingInterval: 1000,
  });
}

/**
 * Hook for fetching recent donations
 * Refreshes every 2 seconds, deduplicates requests within 1 second
 */
export function useRecentDonations(limit: number = 10) {
  return useSWR<Donation[]>(endpoints.recentDonations(limit), fetcher, {
    refreshInterval: 2000,
    dedupingInterval: 1000,
  });
}

/**
 * Hook for fetching pipeline state
 * Refreshes every 1 second, deduplicates requests within 500ms
 */
export function usePipelineState() {
  return useSWR<PipelineState>(endpoints.state, fetcher, {
    refreshInterval: 1000,
    dedupingInterval: 500,
  });
}
