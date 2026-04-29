# Plan — mcp-chatbot

> **Goal**: PM-MCP의 분석 도구를 LLM Function-Calling 으로 호출해 답변하는 대화형
> 챗봇을 백엔드(`/api/chat`) + 프론트엔드(`/chat` 페이지)에 추가한다.

## 1. Background

기존 대시보드는 페이지별로 데이터를 보여주는 정적 인터페이스다. 사용자가
**"AI 반도체 테마에서 매수 시그널 강한 종목 추천해줘"** 같은 자연어 질의를 하면
- 적절한 MCP 도구를 자동 선택하고
- 결과를 종합해 한국어로 답하는

대화형 인터페이스가 필요하다. 새 종목/테마 추천 + 분석 시나리오에 우선 집중한다.

## 2. Scope

| Layer | In Scope | Out of Scope |
|---|---|---|
| Backend | `/api/chat` (Gemini Function Calling), 7개 tool 매핑, 멀티턴 메모리(세션 단위), SSE 스트리밍 | RAG, 사용자 인증, 대화 영구 저장 |
| Frontend | `/chat` 페이지, 메시지 리스트, tool-call trace 표시, 스트리밍 렌더 | 음성 입력, 멀티 세션 탭, 첨부파일 |
| LLM | Google Gemini (`_call_gemma`의 모델 동일) — `tools=` 파라미터로 function calling | OpenAI / Anthropic SDK |

## 3. Functional Requirements (FR)

### Backend (FR-C-B)
| ID | 요구사항 | 우선순위 |
|---|---|---|
| **FR-C-B01** | `POST /api/chat` 엔드포인트: `{messages, session_id?}` → assistant 응답 + tool_calls trace | High |
| **FR-C-B02** | 7개 tool 정의 (Gemini function declaration): `propose_themes`, `analyze_theme`, `rank_stocks`, `stock_comprehensive`, `stock_signal`, `news_sentiment`, `market_condition` | High |
| **FR-C-B03** | LLM tool-calling 루프 (최대 5 hop), 각 tool은 기존 `mcp_server/tools/*` 함수 직접 호출 (REST 우회 → 레이턴시 절감) | High |
| **FR-C-B04** | SSE 스트리밍 (`text/event-stream`): assistant 토큰 + tool_call 이벤트 push | Medium |
| **FR-C-B05** | 세션 메모리 (in-memory dict, TTL 30분) — `session_id`로 멀티턴 유지 | Medium |
| **FR-C-B06** | rate limit `@limiter.limit("20/minute")` (LLM 비용 보호) | Medium |
| **FR-C-B07** | 한국어 system prompt: "시니어 금융 애널리스트, 수치 인용 필수, 도구 결과 근거 명시" | High |
| **FR-C-B08** | tool 실행 실패 시 graceful degradation (에러 메시지를 LLM 에 다시 전달해 자연어 사과) | Low |

### Frontend (FR-C-F)
| ID | 요구사항 | 우선순위 |
|---|---|---|
| **FR-C-F01** | `/chat` 페이지 라우트 + Sidebar 메뉴 추가 (lucide `MessageSquare` 아이콘) | High |
| **FR-C-F02** | 메시지 리스트 (user / assistant / tool 3종 버블), Markdown 렌더 (기존 `<Markdown>` 재사용) | High |
| **FR-C-F03** | 입력창 (Enter=전송, Shift+Enter=줄바꿈), 전송 중 비활성화 | High |
| **FR-C-F04** | SSE 스트리밍 수신 + 점진적 텍스트 렌더 (`fetch` + `ReadableStream`) | Medium |
| **FR-C-F05** | tool-call trace 펼침/접힘 (디버그용, 호출 도구·인자·결과 요약) | Medium |
| **FR-C-F06** | 빠른 시작 칩 4개: "AI 반도체 테마 추천", "오늘 강세 섹터?", "AAPL 매수 의견?", "내 포트폴리오 진단" | Low |
| **FR-C-F07** | 로딩 인디케이터 (도구 실행 중 텍스트: "⚙ rank_stocks 실행 중…") | Medium |
| **FR-C-F08** | API 에러 처리 (`ApiError` catch → 빨간 알림 버블) | Medium |

## 4. Non-Functional

- **Latency**: p50 < 8s, p95 < 25s (Gemini + tool 1회 hop 기준)
- **Cost guard**: 1 요청당 max 5 hop, 출력 max 2048 토큰
- **Security**: API key는 서버 환경변수만 사용, 프론트로 노출 금지
- **Accessibility**: 메시지 리스트 `role="log" aria-live="polite"`

## 5. Success Criteria

1. "AI 반도체 테마 매수 추천" 질의 → `propose_themes` → `analyze_theme` → `rank_stocks` 자동 호출 후 종목 3개 + 근거 요약 반환
2. "AAPL 종합 분석" 질의 → `stock_comprehensive` + `news_sentiment` 호출 후 한국어 리포트 반환
3. 멀티턴: "더 자세히" / "다른 종목은?" 가능
4. tool 실패 시 사과 메시지로 graceful degradation
5. Gap analysis match rate ≥ 90%

## 6. Phased Roadmap

| Phase | 범위 | 산출물 |
|---|---|---|
| **P1** Backend Core | FR-C-B01/02/03/07 (sync, no streaming) | `api/routers/chat.py`, `api/services/chat_tools.py`, `api/schemas/chat.py` |
| **P2** Frontend MVP | FR-C-F01/02/03/06/08 | `dashboard/src/app/chat/page.tsx`, `Sidebar.tsx` 메뉴 추가 |
| **P3** Polish | FR-C-B04/05/06/08, FR-C-F04/05/07 | SSE 스트리밍, 세션 메모리, trace UI |

P1+P2 우선 완성 → 데모 가능 상태 확보 → P3 점진 추가.

## 7. Out of scope (명시적 제외)

- 사용자 인증 / 대화 영구 저장 (DB 스키마 없음)
- 다국어 (한국어 only)
- pm-mcp **stdio MCP 프로토콜** 우회 — in-process tool 호출로 단순화 (필요 시 후속 feature)
- 음성 / 파일 업로드
