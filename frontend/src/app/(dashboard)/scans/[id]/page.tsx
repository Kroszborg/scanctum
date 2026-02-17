"use client";

import { use } from "react";
import Link from "next/link";
import { useScan } from "@/hooks/use-scans";
import { usePolling } from "@/hooks/use-polling";
import { ScanProgress } from "@/components/scan/scan-progress";
import { ResultsTable } from "@/components/scan/results-table";
import { DownloadButton } from "@/components/report/download-button";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft } from "lucide-react";

export default function ScanDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { scan, results, loading, refetch } = useScan(id);

  const isRunning = scan ? ["pending", "crawling", "scanning"].includes(scan.status) : false;
  usePolling(refetch, 3000, isRunning);

  if (loading || !scan) {
    return <div className="animate-pulse text-muted-foreground">Loading scan...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/scans">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold tracking-tight truncate">{scan.target_url}</h1>
          <p className="text-muted-foreground">
            {scan.scan_mode} scan | Created {new Date(scan.created_at).toLocaleString()}
          </p>
        </div>
        {scan.status === "completed" && (
          <div className="flex gap-2">
            <DownloadButton scanId={id} format="pdf" />
            <DownloadButton scanId={id} format="json" />
          </div>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Scan Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <ScanProgress scan={scan} />
        </CardContent>
      </Card>

      {scan.error_message && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-sm text-destructive">{scan.error_message}</p>
          </CardContent>
        </Card>
      )}

      {results.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-4">
            Findings ({results.length})
          </h2>
          <ResultsTable results={results} />
        </div>
      )}

      {scan.status === "completed" && results.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <p className="text-lg font-medium">No vulnerabilities found</p>
            <p className="text-sm text-muted-foreground">The scan completed without finding any issues.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
