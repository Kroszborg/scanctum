export interface SeverityCount {
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
}

export interface RecentScan {
  id: string;
  target_url: string;
  status: string;
  scan_mode: string;
  vuln_count: number;
  created_at: string;
}

export interface DashboardStats {
  total_scans: number;
  active_scans: number;
  total_vulnerabilities: number;
  critical_count: number;
  severity_distribution: SeverityCount;
  recent_scans: RecentScan[];
  scans_over_time: { date: string; count: number }[];
}
