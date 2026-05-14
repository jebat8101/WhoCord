// src/pages/History.tsx
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchInvestigations, investigationReportUrl } from "../utils/api";
import type { Job } from "../types/investigation";

function StatusBadge({ status }: { status: Job["status"] }) {
  const styles = {
    done:    "bg-emerald-900 text-emerald-300",
    running: "bg-indigo-900 text-indigo-300 animate-pulse",
    error:   "bg-red-900 text-red-300",
  };
  return (
    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded uppercase ${styles[status]}`}>
      {status}
    </span>
  );
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export default function History() {
  const navigate                  = useNavigate();
  const [jobs, setJobs]           = useState<Job[]>([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState("");

  const load = async () => {
    setLoading(true);
    try {
      setJobs(await fetchInvestigations());
    } catch (e) {
      setError("Failed to load investigation history.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-white">Investigation History</h1>
          <p className="text-sm text-neutral-500 mt-0.5">
            All past and active investigation runs.
          </p>
        </div>
        <button
          onClick={load}
          className="rounded bg-neutral-800 hover:bg-neutral-700 transition-colors
                     px-3 py-1.5 text-sm text-neutral-400"
        >
          ↻ Refresh
        </button>
      </div>

      {loading && (
        <div className="text-neutral-500 text-sm">Loading…</div>
      )}
      {error && (
        <div className="text-red-400 text-sm">{error}</div>
      )}

      {!loading && !error && jobs.length === 0 && (
        <div className="text-center py-16 text-neutral-600">
          <div className="text-4xl mb-3">🔍</div>
          <p className="text-sm">No investigations yet.</p>
          <button
            onClick={() => navigate("/")}
            className="mt-4 rounded bg-indigo-600 hover:bg-indigo-500 transition-colors
                       px-4 py-2 text-sm text-white"
          >
            Start one
          </button>
        </div>
      )}

      {!loading && jobs.length > 0 && (
        <div className="rounded-xl border border-neutral-800 bg-neutral-900 overflow-hidden">
          {/* Table header */}
          <div className="grid grid-cols-[1fr_80px_160px_80px_120px] px-4 py-2
                          border-b border-neutral-800 text-[10px] font-semibold
                          text-neutral-500 uppercase tracking-wider">
            <span>Target</span>
            <span>Mode</span>
            <span>Started</span>
            <span>Status</span>
            <span>Actions</span>
          </div>

          {jobs.map((job, i) => (
            <div
              key={job.id}
              className={`grid grid-cols-[1fr_80px_160px_80px_120px] px-4 py-3
                          items-center text-sm
                          ${i % 2 === 0 ? "bg-neutral-900" : "bg-neutral-850"}
                          ${i < jobs.length - 1 ? "border-b border-neutral-800" : ""}`}
            >
              {/* Target */}
              <span className="text-neutral-300 font-mono truncate pr-4">
                {job.target || "—"}
              </span>

              {/* Mode */}
              <span className="text-neutral-500 text-xs">{job.mode || "—"}</span>

              {/* Started at */}
              <span className="text-neutral-500 text-xs">
                {formatDate(job.started_at)}
              </span>

              {/* Status */}
              <span><StatusBadge status={job.status} /></span>

              {/* Actions */}
              <div className="flex gap-2">
                {job.has_report && (
                  <a
                    href={investigationReportUrl(job.id)}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[10px] font-semibold px-2 py-1 rounded
                               bg-indigo-900 hover:bg-indigo-800 text-indigo-300
                               transition-colors"
                  >
                    Report
                  </a>
                )}
                {job.has_intel && (
                  <a
                    href={`/api/investigations/${job.id}`}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[10px] font-semibold px-2 py-1 rounded
                               bg-neutral-800 hover:bg-neutral-700 text-neutral-400
                               transition-colors"
                  >
                    JSON
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
