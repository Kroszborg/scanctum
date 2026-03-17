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
      className="rounded-xl p-5 transition-all duration-300"
      style={{
        background: "#141210",
        border: "1px solid #1e1c18",
        boxShadow: "0 0 0 0 rgba(245, 158, 11, 0)",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = "0 8px 32px -12px rgba(245, 158, 11, 0.15)";
        e.currentTarget.style.borderColor = "rgba(245, 158, 11, 0.3)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = "0 0 0 0 rgba(245, 158, 11, 0)";
        e.currentTarget.style.borderColor = "#1e1c18";
      }}
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
        <div
          className="flex h-8 w-8 items-center justify-center rounded-lg"
          style={{
            background: "rgba(245, 158, 11, 0.08)",
            border: "1px solid rgba(245, 158, 11, 0.2)",
          }}
        >
          <svg
            className="h-4 w-4"
            style={{ color: "#f59e0b" }}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
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
        <div className="space-y-3">
          {ROWS.map((row) => {
            const count = distribution[row.key] ?? 0;
            const pct = total > 0 ? (count / total) * 100 : 0;
            return (
              <div
                key={row.key}
                className="group flex items-center gap-3 transition-all duration-300 hover:translate-x-1"
              >
                <div
                  className="text-[9px] w-12 shrink-0 text-right tabular-nums uppercase tracking-wide"
                  style={{
                    fontFamily: "JetBrains Mono, monospace",
                    color: count > 0 ? row.color : "#2c2820",
                  }}
                >
                  {row.label}
                </div>
                <div
                  className="relative flex-1 h-5 rounded-md overflow-hidden transition-all duration-300"
                  style={{
                    background: "#1c1916",
                    boxShadow: count > 0 ? "inset 0 2px 4px rgba(0,0,0,0.3)" : "none",
                  }}
                >
                  <div
                    className="h-full rounded-md transition-all duration-700 ease-out relative overflow-hidden"
                    style={{
                      width: `${pct}%`,
                      background: `linear-gradient(90deg, ${row.bg} 0%, ${row.bg}80 100%)`,
                      borderRight: count > 0 ? `1px solid ${row.color}60` : "none",
                    }}
                  >
                    <div
                      className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                      style={{
                        background: `linear-gradient(90deg, transparent 0%, ${row.color}20 50%, transparent 100%)`,
                        backgroundSize: "200% 100%",
                      }}
                    />
                  </div>
                </div>
                <div
                  className="text-[11px] w-7 shrink-0 tabular-nums text-right font-medium"
                  style={{
                    fontFamily: "JetBrains Mono, monospace",
                    color: count > 0 ? "#e8e0d5" : "#2c2820",
                  }}
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
