# Archive Index — 2026-04

| Feature | Match Rate | Iterations | Archived | Path |
|---|---|---|---|---|
| backend-quality-upgrade | 91% | 1 | 2026-04-15 | [`backend-quality-upgrade/`](./backend-quality-upgrade/) |
| frontend-quality-upgrade | 90% | 1 | 2026-04-15 | [`frontend-quality-upgrade/`](./frontend-quality-upgrade/) |
| mcp-chatbot | 91% | 0 | 2026-04-19 | [`mcp-chatbot/`](./mcp-chatbot/) |
| mcp-chatbot-streaming | 98% | 0 | 2026-04-19 | [`mcp-chatbot-streaming/`](./mcp-chatbot-streaming/) |
| mcp-chatbot-performance | 92% | 0 | 2026-04-19 | [`mcp-chatbot-performance/`](./mcp-chatbot-performance/) |
| mcp-chatbot-ux | 94% | 0 | 2026-04-19 | [`mcp-chatbot-ux/`](./mcp-chatbot-ux/) |
| rich-visual-reports | 92% | 0 | 2026-04-21 | [`rich-visual-reports/`](./rich-visual-reports/) |
| perplexity-style-polish | 94% | 0 | 2026-04-23 | [`perplexity-style-polish/`](./perplexity-style-polish/) |

## Contents per feature

Each archived feature folder contains the full PDCA document set:

- `plan.md` — original Plan document (FR catalog, phased roadmap)
- `design.md` — Design document (architecture decisions, file-level targets)
- `analysis.md` — Gap Analysis (final match rate, per-FR status)
- `report.md` — Completion Report (PDCA cycle summary, lessons learned)

## Summary

Two parallel quality-upgrade features covering Stock Manager's backend FastAPI
facade and Next.js 16 dashboard. Each ran through Plan → Design → Do (3 phases)
→ Check → Act (1 iteration) → Report → Archive within a single day, with
cross-feature parallelism throughout the cycle.

### Backend highlights
- `api/server.py` 968 → ~200 LoC via 7 domain-router split
- Envelope[T] response contract + 6 Pydantic schema modules
- pytest suite 4 → 31 tests, coverage gate at 55%
- CORS/allowlist, Gemini header auth, LLM 300s timeout, circuit 5/60, sector N+1 fix

### Frontend highlights
- `ApiError`-typed client, `useAnalysisReport` hook adoption across 5 pages
- `<AsyncBoundary>` + `<SkeletonReport>` standardization
- `<LazyChart>` render-prop for Recharts code-splitting
- react-markdown + remark-gfm replacing hand-rolled parser
- Mobile hamburger drawer (role=dialog, scroll lock), responsive shell (md:ml-60)
- Design tokens (@theme), ESLint strict no-explicit-any
- Vitest + RTL scaffolding with 3 baseline tests

### Chatbot highlights (mcp-chatbot)
- `POST /api/chat` — tool-augmented LLM loop (prompt-based JSON function calling
  for Gemma 4 compatibility), max 5 hops, 10 MCP-backed tools
- Discovery tools: `propose_tickers`, `dip_candidates`, `watchlist_signals`
- In-process tool dispatch (no HTTP / MCP-stdio round-trip) — reuses router fns
- 503 resilience: `_call_llm_resilient` + `GEMINI_FALLBACK_MODELS` auto-chain
- In-memory session (30-min TTL, lazy GC), 20/min rate limit (graceful)
- `/chat` page with quick-start chips, tool-trace expand/collapse, ARIA
  `role="log" aria-live="polite"`
- Follow-up roadmap: `mcp-chatbot-streaming` → `-performance` + `-ux` parallel
  → integration release `v2.0` (see `docs/00-roadmap/mcp-chatbot-followup.roadmap.md`)

### Streaming highlights (mcp-chatbot-streaming)
- `GET /api/chat/stream` SSE endpoint — 5-event schema (`tool_call`,
  `tool_result`, `token`, `done`, `error`) as frozen discriminated union
- 512-char tool-call detection buffer flips streaming into token mode
  seamlessly; first event reaches client in ~1s
- `_call_gemma_stream` (Gemini `:streamGenerateContent?alt=sse`) with
  inline non-streaming fallback; friendly 503 messaging preserved
- Client `sseClient.ts` (fetch + ReadableStream + AbortController); Stop
  button + automatic POST fallback when stream fails pre-first-event
- Disconnect checkpoints at every I/O boundary — server loop releases <5s
  after client cancel; no partial answer written to session
- `X-Request-ID` passthrough as SSE comment for log correlation
- +11 tests (total 29 chat-related)

### Performance highlights (mcp-chatbot-performance)
- Chat path pinned to `gemini-2.0-flash` via new `settings.default_chat_model`
  — preview models remain opt-in (`CHAT_USE_PREVIEW=1`)
- `call_llm_resilient` + `is_transient_upstream_error` promoted to
  `mcp_server/tools/llm.py`; env-tunable inner retries (3) and fallback
  model chain (`GEMINI_FALLBACK_MODELS`)
- `GET /api/chat/metrics` exposes p50/p95 latency, tool error rate,
  hop averages, llm_errors, uptime — threadsafe counters in
  `api/services/chat_metrics.py`
- Structured `chat.hop session=… hop=… tool=… ok=… latency_ms=…` log
  lines on both sync and streaming paths
- `fetchPOST` grew retry options (1× on 429/502/503/504/network), wired
  into `api.chat()` for 503 recovery without UX break
- +7 tests (total 36 chat-related)

### UX highlights (mcp-chatbot-ux)
- 2-pane workbench layout — Conversation (60%) + ArtifactPanel (40%) on
  md+, collapses to single column + artifact strip on mobile
- New header: `ChatHeader` bundles model selector, ⌘K palette hint, New
  Chat, theme toggle, and session badge
- `ChatModelProvider` context shares the user's chosen model with any
  descendant that needs to forward it to the backend
- `CommandPalette` — native dialog (no external dep), Cmd/Ctrl+K global
  listener, arrow-key navigation, substring filter over quick-starts
- Dark mode via `html[data-theme="dark"]` tokens + persistent
  `localStorage["chat.theme"]`, applied across all chat components
- Tool-result dispatch: last assistant message accumulates artifacts;
  `ArtifactPanel` renders tabbed container with per-tool renderer
  (`RankingsTable` placeholder, `MarketGaugeMini`, `NewsListPanel`)
- `.tabular` utility (`font-variant-numeric: tabular-nums`) applied to
  numeric regions for clean alignment
- Benchmarks: Perplexity Finance, Claude.ai Artifacts, Linear, Bloomberg,
  Vercel v0 (see feature report)

### Rich visual reports highlights (rich-visual-reports)
- **11-kind discriminated `ReportBlock` union** (Pydantic + TS mirror):
  summary / metric / metric_grid / factor_bullet / news_citation /
  price_spark / candlestick / table / heatmap / sector_treemap /
  radar_mini — full frontend/backend symmetry.
- LLM returns structured **JSON blocks** (temperature 0.1) instead of
  prose; 3-strategy parser (whole-JSON → balanced brackets → prose
  fallback) keeps zero-regression promise even when the model misbehaves.
- Deterministic Python **builders** produce metric/price/candle/news/
  radar blocks before the LLM runs — numbers stay correct, LLM only
  owns interpretation (summary + factor bullets).
- Custom Recharts **CandleShape** (wick + body SVG) delivers TradingView-
  style candlesticks with volume overlay + MA20/MA50, no new dependency.
- Dark-mode chart palette via `:root` / `html[data-theme="dark"]` CSS
  variables (`--chart-grid/axis/tooltip-bg/tooltip-fg/pos/neg/neutral/
  accent/accent-2`); shared `<ChartTooltip>` component reads them.
- Chatbot `tool_result.artifact` extension — `rank_stocks` / `analyze_
  theme` / `watchlist_signals` / `stock_comprehensive` auto-emit table +
  radar_mini blocks; rendered inline under the assistant bubble (no
  side panel per user preference).
- framer-motion `FadeIn` + `Stagger` primitives with `useReducedMotion`
  — reports mount with a gentle cascade, accessibility-first.
- +2 analysis routes (`parse_llm_blocks` + `call_llm_json`), +13 new
  frontend components, 0 regressions (pytest 62/62, tsc 0).
- Match rate 92%; 7 gaps tracked as Low/Medium follow-up backlog
  (chart mode tabs, inline SVG helpers, citation auto-link, axis
  standardisation, responsive charts, skeleton charts, axe-core).

### Perplexity-style polish highlights (perplexity-style-polish)
- **Option B**: 25 active FR (24 visual + 1 additive) — FR-PSP-I02
  (Markdown $TICKER auto-replace) and FR-PSP-X01 (Discover EmptyState)
  intentionally excluded to preserve existing UX with **0 functional change**.
- **8 Perplexity patterns adapted** to our finance dashboard:
  single slate-blue accent (`#1E3A8A`), display serif headings
  (`Source_Serif_4` via next/font), card hairline shadows, suggested
  follow-up chips, `[N]` citation linkify + `:target` highlight,
  3-way segmented model selector with tone dots and `1`/`2`/`3`
  shortcuts, opt-in `TickerPill`, sticky Pages-style TOC for ≥5 block
  reports plus mobile floating scroll-to-top.
- **Suggested follow-ups** (FR-PSP-F): backend appends a single
  `<<SUGGEST>>["q1","q2","q3"]` marker line to the LLM answer; new
  `split_suggested_marker()` helper strips it before the answer hits
  session history and surfaces the chips on `DoneEvent.suggested` /
  `ChatResponseData.suggested`. Empty default keeps every existing
  client backward-compatible.
- **Dark mode goes near-black** — `--background: #0a0a0a`,
  `--card-bg: #141414`, with chart palette tokens (`--chart-pos/neg/
  accent`) following the new accent.
- **3 new components**: `SuggestedBlock` (chip row with onPick),
  `Toc` (auto from ReportBlock kinds, threshold 5, mobile fallback to
  `ScrollToTopButton`), `TickerPill` (analyst-style mini badge for
  explicit call sites only).
- **17 modified files** centred on token-only changes — Card,
  Sidebar, Markdown, ModelSelector all consume `--accent`,
  `--accent-soft`, `--shadow-card`, `.font-display`, `.prose-loose`.
- **Quick-fix cycle** pushed match rate from 87 → 94 by adding the
  `suggested` block instruction to `routers/analysis.py`, mobile
  scroll-to-top button, and Flash/Pro tone dots (Mode color hint).
- pytest 70/70 (regression-free), `npx tsc --noEmit` 0 errors,
  bundle impact ≈ +25 KB gzip.
- 3 followups parked as separate features:
  `citation-hover-preview` (200ms popover for `[N]` markers),
  `tickerpill-sparkline` (hover sparkline + KR name), and
  `discover-feed` / `pages-style-deep-research` / `spaces-collections`
  / `a11y-audit` from Plan §12 out-of-cycle list.
