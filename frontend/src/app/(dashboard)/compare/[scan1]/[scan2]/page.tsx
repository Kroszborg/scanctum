"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ComparisonSection } from "@/components/comparison/comparison-table";
import { ArrowLeft } from "lucide-react";
import type { Vulnerability } from "@/types/vulnerability";

interface ComparisonData {
  scan_a_id: string;
  scan_b_id: string;
  new_vulnerabilities: Vulnerability[];
  fixed_vulnerabilities: Vulnerability[];
  unchanged_vulnerabilities: Vulnerability[];
  summary: { new: number; fixed: number; unchanged: number };
}

export default function ComparisonResultPage({
  params,
}: {
  params: Promise<{ scan1: string; scan2: string }>;
}) {
  const { scan1, scan2 } = use(params);
  const [data, setData] = useState<ComparisonData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<ComparisonData>(`/compare/${scan1}/${scan2}`)
      .then((res) => setData(res.data))
      .finally(() => setLoading(false));
  }, [scan1, scan2]);

  if (loading || !data) {
    return <div className="animate-pulse text-muted-foreground">Comparing scans...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/compare">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Scan Comparison</h1>
          <p className="text-muted-foreground">Comparing baseline vs current scan</p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-red-600">New Issues</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{data.summary.new}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-green-600">Fixed</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{data.summary.fixed}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-600">Unchanged</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{data.summary.unchanged}</p>
          </CardContent>
        </Card>
      </div>

      <div className="space-y-6">
        <ComparisonSection title="New Vulnerabilities" vulnerabilities={data.new_vulnerabilities} variant="new" />
        <ComparisonSection title="Fixed Vulnerabilities" vulnerabilities={data.fixed_vulnerabilities} variant="fixed" />
        <ComparisonSection title="Unchanged Vulnerabilities" vulnerabilities={data.unchanged_vulnerabilities} variant="unchanged" />
      </div>
    </div>
  );
}
