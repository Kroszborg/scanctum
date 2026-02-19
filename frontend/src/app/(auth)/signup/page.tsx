"use client";

import { useState } from "react";
import Link from "next/link";
import { Shield } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";

export default function SignupPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { signup } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await signup(email, password, fullName);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Registration failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const inputStyle = {
    fontFamily: "JetBrains Mono, monospace",
    background: "#0c0a08",
    border: "1px solid #2c2820",
    color: "#e8e0d5",
  };

  return (
    <div className="w-full max-w-sm">
      {/* Logo */}
      <div className="mb-10 flex flex-col items-center gap-3">
        <div
          className="flex h-12 w-12 items-center justify-center rounded"
          style={{
            background: "rgba(245,158,11,0.1)",
            border: "1px solid rgba(245,158,11,0.3)",
          }}
        >
          <Shield className="h-6 w-6" style={{ color: "#f59e0b" }} />
        </div>
        <div className="text-center">
          <div
            className="text-[15px] font-bold tracking-[0.2em] uppercase"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#e8e0d5" }}
          >
            SCANCTUM
          </div>
          <div
            className="text-[10px] tracking-widest uppercase mt-0.5"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
          >
            Security Assessment Platform
          </div>
        </div>
      </div>

      {/* Card */}
      <div
        className="rounded-lg p-7"
        style={{
          background: "#141210",
          border: "1px solid #2c2820",
        }}
      >
        <div className="mb-6">
          <div
            className="text-[10px] tracking-[0.25em] uppercase mb-1"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
          >
            Registration
          </div>
          <h1
            className="text-[20px] font-bold"
            style={{ color: "#e8e0d5" }}
          >
            Create Operator Account
          </h1>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label
              className="block text-[10px] tracking-[0.15em] uppercase"
              style={{ fontFamily: "JetBrains Mono, monospace", color: "#6b6259" }}
            >
              Full Name
            </label>
            <input
              type="text"
              placeholder="Jane Doe"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
              className="w-full rounded px-3 py-2.5 text-[13px] outline-none transition-all"
              style={inputStyle}
              onFocus={(e) => (e.currentTarget.style.borderColor = "rgba(245,158,11,0.5)")}
              onBlur={(e) => (e.currentTarget.style.borderColor = "#2c2820")}
            />
          </div>

          <div className="space-y-1.5">
            <label
              className="block text-[10px] tracking-[0.15em] uppercase"
              style={{ fontFamily: "JetBrains Mono, monospace", color: "#6b6259" }}
            >
              Email Address
            </label>
            <input
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full rounded px-3 py-2.5 text-[13px] outline-none transition-all"
              style={inputStyle}
              onFocus={(e) => (e.currentTarget.style.borderColor = "rgba(245,158,11,0.5)")}
              onBlur={(e) => (e.currentTarget.style.borderColor = "#2c2820")}
            />
          </div>

          <div className="space-y-1.5">
            <label
              className="block text-[10px] tracking-[0.15em] uppercase"
              style={{ fontFamily: "JetBrains Mono, monospace", color: "#6b6259" }}
            >
              Password
            </label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              className="w-full rounded px-3 py-2.5 text-[13px] outline-none transition-all"
              style={inputStyle}
              onFocus={(e) => (e.currentTarget.style.borderColor = "rgba(245,158,11,0.5)")}
              onBlur={(e) => (e.currentTarget.style.borderColor = "#2c2820")}
            />
          </div>

          {error && (
            <div
              className="rounded px-3 py-2 text-[11px]"
              style={{
                fontFamily: "JetBrains Mono, monospace",
                background: "rgba(244,63,94,0.08)",
                border: "1px solid rgba(244,63,94,0.2)",
                color: "#f43f5e",
              }}
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded px-4 py-2.5 text-[12px] font-semibold tracking-widest uppercase transition-all"
            style={{
              fontFamily: "JetBrains Mono, monospace",
              background: loading ? "rgba(245,158,11,0.15)" : "rgba(245,158,11,0.12)",
              border: "1px solid rgba(245,158,11,0.35)",
              color: loading ? "#a87c2a" : "#f59e0b",
              cursor: loading ? "not-allowed" : "pointer",
            }}
            onMouseEnter={(e) => {
              if (!loading) e.currentTarget.style.background = "rgba(245,158,11,0.2)";
            }}
            onMouseLeave={(e) => {
              if (!loading) e.currentTarget.style.background = "rgba(245,158,11,0.12)";
            }}
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="animate-cursor">_</span>
                Registering
              </span>
            ) : (
              "Register Account"
            )}
          </button>
        </form>

        <div className="mt-5 pt-5" style={{ borderTop: "1px solid #1e1c18" }}>
          <p
            className="text-center text-[11px]"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
          >
            Already registered?{" "}
            <Link
              href="/login"
              className="transition-colors"
              style={{ color: "#6b6259" }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "#f59e0b")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "#6b6259")}
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>

      <p
        className="mt-6 text-center text-[10px] tracking-widest uppercase"
        style={{ fontFamily: "JetBrains Mono, monospace", color: "#2c2820" }}
      >
        First account becomes admin
      </p>
    </div>
  );
}
