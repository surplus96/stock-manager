"use client";

import type { PriceBarLite, Market } from "@/lib/reportBlocks";
import { formatPrice } from "@/lib/locale";
import { LazyChart } from "@/components/ui/LazyChart";
import { ChartTooltip } from "@/components/charts/ChartTooltip";

interface PriceSparkBlockProps {
  ticker: string;
  market: Market;
  series: PriceBarLite[];
}

export default function PriceSparkBlock({ ticker, market, series }: PriceSparkBlockProps) {
  if (!series || series.length === 0) return null;
  const data = series.map((p) => ({ t: p.t, c: p.c }));
  const first = data[0]?.c ?? 0;
  const last = data[data.length - 1]?.c ?? 0;
  const deltaPct = first > 0 ? (last - first) / first : 0;
  const up = deltaPct >= 0;
  return (
    <div
      className="rounded-xl border bg-white dark:bg-slate-900 p-4"
      style={{ borderColor: "var(--border)" }}
    >
      <div className="flex items-baseline justify-between mb-2">
        <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-50">
          {ticker} Price
        </h4>
        <span
          className={`text-xs tabular ${
            up ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400"
          }`}
        >
          {up ? "+" : ""}
          {(deltaPct * 100).toFixed(2)}%
        </span>
      </div>
      <LazyChart
        height={140}
        render={(R) => (
          <R.ResponsiveContainer width="100%" height={140}>
            <R.AreaChart data={data}>
              <defs>
                <linearGradient id={`sparkgrad-${ticker}`} x1="0" y1="0" x2="0" y2="1">
                  <stop
                    offset="0%"
                    stopColor={up ? "var(--chart-pos)" : "var(--chart-neg)"}
                    stopOpacity={0.25}
                  />
                  <stop
                    offset="100%"
                    stopColor={up ? "var(--chart-pos)" : "var(--chart-neg)"}
                    stopOpacity={0}
                  />
                </linearGradient>
              </defs>
              <R.XAxis dataKey="t" hide />
              <R.YAxis hide domain={["auto", "auto"]} />
              <R.Tooltip
                content={
                  <ChartTooltip
                    formatter={(_, v) => formatPrice(Number(v), market)}
                    labelFormatter={(l) => String(l)}
                  />
                }
              />
              <R.Area
                type="monotone"
                dataKey="c"
                stroke={up ? "var(--chart-pos)" : "var(--chart-neg)"}
                strokeWidth={2}
                fill={`url(#sparkgrad-${ticker})`}
                dot={false}
                isAnimationActive
              />
            </R.AreaChart>
          </R.ResponsiveContainer>
        )}
      />
    </div>
  );
}
