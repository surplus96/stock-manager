/** Portfolio subroute layout — provides route-level metadata (FR-F13). */
import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Portfolio | Stock Manager",
  description: "포트폴리오 구성·상관관계·섹터 분산 진단",
};

export default function PortfolioLayout({ children }: { children: ReactNode }) {
  return children;
}
