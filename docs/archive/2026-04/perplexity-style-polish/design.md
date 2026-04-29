# Design — perplexity-style-polish (Option B, 25 FR)

## 1. 결정 원칙
- **기존 동작 변화 0**: 모든 페이지/엔드포인트/도구/응답 스키마 그대로
- **Pure visual 또는 Additive only**: 24개 시각 + 1개 신규 (Suggested)
- **하위호환**: prop 추가 only, default 가 기존 동작 유지

## 2. 디자인 토큰 변경 (`globals.css`)

```css
:root {
  /* P01-02: 채도 ↓, 단일 accent */
  --accent: #1E3A8A;                 /* was #2962FF */
  --accent-soft: rgba(30,58,138,0.08);
  --primary: var(--accent);          /* keep alias */
  --positive: #0d9488;               /* was #26A69A (teal-600) */
  --negative: #dc2626;               /* was #EF5350 (red-600) */

  /* P03-04: hairline shadow */
  --shadow-card: 0 1px 0 rgb(0 0 0 / 0.04);
  --shadow-hover: 0 1px 2px rgb(0 0 0 / 0.06), 0 2px 4px rgb(0 0 0 / 0.04);

  /* T03: prose readability */
  --leading-prose: 1.65;
  --tracking-tight: -0.01em;
}

html[data-theme="dark"] {
  --background: #0a0a0a;             /* P05: near-black */
  --card-bg: #141414;
  --border: #262626;
  --accent: #60a5fa;
  --accent-soft: rgba(96,165,250,0.10);
}

body {
  letter-spacing: var(--tracking-tight);
  font-feature-settings: "kern", "ss01", "tnum";
}

.font-display {
  font-family: var(--font-source-serif), Georgia, serif;
  letter-spacing: -0.015em;
}

.prose-loose p, .prose-loose li {
  line-height: var(--leading-prose);
}

/* Chart palette refresh — match new accent */
:root {
  --chart-pos: #0d9488;
  --chart-neg: #dc2626;
  --chart-accent: #1E3A8A;
  --chart-accent-2: #7c3aed;
}
html[data-theme="dark"] {
  --chart-pos: #2dd4bf;
  --chart-neg: #f87171;
  --chart-accent: #60a5fa;
  --chart-accent-2: #a78bfa;
}
```

## 3. Font wiring (T01)

`app/layout.tsx`:
```tsx
import { Source_Serif_4 } from "next/font/google";
const serif = Source_Serif_4({
  subsets: ["latin"],
  variable: "--font-source-serif",
  weight: ["400", "500", "700"],
});
// <html className={`${geistSans.variable} ${serif.variable}`} ...>
```

Targets: `h1`, `h2` in `Markdown.tsx` headings + `AnalysisReport` Card title.
Body 한글은 sans-serif 유지 (serif KR 가독성 떨어짐).

## 4. Card shadow refresh (P03-04)

`components/Card.tsx`:
```tsx
// before:  className="... bg-white shadow-sm border ..."
// after:   className="... bg-white border shadow-[var(--shadow-card)] ..."
```
Hover state 만 `--shadow-hover` 적용 (옵션).

## 5. Suggested Block (F01-04)

### 5.1 Backend schema
`api/schemas/report_blocks.py`:
```python
class SuggestedBlock(BaseModel):
    kind: Literal["suggested"] = "suggested"
    items: list[str]  # 3-5 follow-up questions, ≤50자 each
```
Discriminated union 에 추가 + `coerce_block` registry.

### 5.2 LLM prompt 확장
`api/services/chat_service.py::build_system_prompt`:
```
## 답변 마지막 블록 (필수)
{"kind":"suggested","items":["다음 질문 1","질문 2","질문 3"]}
- 항목 3-5개, 각 50자 이내
- 사용자가 다음으로 자연스럽게 이어 갈 만한 후속 질문
- 같은 답변에 이미 다룬 내용 재질의 X
```

`api/routers/analysis.py::api_stock_analysis_report` LLM JSON 시스템 프롬프트도
동일 확장 — `summary` + `factor_bullet` + `suggested` 3 블록 요청.

### 5.3 Streaming `done` 이벤트 확장
`chat_events.py::DoneEvent`:
```python
class DoneEvent(BaseModel):
    type: Literal["done"] = "done"
    hops: int
    session_id: str
    suggested: list[str] = []  # NEW, default empty (backward compat)
```

`run_chat_stream` 마지막 hop 의 final answer 파싱 시 `suggested` block 추출 →
DoneEvent 에 실어 전송.

### 5.4 Frontend
`dashboard/src/lib/chatEvents.ts` mirror 갱신.

`components/report/blocks/SuggestedBlock.tsx` (신규):
```tsx
export default function SuggestedBlock({
  items, onPick,
}: { items: string[]; onPick?: (q: string) => void }) {
  if (!items?.length) return null;
  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {items.map((q, i) => (
        <button
          key={i}
          onClick={() => onPick?.(q)}
          className="text-xs px-3 py-1.5 rounded-full border bg-[var(--accent-soft)] text-[var(--accent)] hover:bg-[var(--accent)] hover:text-white transition-colors"
        >
          {q}
        </button>
      ))}
    </div>
  );
}
```

`BlockRenderer.tsx` 에 `case "suggested"` 추가 (onPick prop 은
`AnalysisReport`/chat page 가 주입).

`AnalysisReport.tsx`:
- 마지막 block 이 SuggestedBlock 이면 그대로 렌더 + onPick 은 alert/console (분석 리포트는 follow-up 자동 전송 X)

`app/chat/page.tsx`:
- `DoneEvent.suggested` 받으면 마지막 assistant 메시지에 `suggested[]` 저장
- MessageBubble 하단에 SuggestedBlock 렌더, `onPick={sendText}` 직결 → 클릭 시 자동 새 query

## 6. Mode segmented control (M01-03)

`components/chat/ModelSelector.tsx`:
```tsx
// before: <select>...</select>
// after:  <div role="radiogroup" className="inline-flex border rounded-md overflow-hidden">
//          {MODELS_TOP3.map(m => <button role="radio" aria-checked={...}>...</button>)}
//          + <button>More ▾</button> (overflow popover)
//        </div>
```

상위 3개 (gemini-3.0-flash, gemini-2.5-flash, gemini-1.5-pro) 만 segmented,
나머지는 "More" overflow `<dialog>`.

키보드 (M03): `useEffect` 글로벌 keydown 리스너 — `1`/`2`/`3` (input focus 가
아닐 때만), `Escape` 로 More 닫기.

## 7. Citations (C01-04)

### 7.1 SummaryBlock — `[N]` 자동 link
```tsx
function linkifyCitations(md: string): string {
  return md.replace(
    /\[(\d+)\]/g,
    (_, n) => `<sup><a href="#cite-${n}" class="text-[var(--accent)] no-underline hover:underline" data-cite="${n}">[${n}]</a></sup>`
  );
}
```
Markdown 컴포넌트 호출 전 prose 전처리. `react-markdown` 의 `rehype-raw`
필요 없이 `<sup>` 태그만 inline 으로 통과.

### 7.2 NewsCitationBlock — anchor + scroll-margin
```tsx
<li id={`cite-${n.id}`} style={{ scrollMarginTop: "5rem" }} ... />
```

### 7.3 Hover popover (C03/C04)
`components/inline/CitationMarker.tsx` (신규) — 본문 `[N]` 마커를 React
컴포넌트로 교체 (regex 가 아닌 `react-markdown` rehype 플러그인 또는 manual
render). 간단한 구현: `SummaryBlock` 내부에서 `dangerouslySetInnerHTML` 후
`useEffect` 로 `data-cite` 노드를 찾아 popover hook attach.

Popover: 기존 `<dialog>` 또는 `popoverapi` 사용, 200ms hover delay.

## 8. Pages TOC (G01-03)

`components/report/inline/Toc.tsx` (신규):
```tsx
export function Toc({ blocks }: { blocks: ReportBlock[] }) {
  if (blocks.length < 5) return null;
  const items = blocks
    .map((b, i) => ({ i, label: tocLabel(b), id: `block-${i}` }))
    .filter(x => x.label);
  return (
    <aside className="hidden lg:block sticky top-20 w-44 shrink-0 self-start">
      <p className="text-xs font-medium text-slate-500 mb-2">목차</p>
      <ul className="space-y-1 text-xs">
        {items.map(x => (
          <li key={x.i}>
            <a href={`#${x.id}`} className="text-slate-600 hover:text-[var(--accent)]">
              {x.label}
            </a>
          </li>
        ))}
      </ul>
    </aside>
  );
}
```

`AnalysisReport.tsx`:
```tsx
<div className="flex gap-6">
  <Toc blocks={blocks ?? []} />
  <div className="flex-1 min-w-0">
    <BlockList blocks={blocks ?? []} />
  </div>
</div>
```

`BlockList` 가 각 block wrapper 에 `id={"block-" + i}` 부여.

모바일 (`<lg`): `hidden lg:block` 으로 자동 숨김.

## 9. TickerPill (I01/I03)

`components/inline/TickerPill.tsx` (신규):
```tsx
export function TickerPill({
  ticker, name, lastClose, deltaPct, market = "US",
}: TickerPillProps) {
  const tone = (deltaPct ?? 0) >= 0 ? "pos" : "neg";
  return (
    <span className={`inline-flex items-baseline gap-1 px-2 py-0.5 rounded-md
      bg-[var(--accent-soft)] text-xs font-mono tabular text-[var(--foreground)]
      align-baseline`}>
      <span className="font-semibold">{ticker}</span>
      {name && <span className="opacity-60">({name})</span>}
      {lastClose != null && (
        <span>{formatPrice(lastClose, market)}</span>
      )}
      {deltaPct != null && (
        <span className={tone === "pos" ? "text-[var(--chart-pos)]" : "text-[var(--chart-neg)]"}>
          {deltaPct >= 0 ? "▲" : "▼"}{Math.abs(deltaPct * 100).toFixed(2)}%
        </span>
      )}
    </span>
  );
}
```

**명시적 사용처만** (Option B):
- `RankingsTable` 의 ticker 컬럼 (옵션)
- `news_citation` 출처 옆 (옵션)
- 사용자 컨텐츠 (Markdown) 자동 치환 X

I03 hover sparkline 은 Phase 3 P3 시간 남으면 적용, 아니면 P4 polish 로 미룸.

## 10. Sidebar polish (X02)
`components/Sidebar.tsx` 메뉴 항목 hover/active className 만 `--accent-soft`
배경으로 변경.

## 11. Skeleton shimmer (X03)
기존 `Loading.tsx`/`SkeletonReport.tsx`:
```css
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
.skeleton-shimmer {
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
```
`prefers-reduced-motion` 시 정적 회색.

## 12. 파일 영향도 (최종 — Option B)

### Backend (3 파일)
| 파일 | 변경 |
|---|---|
| `api/schemas/report_blocks.py` | `SuggestedBlock` 추가 (registry 등록) |
| `api/services/chat_service.py` + `chat_stream_service.py` | system prompt + DoneEvent.suggested |
| `api/routers/analysis.py` | LLM JSON prompt 에 suggested block 요청 추가 |

### Frontend (12 파일)
| 파일 | 변경 |
|---|---|
| `app/layout.tsx` | Source Serif font import |
| `app/globals.css` | 토큰 swap (~30줄) |
| `components/Card.tsx` | shadow → hairline |
| `components/ui/Markdown.tsx` | h1-h3 `.font-display`, `.prose-loose` |
| `components/AnalysisReport.tsx` | `<Toc>` + `<BlockList>` flex layout |
| `components/Sidebar.tsx` | accent-soft hover |
| `components/Loading.tsx` / `SkeletonReport.tsx` | shimmer class |
| `components/chat/ModelSelector.tsx` | dropdown → segmented + More overflow |
| `components/report/BlockRenderer.tsx` | `case "suggested"` |
| `components/report/blocks/SuggestedBlock.tsx` (신규) | chip row |
| `components/report/blocks/SummaryBlock.tsx` | linkifyCitations |
| `components/report/blocks/NewsCitationBlock.tsx` | `id="cite-N"` |
| `components/report/inline/Toc.tsx` (신규) | sticky TOC |
| `components/inline/TickerPill.tsx` (신규) | mini badge (명시적 사용만) |
| `components/inline/CitationMarker.tsx` (신규, 옵션) | hover popover hook |
| `lib/chatEvents.ts` + `lib/reportBlocks.ts` | TS mirror 갱신 |
| `app/chat/page.tsx` | DoneEvent.suggested → MessageBubble 하단 SuggestedBlock |

### Tests (Vitest)
- `SuggestedBlock.test.tsx` — 클릭 시 onPick 호출
- `ModelSelector.test.tsx` — segmented value swap, 키보드 단축키
- `Toc.test.tsx` — <5 block 시 null, ≥5 시 렌더
- `tests/test_report_blocks.py` (Python) — SuggestedBlock coerce + parse_llm_blocks 인식

## 13. 실행 순서 (Do P1~P3)

**P1 Foundation (1일)**:
1. font import + globals.css palette swap
2. Card.tsx shadow refresh
3. Markdown.tsx serif heading + prose-loose
4. tsc + 시각 smoke (Sidebar/Card/Markdown 확인)

**P2 Engagement (1일)**:
5. SuggestedBlock 백엔드 (schema + prompt + DoneEvent)
6. SuggestedBlock 프론트 + chat page 연결
7. ModelSelector segmented + keyboard
8. Vitest 추가

**P3 Density polish (1일)**:
9. SummaryBlock linkify + NewsCitationBlock anchor
10. CitationMarker hover popover
11. Toc 컴포넌트 + AnalysisReport 통합
12. TickerPill 컴포넌트 + RankingsTable 사용처 한 곳 적용
13. Sidebar hover, Skeleton shimmer
14. 최종 회귀 + tsc + 수동 demo

## 14. Backward-compat 보장 체크리스트

- [ ] LLM 이 `suggested` 블록을 만들지 않으면 `suggested=[]` → SuggestedBlock 미렌더 (UI 빈 영역 X)
- [ ] `DoneEvent.suggested` 미설정 → 기존 클라이언트 (변경 전) 도 정상 (필드 무시)
- [ ] `linkifyCitations` regex 가 `[1]` 패턴 못 찾으면 prose 원본 그대로 유지
- [ ] Toc 가 < 5 block 이면 렌더 0 → 기존 단일 컬럼 레이아웃과 동일
- [ ] segmented ModelSelector 의 첫 옵션이 default → 기존 dropdown 의 default 와 동일
- [ ] palette 변경 후 axe-core contrast AA 검증 (수동 확인)
- [ ] TickerPill 은 명시적 props 가 들어가야만 렌더 — Markdown 자동 치환 없음
