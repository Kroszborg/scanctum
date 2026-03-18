"use client";

import { Scan, AlertTriangle, Shield, Activity } from "lucide-react";
import type { DashboardStats } from "@/types/dashboard";
import { motion } from "framer-motion";

interface StatCardProps {
  label: string;
  value: number;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  accent: string;
  gradient: string;
  code: string;
}

function StatCard({ label, value, icon: Icon, accent, gradient, code }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4, scale: 1.02 }}
      transition={{ duration: 0.3, ease: [0.23, 0.86, 0.39, 0.96] }}
      className="group relative overflow-hidden rounded-2xl p-6"
      style={{
        background: "rgba(20, 20, 20, 0.6)",
        backdropFilter: "blur(12px)",
        border: "1px solid rgba(255, 255, 255, 0.06)",
        boxShadow: "0 0 0 0 rgba(124, 58, 237, 0)",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = `0 12px 40px -16px ${accent}60`;
        e.currentTarget.style.borderColor = `${accent}40`;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = "0 0 0 0 rgba(124, 58, 237, 0)";
        e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.06)";
      }}
    >
      {/* Animated gradient orb */}
      <div
        className="absolute -right-12 -top-12 h-40 w-40 rounded-full opacity-0 transition-opacity duration-700 group-hover:opacity-100 blur-3xl"
        style={{ background: `radial-gradient(circle, ${accent}20 0%, transparent 70%)` }}
      />

      {/* Gradient border accent */}
      <div className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
        <div className="absolute bottom-0 left-0 right-0 h-[1px]" style={{ background: `linear-gradient(90deg, transparent, ${accent}, transparent)` }} />
      </div>

      <div className="relative">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div>
            <div
              className="text-[8px] tracking-[0.3em] uppercase mb-1.5"
              style={{ fontFamily: "JetBrains Mono, monospace", color: "#737373" }}
            >
              {code} / {label}
            </div>
            <div
              className="text-4xl font-light leading-none tabular-nums"
              style={{ fontFamily: "Libre Caslon Text, serif", color: "#F5F5F5" }}
            >
              {value.toString().padStart(2, "0")}
            </div>
          </div>

          {/* Icon with gradient background */}
          <div
            className="flex h-12 w-12 items-center justify-center rounded-xl transition-all duration-500 group-hover:scale-110 group-hover:rotate-3"
            style={{
              background: `linear-gradient(135deg, ${accent}15 0%, ${accent}05 100%)`,
              border: `1px solid ${accent}30`,
            }}
          >
            <Icon className="h-5 w-5" stroke={accent} strokeWidth={1.5} />
          </div>
        </div>

        {/* Bottom gradient line */}
        <div className="relative h-px w-full bg-white/5">
          <div
            className="absolute left-0 top-0 h-full w-0 bg-gradient-to-r from-transparent via-current to-transparent transition-all duration-700 group-hover:w-full opacity-50"
            style={{ color: accent }}
          />
        </div>
      </div>
    </motion.div>
  );
}

export function StatsCards({ stats }: { stats: DashboardStats }) {
  const cards = [
    {
      label: "Total Scans",
      value: stats.total_scans,
      icon: Scan,
      accent: "#38bdf8",
      gradient: "from-sky-500/20 to-cyan-500/20",
      code: "01",
    },
    {
      label: "Active Scans",
      value: stats.active_scans,
      icon: Activity,
      accent: "#22c55e",
      gradient: "from-green-500/20 to-emerald-500/20",
      code: "02",
    },
    {
      label: "Vulnerabilities",
      value: stats.total_vulnerabilities,
      icon: AlertTriangle,
      accent: "#f97316",
      gradient: "from-orange-500/20 to-amber-500/20",
      code: "03",
    },
    {
      label: "Critical Issues",
      value: stats.critical_count,
      icon: Shield,
      accent: "#ef4444",
      gradient: "from-red-500/20 to-rose-500/20",
      code: "04",
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {cards.map((card, index) => (
        <StatCard key={card.label} {...card} />
      ))}
    </div>
  );
}
