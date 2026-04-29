"use client";

import { useEffect, useState } from "react";
import Card from "@/components/Card";
import Loading from "@/components/Loading";
import { LazyChart } from "@/components/ui/LazyChart";
import { api } from "@/lib/api";
import type { MarketCondition, PriceBar } from "@/lib/api.types";
import { TrendingUp, TrendingDown, Minus, AlertTriangle } from "lucide-react";

const INDEX_TICKERS = [
  { symbol: "^GSPC", name: "S&P 500" },
  { symbol: "^IXIC", name: "NASDAQ" },
  { symbol: "^DJI", name: "DOW" },
  { symbol: "^VIX", name: "VIX" },
  // FR-K04 — KOSPI / KOSDAQ alongside the US headliners.
  { symbol: "^KS11", name: "KOSPI" },
  { symbol: "^KQ11", name: "KOSDAQ" },
];

const SECTOR_TICKERS = [
  { symbol: "XLK", name: "Technology" },
  { symbol: "XLF", name: "Financial" },
  { symbol: "XLV", name: "Healthcare" },
  { symbol: "XLE", name: "Energy" },
  { symbol: "XLY", name: "Consumer Disc." },
  { symbol: "XLP", name: "Consumer Staples" },
  { symbol: "XLI", name: "Industrials" },
  { symbol: "XLU", name: "Utilities" },
  { symbol: "XLRE", name: "Real Estate" },
  { symbol: "XLB", name: "Materials" },
  { symbol: "XLC", name: "Communication" },
];

interface SectorRow {
  name: string;
  symbol: string;
  returnPct: number;
}

interface IndexPriceData {
  data?: PriceBar[];
}

function MarketGauge({ condition }: { condition: MarketCondition | null }) {
  if (!condition) return null;
  const state = condition.condition ?? "neutral";
  const ret = condition.spy_60d_return ?? 0;
  const icon = state === "bull" ? <TrendingUp className="w-8 h-8 text-emerald-500" /> :
               state === "bear" ? <TrendingDown className="w-8 h-8 text-red-500" /> :
               <Minus className="w-8 h-8 text-slate-500 dark:text-slate-400" />;
  const color = state === "bull" ? "text-emerald-600" : state === "bear" ? "text-red-600" : "text-slate-700 dark:text-slate-200";
  const bg = state === "bull" ? "bg-emerald-50 border-emerald-200" :
             state === "bear" ? "bg-red-50 border-red-200" : "bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700";

  return (
    <div className={`flex items-center gap-4 p-5 rounded-xl border ${bg}`}>
      {icon}
      <div>
        <p className={`text-2xl font-bold capitalize ${color}`}>{state}</p>
        <p className="text-sm text-slate-600 dark:text-slate-300">
          SPY 60D Return: <span className={ret >= 0 ? "text-emerald-600" : "text-red-600"}>
            {(ret * 100).toFixed(1)}%
          </span>
        </p>
      </div>
    </div>
  );
}

function IndexCard({ name, data }: { name: string; data: IndexPriceData | null }) {
  if (!data?.data || data.data.length === 0) {
    return (
      <div className="rounded-xl border bg-white dark:bg-slate-900 p-4" style={{ borderColor: "var(--border)" }}>
        <p className="text-sm font-medium text-slate-600 dark:text-slate-300">{name}</p>
        <p className="text-xs text-slate-500 dark:text-slate-400">No data</p>
      </div>
    );
  }
  const prices = data.data;
  const latest = prices[prices.length - 1];
  const prev = prices.length > 1 ? prices[prices.length - 2] : latest;
  const price = Number(latest.close ?? latest.Close ?? 0);
  const prevPrice = Number(prev.close ?? prev.Close ?? price);
  const change = price - prevPrice;
  const changePct = prevPrice ? (change / prevPrice) * 100 : 0;
  const isUp = change >= 0;
  const chartData = prices.slice(-30).map((d, i) => ({
    i,
    v: Number(d.close ?? d.Close ?? 0),
  }));

  return (
    <div className="rounded-xl border bg-white dark:bg-slate-900 p-4" style={{ borderColor: "var(--border)" }}>
      <p className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-1">{name}</p>
      <p className="text-xl font-bold text-slate-900 dark:text-slate-50">
        {name === "VIX" ? price.toFixed(2) : price.toLocaleString(undefined, { maximumFractionDigits: 0 })}
      </p>
      <p className={`text-sm font-medium ${isUp ? "text-emerald-600" : "text-red-600"}`}>
        {isUp ? "+" : ""}{change.toFixed(2)} ({isUp ? "+" : ""}{changePct.toFixed(2)}%)
      </p>
      {/* Mini spark chart — lightweight, stays as static import (bundle impact acceptable) */}
      <div style={{ width: "100%", height: 48 }} className="mt-2">
        <LazyChart
          height={48}
          render={(R) => (
            <R.ResponsiveContainer width="100%" height={48}>
              <R.AreaChart data={chartData}>
                <defs>
                  <linearGradient id={`grad-${name}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={isUp ? "#26A69A" : "#EF5350"} stopOpacity={0.3} />
                    <stop offset="100%" stopColor={isUp ? "#26A69A" : "#EF5350"} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <R.Area type="monotone" dataKey="v" stroke={isUp ? "#26A69A" : "#EF5350"} fill={`url(#grad-${name})`} strokeWidth={1.5} dot={false} />
              </R.AreaChart>
            </R.ResponsiveContainer>
          )}
        />
      </div>
    </div>
  );
}

export default function MarketOverviewPage() {
  const [condition, setCondition] = useState<MarketCondition | null>(null);
  const [indexData, setIndexData] = useState<Record<string, IndexPriceData | null>>({});
  const [sectorData, setSectorData] = useState<SectorRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    // Bounded-parallel map: runs at most `limit` tasks concurrently to avoid
    // overwhelming the backend (slowapi) and yfinance upstream.
    async function mapLimit<T, R>(items: T[], limit: number, fn: (item: T) => Promise<R>): Promise<R[]> {
      const results: R[] = new Array(items.length);
      let cursor = 0;
      async function worker() {
        while (cursor < items.length) {
          const idx = cursor++;
          results[idx] = await fn(items[idx]);
        }
      }
      await Promise.all(Array.from({ length: Math.min(limit, items.length) }, worker));
      return results;
    }

    // Retry with backoff — recovers from transient "Failed to fetch" (network
    // blips, rate-limit 429) without surfacing an error to the user.
    async function withRetry<T>(fn: () => Promise<T>, retries = 2, baseMs = 400): Promise<T> {
      let lastErr: unknown;
      for (let i = 0; i <= retries; i++) {
        try {
          return await fn();
        } catch (e) {
          lastErr = e;
          if (i === retries) break;
          await new Promise((r) => setTimeout(r, baseMs * 2 ** i));
        }
      }
      throw lastErr;
    }

    async function load() {
      try {
        const cond = await withRetry(() => api.marketCondition());
        if (cancelled) return;
        setCondition(cond);

        const indexPairs = await mapLimit(INDEX_TICKERS, 4, async ({ symbol, name }) => {
          try {
            const d = (await withRetry(() => api.marketPrices(symbol, "3mo"))) as IndexPriceData;
            return [name, d] as const;
          } catch {
            return [name, null] as const;
          }
        });
        if (cancelled) return;
        setIndexData(Object.fromEntries(indexPairs));

        const sectorResults = (
          await mapLimit(SECTOR_TICKERS, 4, async ({ symbol, name }) => {
            try {
              const d = (await withRetry(() => api.marketPrices(symbol, "1mo"))) as IndexPriceData;
              const prices = d?.data ?? [];
              if (prices.length >= 2) {
                const first = Number(prices[0].close ?? prices[0].Close ?? 0);
                const last = Number(prices[prices.length - 1].close ?? prices[prices.length - 1].Close ?? 0);
                const returnPct = first > 0 ? ((last - first) / first) * 100 : 0;
                return { name, symbol, returnPct } as SectorRow;
              }
            } catch {}
            return null;
          })
        ).filter((r): r is SectorRow => r !== null);
        if (cancelled) return;
        sectorResults.sort((a, b) => b.returnPct - a.returnPct);
        setSectorData(sectorResults);
      } catch (e: unknown) {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : "Unknown error");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) return <Loading text="Loading market data..." />;
  if (error) return (
    <div className="flex items-center gap-2 p-4 bg-red-50 text-red-700 rounded-lg">
      <AlertTriangle className="w-5 h-5" />
      <span>{error}</span>
    </div>
  );

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-50">Market Overview</h1>

      <MarketGauge condition={condition} />

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {INDEX_TICKERS.map(({ name }) => (
          <IndexCard key={name} name={name} data={indexData[name] ?? null} />
        ))}
      </div>

      {/* Sector Performance — LazyChart (FR-F06) */}
      <Card title="Sector Performance (1M)">
        <LazyChart
          height={320}
          render={(R) => (
            <R.ResponsiveContainer width="100%" height={320}>
              <R.BarChart data={sectorData} layout="vertical" margin={{ left: 100 }}>
                <R.CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <R.XAxis type="number" tickFormatter={(v: number) => `${v.toFixed(1)}%`} fontSize={12} />
                <R.YAxis type="category" dataKey="name" fontSize={12} width={90} />
                <R.Tooltip formatter={(v: unknown) => `${Number(v ?? 0).toFixed(2)}%`} />
                <R.Bar dataKey="returnPct" radius={[0, 4, 4, 0]}>
                  {sectorData.map((entry, i) => (
                    <R.Cell key={i} fill={entry.returnPct >= 0 ? "#26A69A" : "#EF5350"} />
                  ))}
                </R.Bar>
              </R.BarChart>
            </R.ResponsiveContainer>
          )}
        />
      </Card>
    </div>
  );
}
