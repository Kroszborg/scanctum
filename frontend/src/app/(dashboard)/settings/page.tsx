"use client";

import { useAuth } from "@/hooks/use-auth";
import { LogOut, User, Mail, Shield } from "lucide-react";

export default function SettingsPage() {
  const { user, logout } = useAuth();

  return (
    <div className="space-y-6 animate-fade-up">
      <div>
        <div
          className="text-[9px] tracking-[0.25em] uppercase mb-1"
          style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
        >
          Configuration
        </div>
        <h1 className="text-[24px] font-bold" style={{ color: "#e8e0d5" }}>
          Settings
        </h1>
      </div>

      {/* Profile */}
      <div
        className="max-w-2xl rounded-lg overflow-hidden"
        style={{ border: "1px solid #1e1c18" }}
      >
        <div
          className="px-5 py-3"
          style={{ background: "#141210", borderBottom: "1px solid #1e1c18" }}
        >
          <span
            className="text-[9px] tracking-[0.2em] uppercase"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
          >
            Operator Profile
          </span>
        </div>
        <div className="p-5 space-y-4" style={{ background: "#0c0a08" }}>
          {[
            { icon: User,   label: "Full Name", value: user?.full_name },
            { icon: Mail,   label: "Email",     value: user?.email },
            { icon: Shield, label: "Role",      value: user?.role },
          ].map(({ icon: Icon, label, value }) => (
            <div key={label} className="flex items-center gap-4">
              <div
                className="flex h-8 w-8 items-center justify-center rounded shrink-0"
                style={{ background: "#141210", border: "1px solid #1e1c18" }}
              >
                <Icon className="h-3.5 w-3.5" style={{ color: "#4a4440" }} />
              </div>
              <div>
                <div
                  className="text-[9px] tracking-widest uppercase"
                  style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
                >
                  {label}
                </div>
                <div
                  className="text-[13px] font-medium mt-0.5"
                  style={{ color: "#8a7f74" }}
                >
                  {value ?? "—"}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Session */}
      <div
        className="max-w-2xl rounded-lg overflow-hidden"
        style={{ border: "1px solid #1e1c18" }}
      >
        <div
          className="px-5 py-3"
          style={{ background: "#141210", borderBottom: "1px solid #1e1c18" }}
        >
          <span
            className="text-[9px] tracking-[0.2em] uppercase"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
          >
            Session
          </span>
        </div>
        <div className="p-5" style={{ background: "#0c0a08" }}>
          <p
            className="text-[12px] mb-4"
            style={{ color: "#4a4440" }}
          >
            Terminate your current operator session and return to the login screen.
          </p>
          <button
            onClick={logout}
            className="flex items-center gap-2 rounded px-4 py-2 text-[11px] font-semibold tracking-widest uppercase transition-all"
            style={{
              fontFamily: "JetBrains Mono, monospace",
              background: "rgba(244,63,94,0.08)",
              border: "1px solid rgba(244,63,94,0.2)",
              color: "#f43f5e",
              cursor: "pointer",
            }}
            onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(244,63,94,0.14)"; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = "rgba(244,63,94,0.08)"; }}
          >
            <LogOut className="h-3.5 w-3.5" />
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}
