/**
 * Hand-authored response shapes for Stock Manager API (Phase 1).
 *
 * FR-F02: Run `npm run gen:api` (with backend at http://localhost:8000) to
 * regenerate `api.schema.ts` from the live OpenAPI spec, then update the
 * re-exports below. Until then types are kept in sync manually.
 *
 * Selected schema types are re-exported from api.schema.ts where the shapes
 * are equivalent. New types should be added to api.schema.ts first, then
 * re-exported here for backward compatibility.
 */

// Re-export stable schema types — regenerate via `npm run gen:api`
export type { components } from "./api.schema";

export type ISODateString = string;

// ---------- Error envelope ----------
export interface ApiErrorBody {
  code: string;
  message: string;
  request_id: string;
  details?: Record<string, unknown>;
}
export interface ApiErrorEnvelope {
  error: ApiErrorBody;
}

// ---------- Market ----------
export interface MarketCondition {
  condition: string;
  spy_60d_return: number;
}

export interface PriceBar {
  date?: ISODateString;
  open?: number;
  high?: number;
  low?: number;
  close?: number;
  Close?: number;
  volume?: number;
  [key: string]: string | number | undefined;
}

/**
 * `/api/market/prices` 응답은 배열/`{data:[]}`/`{prices:[]}` 형태가 혼재할 수 있어
 * 호출부에서 안전하게 접근할 수 있도록 느슨한 쉐이프로 둔다 (FR-F05에서 단일화 예정).
 */
export interface MarketPricesResponse {
  data?: PriceBar[];
  prices?: PriceBar[];
  [key: string]: unknown;
}

// ---------- Stock ----------
export interface StockSignal {
  ticker: string;
  signal?: string;
  score?: number;
  [key: string]: unknown;
}

export type StockComprehensive = Record<string, unknown>;
export type StockCompareResult = Record<string, unknown>;
export type FactorInterpretation = Record<string, unknown>;
export type TechnicalAnalysis = Record<string, unknown>;

// ---------- News ----------
export interface NewsItem {
  title: string;
  source?: string;
  date?: string;
  url?: string;
  snippet?: string;
}
export interface NewsSearchResult {
  items: NewsItem[];
  total?: number;
}
export type NewsSentiment = Record<string, unknown>;
export type NewsTimeline = Record<string, unknown>;

// ---------- Portfolio ----------
export type PortfolioComprehensive = Record<string, unknown>;
export type PortfolioPnL = Record<string, unknown>;
export type PortfolioCorrelation = Record<string, unknown>;
export type PortfolioSectors = Record<string, unknown>;

// ---------- Ranking / Theme ----------
/** 랭킹/테마 응답: 배열 또는 `{rankings|data|themes:[]}` 형태가 혼재 */
export type RankingResult =
  | Array<Record<string, unknown>>
  | { rankings?: unknown[]; data?: unknown[]; [key: string]: unknown };
export type ThemeProposeResult =
  | Array<Record<string, unknown> | string>
  | { themes?: unknown[]; data?: unknown[]; [key: string]: unknown };
export type ThemeExploreResult = Record<string, unknown>;
export type ThemeTickersResult = Record<string, unknown>;
export type ThemeAnalyzeResult = Record<string, unknown>;

// ---------- Analysis Reports (LLM) ----------
export interface AnalysisReportPayload {
  title?: string;
  llm_summary?: string;
  summary?: string;
  news?: NewsItem[];
  evidence?: Record<string, string>;
  // rich-visual-reports — structured block array. The frontend uses
  // this when present and falls back to the legacy prose summary when
  // the backend can't produce it.
  blocks?: import("./reportBlocks").ReportBlock[];
  [key: string]: unknown;
}

// ---------- System ----------
export interface HealthResponse {
  status: string;
  version?: string;
}
export type CircuitStatus = Record<string, unknown>;

// ---------- Chat (mcp-chatbot) ----------
export interface ChatToolTrace {
  tool: string;
  args: Record<string, unknown>;
  result_summary: string;
  ok: boolean;
}
export interface ChatResponseData {
  session_id: string;
  answer: string;
  trace: ChatToolTrace[];
  hops: number;
}
