"use client";

import { Scan, AlertTriangle, Shield, Activity } from "lucide-react";
import type { DashboardStats } from "@/types/dashboard";

interface StatCardProps {
  label: string;
  value: number;
  icon: React.ElementType;
  accent: string;
  accentBg: string;
  code: string;
}

function StatCard({ label, value, icon: Icon, accent, accentBg, code }: StatCardProps) {
  return (
    <div
      className="relative overflow-hidden rounded-lg p-5"
      style={{ background: "#141210", border: "1px solid #1e1c18" }}
    >
      {/* Corner accent strip */}
      <div
        className="absolute left-0 top-0 h-full w-[3px] rounded-l-lg"
        style={{ background: accent }}
      />

      <div className="flex items-start justify-between">
        <div>
          <div
            className="text-[9px] tracking-[0.2em] uppercase mb-3"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
          >
            {code} / {label}
          </div>
          <div
            className="text-[36px] font-bold leading-none tabular-nums"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#e8e0d5" }}
          >
            {value.toString().padStart(2, "0")}
          </div>
        </div>
        <div
          className="flex h-9 w-9 items-center justify-center rounded"
          style={{ background: accentBg, border: `1px solid ${accent}40` }}
        >
          <Icon className="h-4 w-4" style={{ color: accent }} />
        </div>
      </div>
    </div>
  );
}

export function StatsCards({ stats }: { stats: DashboardStats }) {
  const cards = [
    {
      label: "Total Scans",
      value: stats.total_scans,
      icon: Scan,
      accent: "#38bdf8",
      accentBg: "rgba(56,189,248,0.08)",
      code: "01",
    },
    {
      label: "Active Scans",
      value: stats.active_scans,
      icon: Activity,
      accent: "#4ade80",
      accentBg: "rgba(74,222,128,0.08)",
      code: "02",
    },
    {
      label: "Vulnerabilities",
      value: stats.total_vulnerabilities,
      icon: AlertTriangle,
      accent: "#fb923c",
      accentBg: "rgba(251,146,60,0.08)",
      code: "03",
    },
    {
      label: "Critical Issues",
      value: stats.critical_count,
      icon: Shield,
      accent: "#f43f5e",
      accentBg: "rgba(244,63,94,0.08)",
      code: "04",
    },
  ];

  return (
    <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <StatCard key={card.label} {...card} />
      ))}
    </div>
  );
}
