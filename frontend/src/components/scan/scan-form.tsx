"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useScans } from "@/hooks/use-scans";
import { Zap, Search } from "lucide-react";

const MODES = [
  {
    value: "quick" as const,
    label: "Quick Scan",
    desc: "Passive + light active modules. ~5 min.",
    icon: Zap,
    color: "#f59e0b",
    bg: "rgba(245,158,11,0.08)",
    border: "rgba(245,158,11,0.3)",
  },
  {
    value: "full" as const,
    label: "Full Scan",
    desc: "All modules — SQLi, XSS, SSRF, IDOR, and more. 15–45 min.",
    icon: Search,
    color: "#38bdf8",
    bg: "rgba(56,189,248,0.08)",
    border: "rgba(56,189,248,0.3)",
  },
];

export function ScanForm() {
  const [url, setUrl] = useState("");
  const [mode, setMode] = useState<"quick" | "full">("quick");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const { createScan } = useScans();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const scan = await createScan({ target_url: url, scan_mode: mode });
      router.push(`/scans/${scan.id}`);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Failed to create scan";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-2xl space-y-6">
      {/* Target URL */}
      <div
        className="rounded-lg p-5"
        style={{ background: "#141210", border: "1px solid #1e1c18" }}
      >
        <div className="space-y-3">
          <label
            className="block text-[9px] tracking-[0.2em] uppercase"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
          >
            Target URL
          </label>
          <input
            type="url"
            placeholder="https://example.com"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
            className="w-full rounded px-4 py-3 text-[13px] outline-none transition-all"
            style={{
              fontFamily: "JetBrains Mono, monospace",
              background: "#0c0a08",
              border: "1px solid #2c2820",
              color: "#e8e0d5",
            }}
            onFocus={(e) => (e.currentTarget.style.borderColor = "rgba(245,158,11,0.5)")}
            onBlur={(e) => (e.currentTarget.style.borderColor = "#2c2820")}
          />
          <p
            className="text-[10px]"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
          >
            Include protocol (https://). Scan stays within the target domain.
          </p>
        </div>
      </div>

      {/* Mode selection */}
      <div
        className="rounded-lg p-5"
        style={{ background: "#141210", border: "1px solid #1e1c18" }}
      >
        <div
          className="text-[9px] tracking-[0.2em] uppercase mb-3"
          style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
        >
          Scan Mode
        </div>
        <div className="grid grid-cols-2 gap-3">
          {MODES.map((m) => {
            const isSelected = mode === m.value;
            return (
              <button
                key={m.value}
                type="button"
                onClick={() => setMode(m.value)}
                className="rounded-lg p-4 text-left transition-all"
                style={{
                  background: isSelected ? m.bg : "transparent",
                  border: `1px solid ${isSelected ? m.border : "#1e1c18"}`,
                  cursor: "pointer",
                }}
                onMouseEnter={(e) => {
                  if (!isSelected) e.currentTarget.style.borderColor = "#2c2820";
                }}
                onMouseLeave={(e) => {
                  if (!isSelected) e.currentTarget.style.borderColor = "#1e1c18";
                }}
              >
                <div className="flex items-center gap-2 mb-2">
                  <m.icon
                    className="h-4 w-4"
                    style={{ color: isSelected ? m.color : "#4a4440" }}
                  />
                  <span
                    className="text-[12px] font-semibold"
                    style={{ color: isSelected ? m.color : "#8a7f74" }}
                  >
                    {m.label}
                  </span>
                  {isSelected && (
                    <span
                      className="ml-auto text-[9px] tracking-widest uppercase"
                      style={{ fontFamily: "JetBrains Mono, monospace", color: m.color }}
                    >
                      Selected
                    </span>
                  )}
                </div>
                <p
                  className="text-[11px]"
                  style={{ color: "#4a4440", lineHeight: 1.5 }}
                >
                  {m.desc}
                </p>
              </button>
            );
          })}
        </div>
      </div>

      {error && (
        <div
          className="rounded px-4 py-3 text-[11px]"
          style={{
            fontFamily: "JetBrains Mono, monospace",
            background: "rgba(244,63,94,0.08)",
            border: "1px solid rgba(244,63,94,0.2)",
            color: "#f43f5e",
          }}
        >
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={submitting}
        className="flex items-center gap-2 rounded px-6 py-2.5 text-[11px] font-semibold tracking-widest uppercase transition-all"
        style={{
          fontFamily: "JetBrains Mono, monospace",
          background: submitting ? "rgba(245,158,11,0.15)" : "rgba(245,158,11,0.12)",
          border: "1px solid rgba(245,158,11,0.35)",
          color: submitting ? "#a87c2a" : "#f59e0b",
          cursor: submitting ? "not-allowed" : "pointer",
        }}
        onMouseEnter={(e) => {
          if (!submitting) e.currentTarget.style.background = "rgba(245,158,11,0.2)";
        }}
        onMouseLeave={(e) => {
          if (!submitting) e.currentTarget.style.background = "rgba(245,158,11,0.12)";
        }}
      >
        {submitting ? (
          <>
            <span className="animate-cursor">_</span>
            Initiating scan...
          </>
        ) : (
          <>
            <Search className="h-3.5 w-3.5" />
            Start Scan
          </>
        )}
      </button>
    </form>
  );
}
