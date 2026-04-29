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
import type { PortfolioComprehensive } from "@/lib/api.types";
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from "recharts";
import { AlertTriangle, TrendingUp, ShieldCheck } from "lucide-react";

const COLORS = ["#2962FF", "#26A69A", "#FF6D00", "#EF5350", "#8b5cf6", "#06b6d4", "#f59e0b", "#ec4899"];
const PHASE_COLORS: Record<string, string> = {
  "Uptrend": "bg-emerald-500",
  "Stable": "bg-blue-500",
  "Unstable": "bg-orange-500",
  "Critical": "bg-red-500",
};
const PHASE_TEXT: Record<string, string> = {
  "Uptrend": "text-emerald-600",
  "Stable": "text-blue-600",
  "Unstable": "text-orange-600",
  "Critical": "text-red-600",
};

interface HoldingRow {
  ticker?: string;
  shares?: number;
  entry_price?: number;
  current_price?: number;
  pnl?: number;
  pnl_pct?: number;
  composite_score?: number;
  signal?: string;
  // Korean-name enrichment from /api/portfolio/comprehensive (FR-K06).
  name_kr?: string;
  market?: string;
}

interface AllocationRow {
  name?: string;
  ticker?: string;
  value?: number;
  weight?: number;
  pct?: number;
}

export default function PortfolioPage() {
  const [holdings, setHoldings] = useState("AAPL:10@150, MSFT:5@400, NVDA:8@120");
  const [cash, setCash] = useState(5000);
  const [loading, setLoading] = useState(false);
  const [portfolio, setPortfolio] = useState<PortfolioComprehensive | null>(null);
  const [error, setError] = useState("");

  const reportFetcher = useCallback(
    () => api.portfolioAnalysisReport(holdings, cash),
    [holdings, cash],
  );
  const analysisReport = useAnalysisReport(reportFetcher);

  async function handleAnalyze() {
    if (!holdings.trim()) return;
    setLoading(true);
    setError("");
    analysisReport.reset();

    try {
      const result = await api.portfolioComprehensive(holdings, cash);
      setPortfolio(result);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  const p = portfolio as Record<string, unknown> | null;

  const allocationData: AllocationRow[] = (
    (p?.sectors as Record<string, AllocationRow[]> | undefined)?.allocations ??
    ((p?.allocation as AllocationRow[] | undefined)?.map((a) => ({
      name: a.ticker ?? a.name,
      value: a.weight ?? a.pct ?? a.value ?? 0,
    })) ?? [])
  );

  const pnlData: HoldingRow[] = (
    (p?.pnl as Record<string, HoldingRow[]> | undefined)?.holdings ??
    (p?.holdings as HoldingRow[] | undefined) ??
    []
  );

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-50">Portfolio Dashboard</h1>

      {/* Input */}
      <Card>
        <div className="space-y-3">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-200">
            Holdings (format: TICKER:shares@entry_price) — US 티커 또는 KR 6자리 코드 혼합 가능
          </label>
          <input
            type="text"
            value={holdings}
            onChange={(e) => setHoldings(e.target.value)}
            placeholder="AAPL:10@150, 005930:20@70000, MSFT:5@400"
            className="w-full px-4 py-2.5 border rounded-lg text-sm text-slate-900 dark:text-slate-50 bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            style={{ borderColor: "var(--border)" }}
          />
          <p className="text-xs text-slate-500 dark:text-slate-400">
            ⓘ 기준 통화는 USD 고정입니다 (설정에 따라). KR 종목의 entry_price 는 USD 환산 값으로 입력하세요.
          </p>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="text-sm text-slate-600 dark:text-slate-300">Cash ($)</label>
              <input
                type="number"
                value={cash}
                onChange={(e) => setCash(Number(e.target.value))}
                className="w-28 px-3 py-2 border rounded-lg text-sm"
                style={{ borderColor: "var(--border)" }}
              />
            </div>
            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="px-6 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              Analyze Portfolio
            </button>
          </div>
        </div>
      </Card>

      {loading && <Loading text="Analyzing portfolio..." />}
      {error && <p className="text-red-600 text-sm">{error}</p>}

      {portfolio && p && (
        <div className="space-y-6">
          {/* Health + Summary */}
          <div className="grid grid-cols-4 gap-4">
            {[
              { label: "Total Value", value: `$${Number(p.total_value ?? 0).toLocaleString()}` },
              { label: "Total P&L", value: `$${Number(p.total_pnl ?? 0).toLocaleString()}`, color: Number(p.total_pnl ?? 0) >= 0 ? "text-emerald-600" : "text-red-600" },
              { label: "Health Score", value: (p.health_score as number | undefined)?.toFixed(0) ?? "N/A" },
              { label: "Phase", value: String(p.phase ?? "N/A"), color: PHASE_TEXT[String(p.phase)] ?? "text-slate-900 dark:text-slate-50" },
            ].map(({ label, value, color }) => (
              <div key={label} className="bg-white dark:bg-slate-900 rounded-xl border p-4" style={{ borderColor: "var(--border)" }}>
                <p className="text-sm text-slate-600 dark:text-slate-300">{label}</p>
                <p className={`text-xl font-bold ${color ?? "text-slate-900 dark:text-slate-50"}`}>{value}</p>
              </div>
            ))}
          </div>

          {/* Holdings Detail Table */}
          <Card title="Holdings Analysis">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-slate-600 dark:text-slate-300 border-b" style={{ borderColor: "var(--border)" }}>
                    <th className="pb-2 font-medium">Ticker</th>
                    <th className="pb-2 font-medium">Shares</th>
                    <th className="pb-2 font-medium">Entry</th>
                    <th className="pb-2 font-medium">Current</th>
                    <th className="pb-2 font-medium">P&L</th>
                    <th className="pb-2 font-medium">P&L %</th>
                    <th className="pb-2 font-medium">Score</th>
                    <th className="pb-2 font-medium">Signal</th>
                  </tr>
                </thead>
                <tbody>
                  {pnlData.map((h, i) => (
                    <tr key={i} className="border-b hover:bg-slate-50 dark:bg-slate-800" style={{ borderColor: "var(--border)" }}>
                      <td className="py-2.5 font-semibold text-slate-900 dark:text-slate-50">
                        {h.name_kr ? (
                          <span>
                            {h.name_kr}
                            <span className="ml-1.5 text-xs font-mono text-slate-500 dark:text-slate-400">
                              ({h.ticker})
                            </span>
                          </span>
                        ) : (
                          h.ticker
                        )}
                      </td>
                      <td className="py-2.5 text-slate-700 dark:text-slate-200">{h.shares}</td>
                      <td className="py-2.5 text-slate-700 dark:text-slate-200">${h.entry_price}</td>
                      <td className="py-2.5 text-slate-700 dark:text-slate-200">${h.current_price}</td>
                      <td className={`py-2.5 font-medium ${(h.pnl ?? 0) >= 0 ? "text-emerald-600" : "text-red-600"}`}>
                        ${(h.pnl ?? 0).toLocaleString()}
                      </td>
                      <td className={`py-2.5 font-medium ${(h.pnl_pct ?? 0) >= 0 ? "text-emerald-600" : "text-red-600"}`}>
                        {(h.pnl_pct ?? 0).toFixed(1)}%
                      </td>
                      <td className="py-2.5 font-mono">{(h.composite_score ?? 0).toFixed(0)}</td>
                      <td className="py-2.5"><SignalBadge signal={h.signal ?? "Hold"} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <div className="grid grid-cols-2 gap-6">
            {/* Allocation Pie */}
            <Card title="Portfolio Allocation">
              <div style={{ width: "100%", height: 290 }}>
                <ResponsiveContainer width="100%" height={290}>
                  <PieChart>
                    <Pie
                      data={allocationData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      dataKey="value"
                      nameKey="name"
                      label={({ name, value }: { name?: string; value?: number }) => `${name ?? ""} ${Number(value ?? 0).toFixed(1)}%`}
                      labelLine={false}
                      fontSize={11}
                    >
                      {allocationData.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(v) => `${Number(v).toFixed(2)}%`} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </Card>

            {/* P&L by Holding */}
            <Card title="P&L by Holding">
              <div style={{ width: "100%", height: 290 }}>
                <ResponsiveContainer width="100%" height={290}>
                  <BarChart data={pnlData} layout="vertical" margin={{ left: 60 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis type="number" fontSize={11} tickFormatter={(v) => `$${v}`} />
                    <YAxis type="category" dataKey="ticker" fontSize={12} width={50} />
                    <Tooltip formatter={(v) => `$${Number(v).toLocaleString()}`} />
                    <Bar dataKey="pnl" radius={[0, 4, 4, 0]}>
                      {pnlData.map((entry, i) => (
                        <Cell key={i} fill={(entry.pnl ?? 0) >= 0 ? "#26A69A" : "#EF5350"} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>

          {/* Alerts & Insights */}
          {(() => {
            const alerts = Array.isArray(p.alerts) ? (p.alerts as Record<string, unknown>[]) : [];
            const insights = Array.isArray(p.insights) ? (p.insights as string[]) : [];
            return (
          <div className="grid grid-cols-2 gap-4">
            {/* Alerts */}
            {alerts.length > 0 && (
              <Card title="Risk Alerts">
                <div className="space-y-2">
                  {alerts.map((alert, i) => (
                    <div key={i} className="flex items-start gap-2 text-sm p-2.5 bg-amber-50 rounded-lg border border-amber-200">
                      <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
                      <div>
                        <span className="font-medium text-amber-700">{String(alert.ticker ?? "!")}</span>
                        <span className="text-slate-700 dark:text-slate-200 ml-1">{String(alert.message ?? JSON.stringify(alert))}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Positive Insights */}
            {insights.length > 0 && (
              <Card title="Positive Signals">
                <div className="space-y-2">
                  {insights.map((insight, i) => (
                    <div key={i} className="flex items-start gap-2 text-sm p-2.5 bg-emerald-50 rounded-lg border border-emerald-200">
                      <TrendingUp className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                      <span className="text-slate-700 dark:text-slate-200">{insight}</span>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* No alerts case */}
            {alerts.length === 0 && insights.length === 0 && (
              <Card title="Portfolio Status">
                <div className="flex items-center gap-2 text-sm text-emerald-600 p-3">
                  <ShieldCheck className="w-5 h-5" />
                  <span>Portfolio is healthy. No alerts or concerns.</span>
                </div>
              </Card>
            )}
          </div>
            );
          })()}

          {/* Comprehensive Analysis Report — useAnalysisReport (FR-F08) + AsyncBoundary (FR-F10) */}
          <AsyncBoundary
            loading={analysisReport.loading}
            error={analysisReport.error}
            loadingFallback={<SkeletonReport />}
          >
            <AnalysisReport
              title="포트폴리오 종합 분석 리포트"
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

// suppress unused import — PHASE_COLORS kept for future phase badge use
void PHASE_COLORS;
