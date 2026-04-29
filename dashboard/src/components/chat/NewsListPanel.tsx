"use client";

/** NewsListPanel — placeholder renderer for ``news_sentiment``. */

import { Newspaper } from "lucide-react";

export default function NewsListPanel({ summary }: { summary: string }) {
  return (
    <div className="text-sm">
      <div className="flex items-center gap-2 mb-2 text-slate-700 dark:text-slate-200">
        <Newspaper className="w-4 h-4 text-emerald-500" />
        <span className="font-medium">News sentiment</span>
      </div>
      <div
        className="rounded-lg border bg-white dark:bg-slate-900 p-3"
        style={{ borderColor: "var(--border)" }}
      >
        <p className="text-sm text-slate-700 dark:text-slate-200">{summary}</p>
      </div>
    </div>
  );
}
