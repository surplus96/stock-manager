/** Chatbot subroute layout — provides route-level metadata (FR-F13). */
import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "AI Chatbot | Stock Manager",
  description: "MCP 도구 기반 AI 챗봇 — 테마 추천, 종목 분석, 시장 진단",
};

export default function ChatLayout({ children }: { children: ReactNode }) {
  return children;
}
