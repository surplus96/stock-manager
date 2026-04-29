"use client";

/**
 * RankingsTable — FR-U11.
 *
 * Placeholder renderer for ``rank_stocks`` / ``analyze_theme`` artifacts.
 * The streaming ``tool_result`` payload only carries a ``summary`` string
 * (e.g. "5 rankings"), so this component currently shows the summary plus
 * a "full data coming soon" hint. Once the streaming schema is extended
 * to carry the structured rankings array (see roadmap follow-up), drop in
 * real sortable rows here without touching the callsite.
 */

import { Trophy } from "lucide-react";

interface RankingsTableProps {
  summary: string;
  tool: string;
}

export default function RankingsTable({ summary, tool }: RankingsTableProps) {
  return (
    <div className="text-sm">
      <div className="flex items-center gap-2 mb-2 text-slate-700 dark:text-slate-200">
        <Trophy className="w-4 h-4 text-amber-500" />
        <span className="font-medium">Rankings</span>
        <span className="ml-auto text-xs text-slate-400 font-mono">{tool}</span>
      </div>
      <div
        className="rounded-lg border bg-white dark:bg-slate-900 p-3 tabular"
        style={{ borderColor: "var(--border)" }}
      >
        <p className="text-sm text-slate-700 dark:text-slate-200">{summary}</p>
        <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-1">
          (상세 표 데이터는 다음 배포에서 제공됩니다.)
        </p>
      </div>
    </div>
  );
}
