"use client";

import Link from "next/link";
import { useScans } from "@/hooks/use-scans";
import { Plus, ArrowRight } from "lucide-react";

const STATUS_CONFIG: Record<string, { color: string; glow: string; label: string; badgeCls: string }> = {
  pending:   { color: "#f59e0b", glow: "rgba(245,158,11,0.5)",  label: "Pending",   badgeCls: "badge-pending" },
  crawling:  { color: "#38bdf8", glow: "rgba(56,189,248,0.5)",  label: "Crawling",  badgeCls: "badge-crawling" },
  scanning:  { color: "#06b6d4", glow: "rgba(6,182,212,0.5)",   label: "Scanning",  badgeCls: "badge-scanning" },
  completed: { color: "#4ade80", glow: "rgba(74,222,128,0.5)",  label: "Completed", badgeCls: "badge-completed" },
  failed:    { color: "#f43f5e", glow: "rgba(244,63,94,0.5)",   label: "Failed",    badgeCls: "badge-failed" },
  cancelled: { color: "#564e45", glow: "transparent",           label: "Cancelled", badgeCls: "badge-cancelled" },
};

export default function ScansPage() {
  const { scans, loading } = useScans();

  return (
    <div className="space-y-6 animate-fade-up">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div
            className="text-[9px] tracking-[0.25em] uppercase mb-1"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
          >
            Assessment Queue
          </div>
          <h1
            className="text-[24px] font-bold"
            style={{ color: "#e8e0d5" }}
          >
            Scans
          </h1>
        </div>
        <Link
          href="/scans/new"
          className="flex items-center gap-2 rounded px-4 py-2 text-[11px] font-semibold tracking-widest uppercase transition-all"
          style={{
            fontFamily: "JetBrains Mono, monospace",
            background: "rgba(245,158,11,0.1)",
            border: "1px solid rgba(245,158,11,0.3)",
            color: "#f59e0b",
          }}
          onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(245,158,11,0.18)"; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = "rgba(245,158,11,0.1)"; }}
        >
          <Plus className="h-3.5 w-3.5" />
          New Scan
        </Link>
      </div>

      {/* Table */}
      <div
        className="rounded-lg overflow-hidden"
        style={{ border: "1px solid #1e1c18" }}
      >
        {/* Column headers */}
        <div
          className="grid grid-cols-[1fr_80px_110px_60px_90px_28px] items-center px-5 py-2.5 gap-4"
          style={{
            background: "#141210",
            borderBottom: "1px solid #1e1c18",
          }}
        >
          {["Target URL", "Mode", "Status", "Prog.", "Date", ""].map((h) => (
            <span
              key={h}
              className="text-[9px] tracking-[0.15em] uppercase"
              style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
            >
              {h}
            </span>
          ))}
        </div>

        {/* Rows */}
        <div style={{ background: "#0c0a08" }}>
          {loading ? (
            <div className="flex items-center gap-3 px-5 py-8">
              <div
                className="h-1.5 w-1.5 rounded-full animate-pulse"
                style={{ background: "#f59e0b" }}
              />
              <span
                className="text-[11px] tracking-widest uppercase"
                style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
              >
                Loading scans...
              </span>
            </div>
          ) : scans.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 gap-3">
              <span
                className="text-[11px] tracking-widest uppercase"
                style={{ fontFamily: "JetBrains Mono, monospace", color: "#2c2820" }}
              >
                No scans yet
              </span>
              <Link
                href="/scans/new"
                className="text-[10px] transition-colors"
                style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
                onMouseEnter={(e) => (e.currentTarget.style.color = "#f59e0b")}
                onMouseLeave={(e) => (e.currentTarget.style.color = "#4a4440")}
              >
                Initiate your first scan →
              </Link>
            </div>
          ) : (
            scans.map((scan, i) => {
              const cfg = STATUS_CONFIG[scan.status] ?? STATUS_CONFIG.cancelled;
              return (
                <Link
                  key={scan.id}
                  href={`/scans/${scan.id}`}
                  className="grid grid-cols-[1fr_80px_110px_60px_90px_28px] items-center px-5 py-3.5 gap-4 group transition-colors"
                  style={{
                    borderBottom: i < scans.length - 1 ? "1px solid #1e1c18" : "none",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "#141210")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                >
                  {/* Target */}
                  <div className="flex items-center gap-2.5 min-w-0">
                    <span
                      className="h-1.5 w-1.5 shrink-0 rounded-full"
                      style={{
                        background: cfg.color,
                        boxShadow: `0 0 5px 1px ${cfg.glow}`,
                      }}
                    />
                    <span
                      className="text-[12px] font-medium truncate"
                      style={{ color: "#8a7f74" }}
                    >
                      {scan.target_url}
                    </span>
                  </div>

                  {/* Mode */}
                  <span
                    className="text-[10px] tracking-widest uppercase"
                    style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
                  >
                    {scan.scan_mode}
                  </span>

                  {/* Status badge */}
                  <span
                    className={`text-[9px] tracking-widest uppercase px-1.5 py-0.5 rounded inline-block ${cfg.badgeCls}`}
                    style={{ fontFamily: "JetBrains Mono, monospace" }}
                  >
                    {cfg.label}
                  </span>

                  {/* Progress */}
                  <span
                    className="text-[11px] tabular-nums"
                    style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
                  >
                    {scan.progress_percent}%
                  </span>

                  {/* Date */}
                  <span
                    className="text-[10px]"
                    style={{ fontFamily: "JetBrains Mono, monospace", color: "#2c2820" }}
                  >
                    {new Date(scan.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                  </span>

                  {/* Arrow */}
                  <ArrowRight
                    className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity"
                    style={{ color: "#f59e0b" }}
                  />
                </Link>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
