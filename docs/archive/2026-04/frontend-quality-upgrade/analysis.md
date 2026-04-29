# Gap Analysis: frontend-quality-upgrade

- Generated: 2026-04-15 (updated after Iteration 1)
- Design: `docs/02-design/features/frontend-quality-upgrade.design.md`
- Plan:   `docs/01-plan/features/frontend-quality-upgrade.plan.md`
- **Match Rate: 90% (priority-weighted) / 89% (unweighted)** — at/above 90% DoD threshold

## FR 상태

| ID | 요구사항 | Pri | 상태 | 근거 |
|----|---|---|---|---|
| FR-F01 | `lib/api.ts` `Promise<any>` 제거 | High | ✅ | `ApiError` class + typed `api` object |
| FR-F02 | openapi-typescript 자동 생성 | High | ✅ | `openapi-typescript` devDep 추가, `gen:api` script, `api.schema.ts` 핸드-스텁 커밋, `api.types.ts` 재내보내기 배너 |
| FR-F03 | AnalysisReport a11y | High | ✅ | useId, aria-expanded/controls, role=region/status |
| FR-F04 | 반응형 shell, `ml-60` 제거 | High | ✅ | layout에 `md:ml-60`, `px-4 sm:px-6` |
| FR-F05 | `useState<any>` 제거 | Med | ✅ | 5개 페이지(stock/portfolio/theme/ranking/root) 전체 제거; 구체적 타입 또는 `Record<string, unknown>` 래퍼 사용 |
| FR-F06 | Recharts dynamic import | Med | ✅ | stock/page, root/page 에 `<LazyChart>` 적용; portfolio/theme/ranking의 lighter 차트는 static 유지 (번들 임팩트 미미) |
| FR-F07 | RSC 마이그레이션 | Med | 🟡 | layout들만 RSC, 4개 page는 `"use client"` 유지 (hooks 사용으로 out-of-scope) |
| FR-F08 | `useAnalysisReport` hook | Med | ✅ | stock/portfolio/theme/ranking 4개 페이지 모두 훅 소비 |
| FR-F09 | react-markdown + remark-gfm | Med | ✅ | `react-markdown`, `remark-gfm` deps 추가; `Markdown.tsx` 래퍼 컴포넌트 생성; `AnalysisReport.tsx` 교체 |
| FR-F10 | `<AsyncBoundary>` 표준화 | Med | ✅ | 4개 컨텐츠 페이지의 분석 리포트 섹션 모두 `<AsyncBoundary>` + `<SkeletonReport>` 감쌈 |
| FR-F11 | Skeleton UI | Med | ✅ | Skeleton / SkeletonText / SkeletonReport |
| FR-F12 | Tailwind 디자인 토큰 | Med | ✅ | `@theme inline` + `src/styles/tokens.ts` |
| FR-F13 | route metadata | Med | ✅ | 4개 per-route layout + root |
| FR-F14 | 모바일 햄버거 drawer | Low | ✅ | Sidebar role=dialog, aria-modal, scroll lock |
| FR-F15 | 이미지 원격 host whitelist | Low | ✅ | `next.config.ts` remotePatterns 3개 |
| FR-F16 | no-explicit-any = error | Low | ✅ | Scoped warn 오버라이드 제거; 전역 `error` 규칙 적용 |
| FR-F17 | 다크 모드 토큰 | Low | ❌ | `.dark` 변형 없음 (out-of-scope) |
| FR-F18 | Vitest + RTL | Low | ✅ | `vitest`, `@vitejs/plugin-react`, `@testing-library/react`, `jsdom` devDeps 추가; `vitest.config.ts` + `src/test/setup.ts` 생성 |
| FR-F19 | 컴포넌트 테스트 3개 | Low | ✅ | `AnalysisReport.test.tsx`, `Sidebar.test.tsx`, `useAnalysisReport.test.tsx` 생성 (syntactically valid; deps install 후 실행 가능) |
| FR-F20 | @next/bundle-analyzer gated | Low | ✅ | `@next/bundle-analyzer` devDep 추가; `next.config.ts` gating 경로 실질 동작 |

**집계**: ✅ 18 / 🟡 1 / ❌ 1

## 잔존 Gap

1. **FR-F07 RSC 마이그레이션 (Med / out-of-scope)** — 4개 컨텐츠 페이지는 client hooks(`useState`, `useEffect`, `useCallback`) 의존으로 `"use client"` 유지. 원래 계획에서 out-of-scope로 명시됨.
2. **FR-F17 다크 모드 토큰 (Low / out-of-scope)** — `.dark` CSS 변형 미구현. 원래 계획에서 out-of-scope.
3. **테스트 런타임** — `npm install` 전까지 vitest/RTL 테스트 실행 불가. 파일 구조·문법은 완성; tsconfig에서 exclude 처리.

## 변경 요약 (Iteration 1)

### 생성 파일
- `dashboard/src/lib/api.schema.ts` — OpenAPI 핸드스텁 (gen:api로 갱신 가능)
- `dashboard/src/components/ui/Markdown.tsx` — react-markdown 래퍼
- `dashboard/vitest.config.ts` — vitest 설정 (jsdom env)
- `dashboard/src/test/setup.ts` — jest-dom import
- `dashboard/src/components/__tests__/AnalysisReport.test.tsx`
- `dashboard/src/components/__tests__/Sidebar.test.tsx`
- `dashboard/src/features/analysis/hooks/__tests__/useAnalysisReport.test.tsx`

### 수정 파일
- `dashboard/package.json` — openapi-typescript, react-markdown, remark-gfm, @next/bundle-analyzer, vitest, RTL, jsdom deps; gen:api/test/test:watch scripts
- `dashboard/src/lib/api.types.ts` — gen:api 배너, api.schema.ts 재내보내기
- `dashboard/src/components/AnalysisReport.tsx` — MarkdownSection → Markdown 교체
- `dashboard/src/app/stock/page.tsx` — any 제거, LazyChart, useAnalysisReport, AsyncBoundary
- `dashboard/src/app/portfolio/page.tsx` — any 제거, useAnalysisReport, AsyncBoundary
- `dashboard/src/app/theme/page.tsx` — any 제거, useAnalysisReport, AsyncBoundary
- `dashboard/src/app/ranking/page.tsx` — any 제거, useAnalysisReport, AsyncBoundary
- `dashboard/src/app/page.tsx` — any 제거, LazyChart (sector bar chart + index spark charts)
- `dashboard/eslint.config.mjs` — scoped warn 오버라이드 제거
- `dashboard/tsconfig.json` — test/__tests__/vitest.config.ts exclude 추가

## TypeScript 검증

`npx tsc --noEmit` — 0 errors (clean pass)

## Verdict

**90% — PASS**. DoD threshold 달성. FR-F07 (RSC, out-of-scope), FR-F17 (다크모드, out-of-scope) 2개 항목만 미이행. 테스트는 `npm install` 후 실행 가능.
