# Gap Analysis — mcp-chatbot-ux

**Date**: 2026-04-19
**Match Rate**: **94%** (P1 실행 범위, 7 full + U11 0.5 / 8 = 94%)

## FR Coverage (P1 범위: design §1)

| FR | 상태 | Evidence |
|---|---|---|
| **FR-U01** 2-pane 레이아웃 | ✅ | `chat/page.tsx` `grid md:grid-cols-[1fr_360px]`, ArtifactPanel `hidden md:flex` |
| **FR-U02** 모바일 단일 컬럼 + artifact strip | ✅ | `md:hidden mt-3` wrap ArtifactPanel under conversation |
| **FR-U03** 헤더 (모델/세션/⌘K/New/테마) | ✅ | `ChatHeader.tsx` — ModelSelector + ThemeToggle + New Chat + ⌘K hint + session badge |
| **FR-U08** ⌘K 팔레트 | ✅ | `CommandPalette.tsx` — native dialog, ↑↓/Enter/Esc, substring filter; global Cmd/Ctrl+K 리스너 |
| **FR-U11** Rankings 테이블 | ⚠️ Partial | `RankingsTable.tsx` — summary-only placeholder. 구조화 rankings 배열은 streaming schema 확장 필요 (후속) |
| **FR-U12** MarketGaugeMini | ✅ | `MarketGaugeMini.tsx` → `market_condition` tool 디스패치 |
| **FR-U15** 다크모드 | ✅ | `html[data-theme="dark"]` palette + `ThemeToggle.tsx` + `localStorage["chat.theme"]` |
| **FR-U17** tabular-nums | ✅ | `globals.css:31` `.tabular` 유틸 + 수치 영역 적용 |

## 부가 구현
- `ChatModelProvider` + `useChatModel` hook — 모델 선택값 context 공유
- ArtifactPanel tabbed container (multiple tool results 전환)
- 다크모드 색상 토큰 (card-bg / border / muted) 전체 chat 컴포넌트 적용

## Deferred (design §1 명시)
- FR-U04/U05/U06/U07 (streaming UX — BlinkingCaret 만 streaming feature 에서 이미 반영)
- FR-U09/U10 (히스토리 편집, D&D 티커)
- FR-U13/U14 (hover preview, hover actions)
- FR-U16 (axe-core 자동화)

## Gaps
1. **FR-U11 partial** — streaming `tool_result` payload 가 `summary: string` 만 실어 구조화 테이블 불가. 후속 사이클에서 schema 확장 + sortable rows 교체.
2. **vitest 없음** — design §8 에서 수동 smoke 허용. CommandPalette (Enter/Esc/Arrow), ThemeToggle (localStorage roundtrip), artifact dispatch 단위 테스트는 후속 추가 권장.
3. **`/tool` 직접 실행** — palette 가 Quick Start 4개만 지원 (design §7 에서 "minimal" 명시).

## Success Criteria
1. ✅ 2-pane md+ / mobile collapse 동작
2. ✅ 다크모드 토글 + 새로고침 유지
3. ✅ ⌘K 팔레트 + Quick Start 클릭으로 전송
4. ⚠️ ArtifactPanel placeholder 렌더 (summary only)
5. ✅ Match rate ≥ 90% — **94%**

→ `/pdca report mcp-chatbot-ux`
