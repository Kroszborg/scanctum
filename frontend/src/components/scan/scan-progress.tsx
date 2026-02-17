"use client";

import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { SCAN_STATUS_LABELS } from "@/lib/constants";
import type { Scan } from "@/types/scan";

const statusColors: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  crawling: "bg-blue-100 text-blue-800",
  scanning: "bg-purple-100 text-purple-800",
  completed: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
  cancelled: "bg-gray-100 text-gray-800",
};

export function ScanProgress({ scan }: { scan: Scan }) {
  const isRunning = ["pending", "crawling", "scanning"].includes(scan.status);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <Badge className={statusColors[scan.status] || ""} variant="secondary">
          {SCAN_STATUS_LABELS[scan.status] || scan.status}
        </Badge>
        {isRunning && (
          <span className="text-sm text-muted-foreground">
            {scan.progress_percent}%
          </span>
        )}
      </div>
      {isRunning && <Progress value={scan.progress_percent} />}
      <div className="flex gap-6 text-sm text-muted-foreground">
        <span>Pages found: {scan.pages_found}</span>
        <span>Pages scanned: {scan.pages_scanned}</span>
        <span>Mode: {scan.scan_mode}</span>
      </div>
    </div>
  );
}
