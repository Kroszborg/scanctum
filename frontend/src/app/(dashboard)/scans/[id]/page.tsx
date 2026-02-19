"use client";

import { use } from "react";
import Link from "next/link";
import { useScan } from "@/hooks/use-scans";
import { usePolling } from "@/hooks/use-polling";
import { ScanProgress } from "@/components/scan/scan-progress";
import { ResultsTable } from "@/components/scan/results-table";
import { DownloadButton } from "@/components/report/download-button";
import { ArrowLeft, FileText, Download } from "lucide-react";

export default function ScanDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { scan, results, loading, refetch } = useScan(id);

  const isRunning = scan ? ["pending", "crawling", "scanning"].includes(scan.status) : false;
  usePolling(refetch, 3000, isRunning);

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
          Loading scan data...
        </span>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-up">
      {/* Header */}
      <div className="flex items-start gap-4">
        <Link
          href="/scans"
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
            Scan Detail
          </div>
          <h1
            className="text-[20px] font-bold truncate"
            style={{ color: "#e8e0d5" }}
          >
            {scan.target_url}
          </h1>
          <div
            className="flex items-center gap-3 mt-1 text-[10px]"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
          >
            <span className="tracking-widest uppercase">{scan.scan_mode} scan</span>
            <span style={{ color: "#1e1c18" }}>|</span>
            <span>
              {new Date(scan.created_at).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>
          </div>
        </div>

        {scan.status === "completed" && (
          <div className="flex gap-2 shrink-0">
            <DownloadButton scanId={id} format="pdf" />
            <DownloadButton scanId={id} format="json" />
          </div>
        )}
      </div>

      {/* Progress card */}
      <div
        className="rounded-lg p-5"
        style={{ background: "#141210", border: "1px solid #1e1c18" }}
      >
        <div
          className="text-[9px] tracking-[0.2em] uppercase mb-4"
          style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
        >
          Scan Status
        </div>
        <ScanProgress scan={scan} />
      </div>

      {/* Error */}
      {scan.error_message && (
        <div
          className="rounded-lg px-5 py-4"
          style={{
            background: "rgba(244,63,94,0.06)",
            border: "1px solid rgba(244,63,94,0.2)",
          }}
        >
          <div
            className="text-[9px] tracking-[0.2em] uppercase mb-1"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "rgba(244,63,94,0.6)" }}
          >
            Error
          </div>
          <p
            className="text-[12px]"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#f43f5e" }}
          >
            {scan.error_message}
          </p>
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div
                className="text-[9px] tracking-[0.25em] uppercase mb-1"
                style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
              >
                Intelligence
              </div>
              <h2 className="text-[18px] font-bold" style={{ color: "#e8e0d5" }}>
                Findings
                <span
                  className="ml-2 text-[14px] font-normal tabular-nums"
                  style={{ fontFamily: "JetBrains Mono, monospace", color: "#6b6259" }}
                >
                  ({results.length})
                </span>
              </h2>
            </div>

            {scan.status === "completed" && (
              <Link
                href={`/scans/${id}/report`}
                className="flex items-center gap-2 rounded px-3 py-1.5 text-[10px] tracking-widest uppercase transition-all"
                style={{
                  fontFamily: "JetBrains Mono, monospace",
                  background: "transparent",
                  border: "1px solid #2c2820",
                  color: "#6b6259",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = "rgba(245,158,11,0.3)";
                  e.currentTarget.style.color = "#f59e0b";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = "#2c2820";
                  e.currentTarget.style.color = "#6b6259";
                }}
              >
                <FileText className="h-3 w-3" />
                View report
              </Link>
            )}
          </div>

          <ResultsTable results={results} />
        </div>
      )}

      {/* Clean scan */}
      {scan.status === "completed" && results.length === 0 && (
        <div
          className="rounded-lg flex flex-col items-center justify-center py-14 gap-3"
          style={{ background: "#141210", border: "1px solid #1e1c18" }}
        >
          <div
            className="h-10 w-10 rounded-full flex items-center justify-center"
            style={{ background: "rgba(74,222,128,0.1)", border: "1px solid rgba(74,222,128,0.3)" }}
          >
            <span className="text-[18px]" style={{ color: "#4ade80" }}>✓</span>
          </div>
          <div
            className="text-[13px] font-semibold"
            style={{ color: "#e8e0d5" }}
          >
            No vulnerabilities detected
          </div>
          <div
            className="text-[11px]"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
          >
            Scan completed clean
          </div>
        </div>
      )}
    </div>
  );
}
