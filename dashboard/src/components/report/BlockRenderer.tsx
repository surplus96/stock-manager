"use client";

import type { ReportBlock } from "@/lib/reportBlocks";
import SummaryBlock from "./blocks/SummaryBlock";
import MetricGridBlock from "./blocks/MetricGridBlock";
import FactorBulletBlock from "./blocks/FactorBulletBlock";
import NewsCitationBlock from "./blocks/NewsCitationBlock";
import PriceSparkBlock from "./blocks/PriceSparkBlock";
import CandlestickBlock from "./blocks/CandlestickBlock";
import TableBlock from "./blocks/TableBlock";
import HeatmapBlock from "./blocks/HeatmapBlock";
import SectorTreemapBlock from "./blocks/SectorTreemapBlock";
import RadarMiniBlock from "./blocks/RadarMiniBlock";
import SuggestedBlock from "./blocks/SuggestedBlock";
import BigNumber from "./inline/BigNumber";

function UnknownBlock({ block }: { block: ReportBlock }) {
  return (
    <div
      className="rounded-lg border bg-slate-50 dark:bg-slate-800 px-3 py-2 text-xs text-slate-600 dark:text-slate-300"
      style={{ borderColor: "var(--border)" }}
    >
      <span className="font-mono">Unknown block: {(block as { kind?: string }).kind ?? "?"}</span>
    </div>
  );
}

export function BlockRenderer({ block }: { block: ReportBlock }) {
  switch (block.kind) {
    case "summary":
      return <SummaryBlock {...block} />;
    case "metric":
      return (
        <div className="rounded-xl border bg-white dark:bg-slate-900 p-3" style={{ borderColor: "var(--border)" }}>
          <BigNumber label={block.label} value={block.value} tone={block.tone} delta={block.delta} hint={block.hint} />
        </div>
      );
    case "metric_grid":
      return <MetricGridBlock items={block.items} />;
    case "factor_bullet":
      return <FactorBulletBlock factors={block.factors} />;
    case "news_citation":
      return <NewsCitationBlock items={block.items} />;
    case "price_spark":
      return <PriceSparkBlock ticker={block.ticker} market={block.market} series={block.series} />;
    case "candlestick":
      return (
        <CandlestickBlock
          ticker={block.ticker}
          market={block.market}
          rows={block.rows}
          overlays={block.overlays}
          with_volume={block.with_volume}
        />
      );
    case "table":
      return <TableBlock columns={block.columns} rows={block.rows} caption={block.caption} />;
    case "heatmap":
      return <HeatmapBlock xs={block.xs} ys={block.ys} matrix={block.matrix} scale={block.scale} />;
    case "sector_treemap":
      return <SectorTreemapBlock items={block.items} />;
    case "radar_mini":
      return <RadarMiniBlock factors={block.factors} max={block.max} />;
    case "suggested":
      // onPick is not threaded through the dispatcher — chat page renders
      // SuggestedBlock directly with sendText so chips submit a new turn.
      // Inside an analysis report this block falls through with no handler.
      return <SuggestedBlock items={block.items} />;
    default:
      return <UnknownBlock block={block as ReportBlock} />;
  }
}

/** Render a list of blocks stacked vertically with a gentle mount
 *  stagger so long reports don't "pop" onto screen all at once. */
import { FadeIn } from "./inline/Motion";

export function BlockList({ blocks }: { blocks: ReportBlock[] }) {
  if (!blocks || blocks.length === 0) return null;
  return (
    <div className="space-y-4">
      {blocks.map((b, i) => (
        <FadeIn key={i} delayMs={i * 40}>
          {/* FR-PSP-G — anchor target for the Pages-style Toc sidebar.
              Plain section wrapper; no extra spacing introduced. */}
          <section id={`block-${i}`} className="scroll-mt-24">
            <BlockRenderer block={b} />
          </section>
        </FadeIn>
      ))}
    </div>
  );
}
