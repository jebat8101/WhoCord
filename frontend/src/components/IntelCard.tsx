// src/components/IntelCard.tsx
// Renders the intelligence_report finding from IntelligenceStage.
import React, { useState } from "react";
import type { FindingPayload } from "../types/investigation";

interface Correlation {
  type: string;
  description: string;
  confidence: number;
}

interface Props {
  payload: FindingPayload;
}

function ConfidencePill({ value }: { value: number }) {
  const pct  = Math.round(value * 100);
  const color = value >= 0.75 ? "bg-orange-900 text-orange-300"
              : value >= 0.50 ? "bg-yellow-900 text-yellow-300"
              :                 "bg-blue-900 text-blue-300";
  return (
    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${color}`}>
      {pct}%
    </span>
  );
}

export default function IntelCard({ payload }: Props) {
  const [open, setOpen] = useState(false);

  const entityCount      = (payload.entity_count as number) ?? 0;
  const correlationCount = (payload.correlation_count as number) ?? 0;
  const hasNarrative     = Boolean(payload.has_narrative);

  return (
    <div className="rounded-lg border border-emerald-800 bg-neutral-900 overflow-hidden">
      {/* Header – always visible */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-neutral-800 transition-colors"
      >
        <span className="text-xl">🧠</span>
        <div className="flex-1">
          <p className="text-sm font-semibold text-emerald-300">
            Intelligence Report
          </p>
          <p className="text-xs text-neutral-500">
            {entityCount} entities · {correlationCount} correlations
            {hasNarrative ? " · AI narrative" : ""}
          </p>
        </div>
        <span className="text-neutral-600 text-sm">{open ? "▲" : "▼"}</span>
      </button>

      {/* Expanded detail */}
      {open && (
        <div className="px-4 pb-4 border-t border-neutral-800">
          {/* Stats row */}
          <div className="flex gap-4 mt-3 mb-3 text-sm">
            <div className="text-center">
              <div className="text-lg font-bold text-emerald-400">{entityCount}</div>
              <div className="text-[10px] text-neutral-500">Entities</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-indigo-400">{correlationCount}</div>
              <div className="text-[10px] text-neutral-500">Correlations</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-amber-400">
                {hasNarrative ? "✓" : "—"}
              </div>
              <div className="text-[10px] text-neutral-500">Narrative</div>
            </div>
          </div>

          {/* Correlations preview */}
          {correlationCount > 0 && (payload.correlations as Correlation[] | undefined) && (
            <div className="space-y-1.5">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-neutral-500 mb-1">
                Top Correlations
              </p>
              {(payload.correlations as Correlation[]).slice(0, 5).map((c, i) => (
                <div
                  key={i}
                  className="flex items-start gap-2 rounded bg-neutral-800 px-2.5 py-1.5"
                >
                  <ConfidencePill value={c.confidence} />
                  <span className="text-xs text-neutral-300 flex-1">{c.description}</span>
                </div>
              ))}
            </div>
          )}

          <p className="mt-3 text-xs text-neutral-600">
            Full intelligence section available in the HTML report.
          </p>
        </div>
      )}
    </div>
  );
}
