"use client";

import { useEffect } from "react";
import { OWASP_LABELS } from "@/lib/constants";
import { X } from "lucide-react";
import type { Vulnerability } from "@/types/vulnerability";

const SEV_CONFIG: Record<string, { color: string; bg: string; border: string; cls: string }> = {
  critical: { color: "#f43f5e", bg: "rgba(244,63,94,0.08)",  border: "rgba(244,63,94,0.25)",  cls: "badge-critical" },
  high:     { color: "#fb923c", bg: "rgba(251,146,60,0.08)", border: "rgba(251,146,60,0.25)", cls: "badge-high" },
  medium:   { color: "#f59e0b", bg: "rgba(245,158,11,0.08)", border: "rgba(245,158,11,0.25)", cls: "badge-medium" },
  low:      { color: "#4ade80", bg: "rgba(74,222,128,0.08)", border: "rgba(74,222,128,0.25)", cls: "badge-low" },
  info:     { color: "#38bdf8", bg: "rgba(56,189,248,0.08)", border: "rgba(56,189,248,0.25)", cls: "badge-info" },
};

interface Props {
  vuln: Vulnerability;
  onClose: () => void;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div
        className="text-[9px] tracking-[0.2em] uppercase mb-1.5"
        style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
      >
        {label}
      </div>
      {children}
    </div>
  );
}

export function VulnDetailDialog({ vuln, onClose }: Props) {
  const cfg = SEV_CONFIG[vuln.severity] ?? SEV_CONFIG.info;

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.7)", backdropFilter: "blur(2px)" }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        className="relative w-full max-w-2xl max-h-[85vh] overflow-y-auto rounded-lg"
        style={{
          background: "#141210",
          border: `1px solid ${cfg.border}`,
          borderLeft: `3px solid ${cfg.color}`,
        }}
      >
        {/* Header */}
        <div
          className="sticky top-0 flex items-start gap-3 px-6 py-4"
          style={{
            background: "#141210",
            borderBottom: "1px solid #1e1c18",
          }}
        >
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1.5">
              <span
                className={`text-[9px] tracking-widest uppercase px-1.5 py-0.5 rounded ${cfg.cls}`}
                style={{ fontFamily: "JetBrains Mono, monospace" }}
              >
                {vuln.severity}
              </span>
              <span
                className="text-[10px] tabular-nums"
                style={{ fontFamily: "JetBrains Mono, monospace", color: cfg.color }}
              >
                CVSS {vuln.cvss_score}
              </span>
              <span
                className="text-[10px]"
                style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
              >
                {vuln.owasp_category}
              </span>
              {vuln.cwe_id && (
                <span
                  className="text-[10px]"
                  style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
                >
                  {vuln.cwe_id}
                </span>
              )}
            </div>
            <h2
              className="text-[16px] font-bold leading-snug"
              style={{ color: "#e8e0d5" }}
            >
              {vuln.vuln_type}
            </h2>
          </div>

          <button
            onClick={onClose}
            className="shrink-0 flex h-7 w-7 items-center justify-center rounded transition-colors"
            style={{ color: "#4a4440", border: "1px solid #1e1c18" }}
            onMouseEnter={(e) => { e.currentTarget.style.color = "#e8e0d5"; e.currentTarget.style.borderColor = "#2c2820"; }}
            onMouseLeave={(e) => { e.currentTarget.style.color = "#4a4440"; e.currentTarget.style.borderColor = "#1e1c18"; }}
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-5">
          <Field label="Affected URL">
            <p
              className="text-[11px] break-all"
              style={{ fontFamily: "JetBrains Mono, monospace", color: "#8a7f74" }}
            >
              {vuln.affected_url}
            </p>
            {vuln.affected_parameter && (
              <p
                className="text-[10px] mt-1"
                style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
              >
                Parameter: <span style={{ color: "#6b6259" }}>{vuln.affected_parameter}</span>
              </p>
            )}
          </Field>

          <Field label="Description">
            <p className="text-[13px]" style={{ color: "#8a7f74", lineHeight: 1.6 }}>
              {vuln.description}
            </p>
          </Field>

          <Field label="Remediation">
            <div
              className="rounded px-4 py-3"
              style={{
                background: "rgba(74,222,128,0.05)",
                border: "1px solid rgba(74,222,128,0.15)",
                borderLeft: "3px solid #4ade80",
              }}
            >
              <p className="text-[13px]" style={{ color: "#8a7f74", lineHeight: 1.6 }}>
                {vuln.remediation}
              </p>
            </div>
          </Field>

          {/* Meta grid */}
          <Field label="Details">
            <div
              className="grid grid-cols-2 gap-x-6 gap-y-3 rounded px-4 py-3"
              style={{ background: "#0c0a08", border: "1px solid #1e1c18" }}
            >
              {[
                { k: "Module", v: vuln.module_name },
                { k: "Confidence", v: vuln.confidence },
                { k: "OWASP", v: `${vuln.owasp_category} — ${OWASP_LABELS[vuln.owasp_category] ?? ""}` },
                { k: "CVSS Vector", v: vuln.cvss_vector },
              ].map(({ k, v }) => (
                <div key={k}>
                  <div
                    className="text-[9px] tracking-widest uppercase"
                    style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
                  >
                    {k}
                  </div>
                  <div
                    className="text-[11px] mt-0.5 break-all"
                    style={{ fontFamily: "JetBrains Mono, monospace", color: "#6b6259" }}
                  >
                    {v ?? "—"}
                  </div>
                </div>
              ))}
            </div>
          </Field>

          {vuln.evidence.length > 0 && (
            <Field label={`Evidence (${vuln.evidence.length})`}>
              <div className="space-y-3">
                {vuln.evidence.map((ev) => (
                  <div key={ev.id}>
                    <div
                      className="text-[9px] tracking-widest uppercase mb-1"
                      style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
                    >
                      {ev.title}
                    </div>
                    <pre
                      className="rounded px-4 py-3 text-[11px] overflow-x-auto whitespace-pre-wrap"
                      style={{
                        fontFamily: "JetBrains Mono, monospace",
                        background: "#0c0a08",
                        border: "1px solid #1e1c18",
                        color: "#6b6259",
                        lineHeight: 1.6,
                      }}
                    >
                      {ev.content}
                    </pre>
                  </div>
                ))}
              </div>
            </Field>
          )}
        </div>
      </div>
    </div>
  );
}
