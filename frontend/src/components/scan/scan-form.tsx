"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useScans } from "@/hooks/use-scans";

export function ScanForm() {
  const [url, setUrl] = useState("");
  const [mode, setMode] = useState<"quick" | "full">("quick");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const { createScan } = useScans();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const scan = await createScan({ target_url: url, scan_mode: mode });
      router.push(`/scans/${scan.id}`);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Failed to create scan";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Card className="max-w-2xl">
      <CardHeader>
        <CardTitle>New Scan</CardTitle>
        <CardDescription>Enter a target URL to begin a security assessment</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Target URL</label>
            <Input
              type="url"
              placeholder="https://example.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Scan Mode</label>
            <Select value={mode} onValueChange={(v) => setMode(v as "quick" | "full")}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="quick">Quick Scan (passive + light active, ~5 min)</SelectItem>
                <SelectItem value="full">Full Scan (all modules, 15-45 min)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <Button type="submit" disabled={submitting}>
            {submitting ? "Starting..." : "Start Scan"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
