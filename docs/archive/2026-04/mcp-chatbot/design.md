# Design — mcp-chatbot

## 1. Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│  Browser  /chat                                                    │
│  ChatPage  (useState messages, fetch /api/chat)                    │
│   ├── MessageList (user / assistant / tool 버블)                   │
│   ├── ToolTrace (펼침/접힘)                                        │
│   └── Composer (textarea + 전송)                                   │
└──────────────────────────────┬─────────────────────────────────────┘
                               │ POST /api/chat
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│  FastAPI  api/routers/chat.py                                      │
│   POST /api/chat ─▶ ChatService.run(messages, session_id)          │
│   GET  /api/chat/session/{id} ─▶ history (디버그)                  │
└──────────────────────────────┬─────────────────────────────────────┘
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│  api/services/chat_service.py                                      │
│   • build_system_prompt(tools)                                     │
│   • run loop (max_hops=5):                                         │
│       1. _call_gemma(system, transcript) → raw_text                │
│       2. parse_tool_call(raw_text)                                 │
│           ├─ if {"tool": ...} ─▶ dispatch & append observation     │
│           └─ else (final) ─▶ break, return answer                  │
│   • session_memory: dict[str, list[Message]] (TTL 30분)            │
└──────────────────────────────┬─────────────────────────────────────┘
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│  api/services/chat_tools.py                                        │
│   TOOL_REGISTRY = {                                                │
│     "propose_themes":      lambda lookback_days=7: ...,            │
│     "analyze_theme":       lambda theme, top_n=5: ...,             │
│     "rank_stocks":         lambda tickers: ...,                    │
│     "stock_comprehensive": lambda ticker: ...,                     │
│     "stock_signal":        lambda ticker: ...,                     │
│     "news_sentiment":      lambda tickers, lookback_days=7: ...,   │
│     "market_condition":    lambda: ...,                            │
│   }                                                                │
│   각 tool은 mcp_server.tools.* 함수를 직접 호출 (REST 우회)       │
└────────────────────────────────────────────────────────────────────┘
```

## 2. Why prompt-based tool calling (not Gemini SDK function calling)?

`GEMINI_MODEL` 기본값이 **`gemma-4-26b-a4b-it`** (Gemma 4) 인데 Gemma는 native
function calling 미지원. 환경변수로 Gemini Pro로 전환 가능하더라도 호환을 위해
**프롬프트 기반 JSON 툴콜** 방식을 채택한다.

### Protocol (system prompt에 박아넣음)

```
당신은 시니어 금융 애널리스트입니다. 사용자 질문에 답하기 위해 아래 도구를
사용할 수 있습니다.

도구 목록:
- propose_themes(lookback_days: int=7) — 최근 시장 이슈 기반 테마 제안
- analyze_theme(theme: str, top_n: int=5) — 테마 종목 + 랭킹 분석
- rank_stocks(tickers: str) — 콤마 구분 티커 멀티팩터 랭킹
- stock_comprehensive(ticker: str) — 종목 종합 분석
- stock_signal(ticker: str) — 매수/매도 시그널
- news_sentiment(tickers: str, lookback_days: int=7) — 뉴스 센티먼트
- market_condition() — Bull/Bear 판단

도구를 호출하려면 **JSON 한 줄만** 출력하세요:
{"tool": "도구이름", "args": {...}}

도구 결과를 받으면 자연어로 답하거나 다른 도구를 호출하세요.
최종 답변은 도구 호출 없이 일반 텍스트로 작성하세요. 수치 인용 필수.
```

### Parse rule
- 첫 줄이 `{` 으로 시작하고 `"tool"` 키 포함 → tool call
- 그 외 → 최종 답변
- JSON parse 실패 시 → 최종 답변으로 간주 (graceful)

## 3. API contract

### `POST /api/chat`
**Request**
```json
{
  "session_id": "uuid-string-or-null",
  "message": "AI 반도체 테마 추천해줘"
}
```

**Response** (Envelope[T])
```json
{
  "data": {
    "session_id": "uuid-string",
    "answer": "AI 반도체 테마는 ...",
    "trace": [
      {"tool": "propose_themes", "args": {"lookback_days": 7}, "result_summary": "10개 테마 제안"},
      {"tool": "analyze_theme",  "args": {"theme": "AI semiconductor"}, "result_summary": "5개 종목 랭킹"}
    ],
    "hops": 2
  },
  "generated_at": "2026-04-17T...",
  "version": "1.0"
}
```

### Schemas — `api/schemas/chat.py`
```python
class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str = Field(min_length=1, max_length=2000)

class ToolTrace(BaseModel):
    tool: str
    args: dict
    result_summary: str  # 처음 200자 또는 row count

class ChatResponseData(BaseModel):
    session_id: str
    answer: str
    trace: list[ToolTrace] = []
    hops: int = 0
```

## 4. Session memory

- `_SESSIONS: dict[str, dict] = {}` — module-global
- key: session_id (UUID4)
- value: `{"messages": [...], "last_used": datetime}`
- TTL: 30분, 매 요청마다 만료된 항목 lazy cleanup
- 메시지는 `[{"role": "user"|"assistant"|"tool", "content": str}]`

## 5. Frontend — `/chat`

### File: `dashboard/src/app/chat/page.tsx`

```typescript
"use client";
import { useState, useRef, useEffect } from "react";
import { api } from "@/lib/api";

interface ChatMessage {
  role: "user" | "assistant" | "tool";
  content: string;
  trace?: ToolTrace[];
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function send() {
    const text = input.trim();
    if (!text || loading) return;
    setMessages(m => [...m, { role: "user", content: text }]);
    setInput("");
    setLoading(true);
    try {
      const res = await api.chat(text, sessionId);
      setSessionId(res.session_id);
      setMessages(m => [...m, { role: "assistant", content: res.answer, trace: res.trace }]);
    } catch (e) {
      setMessages(m => [...m, { role: "assistant", content: `오류: ${String(e)}` }]);
    } finally {
      setLoading(false);
    }
  }
  // ... UI
}
```

### Sidebar entry
`dashboard/src/components/Sidebar.tsx` 의 NAV_ITEMS에 추가:
```typescript
{ href: "/chat", label: "Chatbot", icon: MessageSquare }
```

### API client extension
`dashboard/src/lib/api.ts` 에 추가:
```typescript
chat: (message: string, sessionId?: string | null) =>
  fetchPOST<ChatResponseData>("/api/chat", { message, session_id: sessionId }, 120_000),
```
→ `fetchPOST` helper 신규 추가 (기존 `fetchAPI` 는 GET 전용)

## 6. File-level targets

| 파일 | 변경 내용 | 신규/수정 |
|---|---|---|
| `api/schemas/chat.py` | ChatRequest, ToolTrace, ChatResponseData | 신규 |
| `api/services/chat_tools.py` | TOOL_REGISTRY (7개 어댑터) | 신규 |
| `api/services/chat_service.py` | build_system_prompt, run_chat, session memory | 신규 |
| `api/routers/chat.py` | POST /api/chat, GET /api/chat/session/{id} | 신규 |
| `api/server.py` | `app.include_router(chat.router)` | 수정 |
| `tests/test_chat_service.py` | tool dispatch + parse_tool_call 단위 테스트 | 신규 |
| `dashboard/src/lib/api.ts` | `chat()` + `fetchPOST` 추가 | 수정 |
| `dashboard/src/lib/api.types.ts` | ChatResponseData, ToolTrace 타입 | 수정 |
| `dashboard/src/app/chat/page.tsx` | 챗 UI | 신규 |
| `dashboard/src/app/chat/layout.tsx` | metadata `Chatbot — Stock Manager` | 신규 |
| `dashboard/src/components/Sidebar.tsx` | NAV_ITEMS에 `/chat` 추가 | 수정 |

## 7. Implementation order (Do phase)

1. **Backend P1** (~30분)
   - schemas → tool registry → service → router → server.include_router
   - 단위 테스트 (mock LLM 으로 parse/dispatch 검증)
2. **Frontend P2** (~30분)
   - api.ts 확장 → page.tsx → layout.tsx → Sidebar 메뉴
3. **수동 검증**
   - "AAPL 매수 의견?" → stock_signal/comprehensive 호출 확인
   - "AI 반도체 테마 추천" → propose_themes/analyze_theme 호출 확인

P3 (스트리밍/세션 메모리 강화)는 P1+P2 검증 후 순차 진행.

## 8. Risk & Mitigation

| Risk | Mitigation |
|---|---|
| Gemma가 JSON 형식 안 지키고 자유텍스트 출력 | parse 실패 → 최종 답변으로 fallback |
| 무한 tool call 루프 | `max_hops=5` hard limit |
| LLM 비용 폭주 | rate limit `20/min`, max_tokens 2048 |
| tool 실행 중 예외 | try/except → "tool error: ..." observation 으로 LLM 에 전달 |
| 세션 메모리 leak | 매 요청마다 30분 만료 lazy cleanup |
