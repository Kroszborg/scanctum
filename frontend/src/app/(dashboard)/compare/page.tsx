"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useScans } from "@/hooks/use-scans";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export default function ComparePage() {
  const { scans, loading } = useScans();
  const [scanA, setScanA] = useState("");
  const [scanB, setScanB] = useState("");
  const router = useRouter();

  const completedScans = scans.filter((s) => s.status === "completed");

  const handleCompare = () => {
    if (scanA && scanB && scanA !== scanB) {
      router.push(`/compare/${scanA}/${scanB}`);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Compare Scans</h1>
        <p className="text-muted-foreground">Compare findings between two scans to track security changes</p>
      </div>

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>Select Scans</CardTitle>
          <CardDescription>Choose two completed scans to compare</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Scan A (baseline)</label>
            <Select value={scanA} onValueChange={setScanA}>
              <SelectTrigger>
                <SelectValue placeholder="Select scan..." />
              </SelectTrigger>
              <SelectContent>
                {completedScans.map((s) => (
                  <SelectItem key={s.id} value={s.id}>
                    {s.target_url} ({new Date(s.created_at).toLocaleDateString()})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Scan B (current)</label>
            <Select value={scanB} onValueChange={setScanB}>
              <SelectTrigger>
                <SelectValue placeholder="Select scan..." />
              </SelectTrigger>
              <SelectContent>
                {completedScans.map((s) => (
                  <SelectItem key={s.id} value={s.id}>
                    {s.target_url} ({new Date(s.created_at).toLocaleDateString()})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button onClick={handleCompare} disabled={!scanA || !scanB || scanA === scanB}>
            Compare
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
