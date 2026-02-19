"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import type { Scan } from "@/types/scan";

type ProgressMessage = {
  type: "progress" | "done" | "ping" | "error";
  scan_id?: string;
  status?: string;
  progress?: number;
  pages_found?: number;
  pages_scanned?: number;
  error?: string;
  message?: string;
};

type UseWebSocketOptions = {
  /** Called each time a progress update is received. */
  onProgress?: (msg: ProgressMessage) => void;
  /** Called when the scan reaches a terminal state (completed/failed/cancelled). */
  onDone?: (finalStatus: string) => void;
};

const WS_BASE =
  (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1")
    .replace(/^http/, "ws")   // http → ws, https → wss
    .replace(/\/api\/v1$/, "/api/v1");  // keep prefix

/**
 * Hook that connects to the FastAPI WebSocket scan-progress endpoint.
 * Falls back to polling via `fallbackFetch` if WS fails.
 */
export function useScanWebSocket(
  scanId: string | null,
  options: UseWebSocketOptions = {},
) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [connected, setConnected] = useState(false);
  const [fallbackMode, setFallbackMode] = useState(false);

  const { onProgress, onDone } = options;
  const onProgressRef = useRef(onProgress);
  const onDoneRef = useRef(onDone);
  useEffect(() => { onProgressRef.current = onProgress; }, [onProgress]);
  useEffect(() => { onDoneRef.current = onDone; }, [onDone]);

  const disconnect = useCallback(() => {
    if (reconnectRef.current) clearTimeout(reconnectRef.current);
    if (wsRef.current) {
      wsRef.current.onclose = null; // prevent reconnect loop
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnected(false);
  }, []);

  const connect = useCallback(() => {
    if (!scanId) return;

    const url = `${WS_BASE}/ws/scans/${scanId}/progress`;

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        setFallbackMode(false);
      };

      ws.onmessage = (event) => {
        try {
          const msg: ProgressMessage = JSON.parse(event.data as string);

          if (msg.type === "ping") return; // keepalive — ignore

          if (msg.type === "error") {
            // Server indicated WS not supported → switch to polling
            setFallbackMode(true);
            ws.close();
            return;
          }

          if (msg.type === "progress") {
            onProgressRef.current?.(msg);
          }

          if (msg.type === "done" || msg.status === "completed" || msg.status === "failed") {
            onDoneRef.current?.(msg.status ?? "completed");
            disconnect();
          }
        } catch {
          // ignore malformed messages
        }
      };

      ws.onerror = () => {
        setFallbackMode(true);
      };

      ws.onclose = (event) => {
        setConnected(false);
        // Reconnect unless scan is done or tab hidden (code 1000 = normal close)
        if (event.code !== 1000 && !fallbackMode) {
          reconnectRef.current = setTimeout(connect, 3000);
        }
      };
    } catch {
      // WebSocket not available (SSR or very old browser)
      setFallbackMode(true);
    }
  }, [scanId, disconnect, fallbackMode]);

  useEffect(() => {
    if (!scanId) return;
    connect();
    return () => disconnect();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scanId]);

  return { connected, fallbackMode };
}
