"use client";

import Link from "next/link";
import { useDashboard } from "@/hooks/use-dashboard";
import { StatsCards } from "@/components/dashboard/stats-cards";
import { SeverityChart } from "@/components/dashboard/severity-chart";
import { ScanHistoryChart } from "@/components/dashboard/scan-history-chart";
import { ArrowRight, Plus, Scan, Shield, Activity, AlertTriangle } from "lucide-react";
import { motion } from "framer-motion";

const STATUS_CONFIG: Record<string, { color: string; gradient: string; label: string; icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }> }> = {
  pending:   { color: "#f59e0b", gradient: "from-amber-500/20 to-orange-500/20", label: "Pending", icon: Scan },
  crawling:  { color: "#38bdf8", gradient: "from-sky-400/20 to-cyan-400/20", label: "Crawling", icon: Activity },
  scanning:  { color: "#06b6d4", gradient: "from-cyan-500/20 to-teal-400/20", label: "Scanning", icon: Activity },
  completed: { color: "#22c55e", gradient: "from-green-500/20 to-emerald-400/20", label: "Completed", icon: Shield },
  failed:    { color: "#ef4444", gradient: "from-red-500/20 to-rose-400/20", label: "Failed", icon: AlertTriangle },
  cancelled: { color: "#737373", gradient: "from-gray-500/10 to-neutral-500/10", label: "Cancelled", icon: Scan },
};

interface ContainerProps {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}

function FadeIn({ children, className = "", delay = 0 }: ContainerProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: [0.23, 0.86, 0.39, 0.96] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

export default function DashboardPage() {
  const { stats, loading } = useDashboard();

  if (loading || !stats) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="h-10 w-10 rounded-full border-2 border-transparent border-t-[#f59e0b] border-r-[#f59e0b]/50"
          />
          <span
            className="text-xs tracking-[0.3em] uppercase"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
          >
            Loading...
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen pb-20">
      <div className="mx-auto max-w-7xl px-6 pt-10">
        {/* Header */}
        <FadeIn>
          <div className="mb-10 flex items-end justify-between">
            <div className="space-y-2">
              <p
                className="text-[10px] tracking-[0.3em] uppercase"
                style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
              >
                Command Center
              </p>
              <h1
                className="text-4xl font-bold text-[#e8e0d5] tracking-tight"
                style={{ fontFamily: "Bricolage Grotesque, sans-serif" }}
              >
                Security Overview
              </h1>
              <p className="text-sm text-[#6b6259]">
                Real-time vulnerability detection across your assets.
              </p>
            </div>

            <Link
              href="/scans/new"
              className="group flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-semibold transition-all duration-200"
              style={{
                background: "rgba(245,158,11,0.1)",
                border: "1px solid rgba(245,158,11,0.3)",
                color: "#f59e0b",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "rgba(245,158,11,0.18)";
                e.currentTarget.style.boxShadow = "0 0 20px rgba(245,158,11,0.15)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "rgba(245,158,11,0.1)";
                e.currentTarget.style.boxShadow = "none";
              }}
            >
              <Plus className="h-4 w-4 transition-transform group-hover:rotate-90" />
              <span>New Scan</span>
            </Link>
          </div>
        </FadeIn>

        {/* Stats Grid */}
        <FadeIn delay={0.1}>
          <StatsCards stats={stats} />
        </FadeIn>

        {/* Charts Row */}
        <FadeIn delay={0.2}>
          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            <div
              className="rounded-xl p-6"
              style={{ background: "#141210", border: "1px solid #1e1c18" }}
            >
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <p
                    className="text-[9px] tracking-[0.25em] uppercase mb-1"
                    style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
                  >
                    Threat Distribution
                  </p>
                  <h3 className="text-base font-semibold text-[#e8e0d5]">
                    By Severity
                  </h3>
                </div>
                <div
                  className="flex h-8 w-8 items-center justify-center rounded-lg"
                  style={{ background: "rgba(245,158,11,0.1)", border: "1px solid rgba(245,158,11,0.2)" }}
                >
                  <AlertTriangle className="h-4 w-4" style={{ color: "#f59e0b" }} />
                </div>
              </div>
              <SeverityChart distribution={stats.severity_distribution} />
            </div>

            <div
              className="rounded-xl p-6"
              style={{ background: "#141210", border: "1px solid #1e1c18" }}
            >
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <p
                    className="text-[9px] tracking-[0.25em] uppercase mb-1"
                    style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
                  >
                    Activity Timeline
                  </p>
                  <h3 className="text-base font-semibold text-[#e8e0d5]">
                    Scans Over Time
                  </h3>
                </div>
                <div
                  className="flex h-8 w-8 items-center justify-center rounded-lg"
                  style={{ background: "rgba(56,189,248,0.1)", border: "1px solid rgba(56,189,248,0.2)" }}
                >
                  <Activity className="h-4 w-4" style={{ color: "#38bdf8" }} />
                </div>
              </div>
              <ScanHistoryChart data={stats.scans_over_time} />
            </div>
          </div>
        </FadeIn>

        {/* Recent Scans */}
        <FadeIn delay={0.3}>
          <div className="mt-6">
            <div
              className="rounded-xl overflow-hidden"
              style={{ background: "#141210", border: "1px solid #1e1c18" }}
            >
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4" style={{ borderBottom: "1px solid #1e1c18" }}>
                <div className="flex items-center gap-3">
                  <span
                    className="h-1.5 w-1.5 rounded-full bg-[#f59e0b] animate-pulse"
                  />
                  <span
                    className="text-[9px] tracking-[0.2em] uppercase"
                    style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
                  >
                    Recent Scans
                  </span>
                </div>
                <Link
                  href="/scans"
                  className="group flex items-center gap-1.5 text-xs transition-colors duration-200"
                  style={{ color: "#6b6259", fontFamily: "JetBrains Mono, monospace" }}
                  onMouseEnter={(e) => { e.currentTarget.style.color = "#f59e0b"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.color = "#6b6259"; }}
                >
                  View all
                  <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-0.5" />
                </Link>
              </div>

              {stats.recent_scans.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 px-6">
                  <div
                    className="mb-4 flex h-14 w-14 items-center justify-center rounded-xl"
                    style={{ background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.15)" }}
                  >
                    <Scan className="h-6 w-6" style={{ color: "#4a4440" }} />
                  </div>
                  <p className="text-sm text-[#6b6259]">No scans initiated yet</p>
                  <Link
                    href="/scans/new"
                    className="mt-3 text-xs transition-colors duration-200"
                    style={{ color: "#f59e0b", fontFamily: "JetBrains Mono, monospace" }}
                  >
                    Start your first scan
                  </Link>
                </div>
              ) : (
                <div>
                  {stats.recent_scans.map((scan) => {
                    const config = STATUS_CONFIG[scan.status] ?? STATUS_CONFIG.cancelled;
                    const StatusIcon = config.icon;

                    return (
                      <Link
                        key={scan.id}
                        href={`/scans/${scan.id}`}
                        className="group flex items-center gap-4 px-6 py-4 transition-colors duration-150"
                        style={{ borderBottom: "1px solid #1e1c18" }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = "rgba(245,158,11,0.03)";
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = "transparent";
                        }}
                      >
                        {/* Status indicator */}
                        <div
                          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg transition-transform duration-200 group-hover:scale-105"
                          style={{
                            background: `${config.color}10`,
                            border: `1px solid ${config.color}25`,
                          }}
                        >
                          <StatusIcon className="h-4 w-4" style={{ color: config.color }} />
                        </div>

                        {/* URL */}
                        <div className="flex-1 min-w-0">
                          <p
                            className="truncate text-sm font-medium text-[#e8e0d5]"
                          >
                            {scan.target_url}
                          </p>
                          <p
                            className="mt-0.5 text-[10px] text-[#4a4440]"
                            style={{ fontFamily: "JetBrains Mono, monospace" }}
                          >
                            {scan.scan_mode} &bull; {new Date(scan.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                          </p>
                        </div>

                        {/* Meta */}
                        <div className="flex items-center gap-5 shrink-0">
                          <div className="text-right">
                            <p
                              className="text-[9px] tracking-widest uppercase text-[#4a4440]"
                              style={{ fontFamily: "JetBrains Mono, monospace" }}
                            >
                              Findings
                            </p>
                            <p
                              className="text-sm font-semibold tabular-nums"
                              style={{
                                color: scan.vuln_count > 0 ? "#ef4444" : "#22c55e",
                                fontFamily: "JetBrains Mono, monospace",
                              }}
                            >
                              {scan.vuln_count}
                            </p>
                          </div>

                          <span
                            className="rounded-md px-2.5 py-1 text-[9px] tracking-widest uppercase"
                            style={{
                              fontFamily: "JetBrains Mono, monospace",
                              background: `${config.color}10`,
                              color: config.color,
                              border: `1px solid ${config.color}20`,
                            }}
                          >
                            {config.label}
                          </span>

                          <ArrowRight
                            className="h-4 w-4 opacity-0 -translate-x-1 transition-all duration-200 group-hover:opacity-100 group-hover:translate-x-0"
                            style={{ color: "#4a4440" }}
                          />
                        </div>
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </FadeIn>
      </div>
    </div>
  );
}
