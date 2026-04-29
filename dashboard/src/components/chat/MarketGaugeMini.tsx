"use client";

/** MarketGaugeMini — FR-U12. Compact market-condition pill for artifact panel. */

import { Activity } from "lucide-react";

export default function MarketGaugeMini({ summary }: { summary: string }) {
  return (
    <div className="text-sm">
      <div className="flex items-center gap-2 mb-2 text-slate-700 dark:text-slate-200">
        <Activity className="w-4 h-4 text-blue-500" />
        <span className="font-medium">Market condition</span>
      </div>
      <div
        className="rounded-lg border bg-white dark:bg-slate-900 p-3 tabular"
        style={{ borderColor: "var(--border)" }}
      >
        <p className="text-sm text-slate-700 dark:text-slate-200">{summary}</p>
      </div>
    </div>
  );
}
