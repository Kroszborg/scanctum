"use client";

import { use } from "react";
import Link from "next/link";
import { useScan } from "@/hooks/use-scans";
import { DownloadButton } from "@/components/report/download-button";
import { ResultsTable } from "@/components/scan/results-table";
import { ArrowLeft } from "lucide-react";

const SEV_ORDER = ["critical", "high", "medium", "low", "info"] as const;

const SEV_CONFIG: Record<string, { color: string; cls: string }> = {
  critical: { color: "#f43f5e", cls: "badge-critical" },
  high:     { color: "#fb923c", cls: "badge-high" },
  medium:   { color: "#f59e0b", cls: "badge-medium" },
  low:      { color: "#4ade80", cls: "badge-low" },
  info:     { color: "#38bdf8", cls: "badge-info" },
};

export default function ReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { scan, results, loading } = useScan(id);

  if (loading || !scan) {
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
          Loading report...
        </span>
      </div>
    );
  }

  const severityCounts = results.reduce(
    (acc, v) => { acc[v.severity] = (acc[v.severity] || 0) + 1; return acc; },
    {} as Record<string, number>
  );

  return (
    <div className="space-y-6 animate-fade-up">
      {/* Header */}
      <div className="flex items-start gap-4">
        <Link
          href={`/scans/${id}`}
          className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded transition-colors"
          style={{ border: "1px solid #1e1c18", color: "#4a4440" }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = "#2c2820";
            e.currentTarget.style.color = "#e8e0d5";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = "#1e1c18";
            e.currentTarget.style.color = "#4a4440";
          }}
        >
          <ArrowLeft className="h-3.5 w-3.5" />
        </Link>

        <div className="flex-1 min-w-0">
          <div
            className="text-[9px] tracking-[0.25em] uppercase mb-1"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
          >
            VAPT Report
          </div>
          <h1 className="text-[20px] font-bold" style={{ color: "#e8e0d5" }}>
            Security Assessment Report
          </h1>
          <p
            className="text-[11px] mt-1 truncate"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
          >
            {scan.target_url}
          </p>
        </div>

        <div className="flex gap-2 shrink-0">
          <DownloadButton scanId={id} format="pdf" />
          <DownloadButton scanId={id} format="json" />
        </div>
      </div>

      {/* Summary */}
      <div
        className="rounded-lg p-5"
        style={{ background: "#141210", border: "1px solid #1e1c18" }}
      >
        <div
          className="text-[9px] tracking-[0.2em] uppercase mb-4"
          style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
        >
          Findings Summary
        </div>
        <div className="flex gap-4 flex-wrap">
          {SEV_ORDER.map((sev) => {
            const count = severityCounts[sev] || 0;
            const cfg = SEV_CONFIG[sev];
            return (
              <div key={sev} className="text-center">
                <span
                  className={`text-[9px] tracking-widest uppercase px-1.5 py-0.5 rounded ${cfg.cls}`}
                  style={{ fontFamily: "JetBrains Mono, monospace" }}
                >
                  {sev}
                </span>
                <div
                  className="mt-2 text-[24px] font-bold tabular-nums"
                  style={{ fontFamily: "JetBrains Mono, monospace", color: count > 0 ? cfg.color : "#2c2820" }}
                >
                  {count}
                </div>
              </div>
            );
          })}
          <div className="text-center ml-auto">
            <span
              className="text-[9px] tracking-widest uppercase px-1.5 py-0.5 rounded"
              style={{
                fontFamily: "JetBrains Mono, monospace",
                color: "#6b6259",
                background: "#141210",
                border: "1px solid #2c2820",
              }}
            >
              Total
            </span>
            <div
              className="mt-2 text-[24px] font-bold tabular-nums"
              style={{ fontFamily: "JetBrains Mono, monospace", color: "#e8e0d5" }}
            >
              {results.length}
            </div>
          </div>
        </div>
      </div>

      {/* Results table */}
      <ResultsTable results={results} />
    </div>
  );
}
