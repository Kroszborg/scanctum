"use client";

import type { Vulnerability } from "@/types/vulnerability";

const SEV_CONFIG: Record<string, { cls: string }> = {
  critical: { cls: "badge-critical" },
  high:     { cls: "badge-high" },
  medium:   { cls: "badge-medium" },
  low:      { cls: "badge-low" },
  info:     { cls: "badge-info" },
};

const VARIANT_CONFIG = {
  new:       { color: "#f43f5e", bg: "rgba(244,63,94,0.06)",  border: "rgba(244,63,94,0.2)",  label: "NEW" },
  fixed:     { color: "#4ade80", bg: "rgba(74,222,128,0.06)", border: "rgba(74,222,128,0.2)", label: "FIXED" },
  unchanged: { color: "#564e45", bg: "transparent",           border: "#1e1c18",              label: "SAME" },
};

interface Props {
  title: string;
  vulnerabilities: Vulnerability[];
  variant: "new" | "fixed" | "unchanged";
}

export function ComparisonSection({ title, vulnerabilities, variant }: Props) {
  const vc = VARIANT_CONFIG[variant];

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3">
        <span
          className="text-[9px] tracking-widest uppercase px-1.5 py-0.5 rounded"
          style={{
            fontFamily: "JetBrains Mono, monospace",
            color: vc.color,
            background: vc.bg,
            border: `1px solid ${vc.border}`,
          }}
        >
          {vc.label}
        </span>
        <h3
          className="text-[13px] font-semibold"
          style={{ color: "#8a7f74" }}
        >
          {title}
        </h3>
        <span
          className="text-[11px] tabular-nums"
          style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
        >
          ({vulnerabilities.length})
        </span>
      </div>

      {vulnerabilities.length === 0 ? (
        <div
          className="text-[11px] px-4 py-3 rounded"
          style={{
            fontFamily: "JetBrains Mono, monospace",
            color: "#2c2820",
            background: "#0c0a08",
            border: "1px solid #1e1c18",
          }}
        >
          None
        </div>
      ) : (
        <div className="space-y-1.5">
          {vulnerabilities.map((v) => {
            const sc = SEV_CONFIG[v.severity] ?? SEV_CONFIG.info;
            return (
              <div
                key={v.id}
                className="flex items-center gap-3 rounded px-4 py-3"
                style={{
                  background: "#141210",
                  border: "1px solid #1e1c18",
                  borderLeft: `2px solid ${vc.color}`,
                }}
              >
                <span
                  className={`text-[9px] tracking-widest uppercase px-1.5 py-0.5 rounded shrink-0 ${sc.cls}`}
                  style={{ fontFamily: "JetBrains Mono, monospace" }}
                >
                  {v.severity}
                </span>
                <span
                  className="text-[12px] font-medium flex-1 truncate"
                  style={{ color: "#8a7f74" }}
                >
                  {v.vuln_type}
                </span>
                <span
                  className="text-[10px] tabular-nums shrink-0"
                  style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
                >
                  CVSS {v.cvss_score}
                </span>
                <span
                  className="text-[10px] max-w-[180px] truncate shrink-0"
                  style={{ fontFamily: "JetBrains Mono, monospace", color: "#2c2820" }}
                >
                  {v.affected_url}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
