"use client";

import { Markdown } from "@/components/ui/Markdown";

interface SummaryBlockProps {
  title?: string;
  markdown: string;
  citations?: number[];
}

/**
 * FR-PSP-C01 — replace ``[N]`` markers with anchor links. The Markdown
 * component renders it as plain text, but ``react-markdown`` allows raw
 * HTML when explicitly emitted; we keep things simple by pre-rewriting
 * the source so the existing pipeline doesn't need a rehype plugin.
 *
 * Defensive: if the regex misses a marker (e.g. ``[1, 2]``) the original
 * text passes through untouched — no functional regression.
 */
function linkifyCitations(md: string): string {
  if (!md) return md;
  return md.replace(/\[(\d{1,3})\](?!\()/g, (_, n) => {
    const num = String(n);
    return ` [\`${num}\`](#cite-${num})`;
  });
}

export default function SummaryBlock({ title, markdown, citations }: SummaryBlockProps) {
  const linked = linkifyCitations(markdown);
  return (
    <section className="space-y-2 prose-loose">
      {title && (
        /* FR-PSP-T01 — display serif title */
        <h3 className="font-display text-base font-semibold text-slate-900 dark:text-slate-50">
          {title}
        </h3>
      )}
      <div>
        <Markdown>{linked}</Markdown>
      </div>
      {citations && citations.length > 0 && (
        <p className="text-xs text-slate-500 dark:text-slate-400">
          참조: {citations.map((c) => `[${c}]`).join(" ")}
        </p>
      )}
    </section>
  );
}
