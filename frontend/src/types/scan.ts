export interface Scan {
  id: string;
  user_id: string;
  target_url: string;
  scan_mode: "quick" | "full";
  status: "pending" | "crawling" | "scanning" | "completed" | "failed" | "cancelled";
  progress_percent: number;
  pages_found: number;
  pages_scanned: number;
  celery_task_id: string | null;
  config: Record<string, unknown> | null;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface ScanCreate {
  target_url: string;
  scan_mode: "quick" | "full";
  config?: Record<string, unknown>;
}
