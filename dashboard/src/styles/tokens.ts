/**
 * Design tokens (FR-F12).
 *
 * Mirrors the `@theme` block in globals.css so TS code can reference semantic
 * colors without string-typing hex codes. Update both locations in lockstep.
 */

export const colors = {
  background: "var(--background)",
  foreground: "var(--foreground)",
  brand: "var(--primary)",
  brandAccent: "var(--secondary)",
  positive: "var(--positive)",
  negative: "var(--negative)",
  neutral: "var(--neutral)",
  surface: "var(--card-bg)",
  borderSubtle: "var(--border)",
  sidebar: {
    bg: "var(--sidebar-bg)",
    text: "var(--sidebar-text)",
    active: "var(--sidebar-active)",
  },
} as const;

export const radius = {
  card: "0.75rem",
  pill: "9999px",
} as const;

export const signal = {
  up: colors.positive,
  down: colors.negative,
  flat: colors.neutral,
} as const;

export type SignalColor = keyof typeof signal;
