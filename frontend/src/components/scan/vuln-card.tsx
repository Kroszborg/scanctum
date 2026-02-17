"use client";

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { SEVERITY_BG, OWASP_LABELS } from "@/lib/constants";
import type { Vulnerability } from "@/types/vulnerability";

interface Props {
  vuln: Vulnerability;
  onClose: () => void;
}

export function VulnDetailDialog({ vuln, onClose }: Props) {
  return (
    <Dialog open onOpenChange={() => onClose()}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <Badge className={SEVERITY_BG[vuln.severity]} variant="secondary">
              {vuln.severity.toUpperCase()}
            </Badge>
            <DialogTitle>{vuln.vuln_type}</DialogTitle>
          </div>
          <DialogDescription>
            CVSS {vuln.cvss_score} | {vuln.owasp_category} - {OWASP_LABELS[vuln.owasp_category]} | {vuln.cwe_id}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <h4 className="text-sm font-semibold mb-1">Affected URL</h4>
            <p className="text-sm text-muted-foreground break-all">{vuln.affected_url}</p>
            {vuln.affected_parameter && (
              <p className="text-sm text-muted-foreground">Parameter: {vuln.affected_parameter}</p>
            )}
          </div>

          <div>
            <h4 className="text-sm font-semibold mb-1">Description</h4>
            <p className="text-sm">{vuln.description}</p>
          </div>

          <div>
            <h4 className="text-sm font-semibold mb-1">Remediation</h4>
            <div className="rounded-md border-l-4 border-green-500 bg-green-50 dark:bg-green-900/20 p-3">
              <p className="text-sm">{vuln.remediation}</p>
            </div>
          </div>

          <div>
            <h4 className="text-sm font-semibold mb-1">Details</h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div><span className="text-muted-foreground">Module:</span> {vuln.module_name}</div>
              <div><span className="text-muted-foreground">Confidence:</span> {vuln.confidence}</div>
              <div><span className="text-muted-foreground">CVSS Vector:</span> <code className="text-xs">{vuln.cvss_vector}</code></div>
            </div>
          </div>

          {vuln.evidence.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold mb-2">Evidence</h4>
              {vuln.evidence.map((ev) => (
                <div key={ev.id} className="mb-3">
                  <p className="text-xs font-medium text-muted-foreground mb-1">{ev.title}</p>
                  <pre className="rounded-md bg-muted p-3 text-xs overflow-x-auto whitespace-pre-wrap">
                    {ev.content}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
