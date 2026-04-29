# Design — mcp-chatbot-performance

## 1. 우선 순위 (P1 범위)

| FR | 변경 위치 | 우선 |
|---|---|---|
| **FR-P01** 안정 모델 default | `core/config.py` + `mcp_server/tools/llm.py` | High |
| **FR-P05** `_call_llm_resilient` 를 `llm.py` 로 이동 | `mcp_server/tools/llm.py` | High |
| **FR-P03** 멀티 tool call 병렬 실행 | `api/services/chat_stream_service.py` | High |
| **FR-P09** 구조화 로깅 (session_id/hop/tool/ms) | `api/services/chat_service.py` + `chat_stream_service.py` | Medium |
| **FR-P10** `/api/chat/metrics` | `api/routers/chat.py` | Medium |
| **FR-P11** Frontend retry on POST fallback | `dashboard/src/lib/api.ts` | Medium |

P2/P3/P4 (native function calling, Redis 세션, context cache, debouncing) → 후속 사이클.

## 2. 변경 상세

### FR-P01 — 모델 default 교체
- `core/config.py`: 신규 필드 `default_chat_model = "gemini-2.0-flash"` (env `CHAT_MODEL` override)
- `llm.py`: `_call_gemma(model=None, ...)` — 인자로 모델 override, 미지정 시 `GEMINI_MODEL` 사용
- 챗봇 path 만 `default_chat_model` 강제 사용. 기존 분석 리포트/요약 path 는 영향 없음
- preview model 사용 시 명시 opt-in 환경변수 `CHAT_USE_PREVIEW=1`

### FR-P05 — `_call_llm_resilient` 표준화
현재 `api/services/chat_service.py` 안에 있는 헬퍼를 `mcp_server/tools/llm.py` 로 이동:
- `call_llm_resilient(system, user, *, model=None, fallback_models=None) -> str`
- `is_transient_upstream_error(exc) -> bool` 도 같이 이동 (export)
- `chat_service.py` 는 re-export 하여 기존 import 호환

### FR-P03 — 병렬 tool 실행
JSON prompt 약속을 확장: 모델이 한 turn 에 **JSON 배열** `[{"tool":"a"}, {"tool":"b"}]` 반환 시 둘을 `asyncio.gather` 로 동시 실행. 단일 객체는 기존 동작 유지.
```python
# parse_tool_call 확장 → parse_tool_calls(text) -> list[ToolCall] | None
# stream service: gather + 모든 tool_call/tool_result 이벤트 emit
```

### FR-P09 — 구조화 로깅
```python
logger.info("chat.hop", extra={
    "session_id": sid, "hop": hops, "tool": call["tool"],
    "ok": ok, "latency_ms": ms, "args_keys": list(call["args"].keys()),
})
```
- 기존 logger 가 JSON formatter 미사용일 경우 그대로 print 형식이 됨 (운영 로거 설정과 별개)

### FR-P10 — Metrics
in-memory counters:
```python
_METRICS = {"hops_total": 0, "tool_ok": 0, "tool_err": 0,
            "latencies_ms": collections.deque(maxlen=200),
            "started_at": utcnow()}
```
- `GET /api/chat/metrics` → `Envelope[dict]` with: total_requests, p50_latency, p95_latency, hop_avg, tool_error_rate, uptime_sec
- chat_service / chat_stream_service 가 record_*() 호출

### FR-P11 — Frontend retry
`fetchPOST` 에 `retries=1` 옵션. `api.chat(...)` 호출 시 `retries: 1, retryDelayMs: 800` 전달. 재시도 대상은 503/504/429/network error (status 미정 포함).

## 3. 파일

| 파일 | 변경 |
|---|---|
| `core/config.py` | `default_chat_model`, `chat_use_preview` 추가 |
| `mcp_server/tools/llm.py` | `_call_gemma` 시그니처에 `model` 인자, `call_llm_resilient` + `is_transient_upstream_error` export |
| `api/services/chat_service.py` | resilient helper re-export, 구조화 로깅, parse_tool_calls(복수) |
| `api/services/chat_stream_service.py` | 병렬 tool 실행, 메트릭 기록 |
| `api/services/chat_metrics.py` | (신규) 카운터 + 집계 |
| `api/routers/chat.py` | `GET /api/chat/metrics` |
| `dashboard/src/lib/api.ts` | `fetchPOST` retry 옵션, `api.chat` retries=1 |
| `tests/test_chat_metrics.py` | (신규) record/aggregate 단위 테스트 |
| `tests/test_chat_service.py` | parse_tool_calls 다중 반환 케이스 추가 |

## 4. 호환성
- `parse_tool_call` 시그니처 그대로 유지 (단일 호출 반환). 신규 `parse_tool_calls` 는 `[ToolCall]` 또는 `None` 반환. 단일 객체는 길이 1 배열로 wrap.
- 기존 챗봇 호출 path 영향 없음 (default 모델 변경만 즉시 적용).

## 5. Success Criteria (Plan §5 매핑)
1. ✅ **p50 latency 측정값** `/api/chat/metrics` 에서 즉시 확인 가능
2. ✅ **503 자동 복구**: `_call_llm_resilient` 가 모든 챗봇 path 적용
3. ⏭️ Redis 세션 (P3) — 후속 사이클
4. ⏭️ Native function calling (P2) — 후속 사이클
5. ✅ Match rate ≥ 90%
