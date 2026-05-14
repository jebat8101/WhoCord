// src/components/Layout.tsx
import React from "react";
import { NavLink, Outlet } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/",           label: "🔍 Investigate" },
  { to: "/live",       label: "📡 Live",        hide: true },   // linked programmatically
  { to: "/history",    label: "🕑 History" },
  { to: "/config",     label: "⚙️ Config" },
];

export default function Layout() {
  return (
    <div className="flex h-screen overflow-hidden bg-neutral-950 text-neutral-200 font-sans">
      {/* ── Sidebar ──────────────────────────────────────────────────── */}
      <nav className="w-52 shrink-0 flex flex-col gap-1 border-r border-neutral-800 bg-neutral-900 p-4">
        <div className="mb-4 text-lg font-bold text-white tracking-tight select-none">
          WhoCord
        </div>

        {NAV_ITEMS.filter((n) => !n.hide).map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              [
                "rounded px-3 py-2 text-sm transition-colors",
                isActive
                  ? "bg-indigo-600 text-white font-semibold"
                  : "text-neutral-400 hover:bg-neutral-800 hover:text-white",
              ].join(" ")
            }
          >
            {item.label}
          </NavLink>
        ))}

        <div className="mt-auto">
          <button
            onClick={async () => {
              if (confirm("Shut down WhoCord server?")) {
                await fetch("/shutdown", { method: "POST" }).catch(() => {});
                setTimeout(() => window.close(), 400);
              }
            }}
            className="w-full rounded px-3 py-2 text-sm text-red-400 hover:bg-neutral-800 text-left transition-colors"
          >
            ⏻ Shut down
          </button>
          <p className="mt-3 text-center text-[10px] text-neutral-600">
            WhoCord v1.1
          </p>
        </div>
      </nav>

      {/* ── Main content ─────────────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
