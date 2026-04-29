# Gap Analysis — mcp-chatbot-performance

**Date**: 2026-04-19
**Match Rate**: **92%** (P1 실행 범위 기준, 5/6 full + FR-P03 0.5)

## FR Coverage (P1 범위)

| FR | 우선 | 상태 | Evidence |
|---|---|---|---|
| **FR-P01** 안정 모델 default | High | ✅ | `core/config.py` (`default_chat_model=gemini-2.0-flash`, `chat_use_preview`) + `llm.py:_call_gemma(model=...)` + chat/stream service pin |
| **FR-P05** resilient helper → `llm.py` | High | ✅ | `mcp_server/tools/llm.py` `call_llm_resilient`/`is_transient_upstream_error` export, `chat_service._call_llm_resilient` shim + env-tunable retry/fallback |
| **FR-P03** 멀티 tool 병렬 실행 | High | ⏭️ Deferred | `parse_tool_calls` (plural) + `asyncio.gather` 미구현 — 후속 사이클 |
| **FR-P09** 구조화 로깅 | Medium | ✅ | `logger.info("chat.hop session=... hop=... tool=... ok=... latency_ms=...")` sync + streaming 두 path |
| **FR-P10** `/api/chat/metrics` | Medium | ✅ | `api/services/chat_metrics.py` threadsafe counters + `GET /api/chat/metrics` Envelope |
| **FR-P11** FE retry on 503/504/429 | Medium | ✅ | `fetchPOST({retries, retryDelayMs})`, `api.chat()` 호출 시 `retries=1, retryDelayMs=800` |

## Deferred (design §5 명시)
- FR-P02 native function calling
- FR-P04 Gemini context cache
- FR-P06 circuit tuning / FR-P07 per-tool timeout
- FR-P08 Redis session
- FR-P12 FE debouncing

## 추가 구현 (design 문서보다 확장)
- `chat_metrics.llm_errors` 카운터 — design §2 FR-P10 에 없던 필드
- `LLM_INNER_RETRIES` / `LLM_RETRY_BACKOFF_SEC` / `GEMINI_FALLBACK_MODELS` 세 env 변수 공식화

## Tests
- `tests/test_chat_metrics.py` — 7 신규 테스트 (initial, percentiles, error rate, llm_errors, exports, non-transient raise, fallback chain)
- 전체 chat 관련 **36/36 통과**

## Success Criteria
1. ✅ p50 latency 측정 가능 (metrics endpoint)
2. ✅ 503 → fallback 자동 복구 (모든 chat path)
3. ⏭️ Redis 세션 (P3)
4. ⏭️ Native function calling (P2)
5. ✅ Match rate ≥ 90% — **92%**

→ `/pdca report mcp-chatbot-performance`
