"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import api from "@/lib/api";
import { Globe, ArrowRight, AlertTriangle } from "lucide-react";

interface AssetSummary {
  target_url: string;
  scan_count: number;
  last_scan_id: string;
  last_scan_status: string;
  last_scan_at: string | null;
  total_vulns: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  info_count: number;
  last_scan_mode: string;
}

const STATUS_STYLES: Record<string, { color: string; label: string }> = {
  completed: { color: "#4ade80", label: "Completed" },
  failed:    { color: "#f43f5e", label: "Failed"    },
  scanning:  { color: "#06b6d4", label: "Scanning"  },
  crawling:  { color: "#38bdf8", label: "Crawling"  },
  pending:   { color: "#f59e0b", label: "Pending"   },
  cancelled: { color: "#564e45", label: "Cancelled" },
};

function RiskBar({ critical, high, medium, low, info }: {
  critical: number; high: number; medium: number; low: number; info: number;
}) {
  const total = critical + high + medium + low + info;
  if (total === 0) return <span className="text-[10px]" style={{ fontFamily: "JetBrains Mono, monospace", color: "#2c2820" }}>—</span>;

  const segs = [
    { count: critical, color: "#ef4444" },
    { count: high,     color: "#f97316" },
    { count: medium,   color: "#f59e0b" },
    { count: low,      color: "#38bdf8" },
    { count: info,     color: "#374151" },
  ].filter((s) => s.count > 0);

  return (
    <div className="flex items-center gap-2">
      <div className="flex h-1.5 w-24 overflow-hidden rounded-full" style={{ background: "#1e1c18" }}>
        {segs.map((s, i) => (
          <div
            key={i}
            style={{ width: `${(s.count / total) * 100}%`, background: s.color }}
          />
        ))}
      </div>
      <span className="text-[10px] tabular-nums" style={{ fontFamily: "JetBrains Mono, monospace", color: "#6b6259" }}>
        {total}
      </span>
    </div>
  );
}

export default function AssetsPage() {
  const [assets, setAssets] = useState<AssetSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<AssetSummary[]>("/assets")
      .then((r) => setAssets(r.data))
      .catch(() => setAssets([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div
            className="text-[9px] tracking-[0.25em] uppercase mb-1"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
          >
            Reconnaissance
          </div>
          <h1 className="text-[24px] font-bold" style={{ color: "#e8e0d5" }}>
            Asset Inventory
          </h1>
        </div>
        <div
          className="flex items-center gap-2 px-3 py-1.5 rounded"
          style={{
            fontFamily: "JetBrains Mono, monospace",
            fontSize: "10px",
            color: "#4a4440",
            background: "#141210",
            border: "1px solid #1e1c18",
          }}
        >
          <Globe className="h-3 w-3" />
          {assets.length} targets
        </div>
      </div>

      {loading ? (
        <div className="flex items-center gap-3 py-12">
          <div className="h-1.5 w-1.5 rounded-full animate-pulse" style={{ background: "#f59e0b" }} />
          <span className="text-[11px] tracking-widest uppercase" style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}>
            Loading asset inventory...
          </span>
        </div>
      ) : assets.length === 0 ? (
        <div
          className="flex flex-col items-center justify-center py-16 rounded-lg gap-3"
          style={{ background: "#141210", border: "1px solid #1e1c18" }}
        >
          <Globe className="h-8 w-8" style={{ color: "#2c2820" }} />
          <span className="text-[12px]" style={{ color: "#4a4440", fontFamily: "JetBrains Mono, monospace" }}>
            No targets scanned yet
          </span>
          <Link
            href="/scans/new"
            className="text-[10px] transition-colors"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "#f59e0b")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "#4a4440")}
          >
            Start your first scan →
          </Link>
        </div>
      ) : (
        <div className="rounded-lg overflow-hidden" style={{ border: "1px solid #1e1c18" }}>
          {/* Column headers */}
          <div
            className="grid px-5 py-2.5"
            style={{
              background: "#141210",
              borderBottom: "1px solid #1e1c18",
              gridTemplateColumns: "1fr 80px 80px 120px 80px",
              gap: "12px",
            }}
          >
            {["Target", "Scans", "Risk", "Last Scan", "Status"].map((h) => (
              <span
                key={h}
                className="text-[9px] tracking-[0.2em] uppercase"
                style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
              >
                {h}
              </span>
            ))}
          </div>

          {assets.map((asset, i) => {
            const status = STATUS_STYLES[asset.last_scan_status] ?? STATUS_STYLES.cancelled;
            const hasCritical = asset.critical_count > 0;
            const hasHigh = asset.high_count > 0;

            return (
              <Link
                key={asset.target_url}
                href={`/scans/${asset.last_scan_id}`}
                className="grid items-center px-5 py-3.5 transition-colors"
                style={{
                  gridTemplateColumns: "1fr 80px 80px 120px 80px",
                  gap: "12px",
                  background: "#0c0a08",
                  borderBottom: i < assets.length - 1 ? "1px solid #1e1c18" : "none",
                  display: "grid",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = "#141210")}
                onMouseLeave={(e) => (e.currentTarget.style.background = "#0c0a08")}
              >
                {/* Target URL */}
                <div className="flex items-center gap-2 min-w-0">
                  {(hasCritical || hasHigh) && (
                    <AlertTriangle
                      className="h-3 w-3 shrink-0"
                      style={{ color: hasCritical ? "#ef4444" : "#f97316" }}
                    />
                  )}
                  <div className="min-w-0">
                    <div className="text-[12px] font-medium truncate" style={{ color: "#e8e0d5" }}>
                      {asset.target_url}
                    </div>
                    <div
                      className="text-[9px] mt-0.5"
                      style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
                    >
                      {asset.last_scan_mode} mode
                    </div>
                  </div>
                </div>

                {/* Scan count */}
                <span
                  className="text-[12px] tabular-nums"
                  style={{ fontFamily: "JetBrains Mono, monospace", color: "#6b6259" }}
                >
                  {asset.scan_count}
                </span>

                {/* Risk bar */}
                <RiskBar
                  critical={asset.critical_count}
                  high={asset.high_count}
                  medium={asset.medium_count}
                  low={asset.low_count}
                  info={asset.info_count}
                />

                {/* Last scan date */}
                <span
                  className="text-[10px]"
                  style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
                >
                  {asset.last_scan_at
                    ? new Date(asset.last_scan_at).toLocaleDateString("en-US", {
                        month: "short", day: "numeric", year: "numeric",
                      })
                    : "—"}
                </span>

                {/* Status badge */}
                <div className="flex items-center justify-between">
                  <span
                    className="text-[9px] tracking-widest uppercase px-1.5 py-0.5 rounded"
                    style={{
                      fontFamily: "JetBrains Mono, monospace",
                      color: status.color,
                      background: `${status.color}18`,
                      border: `1px solid ${status.color}30`,
                    }}
                  >
                    {status.label}
                  </span>
                  <ArrowRight className="h-3 w-3" style={{ color: "#2c2820" }} />
                </div>
              </Link>
            );
          })}
        </div>
      )}

      {/* Severity legend */}
      {assets.length > 0 && (
        <div
          className="flex items-center gap-5 px-4 py-3 rounded-lg"
          style={{ background: "#141210", border: "1px solid #1e1c18" }}
        >
          <span className="text-[9px] tracking-widest uppercase" style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}>
            Risk Bar
          </span>
          {[
            { label: "Critical", color: "#ef4444" },
            { label: "High", color: "#f97316" },
            { label: "Medium", color: "#f59e0b" },
            { label: "Low", color: "#38bdf8" },
            { label: "Info", color: "#374151" },
          ].map(({ label, color }) => (
            <div key={label} className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-sm" style={{ background: color }} />
              <span className="text-[9px]" style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}>
                {label}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
