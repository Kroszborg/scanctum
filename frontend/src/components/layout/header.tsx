"use client";

import { Moon, Sun, LogOut, Bell } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { useTheme } from "@/providers/theme-provider";

export function Header() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  return (
    <header
      className="flex h-[60px] items-center justify-between px-6"
      style={{
        background: "#0c0a08",
        borderBottom: "1px solid #1e1c18",
      }}
    >
      {/* Left: current operator */}
      <div className="flex items-center gap-2">
        <span
          className="text-[9px] tracking-widest uppercase"
          style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
        >
          OPERATOR
        </span>
        <span
          className="text-[11px] font-medium"
          style={{ fontFamily: "JetBrains Mono, monospace", color: "#8a7f74" }}
        >
          {user?.email ?? "-"}
        </span>
        {user?.role && (
          <span
            className="rounded px-1.5 py-0.5 text-[9px] font-semibold tracking-widest uppercase"
            style={{
              fontFamily: "JetBrains Mono, monospace",
              background: "rgba(245,158,11,0.1)",
              color: "#f59e0b",
              border: "1px solid rgba(245,158,11,0.2)",
            }}
          >
            {user.role}
          </span>
        )}
      </div>

      {/* Right: actions */}
      <div className="flex items-center gap-1">
        <button
          onClick={toggleTheme}
          className="flex h-8 w-8 items-center justify-center rounded transition-colors"
          style={{ color: "#4a4440" }}
          onMouseEnter={(e) => (e.currentTarget.style.color = "#e8e0d5")}
          onMouseLeave={(e) => (e.currentTarget.style.color = "#4a4440")}
        >
          {theme === "dark" ? (
            <Sun className="h-3.5 w-3.5" />
          ) : (
            <Moon className="h-3.5 w-3.5" />
          )}
        </button>

        <div className="mx-2 h-4 w-px" style={{ background: "#1e1c18" }} />

        <button
          onClick={logout}
          className="flex items-center gap-2 rounded px-3 py-1.5 text-[11px] font-medium transition-all"
          style={{ color: "#6b6259", fontFamily: "JetBrains Mono, monospace" }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = "#f43f5e";
            e.currentTarget.style.background = "rgba(244,63,94,0.06)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = "#6b6259";
            e.currentTarget.style.background = "transparent";
          }}
        >
          <LogOut className="h-3.5 w-3.5" />
          Sign out
        </button>
      </div>
    </header>
  );
}
