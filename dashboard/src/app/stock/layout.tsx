/** Stock Analyzer subroute layout — provides route-level metadata (FR-F13). */
import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Stock Analyzer | Stock Manager",
  description: "40-factor 단일 종목 분석과 AI 투자 리포트",
};

export default function StockLayout({ children }: { children: ReactNode }) {
  return children;
}
