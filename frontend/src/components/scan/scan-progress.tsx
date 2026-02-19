"use client";

import { SCAN_STATUS_LABELS } from "@/lib/constants";
import type { Scan } from "@/types/scan";

const STATUS_CONFIG: Record<string, { color: string; glow: string; badgeCls: string }> = {
  pending:   { color: "#f59e0b", glow: "rgba(245,158,11,0.4)",  badgeCls: "badge-pending" },
  crawling:  { color: "#38bdf8", glow: "rgba(56,189,248,0.4)",  badgeCls: "badge-crawling" },
  scanning:  { color: "#06b6d4", glow: "rgba(6,182,212,0.4)",   badgeCls: "badge-scanning" },
  completed: { color: "#4ade80", glow: "rgba(74,222,128,0.4)",  badgeCls: "badge-completed" },
  failed:    { color: "#f43f5e", glow: "rgba(244,63,94,0.4)",   badgeCls: "badge-failed" },
  cancelled: { color: "#564e45", glow: "transparent",           badgeCls: "badge-cancelled" },
};

export function ScanProgress({ scan }: { scan: Scan }) {
  const isRunning = ["pending", "crawling", "scanning"].includes(scan.status);
  const cfg = STATUS_CONFIG[scan.status] ?? STATUS_CONFIG.cancelled;
  const pct = scan.progress_percent ?? 0;

  return (
    <div className="flex gap-8 items-start">
      {/* Radar / status visual */}
      <div className="shrink-0 relative flex items-center justify-center" style={{ width: 88, height: 88 }}>
        {/* Outer ring */}
        <div
          className="absolute inset-0 rounded-full"
          style={{ border: `1px solid ${cfg.color}20` }}
        />
        {/* Mid ring */}
        <div
          className="absolute rounded-full"
          style={{
            inset: "12px",
            border: `1px solid ${cfg.color}25`,
          }}
        />
        {/* Inner ring */}
        <div
          className="absolute rounded-full"
          style={{
            inset: "24px",
            border: `1px solid ${cfg.color}30`,
          }}
        />

        {/* Sonar rings (only when running) */}
        {isRunning && (
          <>
            <div
              className="absolute rounded-full"
              style={{
                inset: "8px",
                border: `1px solid ${cfg.color}50`,
                animation: "sonar-ring 2s ease-out infinite",
              }}
            />
            <div
              className="absolute rounded-full"
              style={{
                inset: "8px",
                border: `1px solid ${cfg.color}40`,
                animation: "sonar-ring 2s ease-out infinite 0.7s",
              }}
            />
          </>
        )}

        {/* Sweep (only when running) */}
        {isRunning && (
          <div
            className="absolute inset-0 rounded-full overflow-hidden"
            style={{ animation: "radar-sweep 3s linear infinite" }}
          >
            <div
              style={{
                position: "absolute",
                top: "50%",
                left: "50%",
                width: "50%",
                height: "1px",
                transformOrigin: "0 50%",
                background: `linear-gradient(90deg, ${cfg.color}00, ${cfg.color})`,
              }}
            />
          </div>
        )}

        {/* Center dot */}
        <div
          className="relative z-10 rounded-full"
          style={{
            width: 8,
            height: 8,
            background: cfg.color,
            boxShadow: `0 0 10px 2px ${cfg.glow}`,
          }}
        />

        {/* Percentage overlay */}
        {isRunning && (
          <div
            className="absolute bottom-0 left-0 right-0 text-center text-[9px] tabular-nums"
            style={{ fontFamily: "JetBrains Mono, monospace", color: cfg.color }}
          >
            {pct}%
          </div>
        )}
      </div>

      {/* Info */}
      <div className="flex-1 space-y-4">
        {/* Status badge */}
        <div className="flex items-center gap-3">
          <span
            className={`text-[9px] tracking-widest uppercase px-2 py-0.5 rounded ${cfg.badgeCls}`}
            style={{ fontFamily: "JetBrains Mono, monospace" }}
          >
            {SCAN_STATUS_LABELS[scan.status] || scan.status}
          </span>
          {isRunning && (
            <span
              className="text-[10px] animate-cursor"
              style={{ fontFamily: "JetBrains Mono, monospace", color: cfg.color }}
            >
              _
            </span>
          )}
        </div>

        {/* Progress bar */}
        {isRunning && (
          <div>
            <div
              className="h-[3px] rounded-full overflow-hidden"
              style={{ background: "#1c1916" }}
            >
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${pct}%`,
                  background: `linear-gradient(90deg, ${cfg.color}80, ${cfg.color})`,
                  boxShadow: `0 0 8px 0 ${cfg.glow}`,
                }}
              />
            </div>
            <div
              className="mt-1 text-[9px] tabular-nums"
              style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
            >
              {pct}% complete
            </div>
          </div>
        )}

        {/* Stats row */}
        <div className="flex gap-6">
          {[
            { label: "Pages found", value: scan.pages_found },
            { label: "Pages scanned", value: scan.pages_scanned },
            { label: "Mode", value: scan.scan_mode?.toUpperCase() },
          ].map(({ label, value }) => (
            <div key={label}>
              <div
                className="text-[9px] tracking-widest uppercase mb-0.5"
                style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
              >
                {label}
              </div>
              <div
                className="text-[14px] font-medium tabular-nums"
                style={{ fontFamily: "JetBrains Mono, monospace", color: "#8a7f74" }}
              >
                {value ?? "—"}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
