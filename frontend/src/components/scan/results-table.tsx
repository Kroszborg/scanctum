"use client";

import { useState } from "react";
import { OWASP_LABELS } from "@/lib/constants";
import { VulnDetailDialog } from "@/components/scan/vuln-card";
import type { Vulnerability } from "@/types/vulnerability";

const SEV_CONFIG: Record<string, { color: string; bg: string; border: string; cls: string }> = {
  critical: { color: "#f43f5e", bg: "rgba(244,63,94,0.08)",  border: "rgba(244,63,94,0.25)",  cls: "badge-critical" },
  high:     { color: "#fb923c", bg: "rgba(251,146,60,0.08)", border: "rgba(251,146,60,0.25)", cls: "badge-high" },
  medium:   { color: "#f59e0b", bg: "rgba(245,158,11,0.08)", border: "rgba(245,158,11,0.25)", cls: "badge-medium" },
  low:      { color: "#4ade80", bg: "rgba(74,222,128,0.08)", border: "rgba(74,222,128,0.25)", cls: "badge-low" },
  info:     { color: "#38bdf8", bg: "rgba(56,189,248,0.08)", border: "rgba(56,189,248,0.25)", cls: "badge-info" },
};

const FILTERS = ["all", "critical", "high", "medium", "low", "info"] as const;

export function ResultsTable({ results }: { results: Vulnerability[] }) {
  const [selected, setSelected] = useState<Vulnerability | null>(null);
  const [filter, setFilter] = useState<string>("all");

  const filtered = filter === "all" ? results : results.filter((v) => v.severity === filter);

  return (
    <div className="space-y-4">
      {/* Filter pills */}
      <div className="flex flex-wrap gap-1.5">
        {FILTERS.map((sev) => {
          const isActive = filter === sev;
          const cfg = sev !== "all" ? SEV_CONFIG[sev] : null;
          const count = sev === "all" ? results.length : results.filter((v) => v.severity === sev).length;

          return (
            <button
              key={sev}
              onClick={() => setFilter(sev)}
              className="flex items-center gap-1.5 rounded px-2.5 py-1 text-[10px] tracking-widest uppercase transition-all"
              style={{
                fontFamily: "JetBrains Mono, monospace",
                background: isActive
                  ? cfg ? cfg.bg : "rgba(245,158,11,0.1)"
                  : "transparent",
                border: isActive
                  ? `1px solid ${cfg ? cfg.border : "rgba(245,158,11,0.3)"}`
                  : "1px solid #1e1c18",
                color: isActive
                  ? cfg ? cfg.color : "#f59e0b"
                  : "#4a4440",
                cursor: "pointer",
              }}
              onMouseEnter={(e) => {
                if (!isActive) e.currentTarget.style.borderColor = "#2c2820";
                if (!isActive) e.currentTarget.style.color = "#8a7f74";
              }}
              onMouseLeave={(e) => {
                if (!isActive) e.currentTarget.style.borderColor = "#1e1c18";
                if (!isActive) e.currentTarget.style.color = "#4a4440";
              }}
            >
              {sev === "all" ? "All" : sev}
              <span
                className="tabular-nums"
                style={{ color: isActive ? "inherit" : "#2c2820" }}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Table */}
      <div
        className="rounded-lg overflow-hidden"
        style={{ border: "1px solid #1e1c18" }}
      >
        {/* Column headers */}
        <div
          className="grid grid-cols-[90px_1fr_60px_60px_1fr_80px] px-4 py-2.5 gap-3"
          style={{ background: "#141210", borderBottom: "1px solid #1e1c18" }}
        >
          {["Severity", "Vulnerability", "CVSS", "OWASP", "URL", "Confidence"].map((h) => (
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
          {filtered.length === 0 ? (
            <div
              className="flex items-center justify-center py-12 text-[11px] tracking-widest uppercase"
              style={{ fontFamily: "JetBrains Mono, monospace", color: "#2c2820" }}
            >
              No findings
            </div>
          ) : (
            filtered.map((vuln, i) => {
              const cfg = SEV_CONFIG[vuln.severity] ?? SEV_CONFIG.info;
              return (
                <div
                  key={vuln.id}
                  className="grid grid-cols-[90px_1fr_60px_60px_1fr_80px] items-center px-4 py-3 gap-3 cursor-pointer transition-colors"
                  style={{
                    borderBottom: i < filtered.length - 1 ? "1px solid #1e1c18" : "none",
                    borderLeft: `2px solid ${cfg.color}40`,
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "#141210")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                  onClick={() => setSelected(vuln)}
                >
                  {/* Severity */}
                  <span
                    className={`text-[9px] tracking-widest uppercase px-1.5 py-0.5 rounded inline-block ${cfg.cls}`}
                    style={{ fontFamily: "JetBrains Mono, monospace" }}
                  >
                    {vuln.severity}
                  </span>

                  {/* Vuln type */}
                  <span className="text-[12px] font-medium truncate" style={{ color: "#8a7f74" }}>
                    {vuln.vuln_type}
                  </span>

                  {/* CVSS */}
                  <span
                    className="text-[11px] tabular-nums font-bold"
                    style={{ fontFamily: "JetBrains Mono, monospace", color: cfg.color }}
                  >
                    {vuln.cvss_score}
                  </span>

                  {/* OWASP */}
                  <span
                    className="text-[10px] tabular-nums"
                    style={{ fontFamily: "JetBrains Mono, monospace", color: "#6b6259" }}
                    title={OWASP_LABELS[vuln.owasp_category]}
                  >
                    {vuln.owasp_category}
                  </span>

                  {/* URL */}
                  <span className="text-[11px] truncate" style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}>
                    {vuln.affected_url}
                  </span>

                  {/* Confidence */}
                  <span className="text-[10px] capitalize" style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}>
                    {vuln.confidence}
                  </span>
                </div>
              );
            })
          )}
        </div>
      </div>

      {selected && (
        <VulnDetailDialog vuln={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  );
}
