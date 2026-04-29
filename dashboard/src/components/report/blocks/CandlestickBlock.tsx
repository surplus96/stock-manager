"use client";

/**
 * CandlestickBlock — Recharts ComposedChart + custom candle shape
 * (rich-visual-reports FR-R-F08/C04).
 *
 * Why not ``lightweight-charts``? Would add ~40 KB gzip and a second
 * rendering engine. We already depend on Recharts for everything else;
 * a ~50-line custom Bar shape gives us wicks + coloured bodies with
 * no new dependency.
 */

import { useMemo } from "react";
import type { OHLCVRow, Market } from "@/lib/reportBlocks";
import { LazyChart } from "@/components/ui/LazyChart";
import { ChartTooltip } from "@/components/charts/ChartTooltip";
import { formatPrice } from "@/lib/locale";

interface CandlestickBlockProps {
  ticker: string;
  market: Market;
  rows: OHLCVRow[];
  overlays?: ("ma20" | "ma50" | "bb")[];
  with_volume?: boolean;
}

interface ChartRow extends OHLCVRow {
  ma20?: number;
  ma50?: number;
  // Recharts expects a single Y value per data point to draw a Bar; we
  // encode the candle as a 2-tuple [low, high] range. The custom shape
  // reads open/close from payload to decide colour and body size.
  range: [number, number];
}

function movingAverage(rows: OHLCVRow[], window: number): number[] {
  const out: number[] = [];
  for (let i = 0; i < rows.length; i++) {
    if (i < window - 1) {
      out.push(NaN);
      continue;
    }
    let sum = 0;
    for (let j = i - window + 1; j <= i; j++) sum += rows[j].close;
    out.push(sum / window);
  }
  return out;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function CandleShape(props: any) {
  const { x, y, width, height, payload } = props as {
    x: number;
    y: number;
    width: number;
    height: number;
    payload: ChartRow;
  };
  if (!payload) return null;
  const { open, close, high, low } = payload;
  if (![open, close, high, low].every((n) => Number.isFinite(n))) return null;

  // Recharts maps our range=[low,high] into (y, y+height). Convert any
  // price to pixel space by linear interpolation.
  const priceToY = (price: number) => {
    if (high === low) return y + height / 2;
    return y + ((high - price) / (high - low)) * height;
  };

  const up = close >= open;
  const color = up ? "var(--chart-pos)" : "var(--chart-neg)";
  const bodyTop = priceToY(Math.max(open, close));
  const bodyBottom = priceToY(Math.min(open, close));
  const centerX = x + width / 2;
  const bodyWidth = Math.max(2, width * 0.7);
  const bodyH = Math.max(1, bodyBottom - bodyTop);

  return (
    <g>
      {/* wick */}
      <line
        x1={centerX}
        x2={centerX}
        y1={y}
        y2={y + height}
        stroke={color}
        strokeWidth={1}
      />
      {/* body */}
      <rect
        x={centerX - bodyWidth / 2}
        y={bodyTop}
        width={bodyWidth}
        height={bodyH}
        fill={up ? color : color}
        opacity={up ? 0.95 : 0.9}
      />
    </g>
  );
}

export default function CandlestickBlock({
  ticker,
  market,
  rows,
  overlays = [],
  with_volume = true,
}: CandlestickBlockProps) {
  const data: ChartRow[] = useMemo(() => {
    if (!rows || rows.length === 0) return [];
    const ma20 = movingAverage(rows, 20);
    const ma50 = movingAverage(rows, 50);
    return rows.map((r, i) => ({
      ...r,
      range: [r.low, r.high] as [number, number],
      ma20: overlays.includes("ma20") && Number.isFinite(ma20[i]) ? ma20[i] : undefined,
      ma50: overlays.includes("ma50") && Number.isFinite(ma50[i]) ? ma50[i] : undefined,
    }));
  }, [rows, overlays]);

  if (data.length === 0) return null;

  return (
    <div
      className="rounded-xl border bg-white dark:bg-slate-900 p-4"
      style={{ borderColor: "var(--border)" }}
    >
      <div className="flex items-baseline justify-between mb-2">
        <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-50">
          {ticker} · 캔들스틱 (6M)
        </h4>
        <span className="text-[11px] text-slate-500 dark:text-slate-400">
          overlays: {overlays.length > 0 ? overlays.join(", ") : "none"}
          {with_volume ? " · volume" : ""}
        </span>
      </div>
      <LazyChart
        height={with_volume ? 320 : 260}
        render={(R) => (
          <R.ResponsiveContainer width="100%" height={with_volume ? 320 : 260}>
            <R.ComposedChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <R.CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" opacity={0.4} />
              <R.XAxis
                dataKey="date"
                fontSize={11}
                stroke="var(--chart-axis)"
                tickFormatter={(d: string) => d?.slice(5, 10) || ""}
              />
              <R.YAxis
                yAxisId="price"
                fontSize={11}
                stroke="var(--chart-axis)"
                domain={["auto", "auto"]}
                tickFormatter={(v: number) =>
                  market === "KR"
                    ? new Intl.NumberFormat("ko-KR", { notation: "compact" }).format(v)
                    : new Intl.NumberFormat("en-US", { notation: "compact" }).format(v)
                }
              />
              {with_volume && (
                <R.YAxis
                  yAxisId="volume"
                  orientation="right"
                  hide
                  domain={[0, (max: number) => max * 4]}
                />
              )}
              <R.Tooltip
                content={
                  <ChartTooltip
                    formatter={(key, v) => {
                      if (key === "volume") return new Intl.NumberFormat().format(Number(v));
                      if (key === "ma20" || key === "ma50" || key === "open" || key === "high" || key === "low" || key === "close")
                        return formatPrice(Number(v), market);
                      return String(v);
                    }}
                    labelFormatter={(l) => String(l)}
                  />
                }
              />
              {/* Candle bars: range spans low→high, shape draws wick+body */}
              <R.Bar
                yAxisId="price"
                dataKey="range"
                shape={<CandleShape />}
                isAnimationActive={false}
              />
              {overlays.includes("ma20") && (
                <R.Line
                  yAxisId="price"
                  type="monotone"
                  dataKey="ma20"
                  stroke="var(--chart-accent)"
                  strokeWidth={1.2}
                  dot={false}
                  connectNulls
                />
              )}
              {overlays.includes("ma50") && (
                <R.Line
                  yAxisId="price"
                  type="monotone"
                  dataKey="ma50"
                  stroke="var(--chart-accent-2)"
                  strokeWidth={1.2}
                  dot={false}
                  connectNulls
                />
              )}
              {with_volume && (
                <R.Bar
                  yAxisId="volume"
                  dataKey="volume"
                  fill="var(--chart-neutral)"
                  opacity={0.25}
                />
              )}
            </R.ComposedChart>
          </R.ResponsiveContainer>
        )}
      />
    </div>
  );
}
