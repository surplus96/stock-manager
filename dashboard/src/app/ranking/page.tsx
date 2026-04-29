"use client";

import { useState, useCallback } from "react";
import Card from "@/components/Card";
import Loading from "@/components/Loading";
import SignalBadge from "@/components/SignalBadge";
import AnalysisReport from "@/components/AnalysisReport";
import { AsyncBoundary } from "@/components/ui/AsyncBoundary";
import { SkeletonReport } from "@/components/ui/Skeleton";
import { useAnalysisReport } from "@/features/analysis/hooks/useAnalysisReport";
import { api } from "@/lib/api";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import { Trophy, Lightbulb } from "lucide-react";

const PRESET_GROUPS: Record<string, string[]> = {
  "Mega Cap Tech": ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA"],
  "Semiconductor": ["NVDA", "AMD", "INTC", "AVGO", "QCOM", "TSM", "MU"],
  "Healthcare": ["JNJ", "UNH", "PFE", "ABBV", "MRK", "LLY", "TMO"],
  "Finance": ["JPM", "BAC", "GS", "MS", "WFC", "BLK", "C"],
  // FR-K09: Korean preset baskets mirror the domestic theme map so KR
  // tickers flow through the same multi-factor ranker.
  "KR 반도체": ["005930", "000660", "042700", "058470"],
  "KR 2차전지": ["373220", "247540", "006400", "066970"],
  "KR 바이오": ["207940", "068270", "145020"],
  "KR 방산": ["047810", "012450", "272210"],
};

interface RankingRow {
  ticker?: string;
  symbol?: string;
  composite_score?: number;
  score?: number;
  signal?: string;
  factors?: Record<string, number>;
  factor_count?: number;
  sector?: string;
  // Backend annotates KR rows with the canonical Korean company name +
  // market/currency (see api/routers/stock.py::_run_factor_ranking).
  name_kr?: string;
  market?: string;
}

interface ChartRow {
  ticker: string;
  score: number;
}

export default function RankingPage() {
  const [tickers, setTickers] = useState("AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA");
  const [loading, setLoading] = useState(false);
  const [rankings, setRankings] = useState<RankingRow[]>([]);
  const [error, setError] = useState("");

  const reportFetcher = useCallback(
    () => api.rankingAnalysisReport(tickers),
    [tickers],
  );
  const analysisReport = useAnalysisReport(reportFetcher);

  async function handleRank() {
    if (!tickers.trim()) return;
    setLoading(true);
    setError("");
    analysisReport.reset();

    try {
      const result = await api.rankStocks(tickers);
      const data = Array.isArray(result)
        ? result
        : ((result as Record<string, unknown[]>)?.rankings ?? (result as Record<string, unknown[]>)?.data ?? []);
      setRankings(data as RankingRow[]);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  const chartData: ChartRow[] = rankings.slice(0, 15).map((s) => ({
    ticker: String(s.ticker ?? s.symbol ?? ""),
    score: Number(s.composite_score ?? s.score ?? 0),
  }));

  // Generate summary insight
  const summaryInsight = rankings.length > 0 ? (() => {
    const top = rankings[0];
    const avg = rankings.reduce((sum, r) => sum + Number(r.composite_score ?? 0), 0) / rankings.length;
    const buys = rankings.filter(r => r.signal === "Strong Buy" || r.signal === "Buy");
    const sells = rankings.filter(r => r.signal === "Sell" || r.signal === "Strong Sell");
    let text = `Top pick: ${top.ticker} (${Number(top.composite_score ?? 0).toFixed(1)}/100, ${top.signal}). `;
    text += `Average score: ${avg.toFixed(1)}. `;
    if (buys.length > 0) text += `Buy signals: ${buys.map(b => b.ticker).join(", ")}. `;
    if (sells.length > 0) text += `Caution: ${sells.map(s => s.ticker).join(", ")} rated Sell. `;
    return text;
  })() : "";

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-50">Ranking Engine</h1>

      {/* Input */}
      <Card>
        <div className="space-y-3">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-200">
            Enter tickers to rank (comma-separated)
          </label>
          <div className="flex gap-3">
            <input
              type="text"
              value={tickers}
              onChange={(e) => {
                // Uppercase alphabetic tokens only; leave digit-only KR
                // codes (like "005930") in their canonical 6-digit form.
                const v = e.target.value;
                const normalized = v
                  .split(",")
                  .map((t) => {
                    const tok = t.trim();
                    return /^\d/.test(tok) ? tok : tok.toUpperCase();
                  })
                  .join(", ");
                setTickers(normalized);
              }}
              placeholder="AAPL, MSFT, 005930, 373220, ..."
              className="flex-1 px-4 py-2.5 border rounded-lg text-sm text-slate-900 dark:text-slate-50 bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              style={{ borderColor: "var(--border)" }}
            />
            <button
              onClick={handleRank}
              disabled={loading}
              className="px-6 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              <Trophy className="w-4 h-4 inline mr-1" />
              Rank
            </button>
          </div>

          {/* Presets */}
          <div className="flex gap-2 flex-wrap">
            {Object.entries(PRESET_GROUPS).map(([name, list]) => (
              <button
                key={name}
                onClick={() => setTickers(list.join(", "))}
                className="px-3 py-1.5 text-xs border rounded-full text-slate-600 dark:text-slate-300 hover:border-blue-300 hover:text-blue-600 transition-colors"
                style={{ borderColor: "var(--border)" }}
              >
                {name}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {loading && <Loading text="Ranking stocks with multi-factor analysis..." />}
      {error && <p className="text-red-600 text-sm">{error}</p>}

      {rankings.length > 0 && (
        <div className="space-y-6">
          {/* Ranking Insight */}
          {summaryInsight && (
            <Card>
              <div className="flex items-start gap-3 p-1">
                <Lightbulb className="w-5 h-5 text-amber-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-sm font-semibold text-slate-800 dark:text-slate-100 mb-1">Ranking Insight</p>
                  <p className="text-sm text-slate-700 dark:text-slate-200">{summaryInsight}</p>
                </div>
              </div>
            </Card>
          )}

          {/* Chart */}
          <Card title="Composite Score Ranking">
            <div style={{ width: "100%", height: 320 }}>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={chartData} margin={{ bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="ticker" fontSize={12} />
                  <YAxis domain={[0, 100]} fontSize={11} />
                  <Tooltip />
                  <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                    {chartData.map((entry, i) => {
                      const score = entry.score;
                      const fill = score >= 70 ? "#26A69A" : score >= 50 ? "#2962FF" : score >= 30 ? "#FF6D00" : "#EF5350";
                      return <Cell key={i} fill={fill} />;
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          {/* Table */}
          <Card title="Detailed Rankings">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-slate-600 dark:text-slate-300 border-b" style={{ borderColor: "var(--border)" }}>
                    <th className="pb-2 font-medium">Rank</th>
                    <th className="pb-2 font-medium">Ticker</th>
                    <th className="pb-2 font-medium">Score</th>
                    <th className="pb-2 font-medium">Signal</th>
                    <th className="pb-2 font-medium">Financial</th>
                    <th className="pb-2 font-medium">Technical</th>
                    <th className="pb-2 font-medium">Growth</th>
                    <th className="pb-2 font-medium">Quality</th>
                    <th className="pb-2 font-medium">Factors</th>
                    <th className="pb-2 font-medium">Sector</th>
                  </tr>
                </thead>
                <tbody>
                  {rankings.map((s, i) => (
                    <tr key={i} className="border-b hover:bg-slate-50 dark:bg-slate-800" style={{ borderColor: "var(--border)" }}>
                      <td className="py-2.5">
                        <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold ${
                          i === 0 ? "bg-amber-100 text-amber-700" :
                          i === 1 ? "bg-slate-200 text-slate-700 dark:text-slate-200" :
                          i === 2 ? "bg-orange-100 text-orange-700" :
                          "text-slate-500 dark:text-slate-400"
                        }`}>
                          {i + 1}
                        </span>
                      </td>
                      <td className="py-2.5 font-semibold text-slate-900 dark:text-slate-50">
                        {s.name_kr ? (
                          <span>
                            {s.name_kr}
                            <span className="ml-1.5 text-xs font-mono text-slate-500 dark:text-slate-400">
                              ({s.ticker ?? s.symbol})
                            </span>
                          </span>
                        ) : (
                          (s.ticker ?? s.symbol)
                        )}
                      </td>
                      <td className="py-2.5 font-mono font-medium">{(s.composite_score ?? s.score ?? 0).toFixed(1)}</td>
                      <td className="py-2.5"><SignalBadge signal={s.signal ?? "Hold"} /></td>
                      <td className="py-2.5 text-slate-700 dark:text-slate-200">{(s.factors?.financial_score ?? 0).toFixed(0)}</td>
                      <td className="py-2.5 text-slate-700 dark:text-slate-200">{(s.factors?.technical_score ?? 0).toFixed(0)}</td>
                      <td className="py-2.5 text-slate-700 dark:text-slate-200">{(s.factors?.growth_score ?? 0).toFixed(0)}</td>
                      <td className="py-2.5 text-slate-700 dark:text-slate-200">{(s.factors?.quality_score ?? 0).toFixed(0)}</td>
                      <td className="py-2.5 text-slate-500 dark:text-slate-400 text-xs">{s.factor_count ?? "-"}</td>
                      <td className="py-2.5 text-slate-600 dark:text-slate-300">{s.sector ?? "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Comprehensive Analysis Report — useAnalysisReport (FR-F08) + AsyncBoundary (FR-F10) */}
          <AsyncBoundary
            loading={analysisReport.loading}
            error={analysisReport.error}
            loadingFallback={<SkeletonReport />}
          >
            <AnalysisReport
              title="랭킹 종합 분석 리포트"
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
