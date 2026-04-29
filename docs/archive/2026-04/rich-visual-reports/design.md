# Design — rich-visual-reports

## 1. Block schema (freeze)

Python mirror in `api/schemas/report_blocks.py`, TS mirror in
`dashboard/src/lib/reportBlocks.ts`. Names identical, discriminated by
``kind`` so both can consume the same JSON wire format.

```python
class SummaryBlock:   kind="summary";   title?: str; markdown: str; citations?: list[int]
class MetricItem:     label; value; delta?; tone? ("positive"|"negative"|"neutral")
class MetricGrid:     kind="metric_grid"; items: list[MetricItem]
class FactorBullet:   kind="factor_bullet"; factors: list[{name, score, note?}]
class NewsCitation:   kind="news_citation"; items: list[{id,source,title,date,url,snippet?}]
class PriceSpark:     kind="price_spark"; ticker; market; series: list[{t,c}]
class Candlestick:    kind="candlestick"; ticker; rows: list[OHLCV]; overlays?: ["ma20"|"ma50"|"bb"]; withVolume?: bool
class TableBlock:     kind="table"; columns: list[TableColumn]; rows: list[dict]; caption?
class Heatmap:        kind="heatmap"; xs; ys; matrix; scale? ("correlation"|"heat")
class SectorTreemap:  kind="sector_treemap"; items: list[{sector, weight, pnl?}]
class RadarMini:      kind="radar_mini"; factors: list[{name, value}]; max?: float

ReportBlock = Union[...]
```

`AnalysisReportPayload` extended:
```python
class AnalysisReportPayload:
    summary: str = ""             # legacy prose (fallback)
    blocks: list[ReportBlock] = []  # new
    news: list[NewsItem] = []     # legacy (kept for backward compat)
    evidence: dict[str, str] = {}
```

## 2. Report builder (Python)

`api/services/report_builder.py` — convert collected data into blocks
deterministically *before* the LLM summary, then append LLM-produced
`summary` / `factor_bullet` blocks.

```python
def build_stock_report_blocks(ticker, collected, rankings, market, currency) -> list[ReportBlock]:
    blocks = [
        _metric_grid(ticker, collected, rankings, currency),
        _price_spark(ticker, collected["prices"], market),
        _candlestick(ticker, collected["prices"]),
        _news_citation(collected["news_items"]),
        _radar_mini(rankings["factors"]),
    ]
    return blocks
```

LLM is then asked for `summary` + `factor_bullet` blocks with
`citations` referencing `news_citation.items[].id`. Merge strategy:
data blocks first, LLM blocks inserted at natural positions.

## 3. LLM prompt (FR-R-B03)

System prompt excerpt:
```
출력은 JSON 배열만. prose 금지.
스키마:
  [{kind:"summary", title, markdown, citations:[1,2]},
   {kind:"factor_bullet", factors:[{name, score(0-100), note}]}]
규칙:
  - 최소 2 block
  - summary.markdown 은 3~5문단, 수치는 원본 인용 ([1][2])
  - factor_bullet 은 6개 필수 (Financial/Technical/Growth/Quality/Valuation/Momentum)
  - 통화 표기: market=KR 이면 ₩, US 이면 $
Few-shot:
  ...예시 3건
```

`call_llm_json(system, user)` helper in `llm.py` returns parsed list or
raises `JSONDecodeError` → caller falls back to `[{kind:"summary", markdown:raw}]`.

## 4. Frontend layout

`components/report/` (new folder):
```
report/
  BlockRenderer.tsx           # dispatcher
  blocks/
    SummaryBlock.tsx
    MetricCard.tsx + MetricGrid.tsx
    FactorBulletList.tsx
    NewsCitationPanel.tsx
    PriceSparkBlock.tsx
    CandlestickBlock.tsx
    TableBlock.tsx
    HeatmapBlock.tsx
    SectorTreemapBlock.tsx
    RadarMiniBlock.tsx
    UnknownBlock.tsx           # fallback
  inline/
    BigNumber.tsx
    Delta.tsx
    Spark.tsx
    Badge.tsx
    Trend.tsx
```

`components/charts/ChartTooltip.tsx` — common tooltip used by every
Recharts view. Handles multi-value rows, delta coloring, dark mode.

`AnalysisReport.tsx` gets `blocks?` prop. Render order:
```
if (blocks && blocks.length) {
  blocks.map(b => <BlockRenderer block={b} />)
} else {
  <Markdown>{llmSummary}</Markdown>   // fallback
}
```

## 5. Dark-mode chart palette (FR-R-C01)

Add CSS vars in `globals.css`:
```css
:root {
  --chart-grid:          #e2e8f0;
  --chart-axis:          #64748b;
  --chart-tooltip-bg:    rgba(15,23,42,0.95);
  --chart-tooltip-fg:    #f8fafc;
  --chart-pos:           #10b981;  /* emerald-500 */
  --chart-neg:           #ef4444;  /* red-500 */
  --chart-neutral:       #64748b;
  --chart-accent:        #3b82f6;
}
html[data-theme="dark"] {
  --chart-grid:          #1e293b;
  --chart-axis:          #94a3b8;
  --chart-tooltip-bg:    rgba(255,255,255,0.92);
  --chart-tooltip-fg:    #0f172a;
  --chart-pos:           #34d399;
  --chart-neg:           #f87171;
  --chart-neutral:       #94a3b8;
  --chart-accent:        #60a5fa;
}
```

All Recharts components consume via `var(...)` inline style or the
`ChartTooltip` centralized component.

## 6. Candlestick (FR-R-F08 / C04)

Recharts doesn't ship a native candle. Two options:

**(A)** ComposedChart + custom Bar shape drawing the wick + body
(opensource pattern, minimal). Volume overlay → second Bar series on
hidden secondary YAxis.

**(B)** `lightweight-charts` dependency — pro but +40KB gzip.

Choice: **A** for P3, mark B as P5 candidate.

```tsx
<ComposedChart data={rows}>
  <XAxis dataKey="date" />
  <YAxis yAxisId="price" />
  <YAxis yAxisId="volume" orientation="right" hide />
  <Tooltip content={<ChartTooltip />} />
  <Bar dataKey="_candle" yAxisId="price" shape={<CandleShape />} />
  <Bar dataKey="volume" yAxisId="volume" barSize={2} opacity={0.3} />
  {overlays.includes("ma20") && <Line dataKey="ma20" yAxisId="price" dot={false} />}
</ComposedChart>
```

`CandleShape` renders SVG `<line>` (wick) + `<rect>` (body) with
`--chart-pos`/`--chart-neg` based on close >= open.

## 7. Chatbot artifact (FR-R-B06)

`chat_events.py` → `ToolResultEvent` gains `artifact: list[ReportBlock] | None`.

`chat_tools._tag_ranking_item` → when a tool returns rankings, also
produce a `TableBlock` with columns (Rank, Ticker, Score, Signal,
Sector) and emit it as artifact.

Frontend `ArtifactPanel.tsx` existing "tabs with tool names" layout
replaces summary placeholder with `<BlockRenderer block={a} />` when
`ev.artifact` present.

## 8. Implementation order

1. `api/schemas/report_blocks.py` — Pydantic schema
2. `dashboard/src/lib/reportBlocks.ts` — TS mirror
3. `api/services/report_builder.py` — data → blocks helpers
4. `api/routers/analysis.py` — integrate blocks + LLM JSON call
5. `mcp_server/tools/llm.py` — `call_llm_json` helper
6. `globals.css` — chart palette CSS vars
7. `ChartTooltip.tsx`
8. `BlockRenderer.tsx` + `blocks/` core (Metric/Summary/FactorBullet/PriceSpark/Table)
9. `AnalysisReport.tsx` — switch to blocks with fallback
10. `CandlestickBlock.tsx`
11. `HeatmapBlock.tsx` + `SectorTreemapBlock.tsx`
12. Chatbot artifact (events + ArtifactPanel)
13. tests + smoke
