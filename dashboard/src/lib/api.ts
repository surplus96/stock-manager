/**
 * Typed Stock Manager API client (FR-F01).
 *
 * Phase 1: 모든 `Promise<any>` 제거. 응답 스키마는 `./api.types` 에서 관리한다.
 * 에러는 `ApiError` 로 throw 하므로 호출부는 `catch` 로 code/message 접근 가능.
 */

import type {
  AnalysisReportPayload,
  ApiErrorBody,
  ApiErrorEnvelope,
  ChatResponseData,
  CircuitStatus,
  FactorInterpretation,
  HealthResponse,
  MarketCondition,
  NewsSearchResult,
  NewsSentiment,
  NewsTimeline,
  PortfolioComprehensive,
  PortfolioCorrelation,
  PortfolioPnL,
  PortfolioSectors,
  MarketPricesResponse,
  RankingResult,
  StockCompareResult,
  StockComprehensive,
  StockSignal,
  TechnicalAnalysis,
  ThemeAnalyzeResult,
  ThemeExploreResult,
  ThemeProposeResult,
  ThemeTickersResult,
} from "./api.types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type QueryValue = string | number | boolean;

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly requestId?: string;
  readonly details?: Record<string, unknown>;

  constructor(message: string, opts: { code: string; status: number; requestId?: string; details?: Record<string, unknown> }) {
    super(message);
    this.name = "ApiError";
    this.code = opts.code;
    this.status = opts.status;
    this.requestId = opts.requestId;
    this.details = opts.details;
  }
}

function isApiErrorEnvelope(value: unknown): value is ApiErrorEnvelope {
  if (typeof value !== "object" || value === null) return false;
  const err = (value as { error?: unknown }).error;
  return typeof err === "object" && err !== null && typeof (err as ApiErrorBody).code === "string";
}

async function toApiError(res: Response): Promise<ApiError> {
  let body: unknown = null;
  try {
    body = await res.json();
  } catch {
    // non-JSON body; fall through
  }
  if (isApiErrorEnvelope(body)) {
    const e = body.error;
    return new ApiError(e.message, {
      code: e.code,
      status: res.status,
      requestId: e.request_id,
      details: e.details,
    });
  }
  return new ApiError(`API Error: ${res.status} ${res.statusText}`, {
    code: "HTTP_ERROR",
    status: res.status,
  });
}

/**
 * Detect backend Envelope shape `{data, generated_at, version}` and unwrap
 * to the inner `data` so callers consume the raw payload regardless of
 * whether the endpoint went through the FR-B08 router split.
 */
function isEnvelope(value: unknown): value is { data: unknown; generated_at: string; version: string } {
  if (typeof value !== "object" || value === null) return false;
  const v = value as Record<string, unknown>;
  return "data" in v && typeof v.generated_at === "string" && typeof v.version === "string";
}

async function fetchAPI<T>(
  path: string,
  params?: Record<string, QueryValue | undefined | null>,
  timeoutMs = 60_000,
): Promise<T> {
  const url = new URL(`${API_BASE}${path}`);
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== "") {
        url.searchParams.set(k, String(v));
      }
    }
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url.toString(), { signal: controller.signal });
    if (!res.ok) throw await toApiError(res);
    const body = (await res.json()) as unknown;
    if (isEnvelope(body)) return body.data as T;
    return body as T;
  } finally {
    clearTimeout(timer);
  }
}

/**
 * POST helper — JSON body in, Envelope-aware response out.
 * FR-P11: retries transient 503/504/429 / network errors once so the
 * user doesn't see a hiccup from Google AI Studio. Non-transient 4xx
 * errors bubble immediately.
 */
interface FetchPOSTOptions {
  timeoutMs?: number;
  retries?: number;
  retryDelayMs?: number;
}

function isRetriableStatus(status: number): boolean {
  return status === 429 || status === 502 || status === 503 || status === 504;
}

async function fetchPOST<T>(
  path: string,
  body: unknown,
  options: FetchPOSTOptions = {},
): Promise<T> {
  const { timeoutMs = 120_000, retries = 0, retryDelayMs = 800 } = options;
  const url = `${API_BASE}${path}`;

  let lastErr: unknown = null;
  for (let attempt = 0; attempt <= retries; attempt++) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body ?? {}),
        signal: controller.signal,
      });
      if (!res.ok) {
        if (attempt < retries && isRetriableStatus(res.status)) {
          lastErr = await toApiError(res);
          await new Promise((r) => setTimeout(r, retryDelayMs * (attempt + 1)));
          continue;
        }
        throw await toApiError(res);
      }
      const parsed = (await res.json()) as unknown;
      if (isEnvelope(parsed)) return parsed.data as T;
      return parsed as T;
    } catch (e) {
      lastErr = e;
      // Network-level errors (TypeError on abort/dns) are retriable too
      const retriable =
        attempt < retries &&
        (e instanceof TypeError || (e instanceof ApiError && isRetriableStatus(e.status)));
      if (!retriable) throw e;
      await new Promise((r) => setTimeout(r, retryDelayMs * (attempt + 1)));
    } finally {
      clearTimeout(timer);
    }
  }
  // Exhausted retries — throw the last captured error
  throw lastErr;
}

export const api = {
  // Market
  marketCondition: () => fetchAPI<MarketCondition>("/api/market/condition"),
  marketPrices: (ticker: string, period = "6mo", interval = "1d") =>
    fetchAPI<MarketPricesResponse>("/api/market/prices", { ticker, period, interval }),

  // Stock
  stockComprehensive: (ticker: string) =>
    fetchAPI<StockComprehensive>("/api/stock/comprehensive", { ticker }),
  stockSignal: (ticker: string) =>
    fetchAPI<StockSignal>("/api/stock/signal", { ticker }),
  stockCompare: (tickers: string) =>
    fetchAPI<StockCompareResult>("/api/stock/compare", { tickers }),
  stockInvestmentSignal: (ticker: string) =>
    fetchAPI<StockSignal>("/api/stock/investment-signal", { ticker }),
  stockFactorInterpretation: (ticker: string) =>
    fetchAPI<FactorInterpretation>("/api/stock/factor-interpretation", { ticker }),

  // Technical
  technicalAnalyze: (ticker: string) =>
    fetchAPI<TechnicalAnalysis>("/api/technical/analyze", { ticker }),

  // News
  newsSearch: (queries: string, lookbackDays = 7, maxResults = 10) =>
    fetchAPI<NewsSearchResult>("/api/news/search", {
      queries,
      lookback_days: lookbackDays,
      max_results: maxResults,
    }),
  newsSentiment: (tickers: string, lookbackDays = 7) =>
    fetchAPI<NewsSentiment>("/api/news/sentiment", { tickers, lookback_days: lookbackDays }),
  newsTimeline: (ticker: string, lookbackDays = 14) =>
    fetchAPI<NewsTimeline>("/api/news/timeline", { ticker, lookback_days: lookbackDays }),

  // Portfolio
  portfolioComprehensive: (holdings: string, cash = 0) =>
    fetchAPI<PortfolioComprehensive>("/api/portfolio/comprehensive", { holdings, cash }),
  portfolioPnl: (holdings: string, cash = 0) =>
    fetchAPI<PortfolioPnL>("/api/portfolio/pnl", { holdings, cash }),
  portfolioCorrelation: (tickers: string, period = "1y") =>
    fetchAPI<PortfolioCorrelation>("/api/portfolio/correlation", { tickers, period }),
  portfolioSectors: (holdings: string) =>
    fetchAPI<PortfolioSectors>("/api/portfolio/sectors", { holdings }),

  // Ranking
  rankStocks: (tickers: string) =>
    fetchAPI<RankingResult>("/api/ranking/stocks", { tickers }),
  rankingAdvanced: (tickers: string) =>
    fetchAPI<RankingResult>("/api/ranking/advanced", { tickers }),

  // Theme
  themePropose: (lookbackDays = 7) =>
    fetchAPI<ThemeProposeResult>("/api/theme/propose", { lookback_days: lookbackDays }),
  themeExplore: (theme: string) =>
    fetchAPI<ThemeExploreResult>("/api/theme/explore", { theme }),
  themeTickers: (theme: string) =>
    fetchAPI<ThemeTickersResult>("/api/theme/tickers", { theme }),
  themeAnalyze: (theme: string, topN = 5) =>
    fetchAPI<ThemeAnalyzeResult>("/api/theme/analyze", { theme, top_n: topN }),

  // KR theme endpoints (FR-K14) — hand-curated 한국 테마 맵.
  themeKrPropose: () =>
    fetchAPI<{ themes: string[] }>("/api/theme/kr/propose"),
  themeKrTickers: (theme: string) =>
    fetchAPI<{ theme: string; tickers: string[]; names: string[] }>(
      "/api/theme/kr/tickers",
      { theme },
    ),
  themeKrAnalyze: (theme: string, topN = 5) =>
    fetchAPI<ThemeAnalyzeResult>("/api/theme/kr/analyze", { theme, top_n: topN }),

  // Analysis Reports (LLM-powered) — 5min timeout
  stockAnalysisReport: (ticker: string) =>
    fetchAPI<AnalysisReportPayload>("/api/stock/analysis-report", { ticker }, 300_000),
  portfolioAnalysisReport: (holdings: string, cash = 0) =>
    fetchAPI<AnalysisReportPayload>("/api/portfolio/analysis-report", { holdings, cash }, 300_000),
  themeAnalysisReport: (theme: string, topN = 5) =>
    fetchAPI<AnalysisReportPayload>("/api/theme/analysis-report", { theme, top_n: topN }, 300_000),
  rankingAnalysisReport: (tickers: string) =>
    fetchAPI<AnalysisReportPayload>("/api/ranking/analysis-report", { tickers }, 300_000),

  // Finnhub
  finnhubSummary: (ticker: string) =>
    fetchAPI<Record<string, unknown>>("/api/finnhub/summary", { ticker }),

  // System
  health: () => fetchAPI<HealthResponse>("/api/health"),
  circuitStatus: () => fetchAPI<CircuitStatus>("/api/circuit/status"),

  // Chat (mcp-chatbot) — tool-augmented LLM
  chat: (message: string, sessionId?: string | null) =>
    fetchPOST<ChatResponseData>(
      "/api/chat",
      { message, session_id: sessionId ?? null },
      { timeoutMs: 180_000, retries: 1, retryDelayMs: 800 },
    ),

  // Chat metrics (FR-P10)
  chatMetrics: () => fetchAPI<Record<string, unknown>>("/api/chat/metrics"),
};

export type Api = typeof api;
