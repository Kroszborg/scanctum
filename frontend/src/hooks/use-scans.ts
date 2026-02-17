"use client";

import { useState, useEffect, useCallback } from "react";
import api from "@/lib/api";
import type { Scan, ScanCreate } from "@/types/scan";
import type { Vulnerability } from "@/types/vulnerability";

export function useScans() {
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchScans = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get<Scan[]>("/scans");
      setScans(res.data);
    } catch {
      // Error handled by interceptor
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchScans(); }, [fetchScans]);

  const createScan = async (data: ScanCreate): Promise<Scan> => {
    const res = await api.post<Scan>("/scans", data);
    await fetchScans();
    return res.data;
  };

  const cancelScan = async (id: string) => {
    await api.post(`/scans/${id}/cancel`);
    await fetchScans();
  };

  return { scans, loading, fetchScans, createScan, cancelScan };
}

export function useScan(id: string) {
  const [scan, setScan] = useState<Scan | null>(null);
  const [results, setResults] = useState<Vulnerability[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchScan = useCallback(async () => {
    try {
      const [scanRes, resultsRes] = await Promise.all([
        api.get<Scan>(`/scans/${id}`),
        api.get<Vulnerability[]>(`/scans/${id}/results`),
      ]);
      setScan(scanRes.data);
      setResults(resultsRes.data);
    } catch {
      // Error handled by interceptor
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { fetchScan(); }, [fetchScan]);

  return { scan, results, loading, refetch: fetchScan };
}
