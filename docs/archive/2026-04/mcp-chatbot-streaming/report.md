# Completion Report — mcp-chatbot-streaming

**Feature**: `mcp-chatbot-streaming` (follow-up #1 of mcp-chatbot v2)
**Period**: 2026-04-19 (single day)
**Match Rate**: **98%**
**Iterations**: 0
**Tests**: 29 / 29

## 1. Delivered

### Backend
- `api/services/chat_events.py` — 5종 이벤트 Pydantic 스키마 + SSE 직렬화
- `api/services/chat_stream_service.py` — `run_chat_stream(...) -> AsyncIterator[bytes]`
  - 512자 버퍼 기반 tool-call vs 답변 판별
  - hop 경계 + 청크 경계 + tool dispatch 직전 3 곳에서 `request.is_disconnected()` 체크
  - 블로킹 SSE consumer 는 `run_in_executor` 로 감싸서 이벤트 루프 비차단
  - `X-Request-ID` comment frame 선행 출력 (로그 상관관계)
- `mcp_server/tools/llm.py` — `_call_gemma_stream` (Gemini `:streamGenerateContent?alt=sse`, 내부 1회 non-stream fallback)
- `api/routers/chat.py` — `GET /api/chat/stream` 추가, `POST /api/chat` 보존

### Frontend
- `dashboard/src/lib/chatEvents.ts` — TypeScript discriminated union (Python 스키마 1:1)
- `dashboard/src/lib/sseClient.ts` — fetch + ReadableStream + AbortController 파서
- `dashboard/src/app/chat/page.tsx` — 전체 리팩토링
  - `openChatStream` 기반 점진 렌더링
  - `tool_call` → "실행 중…" placeholder → `tool_result` 도착 시 summary + ms 로 업데이트
  - `token` 이벤트 → BlinkingCaret 와 함께 assistant 드래프트에 append
  - Stop 버튼 (Square 아이콘) → AbortController.cancel
  - 첫 이벤트 도착 전 스트림 실패 시 **자동 POST fallback** → UX 단절 방지

### Tests (29/29)
- 기존 chat (18) + streaming (11)
- 신규: serialize roundtrip ×5, parse rejects, final-only, tool→result→token→done, 취소, 503 friendly, X-Request-ID comment

## 2. 핵심 설계 결정

| 결정 | 근거 |
|---|---|
| 512자 버퍼 tool-call 판별 | JSON tool call 은 항상 512자 미만. 버퍼 초과 시 즉시 token 모드 전환 → 첫 화면 도달 빠름 |
| 블로킹 consumer → threadpool 위임 | `requests` + iter_lines 는 동기. 이벤트 루프 점유 방지 |
| 서버는 ErrorEvent, 클라이언트는 POST fallback | 서버 fallback 복잡도 낮추고 클라이언트에서 명확한 UX 제어 |
| `: req-id=...` SSE comment | 파서에 영향 없이 로그 상관관계 확보 |
| 공용 이벤트 스키마 freeze | performance/ux feature 가 의존 — roadmap §5 |

## 3. Freezed contracts (UX/performance 의존)

```typescript
type ChatEvent =
  | { type: "tool_call"; tool: string; args: Record<string, unknown>; hop: number }
  | { type: "tool_result"; tool: string; ok: boolean; summary: string; ms: number; hop: number }
  | { type: "token"; text: string }
  | { type: "done"; hops: number; session_id: string }
  | { type: "error"; message: string; retriable: boolean };
```
- `/api/chat/stream?message=&session_id=` (GET, SSE)
- `/api/chat` (POST, Envelope) — backward compat fallback

## 4. Lessons learned

1. **점진 렌더링 UX 는 첫 tool_call 이벤트 1초 내 표시가 핵심** — 512자 버퍼 크기가 그 임계선을 결정.
2. **취소 체크포인트는 "모든 I/O 경계"에 넣어야** — hop 사이만 검사하면 10초짜리 tool 실행 중 취소가 늦어짐.
3. **SSE comment (`:` 접두)를 활용하면 프로토콜 깨지 않고 메타데이터 실을 수 있음**.
4. **클라이언트 fallback 은 첫 이벤트 도착 여부를 기준으로** — fallback 트리거를 시간이 아닌 "받은 데이터" 기준으로 결정하면 false positive 가 없음.

## 5. Follow-up sequence

| # | Feature | 병합 대상 |
|---|---|---|
| 1 | `mcp-chatbot-streaming` ✅ (현재) | main |
| 2a | `mcp-chatbot-performance` (parallel) | streaming head 에서 분기 |
| 2b | `mcp-chatbot-ux` (parallel) | streaming head 에서 분기 |
| 3 | `feat/mcp-chatbot-v2-integration` | perf + ux 3-way merge → main |

다음 액션:
- `/pdca design mcp-chatbot-performance` (모델 교체, native function calling, Redis)
- `/pdca design mcp-chatbot-ux` (2-pane, ⌘K, 다크모드, 벤치마크)
- 두 디자인은 병렬 진행 가능

## 6. Metrics

| 항목 | 값 |
|---|---|
| 신규 파일 | 5 (backend 3, frontend 2) |
| 수정 파일 | 4 (chat.py, llm.py, page.tsx, Sidebar 무변경) |
| 단위 테스트 | +11 (총 29) |
| 공용 계약 확정 | ChatEvent 스키마 + `/api/chat/stream` |
| 소요 시간 | ~2시간 (plan→archive) |
