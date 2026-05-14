// src/components/PivotConfirmModal.tsx
// Shown when the backend emits a pivot_confirm_request event.
// The user can approve/reject individual seeds or skip the whole batch.
import React, { useEffect, useRef, useState } from "react";
import type { PivotConfirmRequestPayload, PivotSeed } from "../types/investigation";
import { confirmPivot } from "../utils/api";

interface Props {
  payload:   PivotConfirmRequestPayload;
  onClose:   () => void;
}

const SEED_ICONS: Record<string, string> = {
  email:    "✉️",
  username: "👤",
};

export default function PivotConfirmModal({ payload, onClose }: Props) {
  const { job_id, depth, seeds, timeout_seconds } = payload;

  // Which seeds are checked (all on by default)
  const [checked, setChecked] = useState<Set<string>>(() => new Set(seeds.map(s => s.value)));
  const [submitting, setSub]  = useState(false);
  const [countdown, setCD]    = useState(timeout_seconds);
  const timerRef              = useRef<ReturnType<typeof setInterval> | null>(null);

  // Countdown
  useEffect(() => {
    timerRef.current = setInterval(() => {
      setCD(prev => {
        if (prev <= 1) {
          clearInterval(timerRef.current!);
          // Auto-run all on timeout (backend will do the same, but send confirmation anyway)
          handleRun(true);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timerRef.current!);
  }, []);                    // eslint-disable-line react-hooks/exhaustive-deps

  const toggle = (value: string) => {
    setChecked(prev => {
      const next = new Set(prev);
      if (next.has(value)) next.delete(value);
      else                 next.add(value);
      return next;
    });
  };

  const handleRun = async (all = false) => {
    if (submitting) return;
    setSub(true);
    clearInterval(timerRef.current!);

    const approved: PivotSeed[] = all
      ? seeds
      : seeds.filter(s => checked.has(s.value));

    await confirmPivot(job_id, approved).catch(() => {});
    onClose();
  };

  const handleSkipAll = async () => {
    if (submitting) return;
    setSub(true);
    clearInterval(timerRef.current!);
    await confirmPivot(job_id, []).catch(() => {});
    onClose();
  };

  const pct = Math.round((countdown / timeout_seconds) * 100);

  return (
    // Backdrop
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="w-full max-w-md mx-4 rounded-xl border border-green-800 bg-neutral-900
                      shadow-2xl shadow-black/60 overflow-hidden">

        {/* ── Header ─────────────────────────────────────────────── */}
        <div className="bg-gradient-to-r from-green-950 to-neutral-900 px-5 py-4
                        border-b border-green-800">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl">🔄</span>
            <h2 className="text-base font-bold text-white">Pivot Investigation</h2>
            <span className="ml-auto text-xs font-bold px-2 py-0.5 rounded
                             bg-green-900 text-green-300">
              Depth {depth}
            </span>
          </div>
          <p className="text-xs text-neutral-400 leading-relaxed">
            New seeds were discovered. Select which to investigate, or skip all.
          </p>
        </div>

        {/* ── Countdown bar ──────────────────────────────────────── */}
        <div className="px-5 pt-3">
          <div className="flex items-center justify-between text-xs text-neutral-500 mb-1">
            <span>Auto-running in {countdown}s</span>
            <span>{seeds.filter(s => checked.has(s.value)).length} / {seeds.length} selected</span>
          </div>
          <div className="h-1 rounded-full bg-neutral-800 overflow-hidden">
            <div
              className="h-full bg-green-600 rounded-full transition-all duration-1000"
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>

        {/* ── Seed list ──────────────────────────────────────────── */}
        <div className="px-5 py-4 space-y-2 max-h-72 overflow-y-auto">
          {seeds.map(seed => {
            const isChecked = checked.has(seed.value);
            return (
              <label
                key={seed.value}
                className={[
                  "flex items-center gap-3 rounded-lg border px-3 py-2.5 cursor-pointer",
                  "transition-all duration-150",
                  isChecked
                    ? "border-green-700 bg-green-950/40"
                    : "border-neutral-700 bg-neutral-800/40 opacity-50",
                ].join(" ")}
              >
                {/* Custom checkbox */}
                <div
                  onClick={() => toggle(seed.value)}
                  className={[
                    "w-4 h-4 rounded border-2 flex items-center justify-center shrink-0",
                    "transition-colors",
                    isChecked ? "border-green-500 bg-green-500" : "border-neutral-600",
                  ].join(" ")}
                >
                  {isChecked && (
                    <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 10 8">
                      <path d="M1 4l3 3 5-6" stroke="currentColor" strokeWidth="1.8"
                            strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  )}
                </div>

                {/* Seed info */}
                <span className="text-lg leading-none">{SEED_ICONS[seed.type] ?? "•"}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-mono text-neutral-200 truncate">{seed.value}</p>
                  <p className="text-[10px] text-neutral-500 capitalize">{seed.type}</p>
                </div>
              </label>
            );
          })}
        </div>

        {/* ── Actions ────────────────────────────────────────────── */}
        <div className="px-5 pb-5 flex gap-3 border-t border-neutral-800 pt-4">
          <button
            onClick={() => handleRun(false)}
            disabled={submitting || checked.size === 0}
            className="flex-1 rounded-lg bg-green-700 hover:bg-green-600
                       disabled:opacity-40 disabled:cursor-not-allowed
                       transition-colors py-2 text-sm font-bold text-white"
          >
            {submitting ? "Starting…" : `▶ Run ${checked.size} Seed${checked.size !== 1 ? "s" : ""}`}
          </button>
          <button
            onClick={handleSkipAll}
            disabled={submitting}
            className="flex-1 rounded-lg bg-neutral-800 hover:bg-red-900/60
                       border border-neutral-700 hover:border-red-700
                       disabled:opacity-40 disabled:cursor-not-allowed
                       transition-colors py-2 text-sm font-semibold text-neutral-300
                       hover:text-red-300"
          >
            ✕ Skip All
          </button>
        </div>

      </div>
    </div>
  );
}
