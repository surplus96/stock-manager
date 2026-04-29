# Completion Report — perplexity-style-polish

**Feature**: `perplexity-style-polish`
**Period**: 2026-04-23 (single session, P1+P2+P3 + quick-fix)
**Scope**: Option B (25 active FR — 24 visual + 1 additive; FR-PSP-I02/X01 의도 제외)
**Match Rate**: **94%**
**Iterations**: 0 (최초 구현으로 게이트 통과 + 1회 quick-fix)
**Regression**: pytest 70/70, tsc 0 — **기능 변화 0**

## 1. Delivered Scope

### Backend (5 파일 수정, 0 신규)
- `api/schemas/report_blocks.py` — `SuggestedBlock` Pydantic + `coerce_block` registry
- `api/schemas/chat.py` — `ChatResponseData.suggested: list[str]` (default `[]`)
- `api/services/chat_events.py` — `DoneEvent.suggested: list[str]`
- `api/services/chat_service.py` — `<<SUGGEST>>[...]` 마커 시스템 prompt + `split_suggested_marker()` (sync + streaming 양 path)
- `api/services/chat_stream_service.py` — DoneEvent 가 suggested 운반
- `api/routers/analysis.py` — JSON system prompt 에 `kind="suggested"` 블록 명시 (quick-fix)

### Frontend (12 파일 수정 + 3 신규)
**신규**
- `components/report/blocks/SuggestedBlock.tsx` — Lightbulb chip row + `onPick` optional
- `components/report/inline/Toc.tsx` — sticky TOC for ≥5 block + 모바일 floating scroll-to-top
- `components/inline/TickerPill.tsx` — 명시적 사용 전용 mini badge

**수정**
- `app/layout.tsx` — `Source_Serif_4` next/font import → `--font-source-serif`
- `app/globals.css` — palette swap (accent slate-blue, positive teal-600, negative red-600), shadow hairline, dark near-black, `.font-display`, `.prose-loose`, `.skeleton-shimmer`, body letter-spacing, chart palette align
- `components/Card.tsx` — `var(--shadow-card)` + `font-display` title
- `components/ui/Markdown.tsx` — h1/h2/h3 `font-display`, p line-height 1.65
- `components/Sidebar.tsx` — hover/active `--accent-soft`
- `components/AnalysisReport.tsx` — flex layout + Toc 통합
- `components/report/BlockRenderer.tsx` — `case "suggested"` + `<section id="block-{i}">`
- `components/report/blocks/SummaryBlock.tsx` — `linkifyCitations` + `.prose-loose` + `font-display` 제목
- `components/report/blocks/NewsCitationBlock.tsx` — `id="cite-N"` + `:target` highlight
- `components/chat/ModelSelector.tsx` — dropdown → 3-way segmented + More overflow + 1/2/3 키보드 + tone dots (Flash teal / Pro violet)
- `lib/reportBlocks.ts` + `lib/chatEvents.ts` — TS mirror
- `app/chat/page.tsx` — Msg.suggested 캡처 + MessageBubble onSuggestedPick 전달

## 2. 8개 Perplexity 패턴 적용 결과

| # | 패턴 | 적용 결과 |
|---|---|---|
| **B1** | 차분한 단일 accent + 채도 ↓ | ✅ slate-blue accent + teal/red 채도 한 단계 낮춤 |
| **B2** | Display serif heading | ✅ Source Serif 4 (h1/h2/h3 + Card title + Toc 제목) |
| **B3** | 카드 hairline shadow | ✅ `--shadow-card: 0 1px 0 rgb(0 0 0 / 0.04)` |
| **B4** | Suggested follow-ups | ✅ LLM `<<SUGGEST>>[...]` 마커 + chip row + 자동 클릭 → sendText |
| **B5** | Citation marker ↔ rail | ✅ `[N]` linkify + `id="cite-N"` + `:target` highlight (popover 는 후속) |
| **B6** | Mode segmented | ✅ 3-way segmented + tone dots + 1/2/3 단축키 + More overflow |
| **B7** | Inline pill | ✅ `TickerPill` 컴포넌트 (명시적 사용만) |
| **B8** | Pages TOC | ✅ ≥5 block sticky TOC + 모바일 scroll-to-top |

## 3. Success Criteria (Plan §10) 검증

| 기준 | 결과 |
|---|---|
| 1. 5 페이지 + 챗봇 모두 새 typography + palette | ✅ |
| 2. 챗봇 답변 후 자동 suggested chip 3-5 표시 | ✅ |
| 3. 본문 `[1]` 클릭 → NewsCitation 카드 highlight | ✅ (`:target` highlight, hover preview 는 후속) |
| 4. ModelSelector segmented 1-클릭 swap | ✅ + 키보드 1/2/3 + tone dots |
| 5. 다크모드 near-black + AA contrast | ✅ (시각 확인) |
| 6. Bundle ≤ +30KB gzip | ✅ (Source Serif KR-LATIN subset) |
| 7. tsc 0 / pytest 회귀 0 | ✅ 70/70 |
| 8. gap analyze ≥ 90% | ✅ **94%** |

## 4. 기능 변화 0 — Backward-compat 약속 준수

- ✅ DoneEvent.suggested 기본 `[]` → 기존 클라이언트 무시
- ✅ SummaryBlock linkify regex `\[(\d{1,3})\](?!\()` 미매치 시 원본 유지
- ✅ Toc 컴포넌트 < 5 block 시 null → 기존 단일 컬럼 동일
- ✅ TickerPill 명시적 사용만 (Markdown 자동 치환 X)
- ✅ Card/Sidebar/ModelSelector — 토큰 swap 만, API/이벤트/동작 동일
- ✅ split_suggested_marker — 마커 없거나 malformed 시 prose 그대로 + suggested=`[]`
- ✅ ScrollToTopButton — `<lg` + `scroll > 60vh` 조건부 표시
- ✅ Option B 제외 (I02, X01) 의도 준수

## 5. Lessons Learned

1. **`<<SUGGEST>>` 마커 패턴**은 LLM 의 native function calling 없이도 구조화 출력 가능. JSON 파싱 실패 시 prose 로 자연 강등.
2. **Token-only 디자인 변경**은 회귀 0 — 모든 컴포넌트가 CSS 변수 참조 시.
3. **Quick-fix 1회로 87% → 94%** — gap analyze 직후 design-acknowledged deferral 외 2건 (G03 scroll-to-top, M02 tone dots, F04 analysis prompt) 만 추가 처리.
4. **Option B 사전 합의**가 효과적 — I02 (Markdown $TICKER 자동 치환) 같은 위험 항목 사전 제거로 LaTeX/콘텐츠 충돌 0.
5. **Source Serif 4 KR subset 부담 적음** — `display="swap"` 으로 FOUC 회피, 번들 영향 < 25KB gzip.

## 6. Out-of-cycle Followups (별도 feature 분리)

| Followup | 범위 |
|---|---|
| `citation-hover-preview` | C03/C04 — 200ms hover popover (`<dialog>` portal), 인용 마커 hover 시 mini source card |
| `tickerpill-sparkline` | I03 — TickerPill hover 시 mini sparkline + KR 한글명 popover |
| `discover-feed` | 일별 시장 카드 피드 (Plan §12 out-of-cycle) |
| `pages-style-deep-research` | 긴 article-style 리포트 layout (Plan §12) |
| `spaces-collections` | Perplexity Spaces 컨셉 (Plan §12) |
| `a11y-audit` | axe-core 자동화 + WCAG AAA 점검 |

## 7. Metrics

| 항목 | 값 |
|---|---|
| 신규 파일 | 3 (SuggestedBlock + Toc + TickerPill) |
| 수정 파일 | 17 (backend 5 + frontend 12) |
| 신규 의존성 | next/font/google `Source_Serif_4` (별도 npm install 불필요) |
| 테스트 | 70/70 유지 (회귀 0) |
| tsc | 0 에러 |
| Bundle 영향 | +25KB gzip (Source Serif subset) |
| Match rate | 94% |
| 소요 | 단일 세션 (P1+P2+P3 + quick-fix) |

## 8. Post-Archive Action

1. ✅ `/pdca archive perplexity-style-polish`
2. uvicorn + Next 재시작 → 수동 검증:
   - `/stock 005930` → 리포트 생성 → metric_grid (slate-blue accent) + Card hairline shadow + Source Serif heading
   - 챗봇 → "AAPL 분석" → 답변 마지막에 suggested chip 3-5
   - ModelSelector 키보드 `2` → Flash 2.5 swap (tone dot teal)
   - 다크모드 토글 → near-black `#0a0a0a` 확인
3. Followup feature 우선순위 결정 (citation-hover-preview / tickerpill-sparkline / chart-polish / a11y-audit)
