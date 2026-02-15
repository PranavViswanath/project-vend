/**
 * API client for Project Lend Flask backend
 */

import type { Donation, Stats, PipelineState } from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

/**
 * Generic fetcher for SWR
 */
export const fetcher = async (url: string) => {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  return response.json();
};

/**
 * API endpoints
 */
export const endpoints = {
  donations: `${API_URL}/donations`,
  recentDonations: (limit: number = 10) => `${API_URL}/donations/recent?limit=${limit}`,
  stats: `${API_URL}/stats`,
  state: `${API_URL}/state`,
  videoFeed: `${API_URL}/video_feed`,
};

/**
 * Fetch all donations
 */
export async function getDonations(): Promise<Donation[]> {
  return fetcher(endpoints.donations);
}

/**
 * Fetch recent donations
 */
export async function getRecentDonations(limit: number = 10): Promise<Donation[]> {
  return fetcher(endpoints.recentDonations(limit));
}

/**
 * Fetch donation statistics
 */
export async function getStats(): Promise<Stats> {
  return fetcher(endpoints.stats);
}

/**
 * Fetch current pipeline state
 */
export async function getPipelineState(): Promise<PipelineState> {
  return fetcher(endpoints.state);
}
