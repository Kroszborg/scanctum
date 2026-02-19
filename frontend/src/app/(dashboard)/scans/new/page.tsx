"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { ScanForm } from "@/components/scan/scan-form";

export default function NewScanPage() {
  return (
    <div className="space-y-6 animate-fade-up">
      <div className="flex items-center gap-4">
        <Link
          href="/scans"
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
            className="text-[9px] tracking-[0.25em] uppercase mb-0.5"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
          >
            Assessment Configuration
          </div>
          <h1
            className="text-[24px] font-bold"
            style={{ color: "#e8e0d5" }}
          >
            New Scan
          </h1>
        </div>
      </div>

      <ScanForm />
    </div>
  );
}
