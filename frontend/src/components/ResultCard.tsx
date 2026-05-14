// src/components/ResultCard.tsx
import React from "react";
import type { Finding, FindingCategory } from "../types/investigation";

// ── Category theming ────────────────────────────────────────────────────────

const CATEGORY_STYLES: Record<FindingCategory, { border: string; badge: string; icon: string }> = {
  identity:      { border: "border-indigo-700",  badge: "bg-indigo-900 text-indigo-300",  icon: "👤" },
  email:         { border: "border-sky-700",      badge: "bg-sky-900 text-sky-300",        icon: "✉️" },
  social:        { border: "border-violet-700",   badge: "bg-violet-900 text-violet-300",  icon: "🔗" },
  breach:        { border: "border-red-700",      badge: "bg-red-900 text-red-300",        icon: "⚠️" },
  media:         { border: "border-amber-700",    badge: "bg-amber-900 text-amber-300",    icon: "🖼" },
  intelligence:  { border: "border-emerald-700",  badge: "bg-emerald-900 text-emerald-300",icon: "🧠" },
  pivot:         { border: "border-green-700",    badge: "bg-green-900 text-green-300",    icon: "🔄" },
  phone:         { border: "border-neutral-700",  badge: "bg-neutral-800 text-neutral-400",icon: "📱" },
  url:           { border: "border-neutral-700",  badge: "bg-neutral-800 text-neutral-400",icon: "🔗" },
  probe:         { border: "border-neutral-700",  badge: "bg-neutral-800 text-neutral-400",icon: "🔎" },
  network:       { border: "border-neutral-700",  badge: "bg-neutral-800 text-neutral-400",icon: "🌐" },
  other:         { border: "border-neutral-700",  badge: "bg-neutral-800 text-neutral-400",icon: "•" },
};

// ── Finding label helpers ────────────────────────────────────────────────────

const TYPE_LABELS: Record<string, string> = {
  email:               "Email Address",
  name_clue:           "Name Clue",
  avatar_url:          "Avatar URL",
  connected_account:   "Connected Account",
  discord_handle:      "Discord Handle",
  holehe:              "Site Registrations (Holehe)",
  hibp:                "HIBP Breaches",
  h8mail:              "Breach Data (h8mail)",
  gravatar:            "Gravatar Profile",
  ghunt:               "Google Account (GHunt)",
  emailrep:            "EmailRep Score",
  exif_gps:            "EXIF GPS Coordinates",
  reverse_image:       "Reverse Image Match",
  correlations:        "Intelligence Correlations",
  intelligence_report: "Intelligence Report",
  persona_summary:     "AI Persona Summary",
  wayback:             "Wayback Snapshot",
  whois:               "WHOIS Data",
  name_similarity:     "Name Similarity",
  confidence_scores:   "Identity Confidence",
  avatar_downloaded:   "Avatar Downloaded",
  language:            "Language Detected",
  location:            "Location Inferred",
};

function buildDetail(finding: Finding): string {
  const p = finding.payload;
  if (p.value)     return String(p.value);
  if (p.email)     return String(p.email);
  if (p.url)       return String(p.url);
  if (p.domain)    return String(p.domain);
  if (p.platform)  return `${p.platform}${p.value ? `: ${p.value}` : ""}`;
  if (p.sites)     return `${(p.sites as string[]).slice(0, 4).join(", ")}${(p.sites as string[]).length > 4 ? "…" : ""}`;
  if (p.breaches !== undefined)        return `${p.breaches} breach(es)`;
  if (p.entity_count !== undefined)    return `${p.entity_count} entities, ${p.correlation_count} correlations`;
  return "";
}

// ── Component ────────────────────────────────────────────────────────────────

interface Props {
  finding: Finding;
}

export default function ResultCard({ finding }: Props) {
  const styles = CATEGORY_STYLES[finding.category];
  const detail = buildDetail(finding);

  return (
    <div
      className={`rounded-lg border ${styles.border} bg-neutral-900 p-3 flex gap-3 items-start`}
    >
      {/* Icon */}
      <span className="text-lg leading-none mt-0.5 shrink-0">{styles.icon}</span>

      <div className="flex-1 min-w-0">
        {/* Type badge + stage */}
        <div className="flex items-center gap-2 flex-wrap mb-1">
          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider ${styles.badge}`}>
            {TYPE_LABELS[finding.type] ?? finding.type}
          </span>
          <span className="text-[10px] text-neutral-600">{finding.stage}</span>
        </div>

        {/* Main detail */}
        {detail && (
          <p className="text-sm text-neutral-300 break-all">{detail}</p>
        )}

        {/* Source */}
        {finding.payload.source && (
          <p className="text-[10px] text-neutral-600 mt-0.5">
            via {String(finding.payload.source)}
          </p>
        )}
      </div>

      {/* Timestamp */}
      <span className="text-[10px] text-neutral-700 shrink-0 tabular-nums">
        {new Date(finding.timestamp).toLocaleTimeString()}
      </span>
    </div>
  );
}
