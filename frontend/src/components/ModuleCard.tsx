// src/components/ModuleCard.tsx
import React from "react";
import type { ModuleMeta } from "../types/investigation";

interface Props {
  module:       ModuleMeta;
  onClick:      (module: ModuleMeta) => void;
  isActive?:    boolean;
  extraColors?: Record<string, { border: string; hover: string; badge: string }>;
}

const BASE_COLOR_STYLES: Record<string, { border: string; hover: string; badge: string }> = {
  indigo:  { border: "border-indigo-700",  hover: "hover:border-indigo-500",  badge: "bg-indigo-900 text-indigo-300" },
  sky:     { border: "border-sky-700",     hover: "hover:border-sky-500",     badge: "bg-sky-900 text-sky-300" },
  violet:  { border: "border-violet-700",  hover: "hover:border-violet-500",  badge: "bg-violet-900 text-violet-300" },
  emerald: { border: "border-emerald-700", hover: "hover:border-emerald-500", badge: "bg-emerald-900 text-emerald-300" },
  amber:   { border: "border-amber-700",   hover: "hover:border-amber-500",   badge: "bg-amber-900 text-amber-300" },
  rose:    { border: "border-rose-700",    hover: "hover:border-rose-500",    badge: "bg-rose-900 text-rose-300" },
  teal:    { border: "border-teal-700",    hover: "hover:border-teal-500",    badge: "bg-teal-900 text-teal-300" },
  green:   { border: "border-green-700",   hover: "hover:border-green-500",   badge: "bg-green-900 text-green-300" },
};

export default function ModuleCard({ module, onClick, isActive = false, extraColors = {} }: Props) {
  const palette = { ...BASE_COLOR_STYLES, ...extraColors };
  const styles  = palette[module.color] ?? palette.indigo;

  return (
    <button
      onClick={() => onClick(module)}
      className={[
        "group rounded-xl border bg-neutral-900 p-4 text-left w-full",
        "transition-all duration-200 cursor-pointer",
        styles.border, styles.hover,
        isActive
          ? "ring-2 ring-offset-1 ring-offset-neutral-950 ring-indigo-500 bg-neutral-800"
          : "hover:bg-neutral-800 hover:shadow-lg hover:shadow-black/40",
      ].join(" ")}
    >
      <div className="text-2xl mb-2.5">{module.icon}</div>
      <h3 className="text-sm font-semibold text-white mb-1 leading-tight">{module.title}</h3>
      <p className="text-[11px] text-neutral-500 leading-relaxed mb-3 line-clamp-2">
        {module.description}
      </p>
      <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${styles.badge}`}>
        {isActive ? "Selected" : "Launch"}
      </span>
    </button>
  );
}
