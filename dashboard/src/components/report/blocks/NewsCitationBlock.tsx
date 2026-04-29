"use client";

import { Newspaper } from "lucide-react";
import type { NewsCitationItem } from "@/lib/reportBlocks";

export default function NewsCitationBlock({ items }: { items: NewsCitationItem[] }) {
  if (!items || items.length === 0) return null;
  return (
    <div
      className="rounded-xl border bg-white dark:bg-slate-900 p-4"
      style={{ borderColor: "var(--border)" }}
    >
      <h4 className="flex items-center gap-1.5 text-sm font-semibold text-slate-900 dark:text-slate-50 mb-3">
        <Newspaper className="w-4 h-4 text-emerald-500" />
        관련 뉴스 & 인용
      </h4>
      <ol className="space-y-2">
        {items.map((n) => (
          <li
            key={n.id}
            id={`cite-${n.id}`}
            className="text-xs flex items-start gap-2 scroll-mt-24 target:bg-[var(--accent-soft)] target:rounded-md target:transition-colors"
          >
            <span
              aria-label={`citation ${n.id}`}
              className="shrink-0 inline-flex items-center justify-center w-5 h-5 rounded-full bg-[var(--accent-soft)] text-[var(--accent)] text-[10px] font-semibold tabular"
            >
              {n.id}
            </span>
            <div className="flex-1 min-w-0">
              <a
                href={n.url || "#"}
                target="_blank"
                rel="noopener noreferrer"
                className="font-medium text-slate-900 dark:text-slate-50 hover:text-blue-600 dark:hover:text-blue-300 line-clamp-2"
              >
                {n.title}
              </a>
              <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                {n.source}
                {n.date ? ` · ${n.date}` : ""}
              </div>
              {n.snippet && (
                <p className="text-[11px] text-slate-600 dark:text-slate-300 mt-0.5 line-clamp-2">
                  {n.snippet}
                </p>
              )}
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
