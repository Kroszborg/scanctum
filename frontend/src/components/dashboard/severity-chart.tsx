"use client";

import type { SeverityCount } from "@/types/dashboard";

interface SeverityRow {
  label: string;
  key: keyof SeverityCount;
  color: string;
  bg: string;
}

const ROWS: SeverityRow[] = [
  { label: "Critical", key: "critical", color: "#f43f5e", bg: "rgba(244,63,94,0.15)" },
  { label: "High",     key: "high",     color: "#fb923c", bg: "rgba(251,146,60,0.15)" },
  { label: "Medium",   key: "medium",   color: "#f59e0b", bg: "rgba(245,158,11,0.15)" },
  { label: "Low",      key: "low",      color: "#4ade80", bg: "rgba(74,222,128,0.15)" },
  { label: "Info",     key: "info",     color: "#38bdf8", bg: "rgba(56,189,248,0.15)" },
];

export function SeverityChart({ distribution }: { distribution: SeverityCount }) {
  const total = ROWS.reduce((sum, r) => sum + (distribution[r.key] ?? 0), 0);

  return (
    <div
      className="rounded-lg p-5"
      style={{ background: "#141210", border: "1px solid #1e1c18" }}
    >
      <div className="mb-5 flex items-center justify-between">
        <div>
          <div
            className="text-[9px] tracking-[0.2em] uppercase"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
          >
            Severity Distribution
          </div>
          <div
            className="text-[22px] font-bold tabular-nums mt-1"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#e8e0d5" }}
          >
            {total}
            <span
              className="text-[12px] font-normal ml-1.5"
              style={{ color: "#4a4440" }}
            >
              findings
            </span>
          </div>
        </div>
      </div>

      {total === 0 ? (
        <div
          className="flex h-[120px] items-center justify-center text-[11px]"
          style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
        >
          No vulnerabilities found
        </div>
      ) : (
        <div className="space-y-2.5">
          {ROWS.map((row) => {
            const count = distribution[row.key] ?? 0;
            const pct = total > 0 ? (count / total) * 100 : 0;
            return (
              <div key={row.key} className="flex items-center gap-3">
                <div
                  className="text-[9px] w-12 shrink-0 text-right tabular-nums"
                  style={{ fontFamily: "JetBrains Mono, monospace", color: row.color }}
                >
                  {row.label}
                </div>
                <div
                  className="flex-1 h-4 rounded-sm overflow-hidden"
                  style={{ background: "#1c1916" }}
                >
                  <div
                    className="h-full rounded-sm transition-all duration-700"
                    style={{
                      width: `${pct}%`,
                      background: row.bg,
                      borderRight: count > 0 ? `2px solid ${row.color}` : "none",
                    }}
                  />
                </div>
                <div
                  className="text-[11px] w-7 shrink-0 tabular-nums text-right"
                  style={{ fontFamily: "JetBrains Mono, monospace", color: count > 0 ? "#8a7f74" : "#2c2820" }}
                >
                  {count}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
