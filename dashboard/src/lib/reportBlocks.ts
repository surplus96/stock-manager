/**
 * TypeScript mirror of ``api/schemas/report_blocks.py`` (rich-visual-reports).
 *
 * Discriminated by ``kind`` so the UI dispatcher is exhaustive. Any new
 * block variant must be added in both places or the backend/Pydantic
 * coercer will drop it silently.
 */

export type Tone = "positive" | "negative" | "neutral";
export type Market = "US" | "KR";

export interface MetricItem {
  label: string;
  value: string;
  delta?: number;
  tone?: Tone;
  hint?: string;
}

export interface TableColumn {
  key: string;
  label: string;
  numeric?: boolean;
  format?: "currency" | "percent" | "compact" | "integer";
}

export interface OHLCVRow {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface PriceBarLite {
  t: string;
  c: number;
}

export interface NewsCitationItem {
  id: number;
  source: string;
  title: string;
  date: string;
  url?: string;
  snippet?: string;
}

export interface FactorBulletItem {
  name: string;
  score: number;
  note?: string;
}

export type ReportBlock =
  | { kind: "summary"; title?: string; markdown: string; citations?: number[] }
  | { kind: "metric"; label: string; value: string; delta?: number; tone?: Tone; hint?: string }
  | { kind: "metric_grid"; items: MetricItem[] }
  | { kind: "factor_bullet"; factors: FactorBulletItem[] }
  | { kind: "news_citation"; items: NewsCitationItem[] }
  | { kind: "price_spark"; ticker: string; market: Market; series: PriceBarLite[] }
  | {
      kind: "candlestick";
      ticker: string;
      market: Market;
      rows: OHLCVRow[];
      overlays?: ("ma20" | "ma50" | "bb")[];
      with_volume?: boolean;
    }
  | { kind: "table"; columns: TableColumn[]; rows: Record<string, unknown>[]; caption?: string }
  | {
      kind: "heatmap";
      xs: string[];
      ys: string[];
      matrix: number[][];
      scale?: "correlation" | "heat";
    }
  | {
      kind: "sector_treemap";
      items: { sector: string; weight: number; pnl?: number }[];
    }
  | { kind: "radar_mini"; factors: FactorBulletItem[]; max?: number }
  | { kind: "suggested"; items: string[] };

export function isReportBlock(value: unknown): value is ReportBlock {
  if (typeof value !== "object" || value === null) return false;
  const k = (value as { kind?: unknown }).kind;
  return typeof k === "string";
}
