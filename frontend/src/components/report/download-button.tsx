"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";
import api from "@/lib/api";

export function DownloadButton({ scanId, format }: { scanId: string; format: "pdf" | "json" }) {
  const [loading, setLoading] = useState(false);

  const handleDownload = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/reports/${scanId}?format=${format}`, {
        responseType: format === "pdf" ? "blob" : "json",
      });

      if (format === "pdf") {
        const blob = new Blob([response.data], { type: "application/pdf" });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `scanctum-report-${scanId}.pdf`;
        a.click();
        window.URL.revokeObjectURL(url);
      } else {
        const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: "application/json" });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `scanctum-report-${scanId}.json`;
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch {
      // TODO: toast error
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button variant="outline" size="sm" onClick={handleDownload} disabled={loading}>
      <Download className="mr-2 h-4 w-4" />
      {loading ? "Generating..." : `Download ${format.toUpperCase()}`}
    </Button>
  );
}
