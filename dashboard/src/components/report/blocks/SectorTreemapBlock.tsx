"use client";

/**
 * SectorTreemapBlock — simple CSS flex squarified-ish treemap.
 *
 * Recharts ships a ``Treemap`` component but its API is awkward for
 * pnl-colored tiles and its labels are often clipped. We render a tiny
 * flex layout: largest sector takes the first row full-width, the rest
 * flow into a second row scaled by weight. Good enough for a sector
 * allocation overview; drop in d3-hierarchy later if we need exact
 * squarified layout.
 */

interface SectorItem {
  sector: string;
  weight: number;
  pnl?: number;
}

interface SectorTreemapBlockProps {
  items: SectorItem[];
}

function tileColor(pnl: number | undefined): string {
  if (pnl === undefined || pnl === null) return "var(--chart-accent)";
  if (pnl > 0) return "var(--chart-pos)";
  if (pnl < 0) return "var(--chart-neg)";
  return "var(--chart-neutral)";
}

export default function SectorTreemapBlock({ items }: SectorTreemapBlockProps) {
  if (!items || items.length === 0) return null;
  const sorted = [...items].sort((a, b) => b.weight - a.weight).slice(0, 12);
  const totalWeight = sorted.reduce((s, it) => s + Math.max(0, it.weight), 0) || 1;
  return (
    <div
      className="rounded-xl border bg-white dark:bg-slate-900 p-4"
      style={{ borderColor: "var(--border)" }}
    >
      <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-50 mb-2">
        섹터 배분
      </h4>
      <div className="flex flex-wrap gap-1" style={{ minHeight: 160 }}>
        {sorted.map((it, i) => {
          const ratio = (Math.max(0, it.weight) / totalWeight) * 100;
          const bg = tileColor(it.pnl);
          return (
            <div
              key={`${it.sector}-${i}`}
              className="rounded-md text-[11px] text-white flex flex-col items-start justify-end p-2 transition-opacity hover:opacity-90"
              style={{
                backgroundColor: bg,
                flex: `${Math.max(1, ratio)} 1 0`,
                minWidth: 80,
                minHeight: 60,
                opacity: 0.9,
              }}
              title={`${it.sector}: ${ratio.toFixed(1)}%${
                it.pnl !== undefined ? ` · P&L ${((it.pnl ?? 0) * 100).toFixed(1)}%` : ""
              }`}
            >
              <span className="font-semibold truncate max-w-full">{it.sector}</span>
              <span className="tabular opacity-90">{ratio.toFixed(1)}%</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
