"use client";

import Link from "next/link";
import { useScans } from "@/hooks/use-scans";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SCAN_STATUS_LABELS } from "@/lib/constants";
import { Plus } from "lucide-react";

const statusColors: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  crawling: "bg-blue-100 text-blue-800",
  scanning: "bg-purple-100 text-purple-800",
  completed: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
  cancelled: "bg-gray-100 text-gray-800",
};

export default function ScansPage() {
  const { scans, loading } = useScans();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Scans</h1>
          <p className="text-muted-foreground">Manage your security scans</p>
        </div>
        <Link href="/scans/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Scan
          </Button>
        </Link>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="rounded-lg border">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="px-4 py-3 text-left text-sm font-medium">Target</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Mode</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Status</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Progress</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Date</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                      Loading...
                    </td>
                  </tr>
                ) : scans.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                      No scans yet
                    </td>
                  </tr>
                ) : (
                  scans.map((scan) => (
                    <tr key={scan.id} className="border-b hover:bg-muted/50 transition-colors">
                      <td className="px-4 py-3">
                        <Link href={`/scans/${scan.id}`} className="text-sm font-medium hover:underline max-w-[300px] truncate block">
                          {scan.target_url}
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-sm capitalize">{scan.scan_mode}</td>
                      <td className="px-4 py-3">
                        <Badge className={statusColors[scan.status] || ""} variant="secondary">
                          {SCAN_STATUS_LABELS[scan.status] || scan.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-sm">{scan.progress_percent}%</td>
                      <td className="px-4 py-3 text-sm text-muted-foreground">
                        {new Date(scan.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
