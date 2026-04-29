---
template: plan
version: 1.2
feature: frontend-quality-upgrade
date: 2026-04-15
author: Stock Manager Team
project: Stock Manager (adoring-swartz)
status: Draft
---

# frontend-quality-upgrade Planning Document

> **Summary**: Stock Manager 대시보드(Next.js 16 App Router)의 타입 안정성, 접근성, 반응형, 성능, 디자인 일관성을 개선하여 사용자 경험과 유지보수성을 향상시킨다.
>
> **Project**: Stock Manager
> **Version**: 1.0 → 1.1
> **Author**: Stock Manager Team
> **Date**: 2026-04-15
> **Status**: Draft

---

## 1. Overview

### 1.1 Purpose

code-analyzer 점검 결과 도출된 프론트엔드 **20개 이슈 (High 4, Medium 9, Low 7)** 를 우선순위별로 해소하여 다음을 달성한다.

- 타입 안정성: `any` 제거, OpenAPI 기반 타입 자동 생성
- 접근성: WCAG 2.1 AA 준수 (키보드, 스크린 리더, 대비)
- 반응형: 모바일/태블릿/데스크톱 3단 대응 (고정 `ml-60` 제거)
- 성능: Next.js 16 Server Component 전환, Recharts 동적 import, 스켈레톤 UI
- 구조: 커스텀 마크다운 파서 → 검증된 라이브러리, 재사용 훅 도출

### 1.2 Background

code-analyzer 점검 결과(frontend) 주요 이슈:
- `dashboard/src/lib/api.ts:3-99` 모든 메서드 `Promise<any>` 타입 안전성 부재
- `dashboard/src/app/*/page.tsx` 5 pages 모두 `"use client"` 불필요 전역 사용, `useState<any>`
- `dashboard/src/components/AnalysisReport.tsx:39-58` 자체 마크다운 파서, toggle 버튼 a11y 누락(89-94)
- `dashboard/src/app/layout.tsx` 고정 `ml-60`, 반응형 breakpoints 부재

### 1.3 Related Documents

- 기획서: `docs/기획서_투자대시보드.md`
- 관련 병렬 Feature: `backend-quality-upgrade`
- Skills: `Skills.md`

---

## 2. Scope

### 2.1 In Scope

- [ ] 타입: `api.ts` 전 메서드 타입 도입, OpenAPI → TS 자동 생성(openapi-typescript)
- [ ] 접근성: 버튼/토글 aria-*, 포커스 링, 대비 AA, 키보드 내비
- [ ] 반응형: sidebar collapse, `md:`/`lg:` breakpoints, 차트 리플로우
- [ ] 성능: Server Component 적용 가능 페이지 전환, `next/dynamic` + `ssr:false` 로 Recharts 분리
- [ ] UX: 스켈레톤 UI, 에러 Toast 통일, 로딩 일관성
- [ ] 구조: `useAnalysisReport` 커스텀 훅 추출, 마크다운은 `react-markdown` + `remark-gfm`
- [ ] 디자인: Tailwind 디자인 토큰, 타이포 스케일, 컬러 시스템 통일
- [ ] 메타: Next.js 16 `metadata` API로 OG/title 관리
- [ ] 테스트: Vitest + RTL 핵심 컴포넌트 스냅샷/상호작용

### 2.2 Out of Scope

- 백엔드 API 변경 (별도 feature: `backend-quality-upgrade`)
- 디자인 리브랜딩 (대대적 UI 개편 제외)
- 신규 페이지 추가

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-F01 | `lib/api.ts` 의 모든 `Promise<any>` 제거 및 정확한 타입 부여 | High | Pending |
| FR-F02 | openapi-typescript 도입, 백엔드 스키마 기반 타입 자동 생성 | High | Pending |
| FR-F03 | `AnalysisReport` 토글 버튼 a11y 보완 (aria-expanded, role, keyboard) | High | Pending |
| FR-F04 | 전역 레이아웃 반응형 대응 (`ml-60` 제거, Sidebar collapse) | High | Pending |
| FR-F05 | `useState<any>` 전량 타입 지정 | Medium | Pending |
| FR-F06 | Recharts `next/dynamic` 로 code split | Medium | Pending |
| FR-F07 | 서버 컴포넌트 전환 가능한 페이지 식별 후 이동 | Medium | Pending |
| FR-F08 | `useAnalysisReport` 커스텀 훅 추출 (fetch+state+derived) | Medium | Pending |
| FR-F09 | 커스텀 마크다운 파서 → `react-markdown`+`remark-gfm` | Medium | Pending |
| FR-F10 | 에러/로딩 상태를 공통 `<AsyncBoundary>` 로 표준화 | Medium | Pending |
| FR-F11 | 스켈레톤 UI 적용 (dashboard/theme/analysis) | Medium | Pending |
| FR-F12 | 디자인 토큰(색상/타이포) Tailwind `theme.extend` 정의 | Medium | Pending |
| FR-F13 | Next.js `metadata` API 로 페이지별 title/OG 설정 | Medium | Pending |
| FR-F14 | 사이드바/모바일 햄버거 메뉴 | Low | Pending |
| FR-F15 | `<Image>` 최적화(원격 이미지 whitelist) | Low | Pending |
| FR-F16 | ESLint strict + `@typescript-eslint/no-explicit-any` 에러화 | Low | Pending |
| FR-F17 | 다크모드 지원(선택) - 토큰 선대응만 | Low | Pending |
| FR-F18 | Vitest + RTL 초기 환경 구성 | Low | Pending |
| FR-F19 | 핵심 컴포넌트 3개 테스트 추가 | Low | Pending |
| FR-F20 | 번들 사이즈 측정 (`@next/bundle-analyzer`) | Low | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|-------------------|
| Accessibility | WCAG 2.1 AA 준수 | axe-core, Lighthouse a11y ≥ 95 |
| Performance | LCP < 2.5s, TBT < 200ms, Recharts 분리 | Lighthouse, bundle-analyzer |
| Type Safety | `any` 사용 0 (api.ts/페이지) | eslint, tsc --noEmit |
| Responsiveness | 375/768/1280 3 해상도 정상 | 수동 + Playwright |
| UX | 로딩/에러 일관된 패턴 | 스크린샷 리뷰 |

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] High 우선 4개 이슈 100% 해소
- [ ] Medium 이슈 80%+ 해소
- [ ] `any` 사용 0 (핵심 경로)
- [ ] Lighthouse a11y ≥ 95, Performance ≥ 85 (desktop)
- [ ] code-analyzer 재점검 match rate ≥ 90%

### 4.2 Quality Criteria

- [ ] `eslint` 에러 0
- [ ] `tsc --noEmit` 에러 0
- [ ] 모바일 375 뷰 깨짐 없음
- [ ] 번들 사이즈 초기 페이지 < 250KB gzipped

---

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Server Component 전환 시 상태 의존 코드 회귀 | High | Medium | 페이지별 점진 전환 + 스냅샷 테스트 |
| OpenAPI 타입 자동화로 빌드 파이프라인 추가 | Medium | Medium | prebuild 스크립트, 캐시 |
| 마크다운 라이브러리 교체로 렌더 차이 | Medium | Medium | 시각 스냅샷, PR 단위 비교 |
| 반응형 재작업 범위 과대 | Medium | High | Sidebar/Layout만 우선, 페이지는 단계적 |

---

## 6. Architecture Considerations

### 6.1 Project Level Selection

| Level | Characteristics | Selected |
|-------|-----------------|:--------:|
| Starter | 단순 | ☐ |
| **Dynamic** | Feature + hooks + services | ☑ |
| Enterprise | 엄격 레이어 | ☐ |

### 6.2 Key Architectural Decisions

| Decision | Options | Selected | Rationale |
|----------|---------|----------|-----------|
| Framework | Next.js 16 App Router | **유지** | 기존 스택 |
| State Mgmt | useState / Zustand / Jotai | **useState + hooks** | 규모상 충분 |
| API Client | fetch / axios / react-query | **fetch + 얇은 래퍼** | 현재 구조 유지 |
| Markdown | 자체 / react-markdown | **react-markdown + remark-gfm** | 검증 + a11y |
| Styling | Tailwind 유지 + 토큰 | **Tailwind** | 기존 유지 |
| Testing | Jest / Vitest | **Vitest + RTL** | Next 16 호환 |

### 6.3 Folder Structure

```
dashboard/src/
  app/                 (App Router; 가능한 곳 Server Component)
  components/
    ui/                (디자인 시스템 primitive)
    analysis/
  features/
    analysis/
      useAnalysisReport.ts
  lib/
    api.ts             (typed)
    api.types.ts       (openapi-typescript 산출물)
  styles/
    tokens.ts
```

---

## 7. Convention Prerequisites

### 7.1 Existing Project Conventions

- [x] `dashboard/tsconfig.json`
- [x] `dashboard/eslint.config.*` (확인 필요)
- [ ] `CONVENTIONS.md` 없음
- [ ] 디자인 토큰 정의 없음

### 7.2 Conventions to Define/Verify

| Category | Current | To Define | Priority |
|----------|---------|-----------|:--------:|
| `any` 금지 규칙 | 미적용 | eslint error 화 | High |
| 컴포넌트 네이밍 | 혼재 | PascalCase, `Xxx.tsx` | Medium |
| Client 경계 | 과다 | "use client" 최소화 | High |
| 디자인 토큰 | 없음 | 컬러/타이포/스페이싱 | Medium |
| Import order | 미정 | eslint-plugin-import | Medium |

### 7.3 Environment Variables

| Variable | Purpose | Scope | To Be Created |
|----------|---------|-------|:-------------:|
| `NEXT_PUBLIC_API_BASE_URL` | 백엔드 URL | Client | ☑ (정비) |
| `NEXT_PUBLIC_ENABLE_ANALYTICS` | 옵트인 플래그 | Client | ☐ |

---

## 8. Next Steps

1. [ ] `/pdca design frontend-quality-upgrade`
2. [ ] 병렬 Feature `backend-quality-upgrade` 와 API 계약 동기화
3. [ ] Phase 1 착수 (High 4개)

### 8.1 Roadmap Phases

| Phase | 기간 | 포함 이슈 |
|-------|------|-----------|
| Phase 1 | 1주 | FR-F01~F04 (High 4) |
| Phase 2 | 2주 | FR-F05~F13 (구조/성능/UX) |
| Phase 3 | 2-3주 | FR-F14~F20 (품질/테스트) |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-04-15 | code-analyzer 20개 이슈 기반 초안 | Stock Manager Team |
