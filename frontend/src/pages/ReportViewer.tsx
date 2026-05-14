// src/pages/ReportViewer.tsx
// Displays the HTML report for a given investigation job.
// URL param: /report/:jobId
// Falls back to /report (legacy endpoint) when no jobId is present.
import React, { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { investigationReportUrl } from "../utils/api";

type LoadState = "loading" | "ready" | "error";

export default function ReportViewer() {
  const { jobId }           = useParams<{ jobId?: string }>();
  const navigate            = useNavigate();
  const iframeRef           = useRef<HTMLIFrameElement>(null);
  const [loadState, setLS]  = useState<LoadState>("loading");
  const [errorMsg, setEM]   = useState("");

  // Resolve the correct report URL
  const reportUrl = jobId ? investigationReportUrl(jobId) : "/report";

  useEffect(() => {
    setLS("loading");
    setEM("");
  }, [reportUrl]);

  const handleIframeLoad = () => {
    // Check for a 404 / error page inside the iframe
    try {
      const doc = iframeRef.current?.contentDocument;
      if (doc && doc.title === "404" || (doc?.body?.innerText ?? "").includes("not found")) {
        setLS("error");
        setEM("Report not found or not yet generated.");
        return;
      }
    } catch {
      // cross-origin — assume it loaded fine
    }
    setLS("ready");
  };

  const handleIframeError = () => {
    setLS("error");
    setEM("Failed to load report.");
  };

  return (
    <div className="flex flex-col h-full">
      {/* ── Toolbar ─────────────────────────────────────────────── */}
      <div className="flex items-center gap-3 px-4 py-2.5 border-b border-neutral-800
                      bg-neutral-900 shrink-0">
        <button
          onClick={() => navigate(-1)}
          className="text-neutral-500 hover:text-white text-sm transition-colors"
        >
          ←
        </button>
        <span className="text-sm font-semibold text-white flex-1 truncate">
          {jobId ? `Report · ${jobId.slice(0, 8)}…` : "Latest Report"}
        </span>

        {loadState === "loading" && (
          <span className="text-xs text-indigo-400 animate-pulse">Loading…</span>
        )}

        {loadState === "ready" && (
          <a
            href={reportUrl}
            target="_blank"
            rel="noreferrer"
            className="text-xs px-2.5 py-1 rounded bg-neutral-800 hover:bg-neutral-700
                       text-neutral-400 transition-colors"
          >
            ↗ Open in tab
          </a>
        )}

        <button
          onClick={() => { setLS("loading"); iframeRef.current && (iframeRef.current.src = reportUrl); }}
          className="text-xs px-2.5 py-1 rounded bg-neutral-800 hover:bg-neutral-700
                     text-neutral-400 transition-colors"
        >
          ↺ Reload
        </button>
      </div>

      {/* ── Content ─────────────────────────────────────────────── */}
      {loadState === "error" ? (
        <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center p-8">
          <div className="text-4xl">📄</div>
          <p className="text-neutral-400 text-sm">{errorMsg}</p>
          <button
            onClick={() => navigate("/")}
            className="rounded bg-indigo-600 hover:bg-indigo-500 px-4 py-2
                       text-sm text-white transition-colors"
          >
            ← New investigation
          </button>
        </div>
      ) : (
        <div className="flex-1 relative">
          {loadState === "loading" && (
            <div className="absolute inset-0 flex items-center justify-center
                            bg-neutral-950 z-10">
              <div className="flex flex-col items-center gap-3">
                <div className="w-8 h-8 rounded-full border-2 border-indigo-500
                                border-t-transparent animate-spin" />
                <p className="text-sm text-neutral-500">Loading report…</p>
              </div>
            </div>
          )}
          <iframe
            ref={iframeRef}
            src={reportUrl}
            title="Investigation Report"
            className="w-full h-full border-0 bg-white"
            onLoad={handleIframeLoad}
            onError={handleIframeError}
          />
        </div>
      )}
    </div>
  );
}
