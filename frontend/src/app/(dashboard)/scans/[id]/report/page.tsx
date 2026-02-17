"use client";

import { use } from "react";
import Link from "next/link";
import { useScan } from "@/hooks/use-scans";
import { DownloadButton } from "@/components/report/download-button";
import { ResultsTable } from "@/components/scan/results-table";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SEVERITY_BG } from "@/lib/constants";
import { ArrowLeft } from "lucide-react";

export default function ReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { scan, results, loading } = useScan(id);

  if (loading || !scan) {
    return <div className="animate-pulse text-muted-foreground">Loading report...</div>;
  }

  const severityCounts = results.reduce(
    (acc, v) => { acc[v.severity] = (acc[v.severity] || 0) + 1; return acc; },
    {} as Record<string, number>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href={`/scans/${id}`}>
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold tracking-tight">Scan Report</h1>
          <p className="text-muted-foreground truncate">{scan.target_url}</p>
        </div>
        <div className="flex gap-2">
          <DownloadButton scanId={id} format="pdf" />
          <DownloadButton scanId={id} format="json" />
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            {(["critical", "high", "medium", "low", "info"] as const).map((sev) => (
              <div key={sev} className="text-center">
                <Badge className={SEVERITY_BG[sev]} variant="secondary">
                  {sev.toUpperCase()}
                </Badge>
                <p className="mt-1 text-lg font-bold">{severityCounts[sev] || 0}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <ResultsTable results={results} />
    </div>
  );
}
