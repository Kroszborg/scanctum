"use client";

import { useState, useEffect, useCallback } from "react";
import api from "@/lib/api";
import type { Vulnerability } from "@/types/vulnerability";
import { Shield, Filter, ChevronDown, ExternalLink } from "lucide-react";
import Link from "next/link";

const SEVERITY_STYLES: Record<string, { color: string; bg: string; border: string }> = {
  critical: { color: "#ef4444", bg: "rgba(239,68,68,0.08)",  border: "rgba(239,68,68,0.2)"  },
  high:     { color: "#f97316", bg: "rgba(249,115,22,0.08)", border: "rgba(249,115,22,0.2)" },
  medium:   { color: "#f59e0b", bg: "rgba(245,158,11,0.08)", border: "rgba(245,158,11,0.2)" },
  low:      { color: "#38bdf8", bg: "rgba(56,189,248,0.08)", border: "rgba(56,189,248,0.2)" },
  info:     { color: "#6b7280", bg: "rgba(107,114,128,0.08)",border: "rgba(107,114,128,0.2)"},
};

const SEVERITY_OPTIONS = ["all", "critical", "high", "medium", "low", "info"] as const;
const OWASP_OPTIONS = [
  "all", "A01", "A02", "A03", "A04", "A05",
  "A06", "A07", "A08", "A09", "A10",
] as const;

export default function VulnDbPage() {
  const [vulns, setVulns] = useState<Vulnerability[]>([]);
  const [loading, setLoading] = useState(true);
  const [severity, setSeverity] = useState<string>("all");
  const [owasp, setOwasp] = useState<string>("all");
  const [expanded, setExpanded] = useState<string | null>(null);

  const fetchVulns = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (severity !== "all") params.set("severity", severity);
      if (owasp !== "all") params.set("owasp", owasp);
      params.set("limit", "200");
      const res = await api.get<Vulnerability[]>(`/vulnerabilities?${params.toString()}`);
      setVulns(res.data);
    } catch {
      setVulns([]);
    } finally {
      setLoading(false);
    }
  }, [severity, owasp]);

  useEffect(() => { fetchVulns(); }, [fetchVulns]);

  const sev = (v: Vulnerability) => SEVERITY_STYLES[v.severity] ?? SEVERITY_STYLES.info;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div
            className="text-[9px] tracking-[0.25em] uppercase mb-1"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
          >
            Intelligence
          </div>
          <h1 className="text-[24px] font-bold" style={{ color: "#e8e0d5" }}>
            Vulnerability Database
          </h1>
        </div>
        <div
          className="flex items-center gap-2 px-3 py-1.5 rounded"
          style={{
            fontFamily: "JetBrains Mono, monospace",
            fontSize: "10px",
            color: "#4a4440",
            background: "#141210",
            border: "1px solid #1e1c18",
          }}
        >
          <Shield className="h-3 w-3" />
          {vulns.length} findings
        </div>
      </div>

      {/* Filters */}
      <div
        className="flex flex-wrap gap-3 p-4 rounded-lg"
        style={{ background: "#141210", border: "1px solid #1e1c18" }}
      >
        <div className="flex items-center gap-2">
          <Filter className="h-3 w-3" style={{ color: "#4a4440" }} />
          <span
            className="text-[9px] tracking-[0.2em] uppercase"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
          >
            Filters
          </span>
        </div>

        {/* Severity filter */}
        <div className="relative">
          <select
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
            className="appearance-none cursor-pointer rounded px-3 py-1.5 pr-7 text-[10px] tracking-wide"
            style={{
              fontFamily: "JetBrains Mono, monospace",
              background: "#0c0a08",
              border: "1px solid #2c2820",
              color: "#8a7f74",
              outline: "none",
            }}
          >
            {SEVERITY_OPTIONS.map((s) => (
              <option key={s} value={s} style={{ background: "#0c0a08" }}>
                {s === "all" ? "All Severities" : s.charAt(0).toUpperCase() + s.slice(1)}
              </option>
            ))}
          </select>
          <ChevronDown className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 h-3 w-3" style={{ color: "#4a4440" }} />
        </div>

        {/* OWASP filter */}
        <div className="relative">
          <select
            value={owasp}
            onChange={(e) => setOwasp(e.target.value)}
            className="appearance-none cursor-pointer rounded px-3 py-1.5 pr-7 text-[10px] tracking-wide"
            style={{
              fontFamily: "JetBrains Mono, monospace",
              background: "#0c0a08",
              border: "1px solid #2c2820",
              color: "#8a7f74",
              outline: "none",
            }}
          >
            {OWASP_OPTIONS.map((o) => (
              <option key={o} value={o} style={{ background: "#0c0a08" }}>
                {o === "all" ? "All OWASP" : o}
              </option>
            ))}
          </select>
          <ChevronDown className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 h-3 w-3" style={{ color: "#4a4440" }} />
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex items-center gap-3 py-12">
          <div className="h-1.5 w-1.5 rounded-full animate-pulse" style={{ background: "#f59e0b" }} />
          <span className="text-[11px] tracking-widest uppercase" style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}>
            Loading vulnerability data...
          </span>
        </div>
      ) : vulns.length === 0 ? (
        <div
          className="flex flex-col items-center justify-center py-16 rounded-lg gap-3"
          style={{ background: "#141210", border: "1px solid #1e1c18" }}
        >
          <Shield className="h-8 w-8" style={{ color: "#2c2820" }} />
          <span className="text-[12px]" style={{ color: "#4a4440", fontFamily: "JetBrains Mono, monospace" }}>
            No vulnerabilities match current filters
          </span>
        </div>
      ) : (
        <div className="rounded-lg overflow-hidden" style={{ border: "1px solid #1e1c18" }}>
          {/* Column headers */}
          <div
            className="grid px-5 py-2.5"
            style={{
              background: "#141210",
              borderBottom: "1px solid #1e1c18",
              gridTemplateColumns: "90px 1fr 80px 50px 120px",
              gap: "12px",
            }}
          >
            {["Severity", "Finding", "OWASP", "CWE", "Scan"].map((h) => (
              <span
                key={h}
                className="text-[9px] tracking-[0.2em] uppercase"
                style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
              >
                {h}
              </span>
            ))}
          </div>

          {vulns.map((v, i) => {
            const style = sev(v);
            const isOpen = expanded === String(v.id);
            return (
              <div
                key={String(v.id)}
                style={{
                  background: "#0c0a08",
                  borderBottom: i < vulns.length - 1 ? "1px solid #1e1c18" : "none",
                }}
              >
                {/* Row */}
                <button
                  onClick={() => setExpanded(isOpen ? null : String(v.id))}
                  className="w-full text-left"
                >
                  <div
                    className="grid px-5 py-3 hover:bg-[#141210] transition-colors"
                    style={{ gridTemplateColumns: "90px 1fr 80px 50px 120px", gap: "12px" }}
                  >
                    {/* Severity badge */}
                    <span
                      className="self-center px-2 py-0.5 rounded text-[9px] tracking-widest uppercase font-semibold"
                      style={{
                        fontFamily: "JetBrains Mono, monospace",
                        color: style.color,
                        background: style.bg,
                        border: `1px solid ${style.border}`,
                      }}
                    >
                      {v.severity}
                    </span>

                    {/* Finding name */}
                    <div className="self-center min-w-0">
                      <div className="text-[12px] font-medium truncate" style={{ color: "#e8e0d5" }}>
                        {v.vuln_type}
                      </div>
                      <div
                        className="text-[10px] truncate mt-0.5"
                        style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
                      >
                        {v.affected_url}
                        {v.affected_parameter && ` · ${v.affected_parameter}`}
                      </div>
                    </div>

                    {/* OWASP */}
                    <span
                      className="self-center text-[10px]"
                      style={{ fontFamily: "JetBrains Mono, monospace", color: "#6b6259" }}
                    >
                      {v.owasp_category}
                    </span>

                    {/* CWE */}
                    <span
                      className="self-center text-[10px]"
                      style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
                    >
                      {v.cwe_id}
                    </span>

                    {/* Scan link */}
                    <div className="self-center flex items-center gap-1">
                      <Link
                        href={`/scans/${v.scan_id}`}
                        onClick={(e) => e.stopPropagation()}
                        className="flex items-center gap-1 text-[10px] transition-colors"
                        style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
                        onMouseEnter={(e) => (e.currentTarget.style.color = "#f59e0b")}
                        onMouseLeave={(e) => (e.currentTarget.style.color = "#4a4440")}
                      >
                        View scan
                        <ExternalLink className="h-2.5 w-2.5" />
                      </Link>
                    </div>
                  </div>
                </button>

                {/* Expanded detail */}
                {isOpen && (
                  <div
                    className="px-5 pb-4 pt-1 space-y-3"
                    style={{ borderTop: "1px solid #1e1c18", background: "#0e0c0a" }}
                  >
                    <div>
                      <div className="text-[9px] tracking-widest uppercase mb-1" style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}>Description</div>
                      <p className="text-[11px] leading-relaxed" style={{ color: "#8a7f74" }}>{v.description}</p>
                    </div>
                    <div>
                      <div className="text-[9px] tracking-widest uppercase mb-1" style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}>Remediation</div>
                      <p className="text-[11px] leading-relaxed" style={{ color: "#8a7f74" }}>{v.remediation}</p>
                    </div>
                    <div className="flex gap-4 text-[10px]" style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}>
                      <span>CVSS: <span style={{ color: style.color }}>{v.cvss_score.toFixed(1)}</span></span>
                      <span>Confidence: {v.confidence}</span>
                      <span>Module: {v.module_name}</span>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
