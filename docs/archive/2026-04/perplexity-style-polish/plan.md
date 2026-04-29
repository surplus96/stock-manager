# Plan — perplexity-style-polish

> **Goal**: Perplexity 의 시그니처 디자인 패턴 8가지를 우리 도메인(금융 분석
> 대시보드 + 챗봇)에 맞게 적응 적용해 **전문성 + 가독성 + retention** 을 한
> 단계 끌어올린다. 코드 리팩토링 X, 시각·인터랙션 폴리시 중심.

## 1. Background

### 1.1 현재 상태 (v3.0, 2026-04-23 기준)
- 5 분석 페이지 (`/`, `/stock`, `/portfolio`, `/ranking`, `/theme`) + `/chat`
- 11종 ReportBlock (rich-visual-reports 완료) + Markdown fallback
- Sidebar nav + ThemeToggle + ChatHeader + framer-motion stagger
- CSS palette: light/dark 9 chart vars, accent `#2962FF`(채도 높음)
- 챗봇: SSE 스트리밍 + 13 도구 + ⌘K 팔레트 + 4-6 빠른시작 chip

### 1.2 이슈
- accent 색이 selling-trade SaaS 느낌 (전문 analyst 도구 톤 부족)
- 카드 shadow 가 두드러져 시각 노이즈
- sans-only 타이포 → display heading 위계 약함
- 챗봇 답변 후 "다음 액션" 가이드 없음 → 단발성 사용
- 인용 번호는 있으나 본문 ↔ source 연결 약함
- ModelSelector 가 dropdown 1개 → 인지 비용

### 1.3 Perplexity 가 잘하는 8가지 (벤치마킹 대상)

| # | 패턴 | 핵심 |
|---|---|---|
| **B1** | 차분한 단일 accent + 채도 낮춤 | 전문성, 색 노이즈 ↓ |
| **B2** | Display serif heading + body sans | 위계, 우아함 |
| **B3** | 카드 shadow 약화, 1px border 위주 | 종이 질감, 시선 흐름 ↑ |
| **B4** | 답변 하단 Suggested follow-ups (3-5 chips) | retention, 다음 액션 유도 |
| **B5** | 인용 marker hover preview + ↔ rail highlight | 정보 밀도 ↑ |
| **B6** | Mode segmented control (Auto/Pro/Deep) | 인지 비용 ↓ |
| **B7** | Inline pill widget (`AAPL ▲2.3%`) | analyst feel, 본문 임베드 |
| **B8** | Pages-style TOC (긴 리포트) | navigation |

## 2. Scope

### 2.1 In scope (이번 사이클 8개 모두)
- 8개 패턴 전부 우리 페이지/컴포넌트에 적용
- 새 디자인 토큰 셋 (`design-tokens.md` 같은 별도 문서 없이 globals.css 만)
- vitest 단위 테스트 (변경된 컴포넌트 위주)

### 2.2 Out of scope (다음 사이클)
- 다국어 추가 (한국어 only 유지)
- 모바일 햅틱/사운드
- A11y axe-core 자동화 (별도 `a11y-audit` feature)
- 차트 자체 시각 개편 (이미 rich-visual-reports 에서 처리)
- 새 기능 추가 (예: Perplexity Spaces 같은 컬렉션 — 별도 feature)

## 3. Functional Requirements (FR-PSP)

### A. Typography & Density (FR-PSP-T)

| ID | 요구사항 | 우선 | 패턴 |
|---|---|---|---|
| **FR-PSP-T01** | Display serif font (`Source Serif 4` 또는 `Lora`) `next/font/google` 임포트, h1/h2/AnalysisReport 제목에 적용 | High | B2 |
| **FR-PSP-T02** | body sans 유지 (Geist), but tighten letter-spacing `-0.01em` for paragraphs | High | B12 |
| **FR-PSP-T03** | line-height 1.5 → **1.65** for prose blocks (`.prose-sm`, SummaryBlock) | High | B12 |
| **FR-PSP-T04** | 페이지 vertical spacing — `space-y-6` → `space-y-8`, card padding `p-3/p-4` → `p-4/p-5` 통일 | High | B12 |

### B. Palette & Surfaces (FR-PSP-P)

| ID | 요구사항 | 우선 | 패턴 |
|---|---|---|---|
| **FR-PSP-P01** | accent color `#2962FF` → **`#1E3A8A`** (slate-blue-900, 채도 ↓) — light/dark 모두 | High | B1 |
| **FR-PSP-P02** | secondary/positive/negative 채도 한 단계 낮춤 (`#10b981` → `#0d9488` teal, `#ef4444` → `#dc2626` red-600) | High | B1 |
| **FR-PSP-P03** | `--shadow-card` 약화 — `0 1px 2px rgb(0 0 0 / 0.04)` → `0 1px 0 rgb(0 0 0 / 0.04)` (top-only hairline) | High | B3 |
| **FR-PSP-P04** | 카드 border `1px solid var(--border)`, shadow 거의 invisible — 종이 느낌 | High | B3 |
| **FR-PSP-P05** | dark mode bg `#0b1220` → **`#0a0a0a`** (Perplexity-style near-black), surface `#111a2b` → `#141414` | Medium | B1 |
| **FR-PSP-P06** | `--accent-soft` 신규 — `rgba(30,58,138,0.08)` for hover/selected backgrounds | Medium | B1 |

### C. Citations & Source Rail (FR-PSP-C)

| ID | 요구사항 | 우선 | 패턴 |
|---|---|---|---|
| **FR-PSP-C01** | `SummaryBlock` 본문의 `[1]` `[2]` 마커 자동 탐지 → `<a href="#cite-N">` 링크 + accent color | Medium | B5 |
| **FR-PSP-C02** | `NewsCitationBlock` 각 항목에 `id="cite-{N}"` anchor + scroll-margin-top | Medium | B5 |
| **FR-PSP-C03** | 인용 마커 hover → 200ms 딜레이 후 mini popover (제목 + 출처 + date) | Medium | B5/B9 |
| **FR-PSP-C04** | popover는 `<dialog>` 또는 portal 기반 (overflow 안 잘림) | Medium | B9 |

### D. Suggested Follow-ups (FR-PSP-F)

| ID | 요구사항 | 우선 | 패턴 |
|---|---|---|---|
| **FR-PSP-F01** | Backend: 챗봇 응답 마지막에 `suggested: string[]` 필드 추가 (LLM 이 3-5개 다음 질문 생성) | High | B4 |
| **FR-PSP-F02** | `parse_llm_blocks` 가 `{"kind":"suggested","items":[...]}` block kind 도 인식 | High | B4 |
| **FR-PSP-F03** | Frontend `SuggestedBlock` 컴포넌트 — chip row, 클릭 시 `sendText` 자동 호출 | High | B4 |
| **FR-PSP-F04** | 답변 마지막에 자동 표시 — 챗 페이지 + AnalysisReport 둘 다 | High | B4 |

### E. Mode Segmented Control (FR-PSP-M)

| ID | 요구사항 | 우선 | 패턴 |
|---|---|---|---|
| **FR-PSP-M01** | `ModelSelector` dropdown → segmented control (3-way: Flash 3.0 / Flash 2.5 / Pro 1.5) | Medium | B6 |
| **FR-PSP-M02** | 선택 모델 색상 hint (Flash = teal, Pro = violet) | Low | B6 |
| **FR-PSP-M03** | 키보드 단축키 — `1/2/3` for model swap (focus 가 input 아닐 때) | Low | B6 |

### F. Inline Pills (FR-PSP-I)

| ID | 요구사항 | 우선 | 패턴 |
|---|---|---|---|
| **FR-PSP-I01** | `<TickerPill ticker="AAPL" />` 컴포넌트 — small badge with ticker + last close + delta arrow | Medium | B7/B11 |
| ~~FR-PSP-I02~~ | ~~Markdown 컴포넌트 `$AAPL` 자동 치환~~ | **제외 (Option B)** | LaTeX 충돌 + LLM 프롬프트 영향 우려로 명시적 사용처에서만 |
| **FR-PSP-I03** | hover 시 mini sparkline + 한글명 popover (KR 종목) | Low | B11 |

### G. Pages-style TOC (FR-PSP-G)

| ID | 요구사항 | 우선 | 패턴 |
|---|---|---|---|
| **FR-PSP-G01** | AnalysisReport 가 5개 이상 block 보유 시 좌측 sticky TOC (anchor 링크) 자동 생성 | Low | B8 |
| **FR-PSP-G02** | TOC 항목: SummaryBlock title, MetricGrid → "주요 지표", Candlestick → "가격", NewsCitation → "뉴스" | Low | B8 |
| **FR-PSP-G03** | 모바일 (<md) → TOC 숨김, scroll-to-top 버튼만 | Low | B8 |

### H. Polish (FR-PSP-X)

| ID | 요구사항 | 우선 | 패턴 |
|---|---|---|---|
| ~~FR-PSP-X01~~ | ~~EmptyState Discover topic cards~~ | **제외 (Option B)** | 기존 quick-start chip UX 변경 회피 |
| **FR-PSP-X02** | Sidebar 항목 hover → accent-soft bg (subtle) | Low | Polish |
| **FR-PSP-X03** | Loading skeleton — pulse → shimmer animation 전환 | Low | Polish |

## 4. Non-Functional

- **성능**: bundle 증가 ≤ +30KB gzip (serif font subset KR + LATIN, 1 컴포넌트 추가)
- **A11y**: 모든 interactive (citation popover, pill hover) 키보드 접근 가능
- **하위호환**: 기존 컴포넌트 props 변경 X — extension-only
- **다크모드**: 전 변경에서 light/dark 동시 검증
- **Reduced motion**: 새 애니메이션 (popover, segmented swap) 도 `prefers-reduced-motion` 존중

## 5. Phased Roadmap — Option B 25 FR (3일)

> **Option B 결정 (2026-04-23)**: FR-PSP-I02 (Markdown 자동 치환) 와
> FR-PSP-X01 (Discover EmptyState) 는 기존 사용자 UX 보존 차원 제외.
> 25 FR 중 24개 pure visual + 1개 additive (Suggested) → **기존 동작 변화 0**.

| Phase | 범위 | FR | 일수 |
|---|---|---|---|
| **P1 Foundation** | Typography + density + palette | FR-PSP-T01..04, P01..06 (10개) | 1일 |
| **P2 Engagement** | Suggested follow-ups + Mode segmented | FR-PSP-F01..04, M01..03 (7개) | 1일 |
| **P3 Density polish** | Citations + inline pills (명시적 사용) + Pages TOC + Polish | FR-PSP-C01..04, I01/I03, G01..03, X02/X03 (8개) | 1일 |

### Option B 제외 항목 (의도적 미구현)
- **FR-PSP-I02** Markdown `$TICKER` 자동 치환 — LLM 답변 내 LaTeX/달러 표기 충돌 가능 + 사용자 콘텐츠 의도치 않은 변환 위험 → TickerPill 은 만들되 명시적 block 렌더러 내부에서만 사용
- **FR-PSP-X01** Discover-style EmptyState — 기존 6개 quick-start chip 의 명확한 UX 유지

## 6. Architecture / 파일 영향도

### Backend (3 파일)
| 파일 | 변경 |
|---|---|
| `api/services/chat_service.py` | system prompt 에 "마지막에 suggested:[3-5 follow-ups] 추가" 지시 |
| `api/services/chat_stream_service.py` | 응답 객체에 `suggested: list[str]` 필드 (LLM JSON parse 결과 활용) |
| `api/services/report_builder.py` | `SuggestedBlock` Pydantic + `parse_llm_blocks` 가 `kind="suggested"` 인식 |
| `api/schemas/report_blocks.py` | `SuggestedBlock` discriminated union 추가 |

### Frontend (10+ 파일)
| 파일 | 변경 |
|---|---|
| `app/layout.tsx` | `next/font/google` 로 `Source_Serif_4` import |
| `app/globals.css` | typography (line-height 1.65, letter-spacing), palette swap, shadow 약화, accent-soft, dark near-black |
| `components/ui/Markdown.tsx` | h1-h3 serif font 적용, `$TICKER` regex → `<TickerPill>` |
| `components/Card.tsx` | shadow 클래스 제거, border-only |
| `components/report/blocks/SummaryBlock.tsx` | `[N]` 자동 link + cite-N anchor |
| `components/report/blocks/NewsCitationBlock.tsx` | `id="cite-N"` + scroll-margin |
| `components/report/blocks/SuggestedBlock.tsx` (신규) | follow-up chip row |
| `components/inline/TickerPill.tsx` (신규) | small badge with ticker + delta |
| `components/inline/CitationMarker.tsx` (신규) | `<sup><a [N]>` + hover popover |
| `components/chat/ModelSelector.tsx` | dropdown → segmented (3-way) |
| `components/AnalysisReport.tsx` | suggested 영역 + (옵션) TOC sidebar |
| `components/report/inline/Toc.tsx` (신규) | sticky TOC for ≥5 block |
| `app/page.tsx`, `chat/page.tsx`, etc. | EmptyState — Discover-style topic cards |

### CSS Token diff (예시)
```css
:root {
  --accent: #1E3A8A;              /* was #2962FF */
  --accent-soft: rgba(30,58,138,0.08);
  --positive: #0d9488;            /* was #26A69A */
  --negative: #dc2626;            /* was #EF5350 */
  --shadow-card: 0 1px 0 rgb(0 0 0 / 0.04);  /* was 2-shadow */
}
html[data-theme="dark"] {
  --background: #0a0a0a;          /* was #0b1220 */
  --card-bg: #141414;             /* was #111a2b */
  --accent: #60a5fa;              /* lighter for dark */
  --accent-soft: rgba(96,165,250,0.10);
}
body {
  font-family: var(--font-geist-sans);  /* keep */
  letter-spacing: -0.005em;
}
.prose-sm p { line-height: 1.65; }
h1, h2, h3 {
  font-family: var(--font-source-serif), Georgia, serif;
  letter-spacing: -0.01em;
}
```

## 7. 의존성 추가
- `next/font/google` (이미 next 빌드에 포함, dep 추가 X)
- `Source_Serif_4` 또는 `Lora` (subset KR + LATIN, ~30KB gzip)

## 8. Tests

| 파일 | 케이스 |
|---|---|
| `tests/test_report_blocks.py` | `SuggestedBlock` coerce + parse_llm_blocks recognizes `kind=suggested` |
| `dashboard/src/components/report/blocks/__tests__/SuggestedBlock.test.tsx` | 클릭 시 onPick 호출 |
| `dashboard/src/components/inline/__tests__/TickerPill.test.tsx` | ticker + delta render, KR 통화 표기 |
| `dashboard/src/components/inline/__tests__/CitationMarker.test.tsx` | `[N]` 링크 + hover popover |
| `dashboard/src/components/chat/__tests__/ModelSelector.test.tsx` | segmented value swap, 키보드 단축키 |

## 9. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Serif 폰트 KR subset 무거움 | `next/font/google` 로 자동 subset, `display=swap` |
| Accent 색 변경이 brand identity 변경 | 사용자 요청에 따른 변경, 롤백은 globals.css 1줄 |
| Suggested follow-ups → LLM 출력 토큰 ↑ | 프롬프트에 "JSON 끝에 5줄, 각 50자 이내" 강제 |
| TOC 가 모바일 UX 침해 | `<md` 에서 hide, scroll-to-top 만 |
| Inline TickerPill 정규식이 prose 내 `$AAPL$` 같은 LaTeX 와 충돌 | `\$[A-Z]{1,5}(\.[A-Z])?\b` strict regex + word boundary |
| ModelSelector segmented 3-way 가 5개 모델 다 못 표시 | 상위 3개만 segmented, 나머지는 "More" overflow |

## 10. Success Criteria

1. 5 페이지 + 챗봇 모두 새 typography + palette 적용 — 시각 일관성
2. 챗봇 답변 후 자동 suggested chip 3-5 개 표시
3. 본문 `[1]` 클릭 → NewsCitation 카드 highlight
4. ModelSelector segmented 로 1-클릭 모델 swap
5. 다크모드 near-black 적용, 모든 컴포넌트 contrast AA 유지
6. Bundle 증가 ≤ +30KB gzip
7. tsc 0 에러, pytest 회귀 0
8. `/pdca analyze` match rate ≥ 90%

## 11. Acceptance Demo

1. `/stock AAPL` → 리포트 생성 → metric_grid (slate-blue accent), serif heading, 카드 hairline shadow, 답변 하단 suggested 3 chip
2. 챗봇 → "AAPL 분석해줘" → 답변에 `$AAPL ▲1.2%` inline pill, `[1]` 클릭 시 NewsCitation 스크롤+highlight
3. ModelSelector → segmented Flash 3.0 / Flash 2.5 / Pro 1.5
4. 다크 모드 토글 → near-black bg, accent 부드럽게 swap
5. 빈 챗봇 페이지 → Discover-style 6 카드 (인기 KR 종목, US 테마)

## 12. Out-of-cycle Followups
- `pages-style-deep-research` — 긴 리포트 article layout (TOC + chapter nav)
- `discover-feed` — 일별 시장 변동 카드 피드
- `spaces-collections` — 사용자 종목 묶음 보관 (Perplexity Spaces 컨셉)
- `a11y-audit` — axe-core 자동화 (별도)
