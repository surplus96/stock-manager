/** Ranking Engine subroute layout — provides route-level metadata (FR-F13). */
import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Ranking Engine | Stock Manager",
  description: "40-factor 기반 종목 스코어링 및 비교 랭킹",
};

export default function RankingLayout({ children }: { children: ReactNode }) {
  return children;
}
