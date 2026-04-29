# Plan — mcp-chatbot-ux

> **Goal**: 현재 챗봇 페이지를 업계 best-practice 수준의 금융 대시보드형
> chat 인터페이스로 재설계. 단순 메시지 리스트 → 대화+패널이 공존하는
> **analyst workbench** 패턴으로 전환.

## 1. Benchmark references

| 서비스 | 참고 포인트 |
|---|---|
| **Perplexity Finance** | Source chip bar, progressive tool citation, Pro mode toggle |
| **ChatGPT (tool UI)** | "Analysis" expandable panel, code/output split, copy/regenerate 버튼 |
| **Claude.ai Artifacts** | Right-side structured result panel (table/chart) alongside chat |
| **Linear chat** | Dense typography, keyboard-first, command palette (⌘K) |
| **Bloomberg Terminal (웹)** | Tabular density, monospaced numbers, high-contrast dark mode |
| **Vercel v0 chat** | Example prompts, smooth streaming cursor, skeleton during tool |

## 2. Target layout (wireframe)

```
┌─────────────────────────────────────────────────────────────────┐
│  Sidebar (기존)  │   Header: "AI Chatbot"  · Session · Model    │
│                  ├──────────────────────────────────────────────┤
│                  │ 2-pane:                                      │
│                  │  ┌──────────────────┬────────────────────┐   │
│                  │  │ Conversation     │ Artifact Panel     │   │
│                  │  │ (55%)            │ (45%, md 이상)     │   │
│                  │  │                  │  ▸ Rankings table  │   │
│                  │  │  • user bubble   │  ▸ Mini candle     │   │
│                  │  │  • tool chip     │  ▸ 뉴스 센티먼트   │   │
│                  │  │  • assistant …   │  (tool 결과 중     │   │
│                  │  │                  │   표 형식은 오른쪽) │   │
│                  │  └──────────────────┴────────────────────┘   │
│                  │ Composer: [textarea] [⌘↵] [Regenerate] [Stop]│
└─────────────────────────────────────────────────────────────────┘
```

- < md: single-column, artifact 은 assistant 메시지 아래에 collapsible
- ⌘K command palette: 빠른시작 질문 + 도구 직접 실행 shortcut

## 3. Functional Requirements

### Layout & 정보 구조
| ID | 요구사항 |
|---|---|
| **FR-U01** | 2-pane 레이아웃 (대화 / 아티팩트). rankings·news 같은 구조화 결과는 오른쪽 패널로 이동 |
| **FR-U02** | 모바일: 단일 컬럼, 아티팩트는 각 assistant 응답 하단 탭 |
| **FR-U03** | 헤더에 **Model Selector** (`gemini-2.0-flash` / `gemini-1.5-pro` / auto) + 세션 ID + New Chat 버튼 |

### 스트리밍 UX (depends on streaming feature)
| ID | 요구사항 |
|---|---|
| **FR-U04** | 진행 중 도구 이름 + spinner + elapsed ms 인라인 표시 (`⚙ analyze_theme… 2.1s`) |
| **FR-U05** | 타자기 커서 (blinking caret) 로 assistant 텍스트 점진 렌더 |
| **FR-U06** | Stop 버튼 — 스트리밍 중 클릭 시 즉시 중단 |
| **FR-U07** | Regenerate 버튼 — 마지막 assistant 제거 후 재생성 |

### 입력 & 단축키
| ID | 요구사항 |
|---|---|
| **FR-U08** | ⌘K (or Ctrl+K) → 빠른 시작/명령어 팔레트 (cmdk 또는 자체) |
| **FR-U09** | ↑ 방향키 → 직전 user message 편집 |
| **FR-U10** | 드래그 앤 드롭 티커(.csv 또는 텍스트) → 자동으로 `rank_stocks` 호출 |

### 결과 렌더링
| ID | 요구사항 |
|---|---|
| **FR-U11** | `rank_stocks`·`analyze_theme` 결과 → 정렬·검색 가능한 테이블 (headless table 패턴) |
| **FR-U12** | `market_condition` → gauge 컴포넌트 재사용 (홈과 일관성) |
| **FR-U13** | news 링크 → hover 시 preview card (1초 딜레이) |
| **FR-U14** | 메시지 hover → Copy / Share / Cite 버튼 |

### 테마 / 접근성
| ID | 요구사항 |
|---|---|
| **FR-U15** | 다크 모드 (system + manual toggle). 토큰은 `@theme` 재사용 |
| **FR-U16** | 포커스 링, 탭 순서 audit (axe-core 자동화 1회) |
| **FR-U17** | 모노스페이스 숫자 (`font-variant-numeric: tabular-nums`) — 표/수치 정렬 |

## 4. Non-functional
- LCP ≤ 1.5s (빈 /chat 로딩 기준)
- Bundle impact ≤ +40 KB gzip (cmdk + tanstack-table headless)
- Lighthouse a11y ≥ 95

## 5. Depends on
- `mcp-chatbot-streaming` (FR-U04/05/06)
- `mcp-chatbot-performance` (FR-U03 모델 셀렉터와 연계)

## 6. Phased
| Phase | 범위 | 산출물 |
|---|---|---|
| P1 구조 | FR-U01/02/03/11/12/17 | 2-pane 레이아웃 + 아티팩트 패널 + table |
| P2 스트리밍 UX | FR-U04/05/06/07 | 진행 표시 + Stop/Regenerate |
| P3 파워유저 | FR-U08/09/10/14 | ⌘K, 히스토리 편집, hover 액션 |
| P4 폴리시 | FR-U13/15/16 | 다크모드, a11y, news preview |

## 7. Out of scope
- 음성 / 파일 첨부 (본격 업로드는 별도 feature)
- 실시간 다중 사용자 코어보레이션

## 8. Success Criteria
1. 2-pane 레이아웃에서 table/gauge 렌더 확인
2. ⌘K 팔레트로 빠른시작 가능
3. 다크모드 토글 저장
4. axe-core 치명적 위반 0
5. `/pdca analyze` match rate ≥ 90%
