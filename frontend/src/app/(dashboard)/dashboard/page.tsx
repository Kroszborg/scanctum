"use client";

import Link from "next/link";
import { useDashboard } from "@/hooks/use-dashboard";
import { StatsCards } from "@/components/dashboard/stats-cards";
import { SeverityChart } from "@/components/dashboard/severity-chart";
import { ScanHistoryChart } from "@/components/dashboard/scan-history-chart";
import { ArrowRight, Plus } from "lucide-react";

const STATUS_DOT: Record<string, { color: string; glow: string; label: string }> = {
  pending:   { color: "#f59e0b", glow: "rgba(245,158,11,0.5)",  label: "Pending" },
  crawling:  { color: "#38bdf8", glow: "rgba(56,189,248,0.5)",  label: "Crawling" },
  scanning:  { color: "#06b6d4", glow: "rgba(6,182,212,0.5)",   label: "Scanning" },
  completed: { color: "#4ade80", glow: "rgba(74,222,128,0.5)",  label: "Completed" },
  failed:    { color: "#f43f5e", glow: "rgba(244,63,94,0.5)",   label: "Failed" },
  cancelled: { color: "#564e45", glow: "transparent",           label: "Cancelled" },
};

export default function DashboardPage() {
  const { stats, loading } = useDashboard();

  if (loading || !stats) {
    return (
      <div className="flex items-center gap-3 py-12">
        <div
          className="h-1.5 w-1.5 rounded-full animate-pulse"
          style={{ background: "#f59e0b" }}
        />
        <span
          className="text-[11px] tracking-widest uppercase"
          style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
        >
          Loading telemetry...
        </span>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-up">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <div
            className="text-[9px] tracking-[0.25em] uppercase mb-1"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
          >
            Command Center
          </div>
          <h1
            className="text-[24px] font-bold"
            style={{ color: "#e8e0d5" }}
          >
            Overview
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
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "rgba(245,158,11,0.18)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "rgba(245,158,11,0.1)";
          }}
        >
          <Plus className="h-3.5 w-3.5" />
          New Scan
        </Link>
      </div>

      {/* Stats */}
      <StatsCards stats={stats} />

      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        <SeverityChart distribution={stats.severity_distribution} />
        <ScanHistoryChart data={stats.scans_over_time} />
      </div>

      {/* Recent scans */}
      <div
        className="rounded-lg overflow-hidden"
        style={{ border: "1px solid #1e1c18" }}
      >
        {/* Table header */}
        <div
          className="flex items-center justify-between px-5 py-3"
          style={{ background: "#141210", borderBottom: "1px solid #1e1c18" }}
        >
          <span
            className="text-[9px] tracking-[0.2em] uppercase"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
          >
            Recent Scans
          </span>
          <Link
            href="/scans"
            className="flex items-center gap-1 text-[10px] tracking-wide transition-colors"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "#f59e0b")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "#4a4440")}
          >
            View all
            <ArrowRight className="h-3 w-3" />
          </Link>
        </div>

        {stats.recent_scans.length === 0 ? (
          <div
            className="flex flex-col items-center justify-center py-12 gap-3"
            style={{ background: "#0c0a08" }}
          >
            <span
              className="text-[11px] tracking-widest uppercase"
              style={{ fontFamily: "JetBrains Mono, monospace", color: "#2c2820" }}
            >
              No scans initiated
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
          <div style={{ background: "#0c0a08" }}>
            {stats.recent_scans.map((scan, i) => {
              const dot = STATUS_DOT[scan.status] ?? STATUS_DOT.cancelled;
              return (
                <Link
                  key={scan.id}
                  href={`/scans/${scan.id}`}
                  className="flex items-center gap-4 px-5 py-3.5 transition-colors group"
                  style={{
                    borderBottom: i < stats.recent_scans.length - 1 ? "1px solid #1e1c18" : "none",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "#141210")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                >
                  {/* Status dot */}
                  <span
                    className="h-1.5 w-1.5 shrink-0 rounded-full"
                    style={{
                      background: dot.color,
                      boxShadow: `0 0 6px 1px ${dot.glow}`,
                    }}
                  />

                  {/* URL */}
                  <span
                    className="flex-1 text-[12px] font-medium truncate transition-colors"
                    style={{ color: "#8a7f74" }}
                  >
                    {scan.target_url}
                  </span>

                  {/* Meta */}
                  <div className="flex items-center gap-4 shrink-0">
                    <span
                      className="text-[10px] tabular-nums"
                      style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
                    >
                      {scan.vuln_count} findings
                    </span>
                    <span
                      className="text-[9px] tracking-widest uppercase px-1.5 py-0.5 rounded"
                      style={{
                        fontFamily: "JetBrains Mono, monospace",
                        color: dot.color,
                        background: `${dot.color}18`,
                        border: `1px solid ${dot.color}30`,
                      }}
                    >
                      {dot.label}
                    </span>
                    <span
                      className="text-[10px]"
                      style={{ fontFamily: "JetBrains Mono, monospace", color: "#2c2820" }}
                    >
                      {new Date(scan.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                    </span>
                    <ArrowRight className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" style={{ color: "#f59e0b" }} />
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
