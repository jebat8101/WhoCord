// src/pages/Config.tsx
import React, { useRef, useState } from "react";
import ConfigPanel from "../components/ConfigPanel";
import { upgradeToolsUrl, shutdownServer } from "../utils/api";

export default function Config() {
  const [upgradeLog, setLog]        = useState<string[]>([]);
  const [upgrading, setUpgrading]   = useState(false);
  const logEndRef                   = useRef<HTMLDivElement>(null);

  const handleUpgrade = async () => {
    setLog([]);
    setUpgrading(true);

    try {
      const res = await fetch(upgradeToolsUrl(), { method: "POST" });
      const reader = res.body?.getReader();
      const dec    = new TextDecoder();

      if (!reader) {
        setLog(["Upgrade stream unavailable."]);
        setUpgrading(false);
        return;
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = dec.decode(value, { stream: true });
        // Parse SSE lines: "data: {...}\n\n"
        for (const raw of chunk.split("\n")) {
          if (!raw.startsWith("data:")) continue;
          const text = raw.slice(5).trim();
          try {
            const evt = JSON.parse(text) as { type: string; payload: { line?: string; message?: string } };
            const line = evt.payload?.line ?? evt.payload?.message ?? "";
            if (line) {
              setLog((prev) => [...prev, line]);
              requestAnimationFrame(() => logEndRef.current?.scrollIntoView({ behavior: "smooth" }));
            }
          } catch {
            if (text) setLog((prev) => [...prev, text]);
          }
        }
      }
    } catch (err) {
      setLog((prev) => [...prev, `Error: ${err}`]);
    } finally {
      setUpgrading(false);
    }
  };

  const handleShutdown = async () => {
    if (!confirm("Shut down the WhoCord server?")) return;
    await shutdownServer();
    setTimeout(() => window.close(), 500);
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-xl font-bold text-white">Configuration</h1>
        <p className="text-sm text-neutral-500 mt-0.5">
          Manage API keys, tool toggles, and server options.
        </p>
      </div>

      {/* Config panel */}
      <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-5 mb-6">
        <ConfigPanel />
      </div>

      {/* Upgrade tools */}
      <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-5 mb-6">
        <h2 className="text-sm font-semibold text-neutral-300 mb-3">
          ⬆ Upgrade External Tools
        </h2>
        <p className="text-xs text-neutral-500 mb-3">
          Upgrades all pip-installable OSINT tools (Sherlock, Maigret, Holehe…).
          External tools (Scylla, PhoneInfoga) must be upgraded manually.
        </p>
        <button
          onClick={handleUpgrade}
          disabled={upgrading}
          className="rounded bg-neutral-700 hover:bg-neutral-600 disabled:opacity-50
                     disabled:cursor-not-allowed transition-colors px-4 py-2
                     text-sm font-semibold text-neutral-200"
        >
          {upgrading ? "Upgrading…" : "Run Upgrade"}
        </button>

        {upgradeLog.length > 0 && (
          <div className="mt-4 rounded bg-neutral-950 border border-neutral-800
                          p-3 max-h-48 overflow-y-auto font-mono text-[11px]
                          text-neutral-400 space-y-0.5">
            {upgradeLog.map((line, i) => (
              <div key={i}>{line}</div>
            ))}
            <div ref={logEndRef} />
          </div>
        )}
      </div>

      {/* Server controls */}
      <div className="rounded-xl border border-red-900/40 bg-neutral-900 p-5">
        <h2 className="text-sm font-semibold text-red-400 mb-3">
          Danger Zone
        </h2>
        <p className="text-xs text-neutral-500 mb-3">
          Shuts down the Flask process entirely. You will need to restart WhoCord manually.
        </p>
        <button
          onClick={handleShutdown}
          className="rounded bg-red-900 hover:bg-red-800 transition-colors
                     px-4 py-2 text-sm font-semibold text-red-200"
        >
          ⏻ Shut Down Server
        </button>
      </div>
    </div>
  );
}
