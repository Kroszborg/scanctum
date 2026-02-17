"use client";

import { useDashboard } from "@/hooks/use-dashboard";
import { StatsCards } from "@/components/dashboard/stats-cards";
import { SeverityChart } from "@/components/dashboard/severity-chart";
import { ScanHistoryChart } from "@/components/dashboard/scan-history-chart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SCAN_STATUS_LABELS } from "@/lib/constants";
import Link from "next/link";

export default function DashboardPage() {
  const { stats, loading } = useDashboard();

  if (loading || !stats) {
    return <div className="animate-pulse text-muted-foreground">Loading dashboard...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">Security assessment overview</p>
      </div>

      <StatsCards stats={stats} />

      <div className="grid gap-6 md:grid-cols-2">
        <SeverityChart distribution={stats.severity_distribution} />
        <ScanHistoryChart data={stats.scans_over_time} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Recent Scans</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {stats.recent_scans.map((scan) => (
              <Link
                key={scan.id}
                href={`/scans/${scan.id}`}
                className="flex items-center justify-between rounded-lg border p-3 hover:bg-muted/50 transition-colors"
              >
                <div>
                  <p className="text-sm font-medium truncate max-w-[300px]">{scan.target_url}</p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(scan.created_at).toLocaleDateString()} | {scan.scan_mode}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm">{scan.vuln_count} findings</span>
                  <Badge variant="secondary">
                    {SCAN_STATUS_LABELS[scan.status] || scan.status}
                  </Badge>
                </div>
              </Link>
            ))}
            {stats.recent_scans.length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-4">
                No scans yet. Start your first scan!
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
