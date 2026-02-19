"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import api from "@/lib/api";
import { ComparisonSection } from "@/components/comparison/comparison-table";
import { ArrowLeft } from "lucide-react";
import type { Vulnerability } from "@/types/vulnerability";

interface ComparisonData {
  scan_a_id: string;
  scan_b_id: string;
  new_vulnerabilities: Vulnerability[];
  fixed_vulnerabilities: Vulnerability[];
  unchanged_vulnerabilities: Vulnerability[];
  summary: { new: number; fixed: number; unchanged: number };
}

export default function ComparisonResultPage({
  params,
}: {
  params: Promise<{ scan1: string; scan2: string }>;
}) {
  const { scan1, scan2 } = use(params);
  const [data, setData] = useState<ComparisonData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<ComparisonData>(`/compare/${scan1}/${scan2}`)
      .then((res) => setData(res.data))
      .finally(() => setLoading(false));
  }, [scan1, scan2]);

  if (loading || !data) {
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
          Computing delta...
        </span>
      </div>
    );
  }

  const summaryCards = [
    { label: "New Issues",  value: data.summary.new,       color: "#f43f5e", bg: "rgba(244,63,94,0.08)",  border: "rgba(244,63,94,0.2)"  },
    { label: "Fixed",       value: data.summary.fixed,     color: "#4ade80", bg: "rgba(74,222,128,0.08)", border: "rgba(74,222,128,0.2)" },
    { label: "Unchanged",   value: data.summary.unchanged, color: "#564e45", bg: "transparent",           border: "#1e1c18"              },
  ];

  return (
    <div className="space-y-6 animate-fade-up">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          href="/compare"
          className="flex h-7 w-7 items-center justify-center rounded transition-colors"
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
        <div>
          <div
            className="text-[9px] tracking-[0.25em] uppercase mb-1"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
          >
            Delta Analysis
          </div>
          <h1 className="text-[24px] font-bold" style={{ color: "#e8e0d5" }}>
            Scan Comparison
          </h1>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid gap-3 md:grid-cols-3">
        {summaryCards.map(({ label, value, color, bg, border }) => (
          <div
            key={label}
            className="rounded-lg p-5"
            style={{ background: "#141210", border: `1px solid ${border}` }}
          >
            <div
              className="text-[9px] tracking-[0.2em] uppercase mb-3"
              style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
            >
              {label}
            </div>
            <div
              className="text-[36px] font-bold tabular-nums"
              style={{ fontFamily: "JetBrains Mono, monospace", color }}
            >
              {value.toString().padStart(2, "0")}
            </div>
          </div>
        ))}
      </div>

      {/* Sections */}
      <div className="space-y-6">
        <ComparisonSection title="New Vulnerabilities"      vulnerabilities={data.new_vulnerabilities}       variant="new" />
        <ComparisonSection title="Fixed Vulnerabilities"    vulnerabilities={data.fixed_vulnerabilities}     variant="fixed" />
        <ComparisonSection title="Unchanged Vulnerabilities" vulnerabilities={data.unchanged_vulnerabilities} variant="unchanged" />
      </div>
    </div>
  );
}
