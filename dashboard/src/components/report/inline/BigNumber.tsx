"use client";

/** BigNumber — large tabular number with optional delta badge. */

import type { Tone } from "@/lib/reportBlocks";

interface BigNumberProps {
  value: string;
  tone?: Tone;
  delta?: number;
  hint?: string;
  label?: string;
}

function toneColor(tone?: Tone) {
  switch (tone) {
    case "positive":
      return "text-emerald-600 dark:text-emerald-400";
    case "negative":
      return "text-red-600 dark:text-red-400";
    default:
      return "text-slate-900 dark:text-slate-50";
  }
}

export default function BigNumber({ value, tone, delta, hint, label }: BigNumberProps) {
  return (
    <div className="flex flex-col gap-0.5">
      {label && (
        <span className="text-xs text-slate-500 dark:text-slate-400">{label}</span>
      )}
      <div className="flex items-baseline gap-2">
        <span className={`text-2xl font-semibold tabular ${toneColor(tone)}`}>{value}</span>
        {typeof delta === "number" && (
          <span
            className={`text-xs tabular ${
              delta >= 0
                ? "text-emerald-600 dark:text-emerald-400"
                : "text-red-600 dark:text-red-400"
            }`}
          >
            {delta >= 0 ? "+" : ""}
            {(delta * 100).toFixed(2)}%
          </span>
        )}
      </div>
      {hint && (
        <span className="text-[11px] text-slate-500 dark:text-slate-400">{hint}</span>
      )}
    </div>
  );
}
