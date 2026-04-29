# Plan — mcp-chatbot-streaming

> **Goal**: `mcp-chatbot` P3 범위였던 SSE 스트리밍을 독립 feature 로 분리해
> 구현한다. 후속 `performance`/`ux` feature 의 UI 훅(진행 중 도구명 표시 등)에
> 필요한 **기반 레이어** 역할을 한다.

## 1. Why separate feature
- Plan §6 에서 P3 로 deferred 됐으나, 성능/UX 폴리시가 streaming 이벤트 훅에
  의존한다. 별도 feature 로 먼저 완료해 다른 두 후속 feature 의 의존성을 제거.
- 스펙 자체가 작고 독립적 (FR 5~7개) → 1 사이클로 마무리 가능.

## 2. Functional Requirements

| ID | 요구사항 | 우선순위 |
|---|---|---|
| **FR-S01** | `GET /api/chat/stream?session_id=...&message=...` — SSE 엔드포인트 (`text/event-stream`) | High |
| **FR-S02** | 이벤트 타입: `tool_call` (tool name + args), `tool_result` (요약), `token` (assistant 문장 조각), `done` (hops + final), `error` | High |
| **FR-S03** | LLM 스트리밍 — Gemini `streamGenerateContent` 사용, 폴백 model 지원 유지 | High |
| **FR-S04** | 기존 `POST /api/chat` 는 하위호환 유지 (비-스트리밍 클라이언트용) | Medium |
| **FR-S05** | 프론트 `ReadableStream` + `TextDecoder` 기반 파서 (`src/lib/sseClient.ts`) | High |
| **FR-S06** | `/chat` 페이지에서 **점진 렌더링**: user 전송 → `tool_call` 버블 즉시 등장 → `tool_result` 도착 → assistant 토큰 스트림 | High |
| **FR-S07** | 취소 지원 — `AbortController` 로 스트림 중단, 백엔드는 client disconnect 감지 후 루프 종료 | Medium |
| **FR-S08** | 테스트: 이벤트 직렬화 단위테스트 + 통합(stub LLM) SSE frame 검증 | Medium |

## 3. Non-Functional
- First byte ≤ 1.5s (tool_call 이벤트 기준)
- 취소 후 서버 리소스 누수 0 (`request.is_disconnected()`)
- 스트림 실패 시 자동 1회 재시도 후 비-스트리밍 fallback

## 4. Files
| 파일 | 변경 |
|---|---|
| `api/routers/chat.py` | `GET /api/chat/stream` 추가 |
| `api/services/chat_service.py` | `run_chat_stream(...) -> AsyncGenerator[ChatEvent]` 신규 |
| `api/services/chat_events.py` | Pydantic event 모델 (신규) |
| `mcp_server/tools/llm.py` | `_call_gemma_stream` 추가 |
| `dashboard/src/lib/sseClient.ts` | fetch + ReadableStream SSE 파서 (신규) |
| `dashboard/src/app/chat/page.tsx` | 기존 send() → streaming 모드로 교체, 점진 렌더링 |
| `tests/test_chat_stream.py` | frame serialization + cancellation |

## 5. Dependencies (downstream)
- `mcp-chatbot-performance` FR-P03 (병렬 tool 실행 시 tool_call 이벤트 필요) ← streaming
- `mcp-chatbot-ux` FR-U04 (실시간 진행 상태 UI) ← streaming

## 6. Out of scope
- WebSocket/양방향 전이중 (추후 필요 시 별도)
- 히스토리 영구 저장 (performance feature 에서 다룸)

## 7. Success Criteria
1. "AI 반도체 추천" 질의 → 1.5s 이내 첫 이벤트(도구 실행 중 표시)
2. assistant 텍스트가 타자기처럼 점진 렌더
3. 스트리밍 취소 후 5s 내 서버 루프 종료 (로그 확인)
4. `/pdca analyze` match rate ≥ 90%
