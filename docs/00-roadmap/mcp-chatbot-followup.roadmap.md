# Roadmap — mcp-chatbot Follow-up

> `mcp-chatbot` (archive 후) → 3개 후속 feature 를 순차/병렬 진행하고
> 최종적으로 **하나의 통합 릴리스** 로 병합.

## 1. Dependency graph

```
            mcp-chatbot ✅ (archived)
                    │
                    ▼
         ┌──────────────────────┐
         │ mcp-chatbot-streaming│   ← 기반 레이어 (SSE 이벤트)
         │ (FR-S01..S08)        │
         └─────────┬────────────┘
                   │ unblocks ──────────────┐
                   ▼                        ▼
       ┌──────────────────────┐   ┌──────────────────────┐
       │ mcp-chatbot-         │   │ mcp-chatbot-ux       │
       │ performance          │   │ (FR-U01..U17)        │
       │ (FR-P01..P12)        │   │                      │
       └─────────┬────────────┘   └──────────┬───────────┘
                 │                           │
                 └──────────┬────────────────┘
                            ▼
              ┌─────────────────────────────┐
              │ Integration branch          │
              │ feat/mcp-chatbot-v2         │
              │ (3-way merge + QA + docs)   │
              └────────────┬────────────────┘
                           ▼
                    Production release
                    mcp-chatbot v2.0
```

## 2. Execution order

| 단계 | Feature | 예상 기간 | 블로커 |
|---|---|---|---|
| **1** | `mcp-chatbot-streaming` | 1~2일 | 없음 |
| **2 (parallel)** | `mcp-chatbot-performance` | 2~3일 | streaming P1 완료 (FR-P03 병렬 tool UI 피드백용) |
| **2 (parallel)** | `mcp-chatbot-ux` | 3~4일 | streaming P1 완료 (FR-U04/05/06 스트리밍 UX) |
| **3** | Integration branch + QA | 0.5일 | streaming/performance/ux 모두 analyze ≥90% |
| **4** | Release + archive 3종 | 0.5일 | QA 통과 |

## 3. Branch strategy (git)

```
main
 ├── feat/mcp-chatbot-streaming      (PR → main, squash merge)
 ├── feat/mcp-chatbot-performance    ← branches from streaming
 ├── feat/mcp-chatbot-ux             ← branches from streaming
 └── feat/mcp-chatbot-v2-integration ← merges perf + ux, then → main
```

**Merge 원칙**
1. streaming 먼저 main 에 병합 (기반 API 안정화)
2. performance + ux 는 streaming head 에서 분기하여 병렬 개발
3. 둘 다 analyze ≥ 90% 도달 시 integration 브랜치에서 통합 병합
   - 충돌 예상 지점: `dashboard/src/app/chat/page.tsx` (ux 가 2-pane 으로 전체 재작성, performance 는 retry UI 삽입)
   - 해결: ux 브랜치가 최종 shell 을 소유, performance 는 page.tsx 변경 최소화 + `api.ts` / hook 레이어에만 변경 집중
4. integration 브랜치에서 Zero Script QA (qa-monitor agent) 수행 후 main 병합

## 4. PDCA cadence per feature

각 feature 는 독립 PDCA 사이클:
```
plan → design → do → analyze → (iterate?) → report → archive
```
`/pdca` 스킬 그대로 적용. integration 단계는 **별도 PDCA 사이클 없이**
3 feature archive 후 통합 릴리스 노트로 대체.

## 5. Shared contracts (고정)

다음 인터페이스는 streaming 완료 시점에 확정되며 performance/ux 가 의존:

### SSE Event schema (streaming → UX/performance)
```typescript
type ChatEvent =
  | { type: "tool_call"; tool: string; args: Record<string, unknown>; hop: number }
  | { type: "tool_result"; tool: string; ok: boolean; summary: string; ms: number }
  | { type: "token"; text: string }
  | { type: "done"; hops: number; session_id: string }
  | { type: "error"; message: string; retriable: boolean };
```

### Model Selector contract (performance → UX)
```typescript
GET  /api/chat/models  → { available: string[], default: string }
POST /api/chat?model=  → allows per-request override
```

이 두 계약이 freeze 되면 performance 와 ux 는 완전 병렬 개발 가능.

## 6. Definition of Done (통합)

- [ ] 3 feature 각각 analyze ≥ 90%, report, archive 완료
- [ ] integration 브랜치에서 E2E: "AI 반도체 추천" + Stop + Regenerate + 다크모드 + ⌘K 빠른시작 모두 동작
- [ ] Lighthouse performance ≥ 85, a11y ≥ 95
- [ ] 503 복구 + 세션 영속성 실제 재시작 후 확인
- [ ] `docs/archive/YYYY-MM/mcp-chatbot-v2/` 에 통합 릴리스 노트 작성

## 7. Risks & mitigations

| Risk | Mitigation |
|---|---|
| streaming 이벤트 스키마 변경 → UX/performance 재작업 | §5 계약을 streaming do 시작 전에 lock, 변경은 3-way sync 필요 |
| Gemini native function calling 지원 미정 → FR-P02 연기 가능 | fallback: 현재 JSON prompt-hack 유지 + 다른 FR 로 대체 커버 |
| UX 2-pane 재작성이 streaming 점진 렌더와 충돌 | ux 의 Conversation 컴포넌트가 streaming hook 을 prop 으로 수신하는 구조로 설계 |
| 3 feature 동시 진행 중 main drift | 주간 rebase 의무화 (매주 월요일) |
