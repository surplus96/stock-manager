---
template: design
version: 1.2
feature: frontend-quality-upgrade
date: 2026-04-15
author: Stock Manager Team
project: Stock Manager (adoring-swartz)
status: Draft
---

# frontend-quality-upgrade Design Document

> **Summary**: Next.js 16 App Router 대시보드의 타입·접근성·반응형·성능·구조를 동시에 정비한다.
>
> **Project**: Stock Manager
> **Version**: 1.0 → 1.1
> **Author**: Stock Manager Team
> **Date**: 2026-04-15
> **Status**: Draft
> **Planning Doc**: [frontend-quality-upgrade.plan.md](../../01-plan/features/frontend-quality-upgrade.plan.md)

---

## 1. Overview

### 1.1 Design Goals

- `any` 제거 + OpenAPI 기반 타입 자동화로 FE↔BE 계약 명확화
- Server Component 우선, Client Component는 상호작용 경계로 한정
- 반응형 레이아웃(375/768/1280) + a11y AA 만족
- 차트/마크다운/폼 등 무거운 모듈 Code Split + Skeleton UI
- 재사용 훅/컴포넌트/디자인 토큰 레이어 구축

### 1.2 Design Principles

- **Server-first**: 기본은 Server Component, 상호작용은 `"use client"` 섬
- **Typed boundaries**: API 응답은 OpenAPI 산출 타입으로만 수용
- **a11y by default**: Radix 패턴 또는 headless-ui 활용, 수동 aria-*
- **Composable layout**: Shell(Sidebar/Topbar) + Slot(Content)
- **Progressive enhancement**: Skeleton → Data → Error Boundary

---

## 2. Architecture

### 2.1 Component Diagram

```
┌────────────────────────────────────────────────────────────┐
│  App Router (src/app)                                      │
│  layout.tsx (Server) ── Shell(Sidebar + Topbar)            │
│    └── page.tsx (Server: fetch) ── <Client Island>         │
└────────────────────────────────────────────────────────────┘
          │
          ▼
   features/*  (hooks + services + components)
          │
          ▼
   lib/api.ts  (typed, generated from openapi.json)
          │
          ▼
   Backend FastAPI
```

### 2.2 Data Flow

```
URL → RSC fetch(API) → Typed Envelope
   → stream HTML + Skeleton
   → Client Island (interactivity) → optimistic state
   → ErrorBoundary on failure → toast + retry
```

### 2.3 Dependencies

| Component | Depends On | Purpose |
|-----------|-----------|---------|
| `app/*/page.tsx` | `features/*`, `lib/api` | 페이지 조립 |
| `features/analysis` | `lib/api`, UI primitives | 분석 로직/훅 |
| `lib/api.ts` | `api.types.ts (generated)` | 타입 안전 fetch |
| `components/ui/*` | `styles/tokens` | 디자인 시스템 |

---

## 3. Data Model (Typed Contracts)

### 3.1 Generated Types

```bash
# package.json script
"gen:api": "openapi-typescript http://localhost:8000/openapi.json -o src/lib/api.types.ts"
```

```ts
// src/lib/api.types.ts (generated — 수정 금지)
export interface paths { ... }
export interface components { schemas: { AnalysisReport: {...}, ApiError: {...} } }
```

### 3.2 Thin Typed Client

```ts
// src/lib/api.ts
import type { components, paths } from "./api.types";
type Analysis = components["schemas"]["AnalysisReport"];
type Envelope<T> = { data: T; generated_at: string; version: string };

export async function fetchAnalysis(body: paths["/api/analysis"]["post"]["requestBody"]["content"]["application/json"]):
  Promise<Envelope<Analysis>> {
  const res = await fetch(`${BASE}/api/analysis`, { method: "POST", body: JSON.stringify(body) });
  if (!res.ok) throw await toApiError(res);
  return res.json();
}
```

### 3.3 Domain Types

```ts
// src/types/analysis.ts
import type { components } from "@/lib/api.types";
export type AnalysisReport = components["schemas"]["AnalysisReport"];
export type ApiError = components["schemas"]["ApiError"];
```

---

## 4. UI Contract (Page → Component)

### 4.1 Routes

| Path | 렌더링 | 주요 Island |
|------|--------|-------------|
| `/` (dashboard) | RSC | KPI 카드(Client: 차트) |
| `/portfolio` | RSC | 테이블 필터(Client) |
| `/theme` | RSC | 분석 폼(Client) |
| `/analysis/[id]` | RSC | 리포트 토글/탭(Client) |
| `/news` | RSC | 감정 차트(Client) |

### 4.2 Layout Contract

```
<Shell>
  <Sidebar collapsible />   (md↑ = 240px, sm = drawer)
  <Main>
    <Topbar />
    <PageSlot />            (RSC children)
  </Main>
</Shell>
```

- Tailwind breakpoint: `sm 640 / md 768 / lg 1024 / xl 1280`
- 기존 `ml-60` 제거 → `md:ml-60` + 모바일 drawer

### 4.3 AnalysisReport (a11y 보강)

```tsx
<button
  aria-expanded={open}
  aria-controls={`sec-${id}`}
  onClick={toggle}
  onKeyDown={onKey}  // Enter/Space
  className="focus:ring-2 focus:ring-offset-2"
>
  {title}
</button>
<section id={`sec-${id}`} hidden={!open}>...</section>
```

---

## 5. UI/UX Design

### 5.1 Screen Layout (responsive)

```
mobile (375)                   desktop (1280)
┌───────────────┐              ┌──────┬─────────────────┐
│ ☰ Topbar      │              │ Side │ Topbar          │
├───────────────┤              │ bar  ├─────────────────┤
│ Content       │              │      │ Content (grid)  │
│               │              │      │                 │
└───────────────┘              └──────┴─────────────────┘
```

### 5.2 User Flow

```
/ → 종목 선택 → /analysis/[id] → 섹션 토글/탭 → 리포트 PDF/공유
```

### 5.3 Components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| `Shell`, `Sidebar`, `Topbar` | `components/ui/shell/` | 레이아웃 |
| `AsyncBoundary` | `components/ui/async-boundary.tsx` | 로딩/에러 표준 |
| `Skeleton.*` | `components/ui/skeleton/` | 로딩 placeholder |
| `Markdown` | `components/ui/markdown.tsx` | react-markdown 래퍼 |
| `AnalysisReport` | `features/analysis/components/` | 보고서 표현 |
| `useAnalysisReport` | `features/analysis/hooks/` | fetch+state 훅 |

---

## 6. Error Handling

### 6.1 Codes (BE 공유)

| Code | UI 처리 |
|------|---------|
| `VALIDATION_ERROR` | 폼 인라인 메시지 |
| `RATE_LIMITED` | Toast + 재시도 버튼(쿨다운) |
| `LLM_TIMEOUT` | 섹션별 fallback 메시지 + 다시 시도 |
| `UPSTREAM_ERROR` | Empty state + 재시도 |
| `INTERNAL_ERROR` | 전역 ErrorBoundary |

### 6.2 Response Shape

```ts
type ApiErrorEnvelope = { error: { code: string; message: string; request_id: string; details?: unknown } };
```

### 6.3 Boundary

```tsx
<AsyncBoundary fallback={<SkeletonReport/>} onError={toast.error}>
  <AnalysisReport id={id} />
</AsyncBoundary>
```

---

## 7. Security Considerations

- [x] `NEXT_PUBLIC_*` 만 브라우저 노출, 기타 env 서버만
- [x] 외부 링크 `rel="noopener noreferrer"`
- [x] `dangerouslySetInnerHTML` 금지 (react-markdown 사용)
- [x] 이미지 원격 도메인 whitelist(`next.config` remotePatterns)
- [x] CSP 고려 (nonce — 추후)

---

## 8. Test Plan

### 8.1 Scope

| Type | Target | Tool |
|------|--------|------|
| Unit | hooks, utils | Vitest |
| Component | UI primitives, AnalysisReport | RTL |
| a11y | 주요 페이지 | axe-core |
| Visual | Sidebar/Report | Playwright screenshot |

### 8.2 Key Cases

- [ ] `api.ts`: 타입 에러가 빌드에서 검출됨
- [ ] AnalysisReport: 키보드(Enter/Space)로 섹션 토글
- [ ] Sidebar: 375/768/1280 레이아웃 정상
- [ ] Lighthouse a11y ≥ 95, Performance ≥ 85
- [ ] Recharts 초기 번들 미포함(동적 import 확인)
- [ ] Error Boundary: LLM_TIMEOUT 섹션 fallback

---

## 9. Clean Architecture

### 9.1 Layer Structure

| Layer | Responsibility | Location |
|-------|---------------|----------|
| Presentation | RSC pages, UI primitives | `src/app/`, `src/components/ui/` |
| Application | hooks, feature services | `src/features/*/hooks`, `src/features/*/services` |
| Domain | 타입, 상수, 도메인 규칙 | `src/types/`, `src/domain/` |
| Infrastructure | API 클라이언트, storage | `src/lib/api.ts`, `src/lib/storage.ts` |

### 9.2 Dependency Rules

```
app (RSC) ──► features ──► domain ◄── infrastructure
components/ui ─────────────────────────▲
          (no direct infra import)
```

### 9.3 Import Rules

| From | Allowed | Disallowed |
|------|---------|------------|
| `app/*` | `features/*`, `components/ui`, `lib/api` | 내부 컴포넌트 깊이 import |
| `components/ui` | `styles/tokens`, `domain types` | `lib/api` 직접 사용 |
| `features/*` | `lib/*`, `domain` | 타 feature 내부 |
| `lib/*` | `api.types` | feature, components |

### 9.4 Feature Layer Assignment

| Component | Layer | Location |
|-----------|-------|----------|
| `AnalysisPage` | Presentation (RSC) | `app/analysis/[id]/page.tsx` |
| `AnalysisReport` | Presentation (Client) | `features/analysis/components/` |
| `useAnalysisReport` | Application | `features/analysis/hooks/` |
| `AnalysisReport` type | Domain | `types/analysis.ts` |
| `fetchAnalysis` | Infrastructure | `lib/api.ts` |

---

## 10. Coding Convention Reference

### 10.1 Naming

| Target | Rule | Example |
|--------|------|---------|
| Component | PascalCase + `.tsx` | `AnalysisReport.tsx` |
| Hook | `useXxx` camelCase + `.ts` | `useAnalysisReport.ts` |
| Utility | camelCase + `.ts` | `formatCurrency.ts` |
| Folder | kebab-case | `analysis-report/` |
| Type | PascalCase | `AnalysisReport` |
| Constant | UPPER_SNAKE | `MAX_SECTIONS` |

### 10.2 Import Order (eslint-plugin-import)

```ts
// 1. external
import { useEffect, useState } from "react";
// 2. internal absolute
import { Markdown } from "@/components/ui/markdown";
import { fetchAnalysis } from "@/lib/api";
// 3. relative
import { SectionToggle } from "./SectionToggle";
// 4. type
import type { AnalysisReport } from "@/types/analysis";
// 5. styles
import "./styles.css";
```

### 10.3 Env Vars

| Prefix | Purpose | Example |
|--------|---------|---------|
| `NEXT_PUBLIC_` | 브라우저 | `NEXT_PUBLIC_API_BASE_URL` |
| (no prefix) | 서버 전용 | `REVALIDATE_SEC` |

### 10.4 Applied

| Item | Convention |
|------|-----------|
| Client 경계 | 상호작용 컴포넌트만 `"use client"` |
| 상태 | local `useState` + custom hook; 전역 금지 |
| 에러 처리 | `AsyncBoundary` + toast |
| 스타일 | Tailwind + `theme.extend` tokens |
| a11y | aria-*, focus ring, semantic HTML |

---

## 11. Implementation Guide

### 11.1 File Structure

```
dashboard/src/
├── app/
│   ├── layout.tsx              (RSC Shell)
│   ├── page.tsx                (RSC dashboard)
│   ├── portfolio/page.tsx
│   ├── theme/page.tsx
│   ├── analysis/[id]/page.tsx
│   └── news/page.tsx
├── components/
│   └── ui/
│       ├── shell/
│       ├── skeleton/
│       ├── async-boundary.tsx
│       └── markdown.tsx
├── features/
│   └── analysis/
│       ├── components/AnalysisReport.tsx
│       ├── hooks/useAnalysisReport.ts
│       └── services/analysis.client.ts
├── lib/
│   ├── api.ts
│   └── api.types.ts            (generated)
├── styles/
│   └── tokens.ts
└── types/
    └── analysis.ts
```

### 11.2 Implementation Order

1. [ ] eslint strict + `no-explicit-any` error 승격 — FR-F16
2. [ ] `openapi-typescript` 스크립트 + `api.types.ts` 생성 — FR-F02
3. [ ] `lib/api.ts` 타입화 — FR-F01, FR-F05
4. [ ] Shell 레이아웃 분해 + 반응형(`ml-60` 제거) — FR-F04, FR-F14
5. [ ] `AsyncBoundary` + Skeleton + Markdown 래퍼 — FR-F09, FR-F10, FR-F11
6. [ ] `AnalysisReport` 리팩토 + a11y — FR-F03
7. [ ] `useAnalysisReport` 훅 추출 — FR-F08
8. [ ] Recharts `next/dynamic(ssr:false)` — FR-F06
9. [ ] 페이지별 Server Component 전환 검토 + `metadata` — FR-F07, FR-F13
10. [ ] 디자인 토큰 적용 (색상/타이포/spacing) — FR-F12
11. [ ] Vitest + RTL 기본 구성 및 3개 컴포넌트 테스트 — FR-F18, FR-F19
12. [ ] `@next/bundle-analyzer` 측정 + 원격 이미지 whitelist — FR-F15, FR-F20

### 11.3 Parallel Sync with Backend

| Sync Point | What | When |
|------------|------|------|
| `openapi.json` 수신 | FE 타입 재생성 | BE Phase 1 종료 |
| `ApiError` 스키마 | FE 에러 코드 매핑 구현 | BE Phase 1 |
| Rate limit 정책 | FE 재시도/토스트 문구 | BE Phase 2 |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-04-15 | Plan FR-F01~F20 기반 초안 | Stock Manager Team |
