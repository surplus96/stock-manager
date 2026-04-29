"use client";

/**
 * MarketSelector — 3-way pill (AUTO / US / KR).
 *
 * "AUTO" defers to the caller's ticker heuristic (``detectMarketFromTicker``
 * in ``lib/locale``). The component itself only owns the explicit choice —
 * pages decide whether to short-circuit to AUTO on ticker change.
 */

import type { Market } from "@/lib/locale";
import { Flag, Globe2 } from "lucide-react";

export type MarketChoice = "AUTO" | Market;

interface MarketSelectorProps {
  value: MarketChoice;
  onChange: (next: MarketChoice) => void;
  className?: string;
}

const OPTIONS: { value: MarketChoice; label: string; hint: string }[] = [
  { value: "AUTO", label: "AUTO", hint: "티커로 자동 감지" },
  { value: "US", label: "US", hint: "NYSE / NASDAQ" },
  { value: "KR", label: "KR", hint: "KOSPI / KOSDAQ" },
];

export default function MarketSelector({ value, onChange, className = "" }: MarketSelectorProps) {
  return (
    <div
      role="radiogroup"
      aria-label="Market selector"
      className={`inline-flex rounded-lg border overflow-hidden text-xs font-medium ${className}`}
      style={{ borderColor: "var(--border)" }}
    >
      {OPTIONS.map((opt) => {
        const selected = value === opt.value;
        return (
          <button
            key={opt.value}
            type="button"
            role="radio"
            aria-checked={selected}
            onClick={() => onChange(opt.value)}
            title={opt.hint}
            className={`inline-flex items-center gap-1 px-3 py-1.5 transition-colors ${
              selected
                ? "bg-blue-600 text-white"
                : "bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
            }`}
          >
            {opt.value === "US" && <Flag className="w-3 h-3" />}
            {opt.value === "KR" && <Flag className="w-3 h-3" />}
            {opt.value === "AUTO" && <Globe2 className="w-3 h-3" />}
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
