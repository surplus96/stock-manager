# Plan — rich-visual-reports

> **Goal**: 리포트 생성 기능과 챗봇 답변을 **Claude ShowMe 스타일의 구조화된 시각 답변**
> 으로 업그레이드하고, 차트 디자인을 retail-grade 에서 professional-grade 로 끌어올린다.
> "긴 마크다운 단일 블록" → "카드 + 인라인 차트 + 인용 + 요약 넘버" 구성으로 전환.

## 1. Background & 문제 정의

### 1.1 현황 (v2.0 archived 상태)

| 영역 | 현재 구현 | 한계 |
|---|---|---|
| **종목/테마/포트폴리오 LLM 리포트** | 300~500단어 한국어 **마크다운 텍스트** 한 덩어리 + 뉴스 5건 링크 | 스캔 불가, 수치 강조 약함, 시각적 단조 |
| **챗봇 답변** | Markdown 텍스트 + Inline 도구 호출 트레이스 펼침 | 도구 결과는 `summary` 문자열뿐 — 테이블/차트 없음 |
| **차트** | Recharts default (Area/Radar/Bar/Pie) — 4종 | 캔들스틱 없음, 볼륨 overlay 없음, 애니메이션 없음, 다크모드 팔레트 미세조정 부족, tooltip 정보 적음 |
| **평가 이유** | 정보 밀도 낮음, 사용자가 리포트를 "스크롤해서 읽는" 경험 | professional analyst tool (TradingView/Bloomberg) 대비 가독성 격차 |

### 1.2 Claude ShowMe 벤치마크 리서치

`ShowMe` 는 Anthropic 의 Skill 기반 기능으로, 답변에 **자동 생성된 SVG 일러스트·
다이어그램·플로우차트**를 인라인으로 삽입한다. 관찰된 패턴:

| ShowMe 패턴 | Stock Manager 에 적용할 수 있는 점 |
|---|---|
| **구조화된 답변 블록** (제목 + 수치 강조 + 코멘트 카드) | 리포트를 섹션별 카드로 쪼개고, 핵심 수치는 BigNumber 컴포넌트로 독립 표시 |
| **인라인 SVG 차트** (spark line, bar, 화살표 다이어그램) | 문장 중간에 mini candlestick / factor bullet 삽입 |
| **텍스트-비주얼 fusion** | "ROE 17.4% ↑" 옆에 작은 trend arrow, bubble, badge 를 같이 렌더 |
| **Progressive disclosure** | 상위 summary → 클릭 시 drilldown (확장) |
| **인용 하이퍼링크** | 뉴스 각 문장 끝에 `[출처]` 번호 → 우측 사이드 패널에 뉴스 카드 표시 |
| **JSON-first 출력** | LLM 에게 prose 대신 **구조화 JSON** 을 요청해 클라이언트가 렌더 — 안정성 + 재현성 |

### 1.3 기타 벤치마크

| 서비스 | 참고 포인트 |
|---|---|
| **TradingView** | 캔들스틱 + 거래량 overlay, 다중 지표 pane, drawing toolbar, 색감 |
| **Bloomberg Terminal (웹)** | 숫자 컬럼 monospace, high-density 표, 조밀한 헤더 |
| **Perplexity Finance** | 인용 chip, 수치 강조 카드, 관련 종목 미니 위젯 |
| **Claude.ai Artifacts** | 오른쪽 패널에 차트/표 분리, 대화와 결과물 공존 |
| **Robinhood / Toss 증권** | 색감 대비, 모바일 최적화, spark line 빈도 |
| **Apollo / Cursor 대시보드** | 카드 grid, 상단 KPI summary, 하단 detail |

## 2. Scope

### 2.1 In scope (이번 사이클)
- **리포트 구조화**: 4개 `*/analysis-report` 엔드포인트 응답에 `blocks[]` 필드 추가 — 섹션별 카드·수치·차트 스펙을 structured JSON 으로 반환
- **프론트 BlockRenderer**: `SummaryBlock`, `MetricCard`, `FactorBullet`, `NewsCitation`, `InlineChart`, `PriceSparkBlock`, `CandlestickBlock`, `TableBlock` 등 10여종 렌더러
- **챗봇 structured response**: tool_result 이벤트에 `artifact` 필드 신설 — 프론트가 즉시 차트/표로 렌더 (기존 summary string 유지 + 확장)
- **차트 고급화**: 캔들스틱 (volume overlay), 상관 히트맵 (annotations), 섹터 treemap, 멀티 지표 pane, 다크모드 전용 팔레트, 애니메이션 (framer-motion)
- **Inline viz 헬퍼**: `<Spark>`, `<Delta>`, `<Badge>`, `<BigNumber>`, `<Trend>` 경량 SVG 컴포넌트 (외부 라이브러리 없이)

### 2.2 Out of scope (후속)
- 실시간 스트리밍 차트 (WebSocket tick 반영) — P3 feature 별도
- 사용자 정의 dashboard layout (drag & drop) — 후속 cycle
- PDF export 스타일링 — 기획서 export 와 통합 별도
- TradingView Lightweight Charts 도입 — 의존성 추가 큼, 2차 사이클에 검토

## 3. Functional Requirements

### A. Backend: Structured output (FR-R-B)

| ID | 요구사항 | 우선 |
|---|---|---|
| **FR-R-B01** | `AnalysisReportPayload` 에 `blocks: ReportBlock[]` 필드 추가 (하위호환 — `summary` 문자열도 유지) | High |
| **FR-R-B02** | `ReportBlock` discriminated union (`kind` 필드): `summary`/`metric`/`factor_bullet`/`news_citation`/`price_spark`/`candlestick`/`table`/`heatmap`/`sector_treemap`/`radar_mini` | High |
| **FR-R-B03** | LLM 프롬프트 업그레이드 — prose 마크다운 대신 **JSON blocks 배열** 반환을 요청 (one-shot JSON schema + 예시 3건 few-shot) | High |
| **FR-R-B04** | LLM 출력 JSON 파싱 + fallback: 파싱 실패 시 기존 prose `summary` 에 담아 렌더 (회귀 방지) | High |
| **FR-R-B05** | 백엔드 data enrichment — 각 block 에 필요한 raw data 직접 삽입 (가격 시계열, factor raw, 상관 matrix 등). LLM 은 해석 block (`summary`, `factor_bullet`) 만 생성 | High |
| **FR-R-B06** | 챗봇 `tool_result` 이벤트에 `artifact: ReportBlock[]?` 필드 추가 — rank_stocks/analyze_theme/stock_comprehensive/market_condition/news_sentiment 결과를 structured block 으로 변환 | Medium |
| **FR-R-B07** | `chat_service` 시스템 프롬프트에 "수치는 `BigNumber` 권장, 비교는 `Table` 권장" 가이드 추가 (LLM 이 특정 block kind 지정 가능) | Medium |
| **FR-R-B08** | 기존 `news` 배열은 유지하고, 추가로 `news_citations` (id→label→url 매핑) 삽입 — 프론트가 본문 텍스트 속 `[1]` 마커를 상호링크 | Low |

### B. Frontend: Block renderers (FR-R-F)

| ID | 요구사항 | 우선 |
|---|---|---|
| **FR-R-F01** | `components/report/BlockRenderer.tsx` — 분기 dispatcher + 누락 block 은 fallback | High |
| **FR-R-F02** | `SummaryBlock` — 제목 + Markdown 본문 + 인용 참조 `[1]` 하이라이트 | High |
| **FR-R-F03** | `MetricCard` — BigNumber + delta arrow + 소제목 + color (positive/negative/neutral), `tabular-nums` | High |
| **FR-R-F04** | `FactorBulletList` — 팩터명 + 점수 막대 + 해석 한 줄 (Apple HIG Bullet 스타일) | High |
| **FR-R-F05** | `NewsCitationPanel` — 우측 사이드 또는 하단 접이식; 번호 클릭 시 해당 카드 하이라이트 | Medium |
| **FR-R-F06** | `InlineChart` — 문장 중간 spark/bar mini viz (SVG, 의존성 없음) | High |
| **FR-R-F07** | `PriceSparkBlock` — area/line 선택, 6개월 가격, 다크모드 팔레트 | High |
| **FR-R-F08** | `CandlestickBlock` — 거래량 sub-pane 포함, MA20/MA50 overlay, Recharts ComposedChart 확장 또는 SVG 직접 | High |
| **FR-R-F09** | `TableBlock` — headless table (정렬/수치 align/compact), rankings / 섹터 / 비교 공통 | High |
| **FR-R-F10** | `HeatmapBlock` — 상관관계/섹터 성과 RdBu 팔레트, hover tooltip | Medium |
| **FR-R-F11** | `SectorTreemapBlock` — 포트폴리오 섹터 배분 treemap (Recharts Treemap 또는 d3) | Medium |
| **FR-R-F12** | `RadarMiniBlock` — 6대 팩터 레이더 mini (기존 차트보다 작고 조밀) | Medium |

### C. Chart styling upgrade (FR-R-C)

| ID | 요구사항 | 우선 |
|---|---|---|
| **FR-R-C01** | Dark-mode 전용 팔레트 확립 — positive/negative/neutral, grid, tooltip bg 모두 CSS 변수로 추출 | High |
| **FR-R-C02** | framer-motion 도입 — 차트 mount 시 fade-in + stagger (데이터 포인트 순차 등장) | Medium |
| **FR-R-C03** | Tooltip 업그레이드 — 커스텀 `<ChartTooltip>` 공통 컴포넌트 (다중값, delta, 색상 pill, 다크모드) | High |
| **FR-R-C04** | Candlestick + volume — 기존 AreaChart `/stock` 페이지를 탭으로 `Line / Candle / Candle+Volume` 3모드 | High |
| **FR-R-C05** | Axis 스타일링 — fontSize 11, `tabular-nums`, %/$/₩ 접두, 압축표기 (1.2M / 3.4B / 12.5조) | High |
| **FR-R-C06** | Axes gridline dashed, 1dp stroke, opacity 0.4 — Bloomberg-style 낮은 대비 | Medium |
| **FR-R-C07** | 반응형 — 모바일에서 Y축 숨기고 tooltip 만, 가로 스크롤 옵션 | Medium |
| **FR-R-C08** | Loading skeleton 차트 — 스켈레톤 bar/line shimmer, 500ms 이상 걸릴 때만 표시 | Low |

## 4. Non-Functional

- **성능**:
  - LLM 리포트 구조화 후 첫 block 렌더 시간 ≤ 2s (streaming 리포트 path 활용)
  - 차트 mount → interactive ≤ 300ms (framer-motion 애니메이션 포함)
  - Bundle 증가 ≤ +80KB gzip (framer-motion + 내부 SVG 위젯)
- **접근성**: 모든 block 에 `role`, `aria-label`; 차트는 `<figcaption>` + 숫자 요약 제공
- **후방 호환**: `summary` string 응답도 계속 지원 → BlockRenderer 의 default fallback
- **다국어**: 한국어 1차, 영어 예비 (block `locale` 필드)

## 5. Phased Roadmap

| Phase | 범위 | 예상 |
|---|---|---|
| **P1 Backend schema + fallback** | FR-R-B01/02/04/05 + 프롬프트 초안 (FR-R-B03) | 2일 |
| **P2 Frontend renderers (coreSet)** | FR-R-F01/02/03/04/06/07 + FR-R-C01/03/05 (차트 공통 스타일) | 2일 |
| **P3 Advanced charts** | FR-R-F08/10/11 + FR-R-C02/04/06 | 2일 |
| **P4 Chatbot integration** | FR-R-B06/07/08 + tool_result artifact 렌더 | 1일 |
| **P5 Polish** | FR-R-C07/08, FR-R-F05/09/12 | 1일 |

→ **이번 사이클에 P1~P4 까지** (8일). P5 폴리시는 gap analyze 후 결정.

## 6. Architecture

### 6.1 Block schema (freeze)

```typescript
// dashboard/src/lib/reportBlocks.ts
type ReportBlock =
  | { kind: "summary"; title?: string; markdown: string; citations?: number[] }
  | { kind: "metric"; label: string; value: string; delta?: number; tone?: "positive"|"negative"|"neutral" }
  | { kind: "metric_grid"; items: MetricItem[] }
  | { kind: "factor_bullet"; factors: { name: string; score: number; note?: string }[] }
  | { kind: "news_citation"; items: { id: number; source: string; title: string; date: string; url: string; snippet?: string }[] }
  | { kind: "price_spark"; ticker: string; series: { t: string; c: number }[]; market: "US"|"KR" }
  | { kind: "candlestick"; ticker: string; rows: OHLCVRow[]; overlays?: ("ma20"|"ma50"|"bb")[]; withVolume?: boolean }
  | { kind: "table"; columns: TableColumn[]; rows: Record<string, unknown>[]; caption?: string }
  | { kind: "heatmap"; xs: string[]; ys: string[]; matrix: number[][]; scale?: "correlation"|"heat" }
  | { kind: "sector_treemap"; items: { sector: string; weight: number; pnl?: number }[] }
  | { kind: "radar_mini"; factors: { name: string; value: number }[]; max?: number };
```

Python mirror: `api/schemas/report_blocks.py` — Pydantic `ReportBlock = Union[...]` with `kind` discriminator.

### 6.2 LLM prompt 전략 (FR-R-B03)

```
System:
  "당신은 시니어 금융 애널리스트입니다. 아래 데이터 블록들을 종합해
  **분석 블록 배열 JSON만** 출력하세요 (prose 금지). 스키마:
    [{ kind: 'summary', title, markdown, citations? }, ...]
  규칙:
    1. 첫 block 은 kind='metric_grid' — 핵심 수치 4~6개
    2. 그 다음 kind='summary' — 3~5 문단 마크다운 (본문 중 [1][2] 인용)
    3. kind='factor_bullet' — 6대 팩터 bullet
    4. kind='news_citation' — items 배열
    5. 통화 기호는 market 필드 따라 (KR=₩, US=$), 점수는 무단위
  금지:
    - prose 문단만 반환 (kind=summary 1개) 금지 — 최소 3 block
    - 근거 없는 수치 인용 금지
  출력 예시:
    ```
    [
      {"kind":"metric_grid", "items":[
        {"label":"종합점수","value":"78.4","tone":"positive"},
        ...]},
      {"kind":"summary","title":"투자 의견","markdown":"...[1] 참고...",citations:[1]},
      ...
    ]
    ```"
User: "{structured data blocks}"
```

Parse: 응답에서 첫 `[` 부터 마지막 `]` 까지 잘라 `json.loads`. 실패 시 전체를 `kind=summary, markdown=<raw>` 단일 block 으로 wrap.

### 6.3 Frontend dispatch

```tsx
// components/report/BlockRenderer.tsx
export function BlockRenderer({ block }: { block: ReportBlock }) {
  switch (block.kind) {
    case "summary":         return <SummaryBlock {...block} />;
    case "metric":          return <MetricCard {...block} />;
    case "metric_grid":     return <MetricGrid items={block.items} />;
    case "factor_bullet":   return <FactorBulletList factors={block.factors} />;
    case "news_citation":   return <NewsCitationPanel items={block.items} />;
    case "price_spark":     return <PriceSparkBlock {...block} />;
    case "candlestick":     return <CandlestickBlock {...block} />;
    case "table":           return <TableBlock {...block} />;
    case "heatmap":         return <HeatmapBlock {...block} />;
    case "sector_treemap":  return <SectorTreemapBlock items={block.items} />;
    case "radar_mini":      return <RadarMiniBlock {...block} />;
    default:                return <UnknownBlockFallback block={block} />;
  }
}
```

### 6.4 Chatbot `tool_result` extension (FR-R-B06)

```typescript
// chatEvents.ts
| { type: "tool_result"; tool: string; ok: boolean; summary: string; ms: number; hop: number;
    artifact?: ReportBlock[] }  // 신규
```

ArtifactPanel (이미 존재) 이 `artifact` 배열을 우선 렌더, 없으면 기존 summary placeholder.

## 7. 파일 영향도

**Backend (신규 / 수정)**
- `api/schemas/report_blocks.py` — Pydantic ReportBlock union
- `api/services/report_builder.py` — data → blocks 조립 헬퍼
- `api/routers/analysis.py` — 4개 analysis-report 엔드포인트가 blocks 생성 + LLM 파싱
- `api/services/chat_stream_service.py` + `chat_tools.py` — artifact 추가
- `mcp_server/tools/llm.py` — JSON 출력 검증용 thin helper `call_llm_json()` (옵션)

**Frontend (신규)**
- `dashboard/src/lib/reportBlocks.ts` — 타입
- `dashboard/src/components/report/BlockRenderer.tsx`
- `dashboard/src/components/report/blocks/*` — 12종 renderer
- `dashboard/src/components/ui/inline/Spark.tsx`, `Delta.tsx`, `BigNumber.tsx`, `Badge.tsx`, `Trend.tsx`
- `dashboard/src/components/charts/CandlestickChart.tsx`, `HeatmapChart.tsx`, `TreemapChart.tsx`
- `dashboard/src/components/charts/ChartTooltip.tsx`

**Frontend (수정)**
- `dashboard/src/components/AnalysisReport.tsx` — `<Markdown>` 단일 블록 → `blocks?.map(<BlockRenderer/>)` + fallback
- 4 analyze 페이지 report 섹션 → 변경 없음 (컴포넌트 내부 분기)
- `dashboard/src/components/chat/ArtifactPanel.tsx` — `artifact` 가 있으면 BlockRenderer 사용
- `dashboard/src/app/globals.css` — 다크 모드 chart palette 토큰 추가
- `dashboard/package.json` — `framer-motion` 추가

**Tests**
- `tests/test_report_blocks.py` — 스키마 validation + LLM fallback
- `dashboard/src/components/report/__tests__/BlockRenderer.test.tsx` — kind 별 렌더 smoke

## 8. Success Criteria

1. **종목 분석 리포트** — LLM 응답이 평균 **5~7 block** 으로 구조화되어 표시됨 (summary 1개 → 4~6개 카드)
2. **캔들스틱** + 거래량 차트가 `/stock` 페이지에서 Line/Candle/Candle+Volume 3모드 전환 가능
3. **챗봇** — "AAPL 분석해줘" 질의 시 ArtifactPanel 에 candlestick + factor_bullet + news_citation block 렌더
4. **다크 모드** 에서 차트 팔레트가 light 대비 동등한 대비/가독성 확보 (axe-core contrast AA)
5. **회귀 방지** — LLM 이 JSON 파싱 실패해도 prose summary 로 fallback 렌더
6. gap analyze **match rate ≥ 90%**

## 9. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| LLM 이 JSON 스키마 안 지킴 (한국어 prose 혼입) | few-shot 3개 + temperature 0.1 + parse fallback → prose summary block |
| framer-motion 번들 증가 | tree-shake + 차트별 lazy import, 모바일에서 애니메이션 자동 감소 (`prefers-reduced-motion`) |
| 캔들스틱 SVG 구현 복잡 | Recharts ComposedChart + Bar(width=1) 조합으로 MVP, 후속에 lightweight-charts 검토 |
| 구조화 응답이 모델 출력 토큰 늘림 | max_output_tokens 8192 유지 + JSON minified (공백 제거 프롬프트 지시) |
| UI 재설계로 기존 사용자 혼란 | 기존 `<Markdown>` 렌더 블록도 fallback 으로 유지, 점진 rollout |
| Recharts Treemap API 제한 | d3-hierarchy 직접 사용 (dep already transitive via Recharts) 또는 단순 flex grid fallback |

## 10. 의존성 추가

```bash
npm install framer-motion       # 차트 애니메이션
# (선택, P5) npm install lightweight-charts  # TradingView 스타일 — 후속 검토
# d3-hierarchy / d3-scale 은 Recharts 통해 transitive
```

## 11. Acceptance Demo scenario

1. `/stock AAPL` → 리포트 생성 → **6 block 표시**:
   - `metric_grid` (composite 78.4, signal Buy, ROE 17.4%, PE 29.3, 1yr return +34%, vol 28%)
   - `summary` (3문단 한국어, `[1][2]` 인용)
   - `factor_bullet` (6대 팩터 bar)
   - `candlestick` (6M + volume + MA20)
   - `news_citation` (5건)
   - `radar_mini` (inline 레이더)

2. 챗봇 `/chat` → "AAPL 과 삼성전자 비교" → ArtifactPanel 에 `table` (compare) + `radar_mini` × 2 렌더, 각 종목 통화 태그 유지.

3. 다크 모드 토글 → 모든 차트 팔레트 swap 되면서 대비 유지.
