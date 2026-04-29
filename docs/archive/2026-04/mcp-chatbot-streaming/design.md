# Design — mcp-chatbot-streaming

## 1. Architecture

```
Browser /chat                                          FastAPI
──────────────────                                     ─────────────────────────────
ChatPage                                               GET /api/chat/stream
  └─ sseClient.openStream(message, sessionId)  ───▶    │
      (AbortController, ReadableStream, TextDecoder)   ▼
                                                       chat_stream_service.run_chat_stream
                                                         └─ async generator:
                                                             1. yield tool_call   ┐
                                                             2. exec tool         │ per hop
                                                             3. yield tool_result ┘
                                                             4. LLM stream:
                                                                 yield token (chunks)
                                                             5. yield done
      ◀───── SSE events (line-framed) ────────────────     via sse_response(gen)
```

## 2. Event schema (freeze — shared with performance/ux)

```typescript
// dashboard/src/lib/chatEvents.ts
export type ChatEvent =
  | { type: "tool_call";   tool: string; args: Record<string, unknown>; hop: number }
  | { type: "tool_result"; tool: string; ok: boolean; summary: string; ms: number; hop: number }
  | { type: "token";       text: string }
  | { type: "done";        hops: number; session_id: string }
  | { type: "error";       message: string; retriable: boolean };
```

Python mirror: `api/services/chat_events.py` — Pydantic `BaseModel` per variant,
serialized as JSON. Each SSE frame = `data: <json>\n\n`. No `event:` field —
keeps parser simple and mirrors the discriminated union pattern.

## 3. Endpoint contract

### `GET /api/chat/stream`
Query params:
| name | type | default | note |
|---|---|---|---|
| `message` | string | required | min 1, max 2000 |
| `session_id` | string \| null | null | previous session to continue |

- Response content-type: `text/event-stream; charset=utf-8`
- No-cache headers (`Cache-Control: no-cache, X-Accel-Buffering: no`)
- Rate limit 20/min (reuse slowapi limiter from `POST /api/chat`)

### Cancellation
- Client calls `AbortController.abort()` → fetch closes socket
- Server: FastAPI sets `request.is_disconnected() == True`; the generator
  polls between events and returns early. Session message list is *not*
  updated with a partial answer.

## 4. Backend code layout

| 파일 | 역할 |
|---|---|
| `api/services/chat_events.py` | Pydantic models + `serialize(event) -> str` that returns an SSE frame |
| `api/services/chat_stream_service.py` | `run_chat_stream(message, session_id, request) -> AsyncIterator[bytes]` |
| `api/routers/chat.py` | Adds `GET /api/chat/stream` using `StreamingResponse` |
| `mcp_server/tools/llm.py` | `_call_gemma_stream(system, user) -> Iterator[str]` using Gemini `:streamGenerateContent?alt=sse` (falls back to chunked-split if SSE unsupported) |

### `run_chat_stream` contract
```python
async def run_chat_stream(
    message: str, session_id: str | None, request: Request
) -> AsyncIterator[bytes]:
    ...
    yield serialize(ToolCallEvent(...))
    ...
    yield serialize(DoneEvent(...))
```

### Why async generator
- FastAPI `StreamingResponse(content=async_gen, media_type=...)`
- Cooperative checkpoint: `if await request.is_disconnected(): return` after
  each LLM / tool boundary.

## 5. LLM streaming

Gemini endpoint: `POST /v1beta/models/{model}:streamGenerateContent?alt=sse`
→ emits `data: {candidates: [...]}\n\n` chunks with incremental `parts[0].text`.

Pseudocode in `_call_gemma_stream`:
```python
def _call_gemma_stream(system, user, temperature=0.2):
    payload = {...same as _call_gemma...}
    with requests.post(url + "?alt=sse", json=payload, stream=True, timeout=LLM_TIMEOUT) as r:
        r.raise_for_status()
        for line in r.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            blob = line[len("data: "):].strip()
            if blob == "[DONE]":
                break
            try:
                obj = json.loads(blob)
            except json.JSONDecodeError:
                continue
            delta = ((obj.get("candidates") or [{}])[0]
                     .get("content", {}).get("parts") or [{}])[0].get("text", "")
            if delta:
                yield delta
```

Fallback: if `:streamGenerateContent` returns 4xx/5xx, `run_chat_stream`
catches and emits one big `token` chunk from the non-streaming `_call_gemma`.

## 6. Tool-call interaction with streaming

The existing loop yields **either** a JSON tool call **or** a final answer.
For streaming:

1. Accumulate LLM tokens into a buffer.
2. After the first chunk, try `parse_tool_call(buffer)`. If it returns a
   call, stop streaming the buffer and dispatch the tool (tool_call event).
3. If no tool call is detected after the first N chars (~512), commit to
   "final answer" mode and start emitting `token` events per chunk.

This avoids leaking the raw JSON into the user-visible text stream.

## 7. Frontend

### `dashboard/src/lib/sseClient.ts` (new)
```typescript
export interface StreamHandlers {
  onEvent: (e: ChatEvent) => void;
  onError?: (err: Error) => void;
  onClose?: () => void;
}
export function openChatStream(
  opts: { message: string; sessionId: string | null },
  handlers: StreamHandlers,
): AbortController {
  const ctrl = new AbortController();
  fetch(
    `${API_BASE}/api/chat/stream?message=${encodeURIComponent(opts.message)}`
      + (opts.sessionId ? `&session_id=${opts.sessionId}` : ""),
    { signal: ctrl.signal, headers: { Accept: "text/event-stream" } },
  ).then(async (res) => {
    if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      let idx;
      while ((idx = buf.indexOf("\n\n")) >= 0) {
        const frame = buf.slice(0, idx);
        buf = buf.slice(idx + 2);
        const line = frame.split("\n").find((l) => l.startsWith("data: "));
        if (!line) continue;
        try { handlers.onEvent(JSON.parse(line.slice(6))); }
        catch { /* ignore */ }
      }
    }
    handlers.onClose?.();
  }).catch((e) => {
    if ((e as Error).name !== "AbortError") handlers.onError?.(e);
  });
  return ctrl;
}
```

### `chat/page.tsx` changes
- Replace `await api.chat(...)` with `openChatStream(...)`.
- On `tool_call` → push a placeholder "⚙ tool…" message entry, update with
  `tool_result` when it arrives (ms + ok badge).
- On `token` → append chunk to the *current* assistant draft message,
  creating it on first token.
- On `done` → finalize session id, clear draft flag.
- On `error` → inline red bubble.
- Add `Stop` button wired to `ctrl.abort()`.

Backward compatibility: keep `api.chat()` POST path — used as automatic
fallback when `openChatStream` calls `onError`.

## 8. Tests

`tests/test_chat_stream.py`:
- `serialize_event` roundtrip for each event variant
- `run_chat_stream` with stub LLM producing tool call → tool result → token → done
- cancellation: fake `request.is_disconnected()` returning True after 1st event
- frontend sseClient tests are deferred to manual smoke (vitest integration complex)

## 9. Rate limit / ops

- Reuse `Limiter(key_func=get_remote_address)` at 20/min
- Add `X-Request-ID` passthrough in SSE (first comment line `: req-id=...`)
  for log correlation

## 10. Risk & mitigation

| Risk | Mitigation |
|---|---|
| Gemini :streamGenerateContent 500/무응답 | try/except → fallback 1회 비-스트리밍, error 이벤트 |
| Tool-call 판별이 점진 버퍼에서 흔들림 | 512자까지 버퍼 후 결정, 확정되면 token 재생성 없이 바로 emit |
| Long SSE 연결 → proxy buffering | `X-Accel-Buffering: no` + flush 힌트 (FastAPI 기본 flush) |
| Client race (session_id 못 받고 다음 요청) | onClose 이후에만 입력 활성화 |

## 11. Implementation order

1. `chat_events.py` + serializer
2. `_call_gemma_stream`
3. `run_chat_stream` async generator (with request disconnect checkpoint)
4. `GET /api/chat/stream` wiring + `StreamingResponse`
5. Unit tests (stub LLM generator)
6. `sseClient.ts`
7. `chat/page.tsx` streaming integration + Stop button + fallback
8. 수동 smoke test
