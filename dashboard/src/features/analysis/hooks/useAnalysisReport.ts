/**
 * useAnalysisReport — fetch + state + derived values for LLM analysis reports (FR-F08).
 *
 * Replaces ad-hoc `useState<any>` + inline fetch calls in stock/portfolio/theme/ranking pages.
 */
"use client";

import { useCallback, useState } from "react";

import { ApiError } from "@/lib/api";
import type { AnalysisReportPayload, NewsItem } from "@/lib/api.types";
import type { ReportBlock } from "@/lib/reportBlocks";

export type AnalysisFetcher = () => Promise<AnalysisReportPayload>;

export interface AnalysisReportState {
  data: AnalysisReportPayload | null;
  loading: boolean;
  error: string | null;
  errorCode: string | null;
  generated: boolean;
  summary: string | undefined;
  blocks: ReportBlock[];
  news: NewsItem[];
  evidence: Record<string, string>;
  generate: () => Promise<void>;
  reset: () => void;
}

function pickString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function pickNews(value: unknown): NewsItem[] {
  return Array.isArray(value) ? (value as NewsItem[]) : [];
}

function pickEvidence(value: unknown): Record<string, string> {
  if (typeof value !== "object" || value === null) return {};
  const out: Record<string, string> = {};
  for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
    out[k] = typeof v === "string" ? v : v == null ? "" : String(v);
  }
  return out;
}

export function useAnalysisReport(fetcher: AnalysisFetcher): AnalysisReportState {
  const [data, setData] = useState<AnalysisReportPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const [generated, setGenerated] = useState(false);

  const generate = useCallback(async () => {
    setLoading(true);
    setError(null);
    setErrorCode(null);
    try {
      const result = await fetcher();
      setData(result);
      setGenerated(true);
    } catch (e: unknown) {
      if (e instanceof ApiError) {
        setError(e.message);
        setErrorCode(e.code);
      } else if (e instanceof Error) {
        setError(e.message);
      } else {
        setError("Unknown error");
      }
    } finally {
      setLoading(false);
    }
  }, [fetcher]);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setErrorCode(null);
    setGenerated(false);
  }, []);

  const summary = data ? pickString(data.llm_summary) ?? pickString(data.summary) : undefined;
  const news = pickNews(data?.news);
  const evidence = pickEvidence(data?.evidence);
  const blocks: ReportBlock[] = Array.isArray(data?.blocks) ? (data!.blocks as ReportBlock[]) : [];

  return { data, loading, error, errorCode, generated, summary, blocks, news, evidence, generate, reset };
}
