"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";
import { SEVERITY_COLORS } from "@/lib/constants";
import type { SeverityCount } from "@/types/dashboard";

export function SeverityChart({ distribution }: { distribution: SeverityCount }) {
  const data = [
    { name: "Critical", value: distribution.critical, fill: SEVERITY_COLORS.critical },
    { name: "High", value: distribution.high, fill: SEVERITY_COLORS.high },
    { name: "Medium", value: distribution.medium, fill: SEVERITY_COLORS.medium },
    { name: "Low", value: distribution.low, fill: SEVERITY_COLORS.low },
    { name: "Info", value: distribution.info, fill: SEVERITY_COLORS.info },
  ].filter((d) => d.value > 0);

  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Severity Distribution</CardTitle>
        </CardHeader>
        <CardContent className="flex h-[200px] items-center justify-center text-muted-foreground">
          No vulnerabilities found
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Severity Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={80}
              paddingAngle={2}
              dataKey="value"
            >
              {data.map((entry) => (
                <Cell key={entry.name} fill={entry.fill} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
