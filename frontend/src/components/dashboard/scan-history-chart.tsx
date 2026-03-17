"use client";

import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts";

interface Props {
  data: { date: string; count: number }[];
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: { value: number }[]; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div
      className="rounded px-3 py-2 text-[11px]"
      style={{
        fontFamily: "JetBrains Mono, monospace",
        background: "#1c1916",
        border: "1px solid #2c2820",
        color: "#e8e0d5",
      }}
    >
      <div style={{ color: "#4a4440" }}>{label}</div>
      <div style={{ color: "#f59e0b" }}>{payload[0].value} scans</div>
    </div>
  );
}

export function ScanHistoryChart({ data }: Props) {
  const formatted = data.map((d) => ({
    ...d,
    date: new Date(d.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
  }));

  return (
    <div
      className="rounded-xl p-5 transition-all duration-300"
      style={{
        background: "#141210",
        border: "1px solid #1e1c18",
        boxShadow: "0 0 0 0 rgba(245, 158, 11, 0)",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = "0 8px 32px -12px rgba(245, 158, 11, 0.15)";
        e.currentTarget.style.borderColor = "rgba(245, 158, 11, 0.3)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = "0 0 0 0 rgba(245, 158, 11, 0)";
        e.currentTarget.style.borderColor = "#1e1c18";
      }}
    >
      <div className="mb-5 flex items-center justify-between">
        <div>
          <div
            className="text-[9px] tracking-[0.2em] uppercase"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
          >
            Scan Activity
          </div>
          <div
            className="text-[13px] font-medium mt-1"
            style={{ color: "#8a7f74" }}
          >
            Scans over time
          </div>
        </div>
        <div
          className="flex h-8 w-8 items-center justify-center rounded-lg"
          style={{
            background: "rgba(245, 158, 11, 0.08)",
            border: "1px solid rgba(245, 158, 11, 0.2)",
          }}
        >
          <svg
            className="h-4 w-4"
            style={{ color: "#f59e0b" }}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 10V3L4 14h7v7l9-11h-7z"
            />
          </svg>
        </div>
      </div>

      <div className="rounded-lg p-4" style={{ background: "#0f0d0b" }}>
        <ResponsiveContainer width="100%" height={160}>
          <BarChart data={formatted} barSize={20}>
            <defs>
              <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.6} />
                <stop offset="100%" stopColor="#f59e0b" stopOpacity={0.2} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="date"
              fontSize={9}
              tickLine={false}
              axisLine={false}
              tick={{ fill: "#4a4440", fontFamily: "JetBrains Mono, monospace" }}
            />
            <YAxis
              fontSize={9}
              tickLine={false}
              axisLine={false}
              allowDecimals={false}
              tick={{ fill: "#4a4440", fontFamily: "JetBrains Mono, monospace" }}
              width={20}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(245,158,11,0.08)" }} />
            <Bar
              dataKey="count"
              fill="url(#barGradient)"
              radius={[4, 4, 0, 0]}
              stroke="#f59e0b"
              strokeWidth={1.5}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
