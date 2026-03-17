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
      className="group relative overflow-hidden rounded-xl p-5 transition-all duration-300 hover:translate-y-[-2px]"
      style={{
        background: "#141210",
        border: "1px solid #1e1c18",
        boxShadow: "0 0 0 0 rgba(245, 158, 11, 0)",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = `0 8px 32px -12px ${accent}40`;
        e.currentTarget.style.borderColor = `${accent}30`;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = "0 0 0 0 rgba(245, 158, 11, 0)";
        e.currentTarget.style.borderColor = "#1e1c18";
      }}
    >
      {/* Corner accent strip */}
      <div
        className="absolute left-0 top-0 h-full w-[3px] rounded-l-lg transition-all duration-300"
        style={{ background: accent }}
      />

      {/* Background glow */}
      <div
        className="absolute -right-8 -top-8 h-24 w-24 rounded-full opacity-0 transition-opacity duration-500 group-hover:opacity-100"
        style={{ background: `radial-gradient(circle, ${accent}15 0%, transparent 70%)` }}
      />

      <div className="relative flex items-start justify-between">
        <div>
          <div
            className="text-[8px] tracking-[0.25em] uppercase mb-2"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
          >
            {code} / {label}
          </div>
          <div
            className="text-[40px] font-bold leading-none tabular-nums transition-colors duration-300"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#e8e0d5" }}
          >
            {value.toString().padStart(2, "0")}
          </div>
        </div>
        <div
          className="flex h-10 w-10 items-center justify-center rounded-lg transition-transform duration-300 group-hover:scale-110"
          style={{ background: accentBg, border: `1px solid ${accent}40` }}
        >
          <Icon className="h-5 w-5" color={accent} />
        </div>
      </div>

      {/* Bottom accent line */}
      <div
        className="absolute bottom-0 left-0 h-[1px] w-0 transition-all duration-500 group-hover:w-full"
        style={{ background: accent }}
      />
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
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <StatCard key={card.label} {...card} />
      ))}
    </div>
  );
}
