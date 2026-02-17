"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Scan, AlertTriangle, Shield, Activity } from "lucide-react";
import type { DashboardStats } from "@/types/dashboard";

export function StatsCards({ stats }: { stats: DashboardStats }) {
  const cards = [
    {
      title: "Total Scans",
      value: stats.total_scans,
      icon: Scan,
      color: "text-blue-600",
    },
    {
      title: "Active Scans",
      value: stats.active_scans,
      icon: Activity,
      color: "text-green-600",
    },
    {
      title: "Vulnerabilities",
      value: stats.total_vulnerabilities,
      icon: AlertTriangle,
      color: "text-orange-600",
    },
    {
      title: "Critical Issues",
      value: stats.critical_count,
      icon: Shield,
      color: "text-red-600",
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <Card key={card.title}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{card.title}</CardTitle>
            <card.icon className={`h-4 w-4 ${card.color}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{card.value}</div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
