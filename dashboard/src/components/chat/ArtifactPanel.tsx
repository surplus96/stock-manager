"use client";

/**
 * ArtifactPanel — FR-U01.
 *
 * Right-hand column on md+ viewports. Receives the list of tool artifacts
 * accumulated by the most recent assistant turn and renders one of the
 * typed renderers. On mobile (<md) the parent `<ChatShell>` hides this
 * column and shows a collapsed "Artifacts" strip under the conversation.
 */

import { useState } from "react";
import { PanelRightOpen, Wrench } from "lucide-react";

import RankingsTable from "./RankingsTable";
import MarketGaugeMini from "./MarketGaugeMini";
import NewsListPanel from "./NewsListPanel";
import { BlockList } from "@/components/report/BlockRenderer";
import type { ReportBlock } from "@/lib/reportBlocks";

export interface Artifact {
  tool: string;
  summary: string;
  /** rich-visual-reports: structured block array from tool_result events. */
  blocks?: ReportBlock[];
}

interface ArtifactPanelProps {
  artifacts: Artifact[];
  className?: string;
}

function renderArtifact(a: Artifact) {
  // Prefer structured blocks when the backend provided them (FR-R-B06).
  if (a.blocks && a.blocks.length > 0) {
    return <BlockList blocks={a.blocks} />;
  }
  switch (a.tool) {
    case "rank_stocks":
    case "analyze_theme":
    case "ranking_advanced":
      return <RankingsTable tool={a.tool} summary={a.summary} />;
    case "market_condition":
      return <MarketGaugeMini summary={a.summary} />;
    case "news_sentiment":
      return <NewsListPanel summary={a.summary} />;
    default:
      return (
        <div
          className="rounded-lg border bg-white dark:bg-slate-900 p-3 text-sm text-slate-700 dark:text-slate-200"
          style={{ borderColor: "var(--border)" }}
        >
          <div className="flex items-center gap-2 mb-1 text-xs text-slate-500 font-mono">
            <Wrench className="w-3 h-3" />
            {a.tool}
          </div>
          {a.summary}
        </div>
      );
  }
}

export default function ArtifactPanel({ artifacts, className = "" }: ArtifactPanelProps) {
  const [active, setActive] = useState(0);

  if (artifacts.length === 0) {
    return (
      <aside
        aria-label="Artifact panel"
        role="complementary"
        className={`${className} rounded-xl border bg-white dark:bg-slate-900 p-4 flex flex-col items-center justify-center text-center text-slate-400 dark:text-slate-500`}
        style={{ borderColor: "var(--border)" }}
      >
        <PanelRightOpen className="w-8 h-8 mb-2" />
        <p className="text-sm font-medium">Artifacts</p>
        <p className="text-xs mt-1">
          도구 결과(랭킹, 시장 지표 등)가 여기에 표시됩니다.
        </p>
      </aside>
    );
  }

  const current = artifacts[Math.min(active, artifacts.length - 1)];
  return (
    <aside
      aria-label="Artifact panel"
      role="complementary"
      className={`${className} rounded-xl border bg-white dark:bg-slate-900 p-3 overflow-hidden flex flex-col`}
      style={{ borderColor: "var(--border)" }}
    >
      {artifacts.length > 1 && (
        <div
          role="tablist"
          aria-label="Artifact tabs"
          className="flex gap-1 mb-3 border-b pb-2 overflow-x-auto"
          style={{ borderColor: "var(--border)" }}
        >
          {artifacts.map((a, i) => (
            <button
              key={i}
              role="tab"
              aria-selected={i === active}
              type="button"
              onClick={() => setActive(i)}
              className={`shrink-0 rounded-md px-2 py-1 text-xs font-mono transition-colors ${
                i === active
                  ? "bg-blue-50 dark:bg-blue-950 text-blue-600 dark:text-blue-300"
                  : "text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
              }`}
            >
              {a.tool}
            </button>
          ))}
        </div>
      )}
      <div className="flex-1 overflow-y-auto">{renderArtifact(current)}</div>
    </aside>
  );
}
