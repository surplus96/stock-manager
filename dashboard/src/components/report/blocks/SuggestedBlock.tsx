"use client";

/**
 * SuggestedBlock — follow-up question chips (FR-PSP-F).
 *
 * Rendered at the bottom of an assistant turn (chat) or analysis report.
 * Click semantics:
 *   - Chat page: ``onPick`` re-runs ``sendText`` so the chip becomes
 *     the next user query.
 *   - Analysis page: ``onPick`` defaults to a no-op (the user can copy
 *     the text or wire it to a router push later).
 *
 * Defensive against malformed data: empty items / non-string entries
 * filter out and the component renders nothing.
 */

import { Lightbulb } from "lucide-react";

interface SuggestedBlockProps {
  items: string[];
  onPick?: (question: string) => void;
}

export default function SuggestedBlock({ items, onPick }: SuggestedBlockProps) {
  const clean = (items ?? []).filter((s) => typeof s === "string" && s.trim().length > 0);
  if (clean.length === 0) return null;
  return (
    <div className="mt-4">
      <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 mb-2">
        <Lightbulb className="w-3.5 h-3.5" />
        <span>이어 질문해 보세요</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {clean.map((q, i) => (
          <button
            key={i}
            type="button"
            onClick={() => onPick?.(q)}
            disabled={!onPick}
            className="text-xs px-3 py-1.5 rounded-full border transition-colors
              bg-[var(--accent-soft)] text-[var(--accent)]
              hover:bg-[var(--accent)] hover:text-white
              disabled:opacity-60 disabled:cursor-default disabled:hover:bg-[var(--accent-soft)] disabled:hover:text-[var(--accent)]"
            style={{ borderColor: "var(--border)" }}
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
