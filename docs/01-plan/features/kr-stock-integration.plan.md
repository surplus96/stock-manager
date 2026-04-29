# Plan — kr-stock-integration

> **Goal**: 대한민국 국내 주식(KOSPI/KOSDAQ)을 Stock Manager 의 **1급 자산**으로
> 통합한다. 현재는 `KoreanMarketAdapter` 가 PyKrx/FinanceDataReader 로 로컬
> 데이터만 제공하고 REST/프론트에 미노출 — 이를 US 시장과 대등한 UX 로
> 끌어올린다.

## 1. 현황 분석 (Gap scan — 2026-04-20)

| 영역 | 현재 | 부족 |
|---|---|---|
| 어댑터 | `mcp_server/tools/kr_market_data.py` (PyKrx+FDR — listing/OHLCV/fundamental/ticker name) | **REST 엔드포인트 노출 전혀 없음** |
| 티커 정규화 | `normalize_ticker_multi_market(ticker, market)` 존재 — 6자리 → `.KS` 추가 | 시장 자동 감지(6자리면 KR, 영문이면 US) 없음 |
| 가격 차트 | `market_data.get_prices` 가 yfinance 만 | KR은 PyKrx OHLCV 가 더 정확 + 실시간성 ↑ |
| 재무 팩터 | yfinance `.KS`/`.KQ` 일부 커버 | ROE/ROA 등 일부 값 null, DART 연동 없음 |
| 뉴스 | Google News RSS (영어 위주) | 한국어 뉴스(네이버/다음/한경) 없음, KR 센티먼트 사전 없음 |
| 테마 | 영문 테마 (AI/semiconductor 등) | 한국 전용 테마 (2차전지/원전/반도체/조선 etc) 맵 없음 |
| 시장 국면 | SPY 60D 수익률 고정 | KOSPI/KOSDAQ 국면 별도 판정 필요 |
| 포트폴리오 | USD 단일 통화 | KRW/USD 혼합, 환율 변환 없음 |
| 프론트 UI | 종목 검색 US 전용, $ 고정 | 시장 selector, ₩ 포맷, KRX 주요지수 카드 |

## 2. Data source 선정

| 소스 | 장점 | 단점 | 활용 |
|---|---|---|---|
| **PyKrx** | KRX 직접 스크래핑, 정확, 공식 거래량/외국인/기관 | 요청 제한 없지만 IP 차단 리스크 | 기본 OHLCV, 상장 리스트 |
| **FinanceDataReader** | 통합 인터페이스, pandas DF 반환 | PyKrx 위에 얇게 래핑 | 백업 경로 |
| **yfinance `.KS`/`.KQ`** | 글로벌 동일 API, 실시간(15분 지연) | 결측/부정확한 ROE 등 | 종가/차트 보조 |
| **DART Open API** | 공식 공시, 재무제표(K-IFRS) | 2021 이후 분기 보고서 XBRL, 파싱 복잡 | ROE/ROA/EPS 실값 |
| **KIS Developers (한투)** | OAuth2, 실시간 호가/체결 | 증권 계좌 필요 | 후속 phase (실시간성 필요 시) |
| **네이버 금융 스크래핑** | 테마 분류/관련주 풍부 | 차단 리스크, robots.txt | 최후 수단 |

**P1 결정**: **PyKrx + yfinance 하이브리드** 로 시작. DART 은 P3 에서 추가.

## 3. Functional Requirements

### P1 — Core 통합 (MVP, 목표 2~3일)

| ID | 요구사항 | 우선 |
|---|---|---|
| **FR-K01** | **시장 자동 감지**: 6자리 숫자 → KR, 영문 → US (helper: `detect_market(ticker)`) | High |
| **FR-K02** | `get_prices()` 가 KR 티커면 PyKrx 로 경로 분기, US는 yfinance 유지. 반환 DF 스키마 통일 (Date/Open/High/Low/Close/Volume) | High |
| **FR-K03** | `api/routers/market.py` — `/api/market/kr/condition` — KOSPI 60D 수익률 + 국면 판정 | High |
| **FR-K04** | `/api/market/kr/indices` — KOSPI, KOSDAQ, KOSPI200 스냅샷 | High |
| **FR-K05** | `/api/market/kr/prices?ticker=005930` — KR 티커 OHLCV | High |
| **FR-K06** | `/api/stock/comprehensive` 가 KR 티커 입력 시 KR 파이프 경유 (종목명 한글, 섹터 KRX 분류) | High |
| **FR-K07** | 프론트 `/stock` 에 **시장 Selector** (US / KR / Auto) + ₩ 표시 시 KRW locale (`ko-KR`, 천단위) | High |
| **FR-K08** | 홈 Market Overview 에 **KOSPI/KOSDAQ** 카드 추가 (기존 S&P500/NASDAQ 옆) | High |
| **FR-K09** | Sidebar Ranking/Theme 페이지에서 시장 필터 (US/KR/둘다) | Medium |

### P2 — 심화 데이터 (목표 추가 1주)

| ID | 요구사항 | 우선 |
|---|---|---|
| **FR-K10** | **DART Open API** 연동 — ROE/ROA/EPS/매출성장 실값 (`mcp_server/tools/dart.py` 신규) | High |
| **FR-K11** | `financial_factors.py` 가 KR 티커 시 DART 우선, fallback yfinance | High |
| **FR-K12** | 한국어 뉴스 소스 — 네이버 Finance RSS + 한경/매경 (`news_search_kr.py`) | Medium |
| **FR-K13** | KR 센티먼트 사전 — 기존 keyword dict에 한글 용어 추가 ("호재"/"악재"/"매수"/"목표주가" 등) | Medium |
| **FR-K14** | 한국 전용 테마 맵 — `themes_kr.json` (2차전지, 원전, 반도체, 조선, 바이오, 방산 등) | Medium |
| **FR-K15** | KR 기업 공시 이벤트 (`/api/stock/kr/filings?ticker=005930`) — DART 공시 목록 | Low |

### P3 — 실시간성 & 포트폴리오 (목표 추가 1주)

| ID | 요구사항 | 우선 |
|---|---|---|
| **FR-K16** | KIS Developers API OAuth2 연동 — 실시간 호가/체결 (옵션) | Medium |
| **FR-K17** | 포트폴리오 멀티 통화 — KRW/USD 혼합, 환율 API (`exchangerate.host` free) | High |
| **FR-K18** | 포트폴리오 PnL 기준통화 선택 (KRW / USD) | Medium |
| **FR-K19** | 거래시간 감지 — KST 09:00~15:30 표시, 휴장일 캘린더 | Low |
| **FR-K20** | KR 전용 UI: 상한가/하한가(±30%) 경계 표시, 외국인/기관 수급 차트 | Low |

## 4. Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Frontend                                                     │
│    - 시장 Selector (US/KR/Auto)                              │
│    - ko-KR locale (Intl.NumberFormat)                         │
│    - KOSPI/KOSDAQ 카드, 섹터맵, 테마칩                         │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  REST API (api/routers/)                                      │
│    /api/market/kr/* (condition, indices, prices)              │
│    /api/stock/* (market-aware dispatch)                       │
│    /api/theme/kr/* (KR themes)                                │
│    /api/stock/kr/filings (DART)                               │
└───────────┬────────────────────────────────┬─────────────────┘
            ▼                                ▼
┌───────────────────────┐        ┌───────────────────────────┐
│ market_router_dispatch │        │ KoreanMarketAdapter (기존) │
│ (detect_market + 분기) │        │   PyKrx, FinanceDataReader│
└───────────┬───────────┘        └───────────────────────────┘
            │                                ▲
            ▼                                │
┌────────────────────────────────────────────┴──────────────────┐
│  mcp_server/tools/                                             │
│    ├── dart.py           (FR-K10, 신규) — DART XBRL 파싱       │
│    ├── news_search_kr.py (FR-K12, 신규) — 네이버/한경 RSS      │
│    ├── kr_themes.py      (FR-K14, 신규) — 한국 테마 맵         │
│    └── fx.py             (FR-K17, 신규) — USD/KRW 환율         │
└────────────────────────────────────────────────────────────────┘
```

## 5. 시장 자동 감지 규칙 (FR-K01)

```python
def detect_market(ticker: str) -> Literal["KR", "US"]:
    t = ticker.strip().upper()
    if t.endswith(".KS") or t.endswith(".KQ"):
        return "KR"
    if t.isdigit() and len(t) == 6:
        return "KR"
    # 영문 대문자 1~5자 = 대부분 US (NYSE/NASDAQ)
    if t.replace(".", "").isalpha() and len(t) <= 5:
        return "US"
    # 기타 → US default (기존 yfinance 경로)
    return "US"
```

예외:
- `005930` → KR (Samsung Electronics)
- `005930.KS` → KR (suffix 유지)
- `AAPL` → US
- `TSM` → US (대만 ADR, 하지만 US 거래소 상장)
- `BRK.A` → US (dot 포함되지만 digit 아님)

## 6. Data contract (통합 스키마)

모든 KR/US 응답이 **동일한 키 구조**를 사용하도록 통일:

```python
class PriceBar(BaseModel):
    date: str           # "YYYY-MM-DD"
    open: float
    high: float
    low: float
    close: float
    volume: int
    # KR-only (optional)
    foreign_net: int | None = None   # 외국인 순매수
    institutional_net: int | None = None  # 기관 순매수
```

`market` 필드를 응답 envelope 에 추가해 프론트가 통화/locale 결정 가능:
```json
{
  "data": { "ticker": "005930", "market": "KR", "currency": "KRW", "name": "삼성전자", ... }
}
```

## 7. 프론트엔드 변경 (P1)

### 시장 Selector
`/stock` 페이지 상단:
```tsx
<MarketSelector value={market} onChange={setMarket} options={["AUTO","US","KR"]} />
<TickerInput placeholder={market === "KR" ? "005930 또는 삼성전자" : "AAPL"} />
```

### 통화/locale 포맷
```typescript
function formatPrice(value: number, market: "US" | "KR") {
  return market === "KR"
    ? new Intl.NumberFormat("ko-KR", { style: "currency", currency: "KRW", maximumFractionDigits: 0 }).format(value)
    : new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value);
}
```

### Market Overview 카드
기존 4개 (S&P500, NASDAQ, DOW, VIX) → **+2개 (KOSPI, KOSDAQ)** = grid-cols-3 md:grid-cols-6

## 8. 파일 변경 지도

| 파일 | 변경/신규 | Phase |
|---|---|---|
| `mcp_server/tools/yf_utils.py::detect_market` | 신규 helper | P1 |
| `mcp_server/tools/market_data.py` | KR 분기 로직 | P1 |
| `api/routers/market.py` | `/api/market/kr/*` 3개 엔드포인트 | P1 |
| `api/routers/stock.py` | market-aware dispatch | P1 |
| `api/schemas/market.py` | `KRIndicesData`, `KRConditionData` | P1 |
| `dashboard/src/components/MarketSelector.tsx` | 신규 | P1 |
| `dashboard/src/lib/locale.ts` | `formatPrice`, `formatPercent` | P1 |
| `dashboard/src/app/page.tsx` | KOSPI/KOSDAQ 카드 추가 | P1 |
| `dashboard/src/app/stock/page.tsx` | 시장 Selector 통합 | P1 |
| `mcp_server/tools/dart.py` | DART OPEN API 연동 | P2 |
| `mcp_server/tools/news_search_kr.py` | 네이버/한경 RSS | P2 |
| `mcp_server/tools/kr_themes.py` | 한국 테마 맵 | P2 |
| `mcp_server/tools/fx.py` | 환율 API | P3 |

## 9. 환경 변수 신규

```bash
# P2
DART_API_KEY=xxxx              # https://opendart.fss.or.kr/ 에서 발급 (무료)

# P3
KIS_APP_KEY=xxxx               # 한투 Developers
KIS_APP_SECRET=xxxx
FX_API_URL=https://api.exchangerate.host/latest  # 무료, API key 불필요
```

## 10. 의존성 체크

```bash
pip install pykrx FinanceDataReader
# P2
pip install opendartreader   # DART 파이썬 래퍼 (옵션)
```

현재 설치 여부 확인 필요 → Plan 승인 후 Design phase 에서 `requirements.txt` 업데이트.

## 11. Out of scope

- 주식 주문 실행(매수/매도) — 증권 계좌 연동은 별도 feature
- 파생상품(선물/옵션)
- ETF 이외의 펀드
- 암호화폐
- 연금/ISA 세제 혜택 계산

## 12. Success Criteria

1. **`005930` 입력 → 삼성전자 차트 + ₩ 가격 + 한국어 섹터명 표시**
2. **Market Overview 에 KOSPI/KOSDAQ 실시간 카드** (yfinance `^KS11`/`^KQ11` fallback)
3. **US/KR 혼합 포트폴리오** — 환율 변환 후 기준통화로 합산
4. **KR 테마 분석** — "2차전지" 입력 시 LG에너지솔루션/에코프로비엠/삼성SDI 등 랭킹
5. **분석 리포트** — KR 종목 입력 시 한국어 뉴스 기반 LLM 요약
6. `/pdca analyze` match rate ≥ 90% (P1 기준)

## 13. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| PyKrx IP 차단 | 캐시 TTL.DAILY (이미 적용), 배치 요청은 async_utils 로 thr 1개 직렬화 |
| DART XBRL 파싱 복잡 | `opendartreader` 같은 래퍼 라이브러리 우선 시도, 안 되면 공시 목록만 |
| 한국어 NLP 품질 | 키워드 기반 센티먼트 MVP, 향후 KoBERT/KR-FinBERT 확장 |
| 티커 입력 ambiguity (예: "삼성" 일반명사) | 정확 티커(6자리) 우선 매칭, 이름은 fuzzy 2순위 |
| 시차(KST vs UTC) | 모든 백엔드 타임스탬프 UTC 고정 (이미 적용), UI 에서만 KST 변환 |
| Free tier 없는 DART | 무료지만 하루 10,000건 제한 → 캐시 강제 |
| yfinance 한국 티커 품질 | PyKrx 우선, yfinance 보조 (가격만) |

## 14. 단계별 실행 계획 (확정)

**사용자 결정 (2026-04-20)**:
- **P1+P2 한 사이클에 통합**
- DART API key 발급 완료
- KIS API key 발급 완료 — **P3 는 이번 사이클에서 구현 제외, Plan 에만 기록**
- 포트폴리오 기준통화: **USD 고정** (환율 변환은 입력 시점에만, 보관은 USD)
- 종목 범위: **전체 상장** (KOSPI + KOSDAQ)

| Phase | 상태 | 비고 |
|---|---|---|
| **P1 Core 통합** | 🟢 이번 사이클 | FR-K01 ~ FR-K09 |
| **P2 심화 데이터** | 🟢 이번 사이클 | FR-K10 ~ FR-K15 (DART 포함) |
| P3 실시간 & KIS | 🟡 Plan 기록만 | FR-K16 ~ FR-K20 (별도 사이클) |

### KRW 포트폴리오 정책 (단순화)
- 저장: **USD 기준통화 고정**
- KR 종목 추가 시: 사용자가 USD 환산 가격 직접 입력 (P2 단계), 자동 환율 변환은 P3
- P2 에서 fx 헬퍼(`/api/fx/rate?from=USD&to=KRW`) 만 노출 (UI 힌트용), 포트폴리오 계산에는 영향 없음
