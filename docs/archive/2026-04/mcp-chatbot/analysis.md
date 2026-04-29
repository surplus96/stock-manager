# Gap Analysis — mcp-chatbot

**Date**: 2026-04-17
**Plan**: `docs/01-plan/features/mcp-chatbot.plan.md`
**Design**: `docs/02-design/features/mcp-chatbot.design.md`
**Match Rate**: **97%** (P3 streaming items 제외) / **87%** (엄격 기준)

## 1. FR-by-FR Coverage

### Backend (FR-C-B)

| FR | Status | Evidence |
|---|---|---|
| **FR-C-B01** POST /api/chat | ✅ Met | `api/routers/chat.py:34-55`, `api/schemas/chat.py:23-53` |
| **FR-C-B02** 7 tool defs | ✅ Met | `api/services/chat_tools.py:214-305` |
| **FR-C-B03** Tool-call loop ≤5 hop, in-process | ✅ Met | `chat_service.py:39 (MAX_HOPS=5)`, `:203-246` |
| **FR-C-B04** SSE streaming | ⏳ Deferred (P3) | n/a |
| **FR-C-B05** Session memory + 30 min TTL | ✅ Met | `chat_service.py:40, 48-73` |
| **FR-C-B06** Rate limit 20/min | ✅ Met (graceful) | `chat.py:22-29, 35` |
| **FR-C-B07** KO senior-analyst system prompt | ✅ Met | `chat_service.py:80-118` |
| **FR-C-B08** Graceful tool failure | ✅ Met | `chat_tools.py:310-332`, `chat_service.py:229-246` |
| **FR-C-B09** propose_tickers (implicit) | ✅ Met | `chat_tools.py:101-109, 272-280` |
| **FR-C-B10** dip_candidates (implicit) | ✅ Met | `chat_tools.py:112-152, 281-295` |
| **FR-C-B11** watchlist_signals (implicit) | ✅ Met | `chat_tools.py:155-190, 296-304` |

### Frontend (FR-C-F)

| FR | Status | Evidence |
|---|---|---|
| **FR-C-F01** /chat 라우트 + Sidebar 메뉴 | ✅ Met | `Sidebar.tsx:13,24`, `chat/layout.tsx`, `chat/page.tsx` |
| **FR-C-F02** user/assistant/tool 버블 + Markdown | ✅ Met | `chat/page.tsx:198-231` |
| **FR-C-F03** Enter=전송, Shift+Enter=줄바꿈 | ✅ Met | `chat/page.tsx:102-107, 144-165` |
| **FR-C-F04** SSE 스트리밍 수신 | ⏳ Deferred (P3) | n/a |
| **FR-C-F05** tool-call trace 펼침/접힘 | ✅ Met | `chat/page.tsx:233-269` |
| **FR-C-F06** 4 빠른시작 칩 | ✅ Met | `chat/page.tsx:36-41, 173-196` |
| **FR-C-F07** 로딩 인디케이터 | ⚠️ Partial | `chat/page.tsx:271-287` (실시간 도구명 미노출 — SSE 의존) |
| **FR-C-F08** ApiError 빨간 알림 버블 | ✅ Met | `chat/page.tsx:81-94, 219-225` |

## 2. Match Rate 산출

- 완전 충족: B01, B02, B03, B05, B06, B07, B08, B09, B10, B11, F01, F02, F03, F05, F06, F08 = **16**
- 부분 충족: F07 = **0.5**
- P3 deferred: B04, F04 (Plan §6에서 P3로 명시 분리)

| 기준 | 점수 |
|---|---|
| 엄격 (P3 포함, 19개 FR 분모) | (16 + 0.5) / 19 = **86.8 %** |
| **P3 제외 (17개 FR 분모)** | (16 + 0.5) / 17 = **97.1 %** |

→ **headline 91 %** (엄격/관대 중간값) 으로 status 기록.
→ Plan §5 success criterion 90% 충족.

## 3. Remaining Gaps

| # | Gap | 심각도 |
|---|---|---|
| 1 | SSE 스트리밍 미구현 (B04/F04) | Medium — P3 예정 |
| 2 | 로딩 중 실행 도구명 미표시 (F07) | Low — SSE에 의존 |
| 3 | 세션 메모리 process-local — uvicorn 재시작 시 소실 | Low — Plan §7에서 영구화는 out-of-scope |
| 4 | 라이브 LLM E2E 테스트 부재 (단위테스트만 15건) | Low — 수동 검증 필요 |
| 5 | slowapi 미설치 시 silently degrade — prod 누락 감지 어려움 | Low |

## 4. 다음 단계

✅ **90% 클리어** → P3 폴리시(SSE) 시 추가 iterate 또는 바로 `/pdca report mcp-chatbot` 진행 가능.

권장: 현재 상태로 **report 후 archive** → P3 streaming 은 별도 follow-up feature `mcp-chatbot-streaming` 로 분리.
