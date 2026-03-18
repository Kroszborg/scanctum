"use client";

import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts";
import { Activity } from "lucide-react";

interface Props {
  data: { date: string; count: number }[];
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: { value: number }[]; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div
      className="rounded-lg px-3 py-2 text-xs"
      style={{
        fontFamily: "Manrope, sans-serif",
        background: "rgba(20, 20, 20, 0.95)",
        backdropFilter: "blur(8px)",
        border: "1px solid rgba(255, 255, 255, 0.1)",
        color: "#F5F5F5",
        boxShadow: "0 4px 16px rgba(0, 0, 0, 0.3)",
      }}
    >
      <div style={{ color: "#737373", marginBottom: 4 }}>{label}</div>
      <div style={{ color: "#a855f7", fontWeight: 600 }}>{payload[0].value} scans</div>
    </div>
  );
}

export function ScanHistoryChart({ data }: Props) {
  const formatted = data.map((d) => ({
    ...d,
    date: new Date(d.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
  }));

  return (
    <div className="h-full">
      {data.length === 0 ? (
        <div className="flex h-[200px] flex-col items-center justify-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-500/10 to-purple-500/10 border border-cyan-500/20">
            <Activity className="h-6 w-6 text-neutral-600" />
          </div>
          <p className="text-sm text-neutral-500" style={{ fontFamily: "Manrope, sans-serif" }}>
            No scan activity yet
          </p>
        </div>
      ) : (
        <div className="h-full">
          {/* Header */}
          <div className="mb-4 flex items-center justify-between">
            <div>
              <div
                className="mb-1 text-[9px] tracking-[0.3em] uppercase text-neutral-500"
                style={{ fontFamily: "JetBrains Mono, monospace" }}
              >
                Activity
              </div>
              <div className="text-lg font-light text-neutral-300" style={{ fontFamily: "Libre Caslon Text, serif" }}>
                Scan Frequency
              </div>
            </div>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-500/20 to-cyan-500/5 border border-cyan-500/20">
              <Activity className="h-4 w-4" style={{ color: "#06b6d4" }} />
            </div>
          </div>

          {/* Chart */}
          <div className="rounded-xl bg-neutral-900/50 p-4 border border-white/[0.02]">
            <ResponsiveContainer width="100%" height={140}>
              <BarChart data={formatted} barSize={12}>
                <defs>
                  <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#a855f7" stopOpacity={0.8} />
                    <stop offset="100%" stopColor="#a855f7" stopOpacity={0.3} />
                  </linearGradient>
                  <linearGradient id="activeBar" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#06b6d4" stopOpacity={0.8} />
                    <stop offset="100%" stopColor="#06b6d4" stopOpacity={0.3} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="date"
                  fontSize={9}
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: "#525252", fontFamily: "JetBrains Mono, monospace", fontSize: 9 }}
                  dy={8}
                />
                <YAxis
                  fontSize={9}
                  tickLine={false}
                  axisLine={false}
                  allowDecimals={false}
                  tick={{ fill: "#525252", fontFamily: "JetBrains Mono, monospace", fontSize: 9 }}
                  width={16}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar
                  dataKey="count"
                  fill="url(#barGradient)"
                  radius={[6, 6, 0, 0]}
                  style={{
                    filter: "drop-shadow(0 0 8px rgba(168, 85, 247, 0.3))",
                  }}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
