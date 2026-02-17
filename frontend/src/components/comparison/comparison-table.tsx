"use client";

import { Badge } from "@/components/ui/badge";
import { SEVERITY_BG } from "@/lib/constants";
import type { Vulnerability } from "@/types/vulnerability";

interface Props {
  title: string;
  vulnerabilities: Vulnerability[];
  variant: "new" | "fixed" | "unchanged";
}

const variantStyles = {
  new: "border-l-4 border-l-red-500",
  fixed: "border-l-4 border-l-green-500",
  unchanged: "border-l-4 border-l-gray-300",
};

export function ComparisonSection({ title, vulnerabilities, variant }: Props) {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold flex items-center gap-2">
        {title}
        <Badge variant="secondary">{vulnerabilities.length}</Badge>
      </h3>
      {vulnerabilities.length === 0 ? (
        <p className="text-sm text-muted-foreground">None</p>
      ) : (
        <div className="space-y-2">
          {vulnerabilities.map((v) => (
            <div key={v.id} className={`rounded-md border p-3 ${variantStyles[variant]}`}>
              <div className="flex items-center gap-2">
                <Badge className={SEVERITY_BG[v.severity]} variant="secondary">
                  {v.severity.toUpperCase()}
                </Badge>
                <span className="text-sm font-medium">{v.vuln_type}</span>
                <span className="text-xs text-muted-foreground ml-auto">CVSS {v.cvss_score}</span>
              </div>
              <p className="text-xs text-muted-foreground mt-1 truncate">{v.affected_url}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
