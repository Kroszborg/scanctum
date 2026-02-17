"use client";

import { ScanForm } from "@/components/scan/scan-form";

export default function NewScanPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">New Scan</h1>
        <p className="text-muted-foreground">Configure and start a new security assessment</p>
      </div>
      <ScanForm />
    </div>
  );
}
