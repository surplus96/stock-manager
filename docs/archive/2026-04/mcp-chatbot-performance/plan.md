# Plan — mcp-chatbot-performance

> **Goal**: 챗봇 응답 속도와 안정성을 production-grade 수준으로 끌어올린다.
> 503 폭주, 툴 실행 직렬화, 세션 휘발성 같은 운영 리스크를 제거한다.

## 1. Problem statement (measured)

| 증상 | 수치 (현재) | 목표 |
|---|---|---|
| 첫 응답 p50 (1 hop) | ~8~12s | **≤ 4s** |
| 첫 응답 p95 (2~3 hop) | 25~60s / 타임아웃 | **≤ 15s** |
| LLM 503 최근 24h | > 15회 / `gemini-3.1-flash-lite-preview` | **≤ 1%** |
| uvicorn 재시작 → 세션 소실 | 100% | 0% |
| tool 병렬화 | 순차 1개씩 | N hop 내 **병렬** |

## 2. Functional Requirements

### 모델 & 호출
| ID | 요구사항 |
|---|---|
| **FR-P01** | 기본 `GEMINI_MODEL` 을 안정 모델로 교체 (`gemini-2.0-flash` 권장) + preview 모델은 opt-in |
| **FR-P02** | Gemini Native Function Calling (`tools=[{functionDeclarations}]`) — JSON prompt-hack 제거로 hallucinated tool 호출 감소, 파싱 실패율 0 목표 |
| **FR-P03** | 멀티 tool call 병렬 실행 — Gemini 한 턴에 여러 function call 반환 가능 시 `asyncio.gather` 로 동시 처리 |
| **FR-P04** | 시스템/사용자 프롬프트 토큰 캐싱 (Gemini Context Cache API) — 반복 호출 시 40% 이상 latency 절감 |

### 신뢰성
| ID | 요구사항 |
|---|---|
| **FR-P05** | 기존 `_call_llm_resilient` 를 `mcp_server.tools.llm` 으로 이동, 모든 LLM 호출자에 적용 |
| **FR-P06** | Circuit breaker 임계치 튜닝 — Gemini 1분 5fail 시 open, 60s 후 half-open |
| **FR-P07** | Tool 레벨 타임아웃 (기본 20s) + 부분 실패 허용 (`analyze_theme` 내부 `rank` 실패 시 tickers 만 반환) |

### 세션 / 관측성
| ID | 요구사항 |
|---|---|
| **FR-P08** | 세션 저장소를 **Redis** 로 교체 (또는 `~/.cache/pm-mcp/chat-sessions/*.json` 파일 백업). Redis URL 없으면 in-memory fallback |
| **FR-P09** | 구조화 로깅 — `session_id`, `hop`, `tool`, `latency_ms`, `outcome` 필드 JSON 로그 |
| **FR-P10** | `/api/chat/metrics` (Envelope[dict]) — hop count / p50 latency / tool error rate 노출 |

### Frontend 보강
| ID | 요구사항 |
|---|---|
| **FR-P11** | `api.chat` retry — 503/타임아웃 시 1회 재시도, 두 번째 실패는 명확한 에러 UI |
| **FR-P12** | 입력 debouncing (연타 방지) + optimistic echo |

## 3. Phased
| Phase | 범위 | 기대 효과 |
|---|---|---|
| P1 모델/호출 | FR-P01/02/03 | latency −40% 체감 |
| P2 신뢰성 | FR-P04/05/06/07 | 503 복구율 99% |
| P3 관측/세션 | FR-P08/09/10 | 운영 가능 수준 |
| P4 FE 보강 | FR-P11/12 | 사용자 체감 안정성 |

## 4. Depends on
- `mcp-chatbot-streaming` (FR-P03 병렬 tool은 streaming 이벤트로 UI 피드백 필수)

## 5. Success Criteria
1. p50 first-byte ≤ 4s (streaming 활성 상태 기준)
2. 503 → fallback 자동 복구율 ≥ 99% (24h 텔레메트리)
3. uvicorn 재시작 후 세션 유지 (Redis 또는 파일)
4. Gemini native function calling 사용 시 파싱 실패 0건
5. `/pdca analyze` match rate ≥ 90%
