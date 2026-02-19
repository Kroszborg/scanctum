"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useScans } from "@/hooks/use-scans";
import { GitCompareArrows } from "lucide-react";

export default function ComparePage() {
  const { scans, loading } = useScans();
  const [scanA, setScanA] = useState("");
  const [scanB, setScanB] = useState("");
  const router = useRouter();

  const completedScans = scans.filter((s) => s.status === "completed");

  const handleCompare = () => {
    if (scanA && scanB && scanA !== scanB) {
      router.push(`/compare/${scanA}/${scanB}`);
    }
  };

  const selectStyle = {
    fontFamily: "JetBrains Mono, monospace",
    background: "#0c0a08",
    border: "1px solid #2c2820",
    color: "#8a7f74",
    fontSize: "12px",
    padding: "10px 12px",
    borderRadius: "6px",
    width: "100%",
    outline: "none",
    cursor: "pointer",
    appearance: "none" as const,
  };

  return (
    <div className="space-y-6 animate-fade-up">
      <div>
        <div
          className="text-[9px] tracking-[0.25em] uppercase mb-1"
          style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
        >
          Delta Analysis
        </div>
        <h1 className="text-[24px] font-bold" style={{ color: "#e8e0d5" }}>
          Compare Scans
        </h1>
      </div>

      <div
        className="max-w-2xl rounded-lg p-5 space-y-5"
        style={{ background: "#141210", border: "1px solid #1e1c18" }}
      >
        <p
          className="text-[12px]"
          style={{ color: "#4a4440" }}
        >
          Select two completed scans to diff their findings — new vulnerabilities, fixed issues, and unchanged findings.
        </p>

        {loading ? (
          <div
            className="text-[11px] tracking-widest uppercase"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
          >
            Loading scans...
          </div>
        ) : completedScans.length < 2 ? (
          <div
            className="rounded px-4 py-3 text-[11px]"
            style={{
              fontFamily: "JetBrains Mono, monospace",
              background: "rgba(245,158,11,0.06)",
              border: "1px solid rgba(245,158,11,0.15)",
              color: "#6b6259",
            }}
          >
            At least 2 completed scans are required for comparison.
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label
                  className="block text-[9px] tracking-[0.2em] uppercase"
                  style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
                >
                  Scan A — Baseline
                </label>
                <div className="relative">
                  <select
                    value={scanA}
                    onChange={(e) => setScanA(e.target.value)}
                    style={selectStyle}
                    onFocus={(e) => (e.currentTarget.style.borderColor = "rgba(245,158,11,0.5)")}
                    onBlur={(e) => (e.currentTarget.style.borderColor = "#2c2820")}
                  >
                    <option value="">Select baseline...</option>
                    {completedScans.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.target_url.replace(/^https?:\/\//, "")} — {new Date(s.created_at).toLocaleDateString()}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="space-y-2">
                <label
                  className="block text-[9px] tracking-[0.2em] uppercase"
                  style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
                >
                  Scan B — Current
                </label>
                <div className="relative">
                  <select
                    value={scanB}
                    onChange={(e) => setScanB(e.target.value)}
                    style={selectStyle}
                    onFocus={(e) => (e.currentTarget.style.borderColor = "rgba(245,158,11,0.5)")}
                    onBlur={(e) => (e.currentTarget.style.borderColor = "#2c2820")}
                  >
                    <option value="">Select current...</option>
                    {completedScans.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.target_url.replace(/^https?:\/\//, "")} — {new Date(s.created_at).toLocaleDateString()}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            <button
              onClick={handleCompare}
              disabled={!scanA || !scanB || scanA === scanB}
              className="flex items-center gap-2 rounded px-5 py-2.5 text-[11px] font-semibold tracking-widest uppercase transition-all"
              style={{
                fontFamily: "JetBrains Mono, monospace",
                background: (!scanA || !scanB || scanA === scanB)
                  ? "transparent"
                  : "rgba(245,158,11,0.12)",
                border: `1px solid ${(!scanA || !scanB || scanA === scanB) ? "#1e1c18" : "rgba(245,158,11,0.35)"}`,
                color: (!scanA || !scanB || scanA === scanB) ? "#2c2820" : "#f59e0b",
                cursor: (!scanA || !scanB || scanA === scanB) ? "not-allowed" : "pointer",
              }}
              onMouseEnter={(e) => {
                if (scanA && scanB && scanA !== scanB)
                  e.currentTarget.style.background = "rgba(245,158,11,0.2)";
              }}
              onMouseLeave={(e) => {
                if (scanA && scanB && scanA !== scanB)
                  e.currentTarget.style.background = "rgba(245,158,11,0.12)";
              }}
            >
              <GitCompareArrows className="h-3.5 w-3.5" />
              Run Comparison
            </button>
          </>
        )}
      </div>
    </div>
  );
}
