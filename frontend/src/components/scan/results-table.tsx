"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SEVERITY_BG, OWASP_LABELS } from "@/lib/constants";
import { VulnDetailDialog } from "@/components/scan/vuln-card";
import type { Vulnerability } from "@/types/vulnerability";

export function ResultsTable({ results }: { results: Vulnerability[] }) {
  const [selected, setSelected] = useState<Vulnerability | null>(null);
  const [filter, setFilter] = useState<string>("all");

  const filtered = filter === "all" ? results : results.filter((v) => v.severity === filter);

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        {["all", "critical", "high", "medium", "low", "info"].map((sev) => (
          <Button
            key={sev}
            variant={filter === sev ? "default" : "outline"}
            size="sm"
            onClick={() => setFilter(sev)}
          >
            {sev === "all" ? "All" : sev.charAt(0).toUpperCase() + sev.slice(1)}
            {sev !== "all" && (
              <span className="ml-1 text-xs">
                ({results.filter((v) => v.severity === sev).length})
              </span>
            )}
          </Button>
        ))}
      </div>

      <div className="rounded-lg border">
        <table className="w-full">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="px-4 py-3 text-left text-sm font-medium">Severity</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Vulnerability</th>
              <th className="px-4 py-3 text-left text-sm font-medium">CVSS</th>
              <th className="px-4 py-3 text-left text-sm font-medium">OWASP</th>
              <th className="px-4 py-3 text-left text-sm font-medium">URL</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((vuln) => (
              <tr
                key={vuln.id}
                className="border-b cursor-pointer hover:bg-muted/50 transition-colors"
                onClick={() => setSelected(vuln)}
              >
                <td className="px-4 py-3">
                  <Badge className={SEVERITY_BG[vuln.severity]} variant="secondary">
                    {vuln.severity.toUpperCase()}
                  </Badge>
                </td>
                <td className="px-4 py-3 text-sm font-medium">{vuln.vuln_type}</td>
                <td className="px-4 py-3 text-sm">{vuln.cvss_score}</td>
                <td className="px-4 py-3 text-sm" title={OWASP_LABELS[vuln.owasp_category]}>
                  {vuln.owasp_category}
                </td>
                <td className="px-4 py-3 text-sm max-w-[200px] truncate">{vuln.affected_url}</td>
                <td className="px-4 py-3 text-sm capitalize">{vuln.confidence}</td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                  No vulnerabilities found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {selected && (
        <VulnDetailDialog vuln={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  );
}
