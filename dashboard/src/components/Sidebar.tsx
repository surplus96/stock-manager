"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import {
  BarChart3,
  Search,
  Briefcase,
  Trophy,
  Compass,
  Activity,
  MessageSquare,
  Menu,
  X,
} from "lucide-react";
import ThemeToggle from "./chat/ThemeToggle";

const NAV = [
  { href: "/", label: "Market Overview", icon: Activity },
  { href: "/stock", label: "Stock Analyzer", icon: Search },
  { href: "/portfolio", label: "Portfolio", icon: Briefcase },
  { href: "/theme", label: "Theme Explorer", icon: Compass },
  { href: "/ranking", label: "Ranking Engine", icon: Trophy },
  { href: "/chat", label: "AI Chatbot", icon: MessageSquare },
];

/** FR-F14: Sidebar becomes a drawer on < md; hamburger toggles an overlay. */
export default function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  // Auto-close on route change.
  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  // Lock body scroll while the mobile drawer is open.
  useEffect(() => {
    if (typeof document === "undefined") return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = open ? "hidden" : prev;
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  const navList = (
    <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto" aria-label="Primary">
      {NAV.map(({ href, label, icon: Icon }) => {
        const active = pathname === href;
        return (
          <Link
            key={href}
            href={href}
            aria-current={active ? "page" : undefined}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] ${
              active
                ? "bg-[var(--accent-soft)] text-white"
                : "text-slate-400 hover:text-slate-200 hover:bg-[var(--accent-soft)]"
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </Link>
        );
      })}
    </nav>
  );

  const brand = (
    <div className="flex items-center gap-2 px-5 py-5 border-b border-slate-700">
      <BarChart3 className="w-7 h-7 text-blue-500" />
      <span className="text-lg font-bold text-white tracking-tight">
        Stock Manager
      </span>
    </div>
  );

  const footer = (
    <div className="px-3 py-4 border-t border-slate-700 space-y-2">
      <ThemeToggle variant="full" />
      <div className="px-2">
        <p className="text-xs text-slate-500">Powered by PM-MCP</p>
        <p className="text-xs text-slate-600">40-Factor Analysis Engine</p>
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile hamburger trigger (visible < md) */}
      <button
        type="button"
        aria-label={open ? "Close navigation" : "Open navigation"}
        aria-expanded={open}
        aria-controls="primary-drawer"
        onClick={() => setOpen((v) => !v)}
        className="md:hidden fixed top-3 left-3 z-50 inline-flex items-center justify-center w-10 h-10 rounded-md bg-slate-900/90 text-slate-100 shadow focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
      >
        {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {/* Desktop sidebar (>= md) */}
      <aside
        aria-label="Primary navigation"
        className="fixed left-0 top-0 h-full w-60 flex-col z-40 hidden md:flex"
        style={{ backgroundColor: "var(--sidebar-bg)" }}
      >
        {brand}
        {navList}
        {footer}
      </aside>

      {/* Mobile drawer + scrim (< md) */}
      <div
        className={`md:hidden fixed inset-0 z-40 transition-opacity ${
          open ? "pointer-events-auto opacity-100" : "pointer-events-none opacity-0"
        }`}
        aria-hidden={!open}
      >
        <button
          type="button"
          aria-label="Close navigation overlay"
          tabIndex={open ? 0 : -1}
          onClick={() => setOpen(false)}
          className="absolute inset-0 bg-black/50"
        />
        <aside
          id="primary-drawer"
          role="dialog"
          aria-modal="true"
          aria-label="Primary navigation"
          className={`absolute left-0 top-0 h-full w-64 flex flex-col shadow-xl transition-transform ${
            open ? "translate-x-0" : "-translate-x-full"
          }`}
          style={{ backgroundColor: "var(--sidebar-bg)" }}
        >
          {brand}
          {navList}
          {footer}
        </aside>
      </div>
    </>
  );
}
