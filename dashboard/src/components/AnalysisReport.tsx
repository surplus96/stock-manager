"use client";

import { useId, useState } from "react";
import Card from "./Card";
import { Markdown } from "./ui/Markdown";
import { BlockList } from "./report/BlockRenderer";
import Toc from "./report/inline/Toc";
import type { ReportBlock } from "@/lib/reportBlocks";
import { FileText, Newspaper, ExternalLink, ChevronDown, ChevronUp, Loader2 } from "lucide-react";

interface NewsItem {
  title: string;
  source?: string;
  date?: string;
  url?: string;
  snippet?: string;
}

function stripHtml(text?: string): string {
  if (!text) return "";
  return text
    .replace(/<[^>]*>/g, "")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#\d+;/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

interface ReportProps {
  title: string;
  loading: boolean;
  llmSummary?: string;
  news?: NewsItem[];
  evidence?: Record<string, string>;
  /** rich-visual-reports — structured blocks preferred over prose summary. */
  blocks?: ReportBlock[];
  onGenerate: () => void;
  generated: boolean;
}

export default function AnalysisReport({
  title,
  loading,
  llmSummary,
  news,
  evidence,
  blocks,
  onGenerate,
  generated,
}: ReportProps) {
  const [expanded, setExpanded] = useState(true);
  const panelId = useId();
  const toggleLabel = expanded ? "리포트 섹션 접기" : "리포트 섹션 펼치기";

  return (
    <div className="border-t-2 border-blue-100 dark:border-blue-900 pt-6 mt-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400" aria-hidden="true" />
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-50">{title}</h2>
        </div>
        <div className="flex items-center gap-2">
          {!generated && !loading && (
            <button
              type="button"
              onClick={onGenerate}
              aria-label={`${title} 리포트 생성`}
              className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-colors flex items-center gap-2"
            >
              <FileText className="w-4 h-4" aria-hidden="true" />
              리포트 생성
            </button>
          )}
          {generated && (
            <button
              type="button"
              onClick={() => setExpanded((v) => !v)}
              aria-expanded={expanded}
              aria-controls={panelId}
              aria-label={toggleLabel}
              title={toggleLabel}
              className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 dark:text-slate-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
            >
              {expanded
                ? <ChevronUp className="w-4 h-4" aria-hidden="true" />
                : <ChevronDown className="w-4 h-4" aria-hidden="true" />}
            </button>
          )}
        </div>
      </div>

      {loading && (
        <div
          role="status"
          aria-live="polite"
          className="flex items-center gap-3 p-6 bg-blue-50 dark:bg-blue-950/50 rounded-xl border border-blue-100 dark:border-blue-900"
        >
          <Loader2 className="w-5 h-5 text-blue-600 dark:text-blue-400 animate-spin" aria-hidden="true" />
          <span className="text-sm text-blue-700 dark:text-blue-200">AI가 데이터를 분석하고 종합 리포트를 생성 중입니다...</span>
        </div>
      )}

      {generated && expanded && (
        <div id={panelId} role="region" aria-label={`${title} 분석 리포트`} className="space-y-4">
          {/* rich-visual-reports: prefer structured blocks; fall back to prose. */}
          {blocks && blocks.length > 0 ? (
            <Card title="AI 종합 분석 리포트">
              {/* FR-PSP-G — sticky TOC kicks in for ≥5-block reports;
                  otherwise the layout is identical to the previous
                  single-column rendering (Toc returns null). */}
              <div className="flex gap-6">
                <Toc blocks={blocks} />
                <div className="flex-1 min-w-0">
                  <BlockList blocks={blocks} />
                </div>
              </div>
            </Card>
          ) : (
            llmSummary && (
              <Card title="AI 종합 분석 요약">
                <Markdown>{llmSummary}</Markdown>
              </Card>
            )
          )}

          <div className="grid grid-cols-2 gap-4">
            {/* 관련 뉴스 & 이벤트 */}
            {news && news.length > 0 && (
              <Card title="관련 뉴스 & 이벤트">
                <div className="space-y-3">
                  {news.map((item, i) => (
                    <div key={i} className="flex items-start gap-2.5 text-sm p-2.5 bg-slate-50 dark:bg-slate-800 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">
                      <Newspaper className="w-4 h-4 text-blue-500 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        {item.url ? (
                          <a
                            href={item.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-700 dark:text-blue-300 hover:text-blue-900 dark:hover:text-blue-100 hover:underline font-medium flex items-start gap-1"
                          >
                            <span className="line-clamp-2">{stripHtml(item.title)}</span>
                            <ExternalLink className="w-3 h-3 mt-0.5 flex-shrink-0 opacity-50" />
                          </a>
                        ) : (
                          <p className="text-slate-900 dark:text-slate-50 font-medium line-clamp-2">{stripHtml(item.title)}</p>
                        )}
                        {item.snippet && (
                          <p className="text-xs text-slate-600 dark:text-slate-300 mt-1 line-clamp-2">{stripHtml(item.snippet)}</p>
                        )}
                        <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">
                          {[stripHtml(item.source), item.date?.slice(0, 10)].filter(Boolean).join(" · ")}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* 핵심 근거 데이터 */}
            {evidence && Object.keys(evidence).length > 0 && (
              <Card title="핵심 근거 데이터">
                <div className="space-y-2">
                  {Object.entries(evidence).map(([key, val]) => (
                    <div key={key} className="flex justify-between text-sm py-1.5 border-b border-slate-100 dark:border-slate-700 last:border-0">
                      <span className="text-slate-600 dark:text-slate-300">{key}</span>
                      <span className="text-slate-900 dark:text-slate-50 font-medium">{val}</span>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
