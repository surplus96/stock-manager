# Design — mcp-chatbot-ux

## 1. P1 범위 (이번 사이클)

| FR | 내용 | 우선 |
|---|---|---|
| **FR-U01** 2-pane 레이아웃 | Conversation (60%) + Artifact Panel (40%) on md+ | High |
| **FR-U02** 모바일 단일 컬럼 + artifact collapse | < md: 대화 아래 "Artifacts" 섹션 | High |
| **FR-U03** 헤더: Model Selector + Session badge + New Chat | `<ChatHeader>` | High |
| **FR-U11** Rankings 테이블 렌더러 (정렬/검색 미니멀) | `<RankingsTable>` | High |
| **FR-U12** `<MarketGauge>` 재사용 | `market_condition` tool 결과 시 | Medium |
| **FR-U15** 다크 모드 토글 (localStorage 저장) | `<ThemeToggle>` + `html[data-theme]` | Medium |
| **FR-U17** tabular-nums | `globals.css` 에 `.tabular` 유틸 + table/수치에 적용 | High |
| **FR-U08** ⌘K 빠른시작 팔레트 (기본) | `<CommandPalette>` minimal (cmdk 없이 자체) | Medium |

P3/P4 (다크 refine, hover preview, news preview card, a11y audit 자동화) → 후속.

## 2. 레이아웃

```
┌─────────────── ChatHeader ───────────────┐
│ 🟣 AI Chatbot   Model: [flash ▾]  ⌘K  + │
├──────────────────────┬───────────────────┤
│  Conversation        │  Artifacts        │
│  (role=log)          │  (role=complementary)
│                      │                   │
│  • user              │  ▸ Rankings table │
│  • assistant         │  ▸ Market gauge   │
│    (Markdown+caret)  │  ▸ News list      │
│  • tool chip         │  (각 assistant    │
│                      │   message 의      │
│                      │   최신 artifact)  │
├──────────────────────┴───────────────────┤
│ Composer [textarea] [⌘↵ Send] [Stop]    │
└──────────────────────────────────────────┘
```

- **grid**: `md:grid md:grid-cols-[1fr_380px]`, `<md:grid-cols-1`
- Artifact Panel 은 **마지막 assistant 메시지** 의 tool 결과만 렌더
- 결과가 여러 tool 이면 tab 으로 분리 (`Rankings` / `Market` / `News`)

## 3. 컴포넌트 설계

| 컴포넌트 | 파일 | 역할 |
|---|---|---|
| `ChatHeader` | `components/chat/ChatHeader.tsx` | 모델 셀렉터, 세션 badge, New Chat, ⌘K 단축키 힌트, 테마 토글 |
| `ConversationPane` | `components/chat/ConversationPane.tsx` | 메시지 리스트 + Composer + Empty state |
| `ArtifactPanel` | `components/chat/ArtifactPanel.tsx` | tab 컨테이너, active tool 에 따라 표시 컴포넌트 선택 |
| `RankingsTable` | `components/chat/RankingsTable.tsx` | `rankings: [{ticker, composite_score, signal, factors, sector}]` 렌더, 컬럼 정렬, tabular-nums |
| `MarketGaugeMini` | `components/chat/MarketGaugeMini.tsx` | bull/bear/neutral + spy_60d_return 표시 (기존 page.tsx MarketGauge 패턴 축약) |
| `NewsListPanel` | `components/chat/NewsListPanel.tsx` | news 배열 렌더 (제목 + 출처 + 시간) |
| `CommandPalette` | `components/chat/CommandPalette.tsx` | ⌘K 모달, Quick Start 4개 + /tool 직접 실행 |
| `ThemeToggle` | `components/chat/ThemeToggle.tsx` | html dataset 조작 + localStorage |
| `ModelSelector` | `components/chat/ModelSelector.tsx` | dropdown, localStorage 저장, context 로 전역 공유 |

## 4. 모델 선택

- 모델 목록 (하드코딩 initial): `["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]`
- 선택값은 localStorage `chat.model` 에 저장
- 서버로 전달: `api.chat(message, sessionId, { model })` + streaming `openChatStream(..., {model})` → query `&model=...`
- Performance feature 의 `/api/chat/metrics` 와 대응해 두면 좋지만 별도 endpoint `/api/chat/models` 는 이번 사이클 out of scope — 하드코딩 유지.

## 5. 테마 토큰 (다크 모드)

`globals.css`:
```css
:root { --bg:#f8fafc; --surface:#ffffff; --border:#e2e8f0; --fg:#1e293b; ... }
html[data-theme="dark"] {
  --bg:#0f172a; --surface:#1e293b; --border:#334155; --fg:#f1f5f9; ...
}
.tabular { font-variant-numeric: tabular-nums; }
```

`<ThemeToggle>`:
- On mount: 읽은 값 → `document.documentElement.dataset.theme = value`
- Toggle: `"light"` ↔ `"dark"` + localStorage 저장

Existing pages 중 가장 많이 쓰이는 색(텍스트/border/bg)을 토큰으로 치환할 정도면 전체 다크모드 quality 는 나중 폴리시에서 마감. 이번 사이클은 **챗 페이지 우선 적용**.

## 6. 아티팩트 추출 로직

`chat/page.tsx` 의 streaming event handler:
```typescript
onEvent: (ev) => {
  if (ev.type === "tool_result" && ev.ok) {
    // 최근 draft message 의 artifacts 누적
    updateAssistant(draftId, m => ({
      ...m,
      artifacts: [...(m.artifacts ?? []), { tool: ev.tool, summary: ev.summary }],
    }));
  }
  ...
}
```

`ArtifactPanel` 은 마지막 assistant message 의 `artifacts` 배열을 props 로 받아 렌더. Tool 별 렌더러 매핑:
```typescript
const RENDERERS: Record<string, (result: unknown) => ReactNode> = {
  rank_stocks: (r) => <RankingsTable data={r} />,
  analyze_theme: (r) => <RankingsTable data={r} />,
  market_condition: (r) => <MarketGaugeMini data={r} />,
  news_sentiment: (r) => <NewsListPanel data={r} />,
};
```

**주의**: tool_result 의 `summary` 는 짧은 문자열. 실제 데이터는 전달하지 않음. 이번 사이클에선 summary 텍스트만 렌더링하는 **lightweight 모드**로 구현 (상세 데이터 전달은 streaming schema 수정 필요 → 후속 사이클). RankingsTable 은 summary 문자열("N rankings") 만 받아서 "Top-N ranking 도출 완료" 같은 placeholder 표시.

→ **Artifact Panel 은 summary-only placeholder → 후속 사이클에서 실제 데이터 렌더로 확장** 계획 명시.

## 7. ⌘K 팔레트

- 네이티브 구현 (dependency 추가 안 함): `<dialog>` + `<input>` + 필터
- 진입: `Cmd/Ctrl + K` 키 리스너 (mousetrap X — 직접 `useEffect`)
- 목록: Quick Start 4 + "/rank AAPL,MSFT" 같은 raw tool shortcut (기본은 Quick Start 만)

## 8. 파일

| 파일 | 변경/신규 |
|---|---|
| `dashboard/src/app/chat/page.tsx` | 리팩토링 — shell 을 `<ChatShell>` 로 얇게 |
| `dashboard/src/components/chat/ChatShell.tsx` | 2-pane layout + provider 조립 (신규) |
| `dashboard/src/components/chat/ChatHeader.tsx` | (신규) |
| `dashboard/src/components/chat/ConversationPane.tsx` | (신규) |
| `dashboard/src/components/chat/ArtifactPanel.tsx` | (신규) |
| `dashboard/src/components/chat/RankingsTable.tsx` | (신규) |
| `dashboard/src/components/chat/MarketGaugeMini.tsx` | (신규) |
| `dashboard/src/components/chat/NewsListPanel.tsx` | (신규) |
| `dashboard/src/components/chat/CommandPalette.tsx` | (신규) |
| `dashboard/src/components/chat/ThemeToggle.tsx` | (신규) |
| `dashboard/src/components/chat/ModelSelector.tsx` | (신규) |
| `dashboard/src/hooks/useChatStream.ts` | (신규) — openChatStream 래퍼 + 상태 관리 |
| `dashboard/src/app/globals.css` | 다크 토큰 + `.tabular` 유틸 |

## 9. 성능
- 컴포넌트 분리 → re-render 범위 축소
- RankingsTable 은 uncontrolled (정렬만), `useMemo` 로 sorted rows 캐싱
- LCP: shell skeleton + 빈 conversation 으로 즉시 렌더

## 10. Success Criteria
1. 2-pane 레이아웃 md 이상에서 동작, 모바일 단일 컬럼 OK
2. 다크모드 토글 즉시 반영 + 새로고침 후 유지
3. ⌘K 팔레트 열림 + Quick Start 클릭으로 질문 전송
4. tool_result 수신 시 ArtifactPanel 에 placeholder 렌더
5. Match rate ≥ 90%
