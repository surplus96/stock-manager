/**
 * Hand-maintained OpenAPI schema stub — generated from backend route inspection.
 *
 * THIS FILE IS AUTO-REPLACEABLE: run `npm run gen:api` with the backend running
 * at http://localhost:8000 to regenerate from the live OpenAPI spec.
 * Until then this stub provides best-effort shapes derived from mcp_server/main.py
 * and the existing api.types.ts manual types.
 *
 * IMPORTANT: Do NOT hand-edit below the "--- generated ---" marker.
 * Add project-level overrides above it and import selectively in api.types.ts.
 */

// --- generated (hand-maintained stub) ---

export interface paths {
  "/api/health": {
    get: {
      responses: {
        200: { content: { "application/json": components["schemas"]["HealthResponse"] } };
      };
    };
  };
  "/api/market/condition": {
    get: {
      responses: {
        200: { content: { "application/json": components["schemas"]["MarketCondition"] } };
      };
    };
  };
  "/api/market/prices": {
    get: {
      parameters: { query: { ticker: string; period?: string; interval?: string } };
      responses: {
        200: { content: { "application/json": components["schemas"]["MarketPricesResponse"] } };
      };
    };
  };
  "/api/stock/comprehensive": {
    get: {
      parameters: { query: { ticker: string } };
      responses: {
        200: { content: { "application/json": components["schemas"]["StockComprehensive"] } };
      };
    };
  };
  "/api/stock/signal": {
    get: {
      parameters: { query: { ticker: string } };
      responses: {
        200: { content: { "application/json": components["schemas"]["StockSignal"] } };
      };
    };
  };
  "/api/stock/investment-signal": {
    get: {
      parameters: { query: { ticker: string } };
      responses: {
        200: { content: { "application/json": components["schemas"]["StockSignal"] } };
      };
    };
  };
  "/api/stock/factor-interpretation": {
    get: {
      parameters: { query: { ticker: string } };
      responses: {
        200: { content: { "application/json": components["schemas"]["FactorInterpretation"] } };
      };
    };
  };
  "/api/stock/compare": {
    get: {
      parameters: { query: { tickers: string } };
      responses: {
        200: { content: { "application/json": components["schemas"]["StockCompareResult"] } };
      };
    };
  };
  "/api/stock/analysis-report": {
    get: {
      parameters: { query: { ticker: string } };
      responses: {
        200: { content: { "application/json": components["schemas"]["AnalysisReportPayload"] } };
      };
    };
  };
  "/api/technical/analyze": {
    get: {
      parameters: { query: { ticker: string } };
      responses: {
        200: { content: { "application/json": components["schemas"]["TechnicalAnalysis"] } };
      };
    };
  };
  "/api/news/search": {
    get: {
      parameters: { query: { queries: string; lookback_days?: number; max_results?: number } };
      responses: {
        200: { content: { "application/json": components["schemas"]["NewsSearchResult"] } };
      };
    };
  };
  "/api/news/sentiment": {
    get: {
      parameters: { query: { tickers: string; lookback_days?: number } };
      responses: {
        200: { content: { "application/json": components["schemas"]["NewsSentiment"] } };
      };
    };
  };
  "/api/news/timeline": {
    get: {
      parameters: { query: { ticker: string; lookback_days?: number } };
      responses: {
        200: { content: { "application/json": components["schemas"]["NewsTimeline"] } };
      };
    };
  };
  "/api/portfolio/comprehensive": {
    get: {
      parameters: { query: { holdings: string; cash?: number } };
      responses: {
        200: { content: { "application/json": components["schemas"]["PortfolioComprehensive"] } };
      };
    };
  };
  "/api/portfolio/pnl": {
    get: {
      parameters: { query: { holdings: string; cash?: number } };
      responses: {
        200: { content: { "application/json": components["schemas"]["PortfolioPnL"] } };
      };
    };
  };
  "/api/portfolio/correlation": {
    get: {
      parameters: { query: { tickers: string; period?: string } };
      responses: {
        200: { content: { "application/json": components["schemas"]["PortfolioCorrelation"] } };
      };
    };
  };
  "/api/portfolio/sectors": {
    get: {
      parameters: { query: { holdings: string } };
      responses: {
        200: { content: { "application/json": components["schemas"]["PortfolioSectors"] } };
      };
    };
  };
  "/api/portfolio/analysis-report": {
    get: {
      parameters: { query: { holdings: string; cash?: number } };
      responses: {
        200: { content: { "application/json": components["schemas"]["AnalysisReportPayload"] } };
      };
    };
  };
  "/api/ranking/stocks": {
    get: {
      parameters: { query: { tickers: string } };
      responses: {
        200: { content: { "application/json": components["schemas"]["RankingResult"] } };
      };
    };
  };
  "/api/ranking/advanced": {
    get: {
      parameters: { query: { tickers: string } };
      responses: {
        200: { content: { "application/json": components["schemas"]["RankingResult"] } };
      };
    };
  };
  "/api/ranking/analysis-report": {
    get: {
      parameters: { query: { tickers: string } };
      responses: {
        200: { content: { "application/json": components["schemas"]["AnalysisReportPayload"] } };
      };
    };
  };
  "/api/theme/propose": {
    get: {
      parameters: { query: { lookback_days?: number } };
      responses: {
        200: { content: { "application/json": components["schemas"]["ThemeProposeResult"] } };
      };
    };
  };
  "/api/theme/explore": {
    get: {
      parameters: { query: { theme: string } };
      responses: {
        200: { content: { "application/json": components["schemas"]["ThemeExploreResult"] } };
      };
    };
  };
  "/api/theme/tickers": {
    get: {
      parameters: { query: { theme: string } };
      responses: {
        200: { content: { "application/json": components["schemas"]["ThemeTickersResult"] } };
      };
    };
  };
  "/api/theme/analyze": {
    get: {
      parameters: { query: { theme: string; top_n?: number } };
      responses: {
        200: { content: { "application/json": components["schemas"]["ThemeAnalyzeResult"] } };
      };
    };
  };
  "/api/theme/analysis-report": {
    get: {
      parameters: { query: { theme: string; top_n?: number } };
      responses: {
        200: { content: { "application/json": components["schemas"]["AnalysisReportPayload"] } };
      };
    };
  };
  "/api/finnhub/summary": {
    get: {
      parameters: { query: { ticker: string } };
      responses: {
        200: { content: { "application/json": Record<string, unknown> } };
      };
    };
  };
  "/api/circuit/status": {
    get: {
      responses: {
        200: { content: { "application/json": components["schemas"]["CircuitStatus"] } };
      };
    };
  };
}

export interface components {
  schemas: {
    HealthResponse: {
      status: string;
      version?: string;
    };
    MarketCondition: {
      condition: string;
      spy_60d_return: number;
    };
    PriceBar: {
      date?: string;
      open?: number;
      high?: number;
      low?: number;
      close?: number;
      Close?: number;
      volume?: number;
      [key: string]: string | number | undefined;
    };
    MarketPricesResponse: {
      data?: components["schemas"]["PriceBar"][];
      prices?: components["schemas"]["PriceBar"][];
      [key: string]: unknown;
    };
    StockSignal: {
      ticker: string;
      signal?: string;
      score?: number;
      decision?: string;
      confidence?: string;
      reasoning?: string;
      reasons?: string[];
      risks?: string[];
      [key: string]: unknown;
    };
    StockComprehensive: Record<string, unknown>;
    StockCompareResult: Record<string, unknown>;
    FactorInterpretation: Record<string, unknown>;
    TechnicalAnalysis: Record<string, unknown>;
    NewsItem: {
      title: string;
      source?: string;
      date?: string;
      url?: string;
      snippet?: string;
    };
    NewsSearchResult: {
      items: components["schemas"]["NewsItem"][];
      total?: number;
    };
    NewsSentiment: Record<string, unknown>;
    NewsTimeline: Record<string, unknown>;
    PortfolioComprehensive: Record<string, unknown>;
    PortfolioPnL: Record<string, unknown>;
    PortfolioCorrelation: Record<string, unknown>;
    PortfolioSectors: Record<string, unknown>;
    RankingResult:
      | Array<Record<string, unknown>>
      | { rankings?: unknown[]; data?: unknown[]; [key: string]: unknown };
    ThemeProposeResult:
      | Array<Record<string, unknown> | string>
      | { themes?: unknown[]; data?: unknown[]; [key: string]: unknown };
    ThemeExploreResult: Record<string, unknown>;
    ThemeTickersResult: Record<string, unknown>;
    ThemeAnalyzeResult: Record<string, unknown>;
    AnalysisReportPayload: {
      title?: string;
      llm_summary?: string;
      summary?: string;
      news?: components["schemas"]["NewsItem"][];
      evidence?: Record<string, string>;
      [key: string]: unknown;
    };
    ApiErrorBody: {
      code: string;
      message: string;
      request_id: string;
      details?: Record<string, unknown>;
    };
    CircuitStatus: Record<string, unknown>;
  };
}
