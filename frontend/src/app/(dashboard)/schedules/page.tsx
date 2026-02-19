"use client";

import { useState, useEffect, useCallback } from "react";
import api from "@/lib/api";
import { Clock, Plus, Trash2, ToggleLeft, ToggleRight, X, Check } from "lucide-react";

interface Schedule {
  id: string;
  user_id: string;
  target_url: string;
  scan_mode: "quick" | "full";
  cron_expression: string;
  label: string | null;
  is_active: boolean;
  last_run_at: string | null;
  next_run_at: string | null;
  created_at: string;
}

// Friendly cron presets
const CRON_PRESETS = [
  { label: "Every hour",        cron: "0 * * * *"   },
  { label: "Every 6 hours",     cron: "0 */6 * * *" },
  { label: "Daily at 02:00",    cron: "0 2 * * *"   },
  { label: "Weekly (Mon 03:00)",cron: "0 3 * * 1"   },
  { label: "Monthly (1st)",     cron: "0 4 1 * *"   },
  { label: "Custom…",           cron: ""            },
];

const EMPTY_FORM = {
  target_url: "",
  scan_mode: "quick" as "quick" | "full",
  cron_expression: "0 2 * * *",
  label: "",
  is_active: true,
};

export default function SchedulesPage() {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [customCron, setCustomCron] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSchedules = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.get<Schedule[]>("/schedules");
      setSchedules(r.data);
    } catch {
      setSchedules([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchSchedules(); }, [fetchSchedules]);

  const handleCreate = async () => {
    if (!form.target_url || !form.cron_expression) return;
    setSaving(true);
    setError(null);
    try {
      await api.post("/schedules", {
        target_url: form.target_url,
        scan_mode: form.scan_mode,
        cron_expression: form.cron_expression,
        label: form.label || null,
        is_active: form.is_active,
      });
      setForm(EMPTY_FORM);
      setShowForm(false);
      await fetchSchedules();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err?.response?.data?.detail ?? "Failed to create schedule");
    } finally {
      setSaving(false);
    }
  };

  const handleToggle = async (schedule: Schedule) => {
    try {
      await api.patch(`/schedules/${schedule.id}`, { is_active: !schedule.is_active });
      await fetchSchedules();
    } catch {
      // silent
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/schedules/${id}`);
      await fetchSchedules();
    } catch {
      // silent
    }
  };

  const handlePresetChange = (cron: string) => {
    if (cron === "") {
      setCustomCron(true);
    } else {
      setCustomCron(false);
      setForm((f) => ({ ...f, cron_expression: cron }));
    }
  };

  const inputStyle = {
    background: "#0c0a08",
    border: "1px solid #2c2820",
    borderRadius: "4px",
    color: "#e8e0d5",
    fontFamily: "JetBrains Mono, monospace",
    fontSize: "12px",
    padding: "6px 10px",
    outline: "none",
    width: "100%",
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div
            className="text-[9px] tracking-[0.25em] uppercase mb-1"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
          >
            Automation
          </div>
          <h1 className="text-[24px] font-bold" style={{ color: "#e8e0d5" }}>
            Scheduled Scans
          </h1>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 rounded px-4 py-2 text-[11px] font-semibold tracking-widest uppercase transition-all"
          style={{
            fontFamily: "JetBrains Mono, monospace",
            background: "rgba(245,158,11,0.1)",
            border: "1px solid rgba(245,158,11,0.3)",
            color: "#f59e0b",
          }}
          onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(245,158,11,0.18)"; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = "rgba(245,158,11,0.1)"; }}
        >
          <Plus className="h-3.5 w-3.5" />
          New Schedule
        </button>
      </div>

      {/* Create form */}
      {showForm && (
        <div className="rounded-lg p-5 space-y-4" style={{ background: "#141210", border: "1px solid rgba(245,158,11,0.2)" }}>
          <div className="flex items-center justify-between">
            <span className="text-[11px] tracking-widest uppercase" style={{ fontFamily: "JetBrains Mono, monospace", color: "#f59e0b" }}>
              New Schedule
            </span>
            <button onClick={() => { setShowForm(false); setError(null); }}>
              <X className="h-4 w-4" style={{ color: "#4a4440" }} />
            </button>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            {/* Target URL */}
            <div className="md:col-span-2">
              <label className="block text-[9px] tracking-widest uppercase mb-1.5" style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}>
                Target URL *
              </label>
              <input
                type="url"
                placeholder="https://example.com"
                value={form.target_url}
                onChange={(e) => setForm((f) => ({ ...f, target_url: e.target.value }))}
                style={inputStyle}
              />
            </div>

            {/* Label */}
            <div>
              <label className="block text-[9px] tracking-widest uppercase mb-1.5" style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}>
                Label (optional)
              </label>
              <input
                type="text"
                placeholder="Production weekly check"
                value={form.label}
                onChange={(e) => setForm((f) => ({ ...f, label: e.target.value }))}
                style={inputStyle}
              />
            </div>

            {/* Scan mode */}
            <div>
              <label className="block text-[9px] tracking-widest uppercase mb-1.5" style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}>
                Scan Mode
              </label>
              <div className="flex gap-2">
                {(["quick", "full"] as const).map((m) => (
                  <button
                    key={m}
                    onClick={() => setForm((f) => ({ ...f, scan_mode: m }))}
                    className="flex-1 py-1.5 rounded text-[10px] tracking-widest uppercase transition-all"
                    style={{
                      fontFamily: "JetBrains Mono, monospace",
                      background: form.scan_mode === m ? "rgba(245,158,11,0.12)" : "#0c0a08",
                      border: form.scan_mode === m ? "1px solid rgba(245,158,11,0.3)" : "1px solid #2c2820",
                      color: form.scan_mode === m ? "#f59e0b" : "#6b6259",
                    }}
                  >
                    {m}
                  </button>
                ))}
              </div>
            </div>

            {/* Cron preset */}
            <div>
              <label className="block text-[9px] tracking-widest uppercase mb-1.5" style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}>
                Schedule Preset
              </label>
              <select
                onChange={(e) => handlePresetChange(e.target.value)}
                style={{ ...inputStyle, cursor: "pointer" }}
              >
                {CRON_PRESETS.map((p) => (
                  <option key={p.label} value={p.cron} style={{ background: "#0c0a08" }}>
                    {p.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Cron expression */}
            <div>
              <label className="block text-[9px] tracking-widest uppercase mb-1.5" style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}>
                Cron Expression *
              </label>
              <input
                type="text"
                placeholder="0 2 * * *"
                value={form.cron_expression}
                readOnly={!customCron}
                onChange={(e) => setForm((f) => ({ ...f, cron_expression: e.target.value }))}
                style={{ ...inputStyle, opacity: customCron ? 1 : 0.5 }}
              />
              <div className="text-[9px] mt-1" style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}>
                format: min hour dom month dow (UTC)
              </div>
            </div>
          </div>

          {error && (
            <div className="text-[11px] px-3 py-2 rounded" style={{ background: "rgba(244,63,94,0.08)", border: "1px solid rgba(244,63,94,0.2)", color: "#f43f5e", fontFamily: "JetBrains Mono, monospace" }}>
              {error}
            </div>
          )}

          <div className="flex gap-2 justify-end">
            <button
              onClick={() => { setShowForm(false); setError(null); }}
              className="px-4 py-1.5 rounded text-[10px] tracking-widest uppercase"
              style={{ fontFamily: "JetBrains Mono, monospace", border: "1px solid #2c2820", color: "#6b6259", background: "transparent" }}
            >
              Cancel
            </button>
            <button
              onClick={handleCreate}
              disabled={saving || !form.target_url || !form.cron_expression}
              className="flex items-center gap-2 px-4 py-1.5 rounded text-[10px] tracking-widest uppercase transition-all"
              style={{
                fontFamily: "JetBrains Mono, monospace",
                background: "rgba(245,158,11,0.12)",
                border: "1px solid rgba(245,158,11,0.3)",
                color: "#f59e0b",
                opacity: saving || !form.target_url || !form.cron_expression ? 0.5 : 1,
              }}
            >
              <Check className="h-3 w-3" />
              {saving ? "Saving…" : "Create"}
            </button>
          </div>
        </div>
      )}

      {/* Schedule list */}
      {loading ? (
        <div className="flex items-center gap-3 py-12">
          <div className="h-1.5 w-1.5 rounded-full animate-pulse" style={{ background: "#f59e0b" }} />
          <span className="text-[11px] tracking-widest uppercase" style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}>
            Loading schedules...
          </span>
        </div>
      ) : schedules.length === 0 ? (
        <div
          className="flex flex-col items-center justify-center py-16 rounded-lg gap-3"
          style={{ background: "#141210", border: "1px solid #1e1c18" }}
        >
          <Clock className="h-8 w-8" style={{ color: "#2c2820" }} />
          <span className="text-[12px]" style={{ color: "#4a4440", fontFamily: "JetBrains Mono, monospace" }}>
            No scheduled scans configured
          </span>
          <button
            onClick={() => setShowForm(true)}
            className="text-[10px] transition-colors"
            style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "#f59e0b")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "#4a4440")}
          >
            Create your first schedule →
          </button>
        </div>
      ) : (
        <div className="rounded-lg overflow-hidden" style={{ border: "1px solid #1e1c18" }}>
          {/* Header row */}
          <div
            className="grid px-5 py-2.5"
            style={{
              background: "#141210",
              borderBottom: "1px solid #1e1c18",
              gridTemplateColumns: "1fr 100px 130px 80px 80px",
              gap: "12px",
            }}
          >
            {["Target / Label", "Mode", "Schedule", "Status", ""].map((h) => (
              <span
                key={h}
                className="text-[9px] tracking-[0.2em] uppercase"
                style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}
              >
                {h}
              </span>
            ))}
          </div>

          {schedules.map((s, i) => (
            <div
              key={s.id}
              className="grid items-center px-5 py-3.5"
              style={{
                gridTemplateColumns: "1fr 100px 130px 80px 80px",
                gap: "12px",
                background: "#0c0a08",
                borderBottom: i < schedules.length - 1 ? "1px solid #1e1c18" : "none",
              }}
            >
              {/* Target */}
              <div className="min-w-0">
                <div className="text-[12px] font-medium truncate" style={{ color: "#e8e0d5" }}>
                  {s.label || s.target_url}
                </div>
                {s.label && (
                  <div className="text-[10px] truncate mt-0.5" style={{ fontFamily: "JetBrains Mono, monospace", color: "#4a4440" }}>
                    {s.target_url}
                  </div>
                )}
              </div>

              {/* Mode */}
              <span
                className="text-[9px] tracking-widest uppercase px-1.5 py-0.5 rounded self-center"
                style={{
                  fontFamily: "JetBrains Mono, monospace",
                  color: "#f59e0b",
                  background: "rgba(245,158,11,0.08)",
                  border: "1px solid rgba(245,158,11,0.2)",
                }}
              >
                {s.scan_mode}
              </span>

              {/* Cron */}
              <span
                className="text-[11px] self-center"
                style={{ fontFamily: "JetBrains Mono, monospace", color: "#6b6259" }}
              >
                {s.cron_expression}
              </span>

              {/* Active toggle */}
              <button
                onClick={() => handleToggle(s)}
                className="flex items-center gap-1.5 transition-colors self-center"
                title={s.is_active ? "Disable" : "Enable"}
              >
                {s.is_active ? (
                  <ToggleRight className="h-5 w-5" style={{ color: "#4ade80" }} />
                ) : (
                  <ToggleLeft className="h-5 w-5" style={{ color: "#4a4440" }} />
                )}
                <span
                  className="text-[9px] tracking-widest uppercase"
                  style={{ fontFamily: "JetBrains Mono, monospace", color: s.is_active ? "#4ade80" : "#4a4440" }}
                >
                  {s.is_active ? "On" : "Off"}
                </span>
              </button>

              {/* Delete */}
              <button
                onClick={() => handleDelete(s.id)}
                className="flex items-center justify-end transition-colors self-center"
                title="Delete schedule"
              >
                <Trash2
                  className="h-3.5 w-3.5"
                  style={{ color: "#4a4440" }}
                  onMouseEnter={(e) => (e.currentTarget.style.color = "#f43f5e")}
                  onMouseLeave={(e) => (e.currentTarget.style.color = "#4a4440")}
                />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Note */}
      <div
        className="px-4 py-3 rounded-lg text-[10px]"
        style={{
          fontFamily: "JetBrains Mono, monospace",
          color: "#4a4440",
          background: "#141210",
          border: "1px solid #1e1c18",
        }}
      >
        Note: Schedules are stored in-memory for this session. Production deployment requires Celery Beat integration.
      </div>
    </div>
  );
}
