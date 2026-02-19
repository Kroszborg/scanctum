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
      className="rounded-lg p-5"
      style={{ background: "#141210", border: "1px solid #1e1c18" }}
    >
      <div className="mb-5">
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

      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={formatted} barSize={16}>
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
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(245,158,11,0.04)" }} />
          <Bar
            dataKey="count"
            fill="rgba(245,158,11,0.25)"
            radius={[2, 2, 0, 0]}
            stroke="#f59e0b"
            strokeWidth={1}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
