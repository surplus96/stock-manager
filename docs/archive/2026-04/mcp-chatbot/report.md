# Completion Report — mcp-chatbot

**Feature**: `mcp-chatbot`
**Period**: 2026-04-17 ~ 2026-04-19
**Final match rate**: **91 %** (엄격 87 % / P3 제외 97 %)
**Iterations**: 0 (추가 iterate 불필요 — 최초 구현이 ≥90% 달성)
**Status**: ✅ Check 통과 → Report 단계

## 1. Scope delivered

PM-MCP 의 분석 도구를 LLM tool-calling 으로 호출하는 대화형 챗봇을
백엔드(`/api/chat`) + 프론트(`/chat`) 로 완성.

### Backend
- `api/schemas/chat.py` — `ChatRequest`, `ToolTrace`, `ChatResponseData`
- `api/services/chat_tools.py` — **10 개 도구** 레지스트리
  - 원래 7: `propose_themes`, `analyze_theme`, `rank_stocks`, `stock_comprehensive`, `stock_signal`, `news_sentiment`, `market_condition`
  - discovery 3 (FR-C-B09/B10/B11): `propose_tickers`, `dip_candidates`, `watchlist_signals`
- `api/services/chat_service.py` — 시스템 프롬프트 빌더, JSON tool-call 파서,
  max 5-hop 루프, 30분 TTL in-memory 세션 메모리
- `api/routers/chat.py` — `POST /api/chat`, `GET /api/chat/session/{id}`,
  slowapi 20/min rate limit (graceful degradation)
- **503 핫픽스** (`_call_llm_resilient` + `_friendly_llm_error`):
  transient 5xx/429/timeout 재시도, `GEMINI_FALLBACK_MODELS` 자동 체인 전환,
  한국어 사용자 메시지

### Frontend
- `dashboard/src/lib/api.ts` — `fetchPOST` 헬퍼 + `api.chat()` (180s timeout)
- `dashboard/src/lib/api.types.ts` — `ChatToolTrace`, `ChatResponseData`
- `dashboard/src/components/Sidebar.tsx` — NAV 에 `/chat` (MessageSquare)
- `dashboard/src/app/chat/layout.tsx`, `page.tsx` — 메시지 리스트 (user/
  assistant/error 버블), Markdown 렌더, tool trace 펼침/접힘, 4 빠른시작 칩,
  Enter 전송 / Shift+Enter 줄바꿈, `role="log" aria-live="polite"` 접근성

### Tests
- `tests/test_chat_service.py` — **18 / 18 통과**
  - parse_tool_call (codefence, invalid json, prose)
  - system prompt (모든 도구 포함)
  - execute_tool (unknown, kwargs filter)
  - summarize_result (rankings/list/truncation)
  - discovery 도구 등록 + 안전한 실패 처리
  - `_is_transient_upstream_error` + `_friendly_llm_error`

## 2. Key design decisions

| 결정 | 이유 |
|---|---|
| Prompt-based JSON tool call (native function calling 대신) | 기본 `GEMINI_MODEL` 이 Gemma 4 로 native 미지원. 프롬프트 계약으로 호환성 확보, 나중에 model 만 바꿔도 동작 |
| In-process tool dispatch (REST / MCP-stdio 우회) | 라우터 함수 재사용 → 레이턴시 최소화, 코드 중복 0 |
| Defensive `execute_tool` — 예외 삼켜서 LLM 에 ERROR string 전달 | 챗봇이 tool 실패 시에도 자연어로 사과 가능 |
| In-memory 세션 (TTL 30분, lazy GC) | 프로토타입 단계엔 Redis 오버엔지니어링. 영속화는 performance feature 로 분리 |
| 503 resilience (`_call_llm_resilient`) | preview 모델 (`gemini-3.1-flash-lite-preview`) 503 폭주 관찰 → fallback 체인 + 지수 백오프 추가 |

## 3. Gap highlights

| 상태 | FR |
|---|---|
| ✅ 완전 충족 (16) | B01, B02, B03, B05, B06, B07, B08, B09, B10, B11, F01, F02, F03, F05, F06, F08 |
| ⚠️ 부분 (1) | F07 (실시간 도구명 표시 — SSE 필요) |
| ⏳ Deferred (2) | B04, F04 (SSE 스트리밍 — follow-up feature 로 분리) |

분석 문서: `docs/03-analysis/mcp-chatbot.analysis.md`

## 4. Lessons learned

1. **도구 shape normalization 은 서비스 레이어 1곳에서** — 직전 `_collect_news` 버그는
   wrapper 리스트를 플랫하지 않은 채 통과시켜 UI 에 빈 카드 1개가 떴음. 챗봇
   도구도 동일 패턴 주의 필요.
2. **Preview 모델은 opt-in 으로** — prod 기본값을 preview 로 두면 503 폭주 리스크.
   안정 모델 고정 + opt-in 으로 preview 시험.
3. **LLM 호출 계약은 retry + fallback 까지 포함** — 단일 `_call_gemma` 만으로는
   prod 체감 안정성 부족. `_call_llm_resilient` 같은 래퍼를 표준화해야 함.
4. **in-memory 세션은 MVP 에만 OK** — 재시작 시 모든 대화 증발. uvicorn --reload
   환경에서 특히 불편.

## 5. Follow-up features (roadmap)

**Roadmap**: `docs/00-roadmap/mcp-chatbot-followup.roadmap.md`

| Feature | 목적 | 상태 |
|---|---|---|
| `mcp-chatbot-streaming` | SSE 스트리밍 (FR-S01..S08) — 후속 2개의 기반 레이어 | Plan 완료 |
| `mcp-chatbot-performance` | 응답 속도·안정성 (FR-P01..P12), Redis 세션, native function calling | Plan 완료 |
| `mcp-chatbot-ux` | 2-pane analyst workbench, ⌘K, 다크모드, 벤치마크 기반 (Perplexity/Claude.ai/Linear) | Plan 완료 |

병합 전략: streaming 먼저 main 에 → performance + ux 는 그 위에서 병렬 →
integration 브랜치에서 3-way merge + QA → release `mcp-chatbot v2.0`.

## 6. Metrics snapshot

| 항목 | 값 |
|---|---|
| 신규 파일 | 8 (backend 5, frontend 3) |
| 수정 파일 | 4 (api/server.py, api.ts, api.types.ts, Sidebar.tsx) |
| 단위 테스트 | 18 (100% pass) |
| tsc errors | 0 |
| 도구 수 | 10 |
| 소요 시간 | ~3시간 (plan→design→do→check) |

## 7. Action after archive

- `/pdca archive mcp-chatbot` → `docs/archive/2026-04/mcp-chatbot/`
- `mcp-chatbot-streaming` 을 active feature 로 승격 → `/pdca design mcp-chatbot-streaming` 으로 진행
