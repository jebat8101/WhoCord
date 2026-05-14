// src/components/LiveProgress.tsx
import React from "react";

interface Props {
  currentStage: string | null;
  currentMessage: string;
  status: "idle" | "running" | "done" | "error";
  findingCount: number;
  pivotDepth: number;
}

const STAGE_ICON: Record<string, string> = {
  discord_mode:  "🔵",
  discovery:     "🔍",
  scraping:      "🕷",
  media:         "🖼",
  analysis:      "📊",
  intelligence:  "🧠",
  email_intel:   "📧",
  reporting:     "📋",
};

export default function LiveProgress({
  currentStage,
  currentMessage,
  status,
  findingCount,
  pivotDepth,
}: Props) {
  const icon    = currentStage ? (STAGE_ICON[currentStage] ?? "▶") : "⏳";
  const isRunning = status === "running";

  return (
    <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-4">
      {/* Status row */}
      <div className="flex items-center gap-3 mb-3">
        {/* Animated ring when running */}
        <div className="relative shrink-0">
          <span className="text-2xl">{icon}</span>
          {isRunning && (
            <span className="absolute -inset-1 rounded-full border-2 border-indigo-500 animate-ping opacity-40" />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-white truncate">
            {status === "idle"    && "Waiting to start…"}
            {status === "running" && (currentStage
              ? currentStage.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
              : "Starting…")}
            {status === "done"    && "Investigation complete ✓"}
            {status === "error"   && "Investigation encountered an error"}
          </p>
          {currentMessage && (
            <p className="text-xs text-neutral-500 truncate">{currentMessage}</p>
          )}
        </div>

        {/* Stats pills */}
        <div className="flex gap-2 shrink-0">
          <span className="text-xs bg-neutral-800 px-2 py-0.5 rounded text-neutral-400">
            {findingCount} finding{findingCount !== 1 ? "s" : ""}
          </span>
          {pivotDepth > 0 && (
            <span className="text-xs bg-green-900 px-2 py-0.5 rounded text-green-300">
              pivot d={pivotDepth}
            </span>
          )}
        </div>
      </div>

      {/* Progress bar */}
      {isRunning && (
        <div className="h-1 rounded-full bg-neutral-800 overflow-hidden">
          <div className="h-full bg-indigo-500 rounded-full animate-pulse w-3/4" />
        </div>
      )}
      {status === "done" && (
        <div className="h-1 rounded-full bg-emerald-500" />
      )}
      {status === "error" && (
        <div className="h-1 rounded-full bg-red-500" />
      )}
    </div>
  );
}
