# Completion Report — mcp-chatbot-performance

**Feature**: `mcp-chatbot-performance` (follow-up #2 of mcp-chatbot v2)
**Period**: 2026-04-19 (same day)
**Match Rate**: **92%** (P1 scope)
**Tests**: 36 / 36

## Delivered (P1)

### Backend
- `core/config.py` — `default_chat_model=gemini-2.0-flash` + `chat_use_preview` opt-in (FR-P01)
- `mcp_server/tools/llm.py` — `_call_gemma(model=...)` per-call override, `call_llm_resilient` + `is_transient_upstream_error` exported as first-class helpers (FR-P05). 503/429/timeout 자동 감지 + 지수 백오프 + 모델 fallback chain, env 로 전부 튜닝 가능.
- `api/services/chat_service.py` / `chat_stream_service.py` — 챗 path 는 `settings.default_chat_model` 강제 사용, 분석 리포트 등 다른 path 는 기존 `GEMINI_MODEL` 유지. 구조화 로깅 `chat.hop session=... hop=... tool=... ok=... latency_ms=...` (FR-P09).
- `api/services/chat_metrics.py` (신규) — thread-safe 카운터 (requests/hops/tool_ok/tool_err/llm_errors + p50/p95 latency). `GET /api/chat/metrics` Envelope 응답 (FR-P10).

### Frontend
- `dashboard/src/lib/api.ts` — `fetchPOST({retries, retryDelayMs})` 재시도 옵션, `api.chat()` 호출 시 `retries=1, retryDelayMs=800`. 429/502/503/504 및 network TypeError 대상 (FR-P11). `api.chatMetrics()` 신규.

### Tests
- `tests/test_chat_metrics.py` (+7): 초기값, percentile, 에러 비율, llm_errors, `call_llm_resilient` export, non-transient 즉시 raise, fallback chain 성공

## 핵심 변경 효과

| 변경 전 | 변경 후 |
|---|---|
| preview 모델 503 시 raw 에러가 UI 로 노출 | 한국어 friendly 메시지 + fallback chain 자동 복구 |
| 모델 기본값이 preview (불안정) | chat path 만 `gemini-2.0-flash` 고정, 분석 리포트는 건드리지 않음 |
| 관측 불가 | `/api/chat/metrics` 에서 p50/p95 latency + tool 에러율 즉시 확인 |
| 503 1회로 사용자에게 실패 | POST path 1회 자동 재시도 |

## Deferred

| FR | 이유 |
|---|---|
| FR-P02 native function calling | Gemma 계열 비지원 — Gemini Pro 전환 사이클에서 반영 |
| FR-P03 parallel tool 실행 | `parse_tool_calls` 복수 지원 + UI 이벤트 채널 설계 필요 |
| FR-P04 Gemini context cache | API 안정화 대기 |
| FR-P08 Redis 세션 | infra feature 로 분리 예정 |
| FR-P06/P07/P12 | 폴리시 사이클 |

## Lessons
1. **chat path 와 분석 path 의 모델을 분리**하면 preview 실험이 운영 영향 없이 가능.
2. **metrics 는 JSON 배열 샘플로 충분** — Prometheus 붙이기 전에 p50/p95 관찰이 훨씬 저비용.
3. **Fetch retry 는 abort 와 함께 설계**해야 함 — controller 는 루프 밖에서 재생성.

## Follow-up (integration 이전)
- ux feature 와의 `chat/page.tsx` 충돌 없음 (파일 영역 분리) — 병합 시 위 report 와 ux report 한 번에 reference.
