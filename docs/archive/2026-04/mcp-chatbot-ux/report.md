# Completion Report — mcp-chatbot-ux

**Feature**: `mcp-chatbot-ux` (follow-up #3 of mcp-chatbot v2)
**Period**: 2026-04-19
**Match Rate**: **94%** (P1 scope)
**tsc errors**: 0

## Delivered (P1)

### New components (`dashboard/src/components/chat/`)
| 파일 | 역할 |
|---|---|
| `ChatHeader.tsx` | 모델 선택 / ⌘K / New Chat / 테마 / 세션 배지 — FR-U03 |
| `ModelSelector.tsx` | 드롭다운 + `ChatModelProvider` + `useChatModel` hook |
| `ThemeToggle.tsx` | Light/Dark 토글, `localStorage["chat.theme"]`, `<html data-theme>` 반영 — FR-U15 |
| `CommandPalette.tsx` | 네이티브 ⌘K 팔레트 (↑↓/Enter/Esc, 자동 포커스, 필터) — FR-U08 |
| `ArtifactPanel.tsx` | 탭형 artifact 컨테이너, tool 별 렌더러 디스패치 — FR-U01 |
| `RankingsTable.tsx` | rank_stocks/analyze_theme placeholder (summary) — FR-U11 partial |
| `MarketGaugeMini.tsx` | market_condition 아티팩트 — FR-U12 |
| `NewsListPanel.tsx` | news_sentiment 아티팩트 |

### Layout
- `dashboard/src/app/chat/page.tsx` 전체 재작성
  - `ChatModelProvider` 로 감싼 `ChatWorkbench`
  - `grid md:grid-cols-[1fr_360px]` — 2-pane on md+, mobile stacked (FR-U01/U02)
  - `Cmd/Ctrl+K` 글로벌 리스너로 팔레트 오픈
  - `tool_result` 이벤트를 마지막 assistant message 의 `artifacts[]` 에 누적 → 자동으로 ArtifactPanel 렌더
  - 다크모드 대응 className / border 토큰 일관 적용

### Design tokens
- `dashboard/src/app/globals.css`
  - `html[data-theme="dark"]` 토큰 (`--background`, `--foreground`, `--card-bg`, `--border`, `--sidebar-bg`, `--muted`)
  - `.tabular { font-variant-numeric: tabular-nums; }` 유틸 — FR-U17

## 벤치마크 반영 포인트

| 레퍼런스 | 반영 |
|---|---|
| Perplexity Finance | tool chip → 우측 artifact 패널 flow |
| Claude.ai Artifacts | 2-pane + tab 기반 artifact |
| Linear | ⌘K 팔레트, 키보드 우선, 조밀한 타이포 |
| Bloomberg | tabular-nums 숫자 정렬 |
| Vercel v0 | EmptyState + Quick Start 칩, 타자기 caret (이미 streaming feature 에서 반영) |

## Deferred (design §1 out of P1)

- FR-U04/U05/U06/U07 — streaming UX 세부 (caret 은 이미 streaming feature 에 있음)
- FR-U09 히스토리 편집 (↑ 방향키)
- FR-U10 티커 D&D
- FR-U13 news hover preview
- FR-U14 메시지 hover actions
- FR-U16 axe-core 자동화

## Gaps (integration 시 참고)

1. **FR-U11 structured table** — streaming `tool_result` 에 rankings 배열 추가되는 후속 사이클에서 RankingsTable 본체 교체
2. **vitest 부재** — CommandPalette / ThemeToggle / ArtifactPanel 단위 테스트는 다음 폴리시 사이클
3. **`/tool` 직접 실행** — 팔레트 확장 여지

## 파일 영역 분리 (performance 와 충돌 없음)

| feature | 주로 건드린 파일 |
|---|---|
| performance | `core/config.py`, `mcp_server/tools/llm.py`, `api/services/chat_*.py`, `api/services/chat_metrics.py`, `api/routers/chat.py`, `dashboard/src/lib/api.ts` |
| ux | `dashboard/src/app/chat/page.tsx` (shell 재작성), `dashboard/src/components/chat/*` (모두 신규), `dashboard/src/app/globals.css` |

공통 터치: 없음. Integration 브랜치에서 추가 작업 없이 양쪽 쳌지가 자연 병합됨.

## Next — Integration

- 두 feature archive 후 `.pdca-status.json` 정리
- Integration release notes 는 `docs/archive/2026-04/mcp-chatbot-v2-integration/` 폴더에 별도 작성 예정
- 전체 flow 수동 QA: 질문 → 도구 실행 중 표시 → artifact 패널 업데이트 → done → ⌘K → New Chat → 다크모드 토글
