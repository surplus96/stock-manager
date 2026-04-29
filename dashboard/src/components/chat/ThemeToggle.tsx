"use client";

/**
 * ThemeToggle — global light/dark mode toggle.
 *
 * Originally shipped inside the chat header (FR-U15) but lifted to the
 * Sidebar so every page can flip theme. Persists the choice in
 * ``localStorage["chat.theme"]`` (kept the key for backward compat) and
 * mirrors the value onto ``<html data-theme>``; globals.css swaps the
 * CSS token palette.
 *
 * The component also reads the saved value on mount so a fresh tab lands
 * in the previously chosen mode without a flash.
 */

import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";

type Theme = "light" | "dark";
const STORAGE_KEY = "chat.theme";

function applyTheme(theme: Theme) {
  if (typeof document === "undefined") return;
  document.documentElement.dataset.theme = theme;
}

interface ThemeToggleProps {
  /** "compact" = 32px icon button (chat header). "full" = icon + label (sidebar footer). */
  variant?: "compact" | "full";
  className?: string;
}

export default function ThemeToggle({ variant = "compact", className = "" }: ThemeToggleProps) {
  const [theme, setTheme] = useState<Theme>("light");

  useEffect(() => {
    const saved = (typeof window !== "undefined" && localStorage.getItem(STORAGE_KEY)) as Theme | null;
    const initial: Theme = saved === "dark" ? "dark" : "light";
    setTheme(initial);
    applyTheme(initial);
  }, []);

  function toggle() {
    const next: Theme = theme === "dark" ? "light" : "dark";
    setTheme(next);
    applyTheme(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      /* localStorage unavailable — toggle still works for this session. */
    }
  }

  const label = theme === "dark" ? "라이트 모드" : "다크 모드";
  const Icon = theme === "dark" ? Sun : Moon;

  if (variant === "full") {
    return (
      <button
        type="button"
        onClick={toggle}
        aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
        className={`${className} w-full flex items-center gap-2 rounded-md px-2 py-1.5 text-xs text-slate-300 hover:text-white hover:bg-slate-800 transition-colors`}
      >
        <Icon className="w-4 h-4" />
        <span>{label}</span>
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
      title={label}
      className={`${className} inline-flex items-center justify-center w-8 h-8 rounded-md border text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800`}
      style={{ borderColor: "var(--border)" }}
    >
      <Icon className="w-4 h-4" />
    </button>
  );
}
