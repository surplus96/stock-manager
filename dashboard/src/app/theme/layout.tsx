/** Theme Explorer subroute layout — provides route-level metadata (FR-F13). */
import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Theme Explorer | Stock Manager",
  description: "시장 테마 탐색 및 테마 기반 종목 분석 리포트",
};

export default function ThemeLayout({ children }: { children: ReactNode }) {
  return children;
}
