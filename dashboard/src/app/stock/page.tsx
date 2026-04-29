"use client";

import { useState, useCallback, useMemo, type ReactNode } from "react";
import Card from "@/components/Card";
import Loading from "@/components/Loading";
import SignalBadge from "@/components/SignalBadge";
import AnalysisReport from "@/components/AnalysisReport";
import MarketSelector, { type MarketChoice } from "@/components/MarketSelector";
import { AsyncBoundary } from "@/components/ui/AsyncBoundary";
import { LazyChart } from "@/components/ui/LazyChart";
import { SkeletonReport } from "@/components/ui/Skeleton";
import { useAnalysisReport } from "@/features/analysis/hooks/useAnalysisReport";
import { api } from "@/lib/api";
import {
  detectMarketFromTicker,
  formatCompact,
  formatPercent,
  formatPrice,
  type Market,
} from "@/lib/locale";
import type {
  StockComprehensive,
  StockSignal,
} from "@/lib/api.types";
import { Search, TrendingUp, TrendingDown, AlertTriangle, ShieldCheck, Brain } from "lucide-react";

interface PricePoint {
  date: string;
  close: number;
  volume: number;
}

interface RadarPoint {
  factor: string;
  value: number;
}

/** Null-safe render helper that avoids unknown-typed JSX short-circuits (React 19 strict). */
function renderMaybe<T>(value: T | null | undefined, render: (v: T) => ReactNode): ReactNode {
  return value != null ? render(value) : null;
}

function InvestSignalPanel({ sig }: { sig: Record<string, unknown> }) {
  const reasons = Array.isArray(sig.reasons) ? (sig.reasons as unknown[]) : [];
  const risks = Array.isArray(sig.risks) ? (sig.risks as unknown[]) : [];
  return (
    <div className="grid grid-cols-2 gap-4">
      <Card title="Investment Rationale">
        <div className="space-y-2">
          <div className="flex items-center gap-2 mb-3">
            <Brain className="w-5 h-5 text-blue-600" />
            <span className="text-sm font-semibold text-slate-800 dark:text-slate-100">
              Decision: <span className={
                String(sig.decision ?? "").includes("Buy") ? "text-emerald-600" :
                String(sig.decision ?? "").includes("Sell") ? "text-red-600" : "text-slate-700 dark:text-slate-200"
              }>{String(sig.decision ?? "Hold")}</span>
            </span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
              {String(sig.confidence ?? "Moderate")} confidence
            </span>
          </div>
          {reasons.map((r, i) => (
            <div key={i} className="flex items-start gap-2 text-sm">
              <TrendingUp className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" />
              <span className="text-slate-700 dark:text-slate-200">{String(r)}</span>
            </div>
          ))}
          {reasons.length === 0 && (
            <p className="text-sm text-slate-500 dark:text-slate-400">Loading analysis...</p>
          )}
        </div>
      </Card>
      <Card title="Risk Assessment">
        <div className="space-y-2">
          {risks.map((r, i) => (
            <div key={i} className="flex items-start gap-2 text-sm">
              <AlertTriangle className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
              <span className="text-slate-700 dark:text-slate-200">{String(r)}</span>
            </div>
          ))}
          {risks.length === 0 && (
            <div className="flex items-center gap-2 text-sm text-emerald-600">
              <ShieldCheck className="w-4 h-4" />
              <span>No significant risks identified</span>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}

function FactorInterpPanel({ interp }: { interp: Record<string, unknown> }) {
  const fi = interp as Record<string, Record<string, unknown> | undefined>;
  return (
    <div className="grid grid-cols-3 gap-4">
      {(["financial", "technical", "sentiment"] as const).map((key) => {
        const section = fi[key];
        const title = key.charAt(0).toUpperCase() + key.slice(1) + " Analysis";
        return (
          <Card key={key} title={title}>
            <div className="space-y-1.5">
              {section?.interpretation != null &&
                typeof section.interpretation === "object" &&
                Object.entries(section.interpretation as Record<string, unknown>).map(([k, val]) => (
                  <div key={k} className="flex justify-between text-xs">
                    <span className="text-slate-600 dark:text-slate-300">{k.replace(/_/g, " ")}</span>
                    <span className="text-slate-800 dark:text-slate-100 font-medium text-right max-w-[60%] truncate">{String(val)}</span>
                  </div>
                ))
              }
              {section?.error != null && (
                <p className="text-xs text-slate-500 dark:text-slate-400">{String(section.error)}</p>
              )}
            </div>
          </Card>
        );
      })}
    </div>
  );
}

function MarketGauge({ condition }: { condition: Record<string, unknown> | null }) {
  if (!condition) return null;
  const state = String(condition.condition ?? condition.state ?? "neutral");
  const ret = Number(condition.spy_60d_return ?? condition.return_60d ?? 0);
  const icon = state === "bull" ? <TrendingUp className="w-8 h-8 text-emerald-500" /> :
               state === "bear" ? <TrendingDown className="w-8 h-8 text-red-500" /> :
               <span className="w-8 h-8 inline-block text-slate-500 dark:text-slate-400">—</span>;
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

export default function StockAnalyzerPage() {
  const [ticker, setTicker] = useState("");
  // FR-K07: explicit market override. "AUTO" delegates to the ticker
  // heuristic (6-digit → KR, alphabetic → US) — the common case.
  const [marketChoice, setMarketChoice] = useState<MarketChoice>("AUTO");
  const [loading, setLoading] = useState(false);
  // Use a discriminated wrapper so `analysis` being non-null is safe for JSX conditionals
  const [analysisData, setAnalysisData] = useState<{ data: StockComprehensive } | null>(null);
  const analysis = analysisData?.data ?? null;
  const [signal, setSignal] = useState<StockSignal | null>(null);
  const [investSignalData, setInvestSignalData] = useState<{ data: Record<string, unknown> } | null>(null);
  const investSignal = investSignalData?.data ?? null;
  const [factorInterpData, setFactorInterpData] = useState<{ data: Record<string, unknown> } | null>(null);
  const factorInterp = factorInterpData?.data ?? null;
  const [priceData, setPriceData] = useState<PricePoint[]>([]);
  const [error, setError] = useState("");

  // FR-K07: Resolved market — either the explicit choice or the ticker heuristic.
  const resolvedMarket: Market = useMemo(() => {
    if (marketChoice === "US" || marketChoice === "KR") return marketChoice;
    return detectMarketFromTicker(ticker);
  }, [marketChoice, ticker]);

  const queryTicker = useMemo(() => {
    const t = ticker.trim();
    // KR digit codes stay untouched; everything else uppercases for yfinance.
    return /^\d{6}(\.KS|\.KQ)?$/i.test(t) ? t : t.toUpperCase();
  }, [ticker]);

  const reportFetcher = useCallback(
    () => api.stockAnalysisReport(queryTicker),
    [queryTicker],
  );
  const analysisReport = useAnalysisReport(reportFetcher);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!ticker.trim()) return;
    setLoading(true);
    setError("");
    setAnalysisData(null);
    setSignal(null);
    setInvestSignalData(null);
    setFactorInterpData(null);
    analysisReport.reset();

    try {
      const [comp, sig, prices] = await Promise.all([
        api.stockComprehensive(queryTicker),
        api.stockSignal(queryTicker),
        api.marketPrices(queryTicker, "6mo"),
      ]);
      setAnalysisData({ data: comp });
      setSignal(sig);
      setPriceData(
        (prices?.data ?? []).map((d) => ({
          date: String(d.date ?? d.Date ?? ""),
          close: Number(d.close ?? d.Close ?? 0),
          volume: Number(d.volume ?? d.Volume ?? 0),
        }))
      );

      // Backend's resolve_korean_ticker may have rewritten the input
      // (e.g. "삼성전자" → "005930"). Sync the canonical code back into
      // the input so subsequent renders, charts and the URL-derived
      // queryTicker memoization all align.
      const respTicker = (comp as Record<string, unknown>)?.ticker;
      if (typeof respTicker === "string" && respTicker && respTicker !== queryTicker) {
        setTicker(respTicker);
      }

      // Load detailed analysis in background (non-blocking) — use the
      // resolved ticker so we don't re-pay the resolver round-trip.
      const followupTicker = typeof respTicker === "string" && respTicker ? respTicker : queryTicker;
      api.stockInvestmentSignal(followupTicker)
        .then((r) => setInvestSignalData({ data: r as Record<string, unknown> }))
        .catch(() => {});
      api.stockFactorInterpretation(followupTicker)
        .then((r) => setFactorInterpData({ data: r as Record<string, unknown> }))
        .catch(() => {});
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  function getRadarData(): RadarPoint[] {
    if (!analysis) return [];
    const f = (analysis as Record<string, Record<string, number>>).factors ?? {};
    return [
      { factor: "Financial", value: f.financial_score ?? 50 },
      { factor: "Technical", value: f.technical_score ?? 50 },
      { factor: "Sentiment", value: f.sentiment_score != null ? (f.sentiment_score + 1) * 50 : 50 },
      { factor: "Growth", value: f.growth_score ?? 50 },
      { factor: "Quality", value: f.quality_score ?? 50 },
      { factor: "Value", value: f.valuation_score ?? 50 },
    ];
  }

  const fundamentals = (analysis as Record<string, Record<string, unknown>> | null)?.fundamentals ?? {};
  const compositeScore = (analysis as Record<string, number> | null)?.composite_score;
  const analysisInterpretation = (analysis as Record<string, unknown> | null)?.interpretation;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-50">Stock Analyzer</h1>

      {/* Search Bar — now market-aware (FR-K07) */}
      <form onSubmit={handleSearch} className="flex gap-3 flex-wrap items-center">
        <MarketSelector value={marketChoice} onChange={setMarketChoice} />
        <div className="relative flex-1 min-w-[220px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 dark:text-slate-400" />
          <input
            type="text"
            value={ticker}
            onChange={(e) => {
              // Preserve 6-digit KR codes verbatim; uppercase only when the
              // user is typing an alphabetic ticker. Mixed case (BRK.A)
              // still gets normalised by the uppercase transform.
              // Hangul (e.g. "삼성전자") is preserved as-is so the backend
              // resolver can do its job without local mangling.
              const v = e.target.value;
              const hasHangul = /[가-힣]/.test(v);
              setTicker(
                hasHangul
                  ? v
                  : /^[0-9.\s]+$/.test(v)
                    ? v.trim()
                    : v.toUpperCase(),
              );
            }}
            placeholder={
              marketChoice === "KR"
                ? "6자리 코드 또는 한글명 (예: 005930, 삼성전자, 247540)"
                : marketChoice === "US"
                  ? "Enter US ticker (e.g. AAPL)"
                  : "Ticker / 한글명 (AAPL · 005930 · 삼성전자)"
            }
            className="w-full pl-10 pr-4 py-2.5 border rounded-lg text-sm text-slate-900 dark:text-slate-50 bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            style={{ borderColor: "var(--border)" }}
          />
        </div>
        {/* Resolution badge — shows after a successful search how the
            backend resolved a Korean name / partial input. */}
        {analysis && (analysis as Record<string, unknown>).name_kr ? (
          <span className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-md bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 self-center">
            ✓ {String((analysis as Record<string, unknown>).name_kr)} (
            {String((analysis as Record<string, unknown>).ticker ?? ticker)})
          </span>
        ) : null}
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          Analyze
        </button>
      </form>

      {loading && <Loading text={`Analyzing ${ticker}...`} />}
      {error && <p className="text-red-600 text-sm">{error}</p>}

      {analysisData != null && (
        <div className="space-y-6">
          {/* Top Row: Signal + Radar */}
          <div className="grid grid-cols-3 gap-4">
            {/* Investment Signal */}
            <Card title="Investment Signal">
              <div className="text-center space-y-3">
                <p className="text-4xl font-bold text-slate-900 dark:text-slate-50">
                  {compositeScore != null ? compositeScore.toFixed(1) : "N/A"}
                </p>
                <p className="text-sm text-slate-600 dark:text-slate-300">Composite Score (0-100)</p>
                <SignalBadge signal={String(signal?.signal ?? (analysis as Record<string, unknown>).signal ?? "Hold")} />
                {signal?.reasoning != null && (
                  <p className="text-xs text-slate-600 dark:text-slate-300 mt-2 text-left">{String(signal.reasoning as string)}</p>
                )}
              </div>
            </Card>

            {/* Radar Chart — LazyChart (FR-F06) */}
            <Card title="Factor Analysis" className="col-span-2">
              <LazyChart
                height={260}
                render={(R) => (
                  <R.ResponsiveContainer width="100%" height={260}>
                    <R.RadarChart data={getRadarData()}>
                      <R.PolarGrid stroke="#e2e8f0" />
                      <R.PolarAngleAxis dataKey="factor" fontSize={12} />
                      <R.PolarRadiusAxis domain={[0, 100]} tick={false} />
                      <R.Radar dataKey="value" stroke="#2962FF" fill="#2962FF" fillOpacity={0.2} strokeWidth={2} />
                    </R.RadarChart>
                  </R.ResponsiveContainer>
                )}
              />
            </Card>
          </div>

          {/* Investment Decision: Reasons & Risks */}
          {renderMaybe(investSignalData, (d) => <InvestSignalPanel sig={d.data} />)}

          {/* Factor Interpretations */}
          {renderMaybe(factorInterpData, (d) => <FactorInterpPanel interp={d.data} />)}

          {/* Key Fundamentals — FR-K07 locale-aware formatting */}
          {(fundamentals as Record<string, unknown>).ticker != null && (() => {
            // Backend tags the response with market/currency; fall back to
            // the ticker heuristic when the field is missing (US-only
            // deployments that haven't redeployed yet).
            const cmarket = (String((analysis as Record<string, unknown>).market ?? "") as Market) || resolvedMarket;
            const f = fundamentals as Record<string, number>;
            return (
              <Card title="Key Fundamentals">
                <div className="grid grid-cols-4 gap-4 text-sm">
                  {[
                    { label: "Market Cap", value: f.market_cap ? (
                        cmarket === "KR"
                          ? formatCompact(f.market_cap, "KR") + "원"
                          : `$${(f.market_cap / 1e9).toFixed(1)}B`
                      ) : "N/A" },
                    { label: "P/E Ratio", value: f.pe?.toFixed(1) || "N/A" },
                    { label: "EPS", value: f.eps != null ? formatPrice(f.eps, cmarket) : "N/A" },
                    { label: "P/B Ratio", value: f.pb?.toFixed(1) || "N/A" },
                    { label: "ROE", value: f.returnOnEquity != null ? formatPercent(f.returnOnEquity, 1) : "N/A" },
                    { label: "Profit Margin", value: f.profitMargins != null ? formatPercent(f.profitMargins, 1) : "N/A" },
                    { label: "Revenue Growth", value: f.revenueGrowth != null ? formatPercent(f.revenueGrowth, 1) : "N/A" },
                    { label: "Sector", value: String((fundamentals as Record<string, unknown>).sector ?? (analysis as Record<string, unknown>).sector ?? "N/A") },
                  ].map(({ label, value }) => (
                    <div key={label} className="p-2 bg-slate-50 dark:bg-slate-800 rounded-lg">
                      <p className="text-xs text-slate-600 dark:text-slate-300">{label}</p>
                      <p className="font-semibold text-slate-900 dark:text-slate-50 tabular">{value}</p>
                    </div>
                  ))}
                </div>
              </Card>
            );
          })()}

          {/* Price Chart — LazyChart (FR-F06) */}
          {priceData.length > 0 && (
            <Card title={(() => {
              const nameKr = (analysis as Record<string, unknown>).name_kr;
              const prefix = nameKr ? `${String(nameKr)} (${ticker})` : ticker;
              return `${prefix} Price (6M)`;
            })()}>
              <LazyChart
                height={290}
                render={(R) => (
                  <R.ResponsiveContainer width="100%" height={290}>
                    <R.AreaChart data={priceData}>
                      <defs>
                        <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#2962FF" stopOpacity={0.2} />
                          <stop offset="100%" stopColor="#2962FF" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <R.CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <R.XAxis
                        dataKey="date"
                        fontSize={11}
                        tickFormatter={(d: string) => d?.slice(5, 10) || ""}
                      />
                      <R.YAxis fontSize={11} domain={["auto", "auto"]} />
                      <R.Tooltip />
                      <R.Area type="monotone" dataKey="close" stroke="#2962FF" fill="url(#priceGrad)" strokeWidth={2} dot={false} />
                    </R.AreaChart>
                  </R.ResponsiveContainer>
                )}
              />
            </Card>
          )}

          {/* Interpretation */}
          {analysisInterpretation != null && (
            <Card title="Analysis Summary">
              <div className="text-sm text-slate-700 dark:text-slate-200 space-y-2 whitespace-pre-wrap">
                {typeof analysisInterpretation === "string"
                  ? analysisInterpretation
                  : JSON.stringify(analysisInterpretation, null, 2)}
              </div>
            </Card>
          )}

          {/* Comprehensive Analysis Report — useAnalysisReport (FR-F08) + AsyncBoundary (FR-F10) */}
          <AsyncBoundary
            loading={analysisReport.loading}
            error={analysisReport.error}
            loadingFallback={<SkeletonReport />}
          >
            <AnalysisReport
              title={`${ticker} 종합 분석 리포트`}
              loading={analysisReport.loading}
              llmSummary={analysisReport.summary}
              blocks={analysisReport.blocks}
              news={analysisReport.news}
              evidence={analysisReport.evidence}
              onGenerate={analysisReport.generate}
              generated={analysisReport.generated}
            />
          </AsyncBoundary>
        </div>
      )}
    </div>
  );
}
