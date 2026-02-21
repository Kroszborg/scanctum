"use client";

import { useState } from "react";
import { Download } from "lucide-react";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export function DownloadButton({
  scanId,
  format,
}: {
  scanId: string;
  format: "pdf" | "json";
}) {
  const [loading, setLoading] = useState(false);

  const handleDownload = async () => {
    setLoading(true);
    try {
      const token =
        typeof window !== "undefined"
          ? localStorage.getItem("scanctum_token")
          : null;
      const res = await fetch(
        `${API_BASE}/reports/${scanId}?format=${format}`,
        {
          method: "GET",
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        },
      );
      if (!res.ok) throw new Error("Download failed");

      if (format === "pdf") {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `scanctum-report-${scanId}.pdf`;
        a.click();
        window.URL.revokeObjectURL(url);
      } else {
        const data = await res.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], {
          type: "application/json",
        });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `scanctum-report-${scanId}.json`;
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleDownload}
      disabled={loading}
      className="flex items-center gap-2 rounded px-3 py-1.5 text-[10px] tracking-widest uppercase transition-all"
      style={{
        fontFamily: "JetBrains Mono, monospace",
        background: "transparent",
        border: "1px solid #2c2820",
        color: loading ? "#2c2820" : "#6b6259",
        cursor: loading ? "not-allowed" : "pointer",
      }}
      onMouseEnter={(e) => {
        if (!loading) {
          e.currentTarget.style.borderColor = "rgba(245,158,11,0.3)";
          e.currentTarget.style.color = "#f59e0b";
        }
      }}
      onMouseLeave={(e) => {
        if (!loading) {
          e.currentTarget.style.borderColor = "#2c2820";
          e.currentTarget.style.color = "#6b6259";
        }
      }}
    >
      <Download className="h-3 w-3" />
      {loading ? "Generating..." : format.toUpperCase()}
    </button>
  );
}
