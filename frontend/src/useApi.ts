import { useEffect, useState, useCallback } from "react";
import type { Stats, Donation, PipelineState } from "./types";

const API = import.meta.env.VITE_API_URL || "http://localhost:5001";

export function useApi(intervalMs = 800) {
  const [stats, setStats] = useState<Stats | null>(null);
  const [donations, setDonations] = useState<Donation[]>([]);
  const [pipeline, setPipeline] = useState<PipelineState | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    try {
      const [s, d, p] = await Promise.all([
        fetch(`${API}/stats`).then((r) => r.json()),
        fetch(`${API}/donations`).then((r) => r.json()),
        fetch(`${API}/pipeline/state`).then((r) => r.json()),
      ]);
      setStats(s);
      setDonations(d);
      setPipeline(p);
      setError(null);
    } catch {
      setError("Unable to connect to API. Make sure python api.py is running.");
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const id = setInterval(fetchAll, intervalMs);
    return () => clearInterval(id);
  }, [fetchAll, intervalMs]);

  return { stats, donations, pipeline, error };
}

export const API_BASE = API;
