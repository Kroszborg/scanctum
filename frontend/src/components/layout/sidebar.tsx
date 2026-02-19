"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Scan,
  GitCompareArrows,
  Settings,
  Shield,
  ShieldAlert,
  Globe,
  Clock,
} from "lucide-react";

const navItems = [
  { href: "/dashboard",  label: "Overview",    icon: LayoutDashboard, code: "01" },
  { href: "/scans",      label: "Scans",       icon: Scan,            code: "02" },
  { href: "/compare",    label: "Compare",     icon: GitCompareArrows,code: "03" },
  { href: "/vuln-db",    label: "Vuln DB",     icon: ShieldAlert,     code: "04" },
  { href: "/assets",     label: "Assets",      icon: Globe,           code: "05" },
  { href: "/schedules",  label: "Schedules",   icon: Clock,           code: "06" },
  { href: "/settings",   label: "Settings",    icon: Settings,        code: "07" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside
      className="flex h-screen w-[220px] flex-col"
      style={{
        background: "#0a0908",
        borderRight: "1px solid #1e1c18",
      }}
    >
      {/* Logo */}
      <div
        className="flex h-[60px] items-center gap-3 px-5"
        style={{ borderBottom: "1px solid #1e1c18" }}
      >
        <div
          className="flex h-8 w-8 items-center justify-center rounded"
          style={{
            background: "rgba(245,158,11,0.12)",
            border: "1px solid rgba(245,158,11,0.3)",
          }}
        >
          <Shield className="h-4 w-4" style={{ color: "#f59e0b" }} />
        </div>
        <div>
          <div
            className="text-[13px] font-bold tracking-[0.15em] uppercase"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#e8e0d5", letterSpacing: "0.12em" }}
          >
            SCANCTUM
          </div>
          <div
            className="text-[9px] tracking-widest uppercase"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
          >
            v0.2.0
          </div>
        </div>
      </div>

      {/* Nav label */}
      <div className="px-5 pt-5 pb-2">
        <span
          className="text-[9px] font-semibold tracking-[0.2em] uppercase"
          style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
        >
          Navigation
        </span>
      </div>

      {/* Nav items */}
      <nav className="flex-1 space-y-0.5 px-3 overflow-y-auto">
        {navItems.map((item) => {
          const isActive =
            item.href === "/dashboard"
              ? pathname === "/dashboard"
              : pathname.startsWith(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group relative flex items-center gap-3 rounded px-3 py-2.5 text-sm transition-all duration-150",
                isActive
                  ? "text-[#f59e0b]"
                  : "text-[#6b6259] hover:text-[#e8e0d5]"
              )}
              style={{
                background: isActive ? "rgba(245,158,11,0.07)" : "transparent",
                ...(isActive && { outline: "none" }),
              }}
            >
              {/* Active left border */}
              {isActive && (
                <span
                  className="absolute left-0 top-1/2 -translate-y-1/2 w-[2px] h-[60%] rounded-r"
                  style={{ background: "#f59e0b" }}
                />
              )}

              {/* Code number */}
              <span
                className="text-[9px] w-4 shrink-0 tabular-nums"
                style={{
                  fontFamily: "JetBrains Mono, monospace",
                  color: isActive ? "rgba(245,158,11,0.5)" : "#2c2820",
                }}
              >
                {item.code}
              </span>

              <item.icon className="h-[15px] w-[15px] shrink-0" />

              <span className="text-[13px] font-medium tracking-wide">
                {item.label}
              </span>
            </Link>
          );
        })}
      </nav>

      {/* Status footer */}
      <div className="px-5 py-4" style={{ borderTop: "1px solid #1e1c18" }}>
        <div className="flex items-center gap-2">
          <span
            className="h-1.5 w-1.5 rounded-full"
            style={{
              background: "#4ade80",
              boxShadow: "0 0 6px 1px rgba(74,222,128,0.5)",
            }}
          />
          <span
            className="text-[10px] tracking-widest uppercase"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
          >
            System Online
          </span>
        </div>
      </div>
    </aside>
  );
}
