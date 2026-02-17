export const SEVERITY_COLORS = {
  critical: "#dc2626",
  high: "#ea580c",
  medium: "#ca8a04",
  low: "#16a34a",
  info: "#2563eb",
} as const;

export const SEVERITY_BG = {
  critical: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
  high: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400",
  medium: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
  low: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
  info: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
} as const;

export const OWASP_LABELS: Record<string, string> = {
  A01: "Broken Access Control",
  A02: "Cryptographic Failures",
  A03: "Injection",
  A04: "Insecure Design",
  A05: "Security Misconfiguration",
  A06: "Vulnerable Components",
  A07: "Auth Failures",
  A08: "Integrity Failures",
  A09: "Logging Failures",
  A10: "SSRF",
};

export const SCAN_STATUS_LABELS: Record<string, string> = {
  pending: "Pending",
  crawling: "Crawling",
  scanning: "Scanning",
  completed: "Completed",
  failed: "Failed",
  cancelled: "Cancelled",
};
