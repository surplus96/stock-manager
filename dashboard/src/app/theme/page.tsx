"use client";

import { useEffect, useState, useCallback } from "react";
import Card from "@/components/Card";
import Loading from "@/components/Loading";
import SignalBadge from "@/components/SignalBadge";
import AnalysisReport from "@/components/AnalysisReport";
import { AsyncBoundary } from "@/components/ui/AsyncBoundary";
import { SkeletonReport } from "@/components/ui/Skeleton";
import { useAnalysisReport } from "@/features/analysis/hooks/useAnalysisReport";
import { api } from "@/lib/api";
import type { ThemeAnalyzeResult } from "@/lib/api.types";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import { Compass, Sparkles, Lightbulb } from "lucide-react";

interface ThemeStock {
  ticker?: string;
  symbol?: string;
  composite_score?: number;
  score?: number;
  signal?: string;
  recommendation?: string;
  factors?: Record<string, number>;
  sector?: string;
  name_kr?: string;
  market?: string;
}

interface ChartRow {
  ticker: string;
  score: number;
  signal: string;
}

type ThemeMarket = "US" | "KR";

export default function ThemeExplorerPage() {
  // FR-K14: US / KR 탭. KR 탭은 하드-큐레이트된 테마 맵을 사용하고 backend
  // 의 `/api/theme/kr/*` 로 routing 된다.
  const [market, setMarket] = useState<ThemeMarket>("US");
  const [themes, setThemes] = useState<string[]>([]);
  const [krThemes, setKrThemes] = useState<string[]>([]);
  const [selectedTheme, setSelectedTheme] = useState("");
  const [customTheme, setCustomTheme] = useState("");
  const [themeResult, setThemeResult] = useState<ThemeAnalyzeResult | null>(null);
  const [loadingThemes, setLoadingThemes] = useState(true);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [error, setError] = useState("");

  const reportFetcher = useCallback(
    () => api.themeAnalysisReport(selectedTheme, 5),
    [selectedTheme],
  );
  const analysisReport = useAnalysisReport(reportFetcher);

  useEffect(() => {
    async function loadThemes() {
      try {
        const [usResult, krResult] = await Promise.all([
          api.themePropose(7),
          api.themeKrPropose().catch(() => ({ themes: [] as string[] })),
        ]);
        const usList = Array.isArray(usResult)
          ? usResult
          : (usResult as Record<string, unknown[]>)?.themes ??
              (usResult as Record<string, unknown[]>)?.data ??
              [];
        setThemes(
          (usList as (string | Record<string, string>)[]).map((t) =>
            typeof t === "string" ? t : String(t.theme ?? t.name ?? ""),
          ),
        );
        setKrThemes(Array.isArray(krResult?.themes) ? krResult.themes : []);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Unknown error");
      } finally {
        setLoadingThemes(false);
      }
    }
    loadThemes();
  }, []);

  async function handleExplore(theme: string, overrideMarket?: ThemeMarket) {
    if (!theme.trim()) return;
    const m = overrideMarket ?? market;
    setSelectedTheme(theme);
    setLoadingAnalysis(true);
    setError("");
    analysisReport.reset();

    try {
      const result = m === "KR"
        ? await api.themeKrAnalyze(theme, 5)
        : await api.themeAnalyze(theme, 5);
      setThemeResult(result);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoadingAnalysis(false);
    }
  }

  const visibleThemes = market === "KR" ? krThemes : themes;

  const tr = themeResult as Record<string, unknown> | null;
  const rankings: ThemeStock[] = (tr?.rankings ?? tr?.stocks ?? []) as ThemeStock[];
  const chartData: ChartRow[] = rankings.map((s) => ({
    ticker: String(s.ticker ?? s.symbol ?? ""),
    score: Number(s.composite_score ?? s.score ?? 0),
    signal: String(s.signal ?? s.recommendation ?? "Hold"),
  }));

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-50">Theme Explorer</h1>

      {/* Market tab — FR-K14 */}
      <div
        role="tablist"
        aria-label="Theme market"
        className="inline-flex rounded-lg border overflow-hidden text-sm"
        style={{ borderColor: "var(--border)" }}
      >
        {(["US", "KR"] as ThemeMarket[]).map((m) => (
          <button
            key={m}
            role="tab"
            aria-selected={market === m}
            onClick={() => {
              setMarket(m);
              setSelectedTheme("");
              setThemeResult(null);
            }}
            className={`px-4 py-1.5 transition-colors ${
              market === m
                ? "bg-blue-600 text-white"
                : "bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
            }`}
          >
            {m === "US" ? "US 테마" : "한국 테마"}
          </button>
        ))}
      </div>

      {/* Trending Themes */}
      <Card title={market === "KR" ? "한국 투자 테마" : "Trending Investment Themes"} action={
        <span className="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
          <Sparkles className="w-3 h-3" /> {market === "KR" ? "Hand-curated" : "AI-Suggested"}
        </span>
      }>
        {loadingThemes ? <Loading text="Discovering themes..." /> : (
          <div className="flex flex-wrap gap-2">
            {visibleThemes.length === 0 && (
              <p className="text-sm text-slate-500 dark:text-slate-400">테마 목록을 불러오지 못했습니다.</p>
            )}
            {visibleThemes.map((theme) => (
              <button
                key={theme}
                onClick={() => handleExplore(theme)}
                className={`px-4 py-2 rounded-full text-sm font-medium border transition-colors ${
                  selectedTheme === theme
                    ? "bg-blue-600 text-white border-blue-600"
                    : "bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 border-slate-200 dark:border-slate-700 hover:border-blue-300 hover:text-blue-600"
                }`}
              >
                {theme}
              </button>
            ))}
          </div>
        )}

        {/* Custom theme */}
        <div className="flex gap-2 mt-4">
          <input
            type="text"
            value={customTheme}
            onChange={(e) => setCustomTheme(e.target.value)}
            placeholder={market === "KR" ? "직접 입력 (예: 원전, 조선)..." : "Or enter custom theme..."}
            className="flex-1 max-w-sm px-4 py-2 border rounded-lg text-sm text-slate-900 dark:text-slate-50 bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            style={{ borderColor: "var(--border)" }}
            onKeyDown={(e) => e.key === "Enter" && handleExplore(customTheme)}
          />
          <button
            onClick={() => handleExplore(customTheme)}
            disabled={!customTheme.trim() || loadingAnalysis}
            className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <Compass className="w-4 h-4" />
          </button>
        </div>
      </Card>

      {loadingAnalysis && <Loading text={`Analyzing "${selectedTheme}"...`} />}
      {error && <p className="text-red-600 text-sm">{error}</p>}

      {themeResult && tr && (
        <div className="space-y-6">
          {/* Theme Recommendation */}
          {tr.recommendation != null && (
            <Card>
              <div className="flex items-start gap-3 p-1">
                <Lightbulb className="w-5 h-5 text-amber-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-sm font-semibold text-slate-800 dark:text-slate-100 mb-1">Theme Insight</p>
                  <p className="text-sm text-slate-700 dark:text-slate-200">{String(tr.recommendation)}</p>
                </div>
              </div>
            </Card>
          )}

          {/* Score Chart */}
          <Card title={`Theme: ${selectedTheme} — Top Stocks`}>
            <div style={{ width: "100%", height: 290 }}>
              <ResponsiveContainer width="100%" height={290}>
                <BarChart data={chartData} margin={{ bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="ticker" fontSize={12} />
                  <YAxis domain={[0, 100]} fontSize={11} />
                  <Tooltip />
                  <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                    {chartData.map((_, i) => (
                      <Cell key={i} fill={i === 0 ? "#2962FF" : i < 3 ? "#26A69A" : "#78909C"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          {/* Rankings Table */}
          <Card title="Stock Rankings">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-slate-600 dark:text-slate-300 border-b" style={{ borderColor: "var(--border)" }}>
                    <th className="pb-2 font-medium">#</th>
                    <th className="pb-2 font-medium">Ticker</th>
                    <th className="pb-2 font-medium">Score</th>
                    <th className="pb-2 font-medium">Signal</th>
                    <th className="pb-2 font-medium">Financial</th>
                    <th className="pb-2 font-medium">Technical</th>
                    <th className="pb-2 font-medium">Quality</th>
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
                      <td className="py-2.5"><SignalBadge signal={s.signal ?? s.recommendation ?? "Hold"} /></td>
                      <td className="py-2.5 text-slate-700 dark:text-slate-200">{(s.factors?.financial_score ?? 0).toFixed(0)}</td>
                      <td className="py-2.5 text-slate-700 dark:text-slate-200">{(s.factors?.technical_score ?? 0).toFixed(0)}</td>
                      <td className="py-2.5 text-slate-700 dark:text-slate-200">{(s.factors?.quality_score ?? 0).toFixed(0)}</td>
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
              title={`"${selectedTheme}" 테마 종합 분석 리포트`}
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
