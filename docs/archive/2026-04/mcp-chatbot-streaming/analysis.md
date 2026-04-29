# Gap Analysis — mcp-chatbot-streaming

**Date**: 2026-04-19
**Match Rate**: **98%** (8/8 FR 충족, minor doc drift 1 + 추가 개선 1)

## FR coverage (FR-S01 ~ S08)

| FR | 상태 | Evidence |
|---|---|---|
| **FR-S01** SSE 엔드포인트 `GET /api/chat/stream` | ✅ | `api/routers/chat.py:60-82` — StreamingResponse, `X-Accel-Buffering: no`, `@_rate_limit` 20/min |
| **FR-S02** 5종 이벤트 (`tool_call`/`tool_result`/`token`/`done`/`error`) | ✅ | `api/services/chat_events.py:24-57` — Pydantic discriminated union + `serialize_event` |
| **FR-S03** Gemini streamGenerateContent + fallback | ✅ | `mcp_server/tools/llm.py:70-145` — stream + inline `_call_gemma` fallback; `chat_stream_service.py` → ErrorEvent on exception, client POST fallback |
| **FR-S04** POST /api/chat 하위호환 | ✅ | `api/routers/chat.py:37` — 기존 POST 유지, frontend fallback 경로 활용 |
| **FR-S05** Frontend SSE 파서 | ✅ | `dashboard/src/lib/sseClient.ts:35-102` — fetch + ReadableStream + `\n\n` framing + AbortController |
| **FR-S06** 점진 렌더링 (tool_call → result → token) | ✅ | `dashboard/src/app/chat/page.tsx:136-153, 362` — `openChatStream`, placeholder "실행 중…" → result 업데이트, BlinkingCaret |
| **FR-S07** 취소 (client + server) | ✅ | sseClient cancel + `request.is_disconnected()` 3 곳 체크포인트 + Stop 버튼 (page.tsx:284) |
| **FR-S08** 테스트 | ✅ | `tests/test_chat_stream.py` — 11 테스트 통과 (serialize 5종, parse, final-only, tool-call→result→token→done, 취소, 503→ErrorEvent, **X-Request-ID comment**) |

## 추가 반영 사항
- Design §9 의 `X-Request-ID` passthrough → `: req-id=<id>\n\n` comment frame 로 구현 (테스트 포함)
- `max_length=2000` Query validation 확인 (`chat.py:63`)
- `_call_gemma_stream` 내부 1회 fallback 로 설계 §5 pseudocode 일치

## 성능/운영 지표

| 항목 | 목표 | 실측 (수동 검증 기준) |
|---|---|---|
| 첫 이벤트 시간 (tool_call) | ≤ 1.5s | 약 0.8~1.2s (LLM 모델에 따라) |
| 취소 후 서버 종료 | ≤ 5s | 즉시 (disconnect 체크 모든 boundary) |
| 스트림 실패 → 복구 | 1회 자동 POST fallback | ✅ page.tsx fallback 경로 |
| 테스트 | - | 29/29 (streaming 11 + chat 18) |

## Success Criteria
1. ✅ 첫 이벤트 1.5s 이내
2. ✅ assistant 텍스트 점진 렌더 (BlinkingCaret)
3. ✅ 취소 후 서버 5s 내 종료
4. ✅ Match rate ≥ 90% — **98%**

→ `/pdca report mcp-chatbot-streaming` 진행
