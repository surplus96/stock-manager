"use client";

/**
 * TickerPill — analyst-style inline ticker badge (FR-PSP-I01).
 *
 * Used **only** in explicit rendering sites (rankings table, news
 * sources, …). We deliberately do **not** auto-rewrite Markdown text
 * via regex (FR-PSP-I02 was excluded under Option B) so user content
 * and LLM output stay verbatim — no surprise substitutions inside
 * LaTeX or Korean prose.
 *
 * Render shape:
 *   AAPL ($190.25 ▲1.23%)
 *   삼성전자 (005930)
 */

import { formatPrice, type Market } from "@/lib/locale";

interface TickerPillProps {
  ticker: string;
  /** Korean company name (optional). When present rendered as "name (ticker)". */
  name?: string | null;
  lastClose?: number | null;
  deltaPct?: number | null;
  market?: Market;
  className?: string;
}

export default function TickerPill({
  ticker,
  name,
  lastClose,
  deltaPct,
  market = "US",
  className = "",
}: TickerPillProps) {
  const positive = (deltaPct ?? 0) >= 0;
  return (
    <span
      className={`inline-flex items-baseline gap-1 px-2 py-0.5 rounded-md
        bg-[var(--accent-soft)] text-xs font-mono tabular align-baseline
        ${className}`}
      title={name ? `${name} (${ticker})` : ticker}
    >
      <span className="font-semibold text-slate-900 dark:text-slate-50">
        {name ? `${name}` : ticker}
      </span>
      {name && (
        <span className="text-slate-500 dark:text-slate-400">({ticker})</span>
      )}
      {lastClose != null && Number.isFinite(lastClose) && (
        <span className="text-slate-700 dark:text-slate-200">
          {formatPrice(lastClose, market)}
        </span>
      )}
      {deltaPct != null && Number.isFinite(deltaPct) && (
        <span
          className={
            positive
              ? "text-[var(--chart-pos)]"
              : "text-[var(--chart-neg)]"
          }
        >
          {positive ? "▲" : "▼"}
          {Math.abs(deltaPct * 100).toFixed(2)}%
        </span>
      )}
    </span>
  );
}
