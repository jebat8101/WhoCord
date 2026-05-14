// src/components/ConfigPanel.tsx
import React, { useEffect, useState } from "react";
import { fetchConfig, savePivotConfig, setToken, toggleDebug, toggleTool } from "../utils/api";
import type { AppConfig, PivotConfig, ToolConfig } from "../types/investigation";

const DEFAULT_PIVOT: PivotConfig = {
  enabled:         false,
  pivot_email:     true,
  pivot_username:  true,
  max_depth:       3,
  max_seeds:       5,
  require_confirm: false,
};

export default function ConfigPanel() {
  const [cfg, setCfg]           = useState<AppConfig | null>(null);
  const [loading, setLoading]   = useState(true);
  const [tokenInputs, setTI]    = useState<Record<string, string>>({});
  const [saveMsg, setSaveMsg]   = useState("");
  const [pivot, setPivot]       = useState<PivotConfig>(DEFAULT_PIVOT);
  const [pivotSaved, setPivotSaved] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const data = await fetchConfig();
      setCfg(data);
      setPivot(data.pivot ?? DEFAULT_PIVOT);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleSaveTokens = async () => {
    for (const [key, value] of Object.entries(tokenInputs)) {
      if (value.trim()) await setToken(key, value.trim());
    }
    setTI({});
    setSaveMsg("Saved ✓");
    await load();
    setTimeout(() => setSaveMsg(""), 2500);
  };

  const handleToggleTool = async (tool: ToolConfig) => {
    await toggleTool(tool.key, !tool.enabled);
    await load();
  };

  const handleToggleDebug = async () => {
    await toggleDebug();
    await load();
  };

  const handleSavePivot = async () => {
    await savePivotConfig(pivot);
    setPivotSaved(true);
    setTimeout(() => setPivotSaved(false), 2500);
  };

  if (loading) return <div className="p-8 text-neutral-500 text-sm">Loading config…</div>;
  if (!cfg)    return <div className="p-8 text-red-400 text-sm">Failed to load config.</div>;

  const TOKEN_LABELS: Record<string, string> = {
    DISCORD_TOKEN:     "Discord Token",
    GITHUB_TOKEN:      "GitHub Token",
    GROQ_API_KEY:      "Groq API Key",
    INSTAGRAM_SESSION: "Instagram Session",
  };

  // Reusable toggle component
  const Toggle = ({
    on, onToggle, label, sublabel,
  }: { on: boolean; onToggle: () => void; label: string; sublabel?: string }) => (
    <label className="flex items-center gap-3 cursor-pointer">
      <div
        onClick={onToggle}
        className={`relative w-10 h-5 rounded-full transition-colors shrink-0 ${on ? "bg-indigo-600" : "bg-neutral-700"}`}
      >
        <div className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white
                        transition-transform ${on ? "translate-x-5" : ""}`} />
      </div>
      <div>
        <span className="text-sm text-neutral-400">{label}</span>
        {sublabel && <p className="text-xs text-neutral-600">{sublabel}</p>}
      </div>
      <span className={`ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded ${
        on ? "bg-indigo-900 text-indigo-300" : "bg-neutral-800 text-neutral-600"
      }`}>
        {on ? "ON" : "OFF"}
      </span>
    </label>
  );

  return (
    <div className="space-y-6">

      {/* ── API Tokens ─────────────────────────────────────────── */}
      <section>
        <h3 className="text-sm font-semibold text-neutral-300 mb-3">API Tokens</h3>
        <div className="space-y-3">
          {Object.entries(TOKEN_LABELS).map(([key, label]) => (
            <div key={key}>
              <label className="flex items-center justify-between text-xs text-neutral-400 mb-1">
                <span>{label}</span>
                <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                  cfg.tokens[key as keyof typeof cfg.tokens]
                    ? "bg-emerald-900 text-emerald-400"
                    : "bg-neutral-800 text-neutral-600"
                }`}>
                  {cfg.tokens[key as keyof typeof cfg.tokens] ? "set" : "not set"}
                </span>
              </label>
              <input
                type="password"
                placeholder={`Enter ${label}…`}
                value={tokenInputs[key] ?? ""}
                onChange={e => setTI(p => ({ ...p, [key]: e.target.value }))}
                className="w-full rounded bg-neutral-800 border border-neutral-700 px-3 py-1.5
                           text-sm text-neutral-200 placeholder-neutral-600
                           focus:outline-none focus:border-indigo-500 transition-colors"
              />
            </div>
          ))}
        </div>
        <button
          onClick={handleSaveTokens}
          className="mt-3 rounded bg-indigo-600 hover:bg-indigo-500 transition-colors
                     px-4 py-1.5 text-sm font-semibold text-white"
        >
          Save Tokens
        </button>
        {saveMsg && <span className="ml-3 text-sm text-emerald-400">{saveMsg}</span>}
      </section>

      {/* ── Adaptive Pivoting ──────────────────────────────────── */}
      <section>
        <h3 className="text-sm font-semibold text-neutral-300 mb-1 flex items-center gap-2">
          🔄 Adaptive Pivoting
          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
            pivot.enabled ? "bg-green-900 text-green-400" : "bg-neutral-800 text-neutral-600"
          }`}>
            {pivot.enabled ? "ENABLED" : "DISABLED"}
          </span>
        </h3>
        <p className="text-xs text-neutral-600 mb-4">
          Automatically investigate newly discovered emails and usernames during the investigation.
        </p>

        <div className="space-y-4">
          {/* Master toggle */}
          <Toggle
            on={pivot.enabled}
            onToggle={() => setPivot(p => ({ ...p, enabled: !p.enabled }))}
            label="Enable pivoting"
            sublabel="Follow discovered seeds in sub-investigations"
          />

          {pivot.enabled && (
            <>
              {/* Seed type toggles */}
              <div className="ml-3 pl-3 border-l border-neutral-700 space-y-3">
                <Toggle
                  on={pivot.pivot_email}
                  onToggle={() => setPivot(p => ({ ...p, pivot_email: !p.pivot_email }))}
                  label="Pivot on emails"
                  sublabel="Follow discovered email addresses"
                />
                <Toggle
                  on={pivot.pivot_username}
                  onToggle={() => setPivot(p => ({ ...p, pivot_username: !p.pivot_username }))}
                  label="Pivot on usernames"
                  sublabel="Follow discovered usernames and handles"
                />
              </div>

              {/* Depth slider */}
              <div>
                <label className="flex items-center justify-between text-xs text-neutral-400 mb-1.5">
                  <span>Max recursion depth</span>
                  <span className="font-bold text-white">{pivot.max_depth}</span>
                </label>
                <input
                  type="range"
                  min={1} max={5} step={1}
                  value={pivot.max_depth}
                  onChange={e => setPivot(p => ({ ...p, max_depth: Number(e.target.value) }))}
                  className="w-full accent-indigo-500"
                />
                <div className="flex justify-between text-[10px] text-neutral-600 mt-0.5">
                  <span>1 (shallow)</span>
                  <span>5 (deep)</span>
                </div>
              </div>

              {/* Seeds per depth */}
              <div>
                <label className="flex items-center justify-between text-xs text-neutral-400 mb-1.5">
                  <span>Max seeds per depth level</span>
                  <span className="font-bold text-white">{pivot.max_seeds}</span>
                </label>
                <input
                  type="range"
                  min={1} max={20} step={1}
                  value={pivot.max_seeds}
                  onChange={e => setPivot(p => ({ ...p, max_seeds: Number(e.target.value) }))}
                  className="w-full accent-indigo-500"
                />
                <div className="flex justify-between text-[10px] text-neutral-600 mt-0.5">
                  <span>1 (conservative)</span>
                  <span>20 (aggressive)</span>
                </div>
              </div>

              {/* Confirmation toggle */}
              <Toggle
                on={pivot.require_confirm}
                onToggle={() => setPivot(p => ({ ...p, require_confirm: !p.require_confirm }))}
                label="Confirm before each pivot"
                sublabel="Pause and ask you to approve seeds before running"
              />
            </>
          )}
        </div>

        <button
          onClick={handleSavePivot}
          className="mt-4 rounded bg-green-700 hover:bg-green-600 transition-colors
                     px-4 py-1.5 text-sm font-semibold text-white"
        >
          Save Pivot Settings
        </button>
        {pivotSaved && <span className="ml-3 text-sm text-emerald-400">Saved ✓</span>}
      </section>

      {/* ── Debug ──────────────────────────────────────────────── */}
      <section>
        <h3 className="text-sm font-semibold text-neutral-300 mb-3">Debug</h3>
        <label className="flex items-center gap-3 cursor-pointer">
          <div
            onClick={handleToggleDebug}
            className={`relative w-10 h-5 rounded-full transition-colors ${
              cfg.debug ? "bg-indigo-600" : "bg-neutral-700"
            }`}
          >
            <div className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white
                            transition-transform ${cfg.debug ? "translate-x-5" : ""}`} />
          </div>
          <span className="text-sm text-neutral-400">
            Verbose logging
            <span className={`ml-2 text-[10px] font-bold px-1.5 py-0.5 rounded ${
              cfg.debug ? "bg-indigo-900 text-indigo-300" : "bg-neutral-800 text-neutral-600"
            }`}>
              {cfg.debug ? "ON" : "OFF"}
            </span>
          </span>
        </label>
      </section>

      {/* ── Tool Toggles ───────────────────────────────────────── */}
      <section>
        <h3 className="text-sm font-semibold text-neutral-300 mb-3">Tools</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {cfg.tools.map(tool => (
            <label
              key={tool.key}
              className="flex items-center justify-between rounded bg-neutral-800
                         border border-neutral-700 px-3 py-2 cursor-pointer
                         hover:border-neutral-600 transition-colors"
            >
              <span className="text-xs text-neutral-400">{tool.desc}</span>
              <div
                onClick={() => handleToggleTool(tool)}
                className={`relative w-8 h-4 rounded-full transition-colors shrink-0 ${
                  tool.enabled ? "bg-indigo-600" : "bg-neutral-700"
                }`}
              >
                <div className={`absolute top-0.5 left-0.5 w-3 h-3 rounded-full bg-white
                                transition-transform ${tool.enabled ? "translate-x-4" : ""}`} />
              </div>
            </label>
          ))}
        </div>
      </section>
    </div>
  );
}
