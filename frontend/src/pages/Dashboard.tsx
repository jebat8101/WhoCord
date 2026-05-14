// src/pages/Dashboard.tsx
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import ModuleCard from "../components/ModuleCard";
import { buildRunUrl } from "../utils/api";
import type { InvestigationMode, ModuleMeta, RunParams } from "../types/investigation";

// ---------------------------------------------------------------------------
// Module definitions
// ---------------------------------------------------------------------------

const MODULES: ModuleMeta[] = [
  // ── Legacy modules ────────────────────────────────────────────────────
  {
    id:               "manual",
    icon:             "🔍",
    title:            "Username / Manual",
    description:      "Investigate any username across hundreds of platforms using Sherlock, Maigret, and more.",
    color:            "indigo",
    inputLabel:       "Username",
    inputPlaceholder: "e.g. johndoe",
    inputType:        "text",
    extraFields: [
      { name: "email", label: "Email (optional)", placeholder: "email@example.com", required: false, type: "text" },
    ],
  },
  {
    id:               "discord",
    icon:             "💬",
    title:            "Discord User",
    description:      "Deep-dive a Discord user ID: profile, connections, message history, and pivots.",
    color:            "violet",
    inputLabel:       "Target User ID",
    inputPlaceholder: "e.g. 123456789012345678",
    inputType:        "text",
    extraFields: [
      { name: "guild_id",    label: "Guild ID (optional)", placeholder: "Guild snowflake", required: false, type: "text" },
      { name: "multi_guild", label: "Search all guilds",   placeholder: "",                required: false, type: "checkbox" },
    ],
  },
  // ── Phase 4 modules ───────────────────────────────────────────────────
  {
    id:               "email",
    icon:             "✉️",
    title:            "Email Address",
    description:      "Breach lookup (HIBP, h8mail), site registrations (Holehe), GHunt, EmailRep, and linked profiles.",
    color:            "sky",
    inputLabel:       "Email Address",
    inputPlaceholder: "target@example.com",
    inputType:        "email",
  },
  {
    id:               "domain",
    icon:             "🌐",
    title:            "Domain",
    description:      "WHOIS, DNS records, SSL certificate, subdomain enumeration, IP geolocation, and Wayback Machine.",
    color:            "amber",
    inputLabel:       "Domain",
    inputPlaceholder: "example.com",
    inputType:        "text",
  },
  {
    id:               "phone",
    icon:             "📱",
    title:            "Phone Number",
    description:      "Number validation, carrier lookup, country/region, and PhoneInfoga OSINT scan.",
    color:            "rose",
    inputLabel:       "Phone Number",
    inputPlaceholder: "+1 555 000 0000",
    inputType:        "tel",
  },
  {
    id:               "image",
    icon:             "🖼",
    title:            "Image Analysis",
    description:      "EXIF metadata, GPS coordinates, perceptual hash, reverse image search, and OCR text extraction.",
    color:            "violet",
    inputLabel:       "Image URL",
    inputPlaceholder: "https://example.com/image.jpg",
    inputType:        "url",
  },
  {
    id:               "url",
    icon:             "🔗",
    title:            "URL Analysis",
    description:      "HTTP headers, redirect chain, page metadata, Open Graph tags, Safe Browsing check, and Wayback.",
    color:            "teal",
    inputLabel:       "URL",
    inputPlaceholder: "https://example.com",
    inputType:        "url",
  },
  {
    id:               "probe",
    icon:             "🔎",
    title:            "Data Probe",
    description:      "Paste anything – email, domain, phone, URL, or username – and WhoCord auto-detects the type.",
    color:            "emerald",
    inputLabel:       "Probe Input",
    inputPlaceholder: "Paste an email, domain, phone number, URL, or username…",
    inputType:        "text",
  },
];

// Tailwind color map for the "teal" variant not in original ModuleCard
const EXTRA_COLORS: Record<string, { border: string; hover: string; badge: string }> = {
  teal: {
    border: "border-teal-700",
    hover:  "hover:border-teal-500",
    badge:  "bg-teal-900 text-teal-300",
  },
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function Dashboard() {
  const navigate = useNavigate();
  const [activeModule, setActive]   = useState<ModuleMeta | null>(null);
  const [formValues, setFormValues] = useState<Record<string, string | boolean>>({});
  const [error, setError]           = useState("");

  const openModule = (module: ModuleMeta) => {
    setActive(module);
    setFormValues({});
    setError("");
  };

  const handleLaunch = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!activeModule) return;

    const mode = activeModule.id as InvestigationMode;
    let params: RunParams = { mode };

    if (mode === "discord") {
      const user_id = String(formValues["input"] ?? "").trim();
      if (!user_id) { setError("Discord User ID is required."); return; }
      params.user_id   = user_id;
      params.guild_id  = String(formValues["guild_id"] ?? "").trim() || undefined;
      params.multi_guild = Boolean(formValues["multi_guild"]);

    } else if (mode === "manual") {
      const username = String(formValues["input"] ?? "").trim();
      const email    = String(formValues["email"]  ?? "").trim();
      if (!username && !email) { setError("Username or email is required."); return; }
      params.username = username || undefined;
      params.email    = email    || undefined;

    } else {
      // All Phase 4 module modes use a single "target" field
      const target = String(formValues["input"] ?? "").trim();
      if (!target) { setError(`${activeModule.inputLabel} is required.`); return; }
      params.target = target;
    }

    const sseUrl = buildRunUrl(params);
    navigate("/live", {
      state: {
        sseUrl,
        mode:   mode,
        target: String(formValues["input"] ?? params.username ?? params.email ?? ""),
      },
    });
  };

  return (
    <div className="p-6 max-w-5xl mx-auto">

      {/* ── Header ────────────────────────────────────────────── */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-1">New Investigation</h1>
        <p className="text-sm text-neutral-500">
          Choose an investigation module to get started.
        </p>
      </div>

      {/* ── Module grid ───────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {MODULES.map(m => (
          <ModuleCard
            key={m.id}
            module={m}
            onClick={openModule}
            isActive={activeModule?.id === m.id}
            extraColors={EXTRA_COLORS}
          />
        ))}
      </div>

      {/* ── Launch form ───────────────────────────────────────── */}
      {activeModule && (
        <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-6 max-w-lg">
          <div className="flex items-center gap-3 mb-5">
            <span className="text-2xl">{activeModule.icon}</span>
            <div>
              <h2 className="text-base font-bold text-white">{activeModule.title}</h2>
              <p className="text-xs text-neutral-500">{activeModule.description}</p>
            </div>
          </div>

          <form onSubmit={handleLaunch} className="space-y-4">
            {/* Primary input */}
            <div>
              <label className="text-xs text-neutral-400 block mb-1">
                {activeModule.inputLabel}
              </label>
              <input
                type={activeModule.inputType}
                placeholder={activeModule.inputPlaceholder}
                value={String(formValues["input"] ?? "")}
                onChange={e => setFormValues(p => ({ ...p, input: e.target.value }))}
                autoFocus
                className="w-full rounded bg-neutral-800 border border-neutral-700 px-3 py-2
                           text-sm text-white placeholder-neutral-600
                           focus:outline-none focus:border-indigo-500 transition-colors"
              />
            </div>

            {/* Extra fields (Discord guild ID, manual email, etc.) */}
            {(activeModule.extraFields ?? []).map(field => (
              <div key={field.name}>
                {field.type === "checkbox" ? (
                  <label className="flex items-center gap-2 cursor-pointer text-xs text-neutral-400">
                    <input
                      type="checkbox"
                      checked={Boolean(formValues[field.name])}
                      onChange={e => setFormValues(p => ({ ...p, [field.name]: e.target.checked }))}
                      className="accent-indigo-500"
                    />
                    {field.label}
                  </label>
                ) : (
                  <>
                    <label className="text-xs text-neutral-400 block mb-1">
                      {field.label}
                      {!field.required && (
                        <span className="text-neutral-600 ml-1">(optional)</span>
                      )}
                    </label>
                    <input
                      type="text"
                      placeholder={field.placeholder}
                      value={String(formValues[field.name] ?? "")}
                      onChange={e => setFormValues(p => ({ ...p, [field.name]: e.target.value }))}
                      className="w-full rounded bg-neutral-800 border border-neutral-700 px-3 py-2
                                 text-sm text-white placeholder-neutral-600
                                 focus:outline-none focus:border-indigo-500 transition-colors"
                    />
                  </>
                )}
              </div>
            ))}

            {error && <p className="text-sm text-red-400">{error}</p>}

            <div className="flex gap-3 pt-1">
              <button
                type="submit"
                className="flex-1 rounded bg-indigo-600 hover:bg-indigo-500
                           transition-colors py-2 text-sm font-bold text-white"
              >
                ▶ Start Investigation
              </button>
              <button
                type="button"
                onClick={() => setActive(null)}
                className="rounded bg-neutral-800 hover:bg-neutral-700 transition-colors
                           px-4 py-2 text-sm text-neutral-400"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
