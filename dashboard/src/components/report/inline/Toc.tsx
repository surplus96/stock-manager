"use client";

/**
 * Toc — Pages-style sticky table of contents (FR-PSP-G).
 *
 * Auto-generated from a ``ReportBlock[]`` and only mounted when the
 * report exceeds the threshold (default 5 blocks). Hidden on viewports
 * narrower than ``lg`` to preserve our existing single-column mobile
 * experience — there's no replacement scroll-to-top for now because
 * mobile reports are short enough not to need one.
 *
 * Anchor scheme matches ``BlockList`` which wraps each block in
 * ``<section id="block-{i}">`` so plain anchor links handle navigation
 * — no scroll-spy library, no JS scroll handling.
 */

import { useEffect, useState } from "react";
import { ArrowUp } from "lucide-react";
import type { ReportBlock } from "@/lib/reportBlocks";

interface TocProps {
  blocks: ReportBlock[];
  threshold?: number;
}

function tocLabel(b: ReportBlock): string | null {
  switch (b.kind) {
    case "summary":
      return b.title || "요약";
    case "metric_grid":
    case "metric":
      return "주요 지표";
    case "factor_bullet":
      return "팩터 점수";
    case "candlestick":
      return "캔들스틱";
    case "price_spark":
      return "가격 추이";
    case "news_citation":
      return "관련 뉴스";
    case "table":
      return b.caption || "표";
    case "heatmap":
      return "히트맵";
    case "sector_treemap":
      return "섹터 배분";
    case "radar_mini":
      return "팩터 레이더";
    case "suggested":
      return null; // Suggested chips don't deserve their own TOC entry.
    default:
      return null;
  }
}

export default function Toc({ blocks, threshold = 5 }: TocProps) {
  if (!blocks || blocks.length < threshold) return null;
  const items = blocks
    .map((b, i) => ({ i, label: tocLabel(b) }))
    .filter((x): x is { i: number; label: string } => Boolean(x.label));
  if (items.length === 0) return null;
  return (
    <>
      {/* Desktop sidebar (lg+): sticky table of contents. */}
      <aside
        aria-label="Report contents"
        className="hidden lg:block sticky top-20 w-44 shrink-0 self-start"
      >
        <p className="font-display text-xs font-medium text-slate-500 dark:text-slate-400 mb-2">
          목차
        </p>
        <ul className="space-y-1 text-xs border-l" style={{ borderColor: "var(--border)" }}>
          {items.map((x) => (
            <li key={x.i}>
              <a
                href={`#block-${x.i}`}
                className="block pl-3 py-1 text-slate-600 dark:text-slate-300 hover:text-[var(--accent)] hover:bg-[var(--accent-soft)] transition-colors"
              >
                {x.label}
              </a>
            </li>
          ))}
        </ul>
      </aside>
      {/* FR-PSP-G03 — mobile fallback: floating scroll-to-top button only. */}
      <ScrollToTopButton />
    </>
  );
}

/** Mobile-only floating button (lg breakpoint hides it). Appears after the
 *  user has scrolled past the first viewport so it doesn't compete with the
 *  initial reading area. */
function ScrollToTopButton() {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    if (typeof window === "undefined") return;
    function onScroll() {
      setVisible(window.scrollY > window.innerHeight * 0.6);
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  if (!visible) return null;
  return (
    <button
      type="button"
      onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
      aria-label="Scroll to top"
      title="맨 위로"
      className="lg:hidden fixed bottom-6 right-6 z-30 inline-flex items-center justify-center w-10 h-10 rounded-full border bg-[var(--accent)] text-white shadow-lg hover:opacity-90 transition-opacity focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)]"
      style={{ borderColor: "var(--border)" }}
    >
      <ArrowUp className="w-4 h-4" />
    </button>
  );
}
