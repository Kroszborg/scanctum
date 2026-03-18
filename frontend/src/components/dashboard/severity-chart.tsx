"use client";

import type { SeverityCount } from "@/types/dashboard";
import { motion } from "framer-motion";
import { AlertTriangle, Shield, Zap, TrendingDown, Info } from "lucide-react";

interface SeverityRow {
  label: string;
  key: keyof SeverityCount;
  color: string;
  gradient: string;
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
}

const ROWS: SeverityRow[] = [
  { label: "Critical", key: "critical", color: "#ef4444", gradient: "from-red-500 to-red-600", icon: AlertTriangle },
  { label: "High",     key: "high",     color: "#f97316", gradient: "from-orange-500 to-orange-600", icon: Shield },
  { label: "Medium",   key: "medium",   color: "#f59e0b", gradient: "from-amber-500 to-amber-600", icon: Zap },
  { label: "Low",      key: "low",      color: "#22c55e", gradient: "from-green-500 to-green-600", icon: TrendingDown },
  { label: "Info",     key: "info",     color: "#38bdf8", gradient: "from-sky-500 to-sky-600", icon: Info },
];

export function SeverityChart({ distribution }: { distribution: SeverityCount }) {
  const total = ROWS.reduce((sum, r) => sum + (distribution[r.key] ?? 0), 0);

  return (
    <div className="h-full">
      {total === 0 ? (
        <div className="flex h-[200px] flex-col items-center justify-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-purple-500/10 to-cyan-500/10 border border-purple-500/20">
            <Shield className="h-6 w-6 text-neutral-600" />
          </div>
          <p className="text-sm text-neutral-500" style={{ fontFamily: "Manrope, sans-serif" }}>
            No vulnerabilities detected
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Total count */}
          <div className="mb-6 flex items-center gap-3">
            <div
              className="text-3xl font-light"
              style={{ fontFamily: "Libre Caslon Text, serif", color: "#F5F5F5" }}
            >
              {total}
            </div>
            <span className="text-sm text-neutral-500" style={{ fontFamily: "Manrope, sans-serif" }}>
              total findings
            </span>
          </div>

          {/* Severity bars */}
          <div className="space-y-3">
            {ROWS.map((row, index) => {
              const count = distribution[row.key] ?? 0;
              const pct = total > 0 ? (count / total) * 100 : 0;
              const Icon = row.icon;

              return (
                <motion.div
                  key={row.key}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1, duration: 0.4 }}
                  className="group flex items-center gap-3"
                >
                  {/* Icon */}
                  <div
                    className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg transition-all duration-300 group-hover:scale-110"
                    style={{
                      background: `${row.color}10`,
                      border: `1px solid ${row.color}30`,
                    }}
                  >
                    <Icon className="h-3.5 w-3.5" style={{ color: row.color }} />
                  </div>

                  {/* Label */}
                  <span
                    className="w-16 shrink-0 text-[10px] tracking-wider uppercase text-neutral-400 transition-colors group-hover:text-neutral-300"
                    style={{ fontFamily: "JetBrains Mono, monospace" }}
                  >
                    {row.label}
                  </span>

                  {/* Bar */}
                  <div className="relative flex-1 h-2 overflow-hidden rounded-full bg-neutral-800/50">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${pct}%` }}
                      transition={{ delay: index * 0.1 + 0.2, duration: 0.6, ease: [0.23, 0.86, 0.39, 0.96] }}
                      className="h-full rounded-full relative"
                      style={{
                        background: `linear-gradient(90deg, ${row.color}40 0%, ${row.color} 100%)`,
                      }}
                    >
                      {/* Shimmer effect on hover */}
                      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500">
                        <div
                          className="absolute inset-0 animate-shimmer"
                          style={{
                            background: `linear-gradient(90deg, transparent 0%, ${row.color}40 50%, transparent 100%)`,
                            backgroundSize: "200% 100%",
                          }}
                        />
                      </div>
                    </motion.div>
                  </div>

                  {/* Count */}
                  <span
                    className="w-8 shrink-0 text-right text-xs font-medium tabular-nums transition-colors"
                    style={{
                      fontFamily: "JetBrains Mono, monospace",
                      color: count > 0 ? "#A1A1A1" : "#404040",
                    }}
                  >
                    {count}
                  </span>
                </motion.div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
