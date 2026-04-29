# Design — kr-stock-integration (P1 + P2)

## 1. 실행 전제
- P1+P2 단일 사이클 (확정)
- DART + KIS 키 발급 완료 (KIS 는 이번 구현 제외)
- 포트폴리오 기준통화 USD 고정
- 전체 KOSPI+KOSDAQ 상장 종목 대상

## 2. 구현 파일 지도

| 파일 | P1 | P2 | 역할 |
|---|---|---|---|
| `mcp_server/tools/yf_utils.py::detect_market` | ✅ | | 티커 → "KR"/"US" |
| `mcp_server/tools/market_data.py` | ✅ | | `get_prices` dispatch |
| `mcp_server/tools/kr_market_data.py` | ✅ | | 기존 어댑터 활용 (get_ohlcv/fundamental) |
| `mcp_server/tools/dart.py` (신규) | | ✅ | DART OPEN API — 재무제표, 공시 |
| `mcp_server/tools/news_search_kr.py` (신규) | | ✅ | 네이버 Finance / Google News KR RSS |
| `mcp_server/tools/kr_themes.py` (신규) | | ✅ | 한국 테마 → 티커 맵 (JSON) |
| `mcp_server/tools/financial_factors.py` | | ✅ | KR 티커 → DART 우선 |
| `api/schemas/market.py` | ✅ | | `KRIndicesData`, `KRConditionData`, `PriceBar.market` |
| `api/schemas/stock.py` | ✅ | | `StockComprehensive.market, currency, name_kr` |
| `api/routers/market.py` | ✅ | | `/api/market/kr/*` 3 엔드포인트 |
| `api/routers/stock.py` | ✅ | | market-aware dispatch |
| `api/routers/theme.py` | | ✅ | `/api/theme/kr/*` |
| `api/routers/dart.py` (신규) | | ✅ | `/api/dart/filings`, `/api/dart/financials` |
| `dashboard/src/lib/locale.ts` (신규) | ✅ | | `formatPrice`, `formatPercent`, `formatCompact` |
| `dashboard/src/components/MarketSelector.tsx` (신규) | ✅ | | US/KR 선택기 |
| `dashboard/src/app/page.tsx` | ✅ | | KOSPI/KOSDAQ 카드 +2 |
| `dashboard/src/app/stock/page.tsx` | ✅ | | MarketSelector + locale 적용 |
| `dashboard/src/app/theme/page.tsx` | | ✅ | KR 테마 토글 |
| `tests/test_kr_market.py` (신규) | ✅ | | detect_market + dispatch |
| `tests/test_dart.py` (신규) | | ✅ | DART 응답 파싱 (fixture) |

## 3. detect_market (FR-K01)

```python
def detect_market(ticker: str) -> Literal["KR", "US"]:
    t = ticker.strip().upper()
    if t.endswith(".KS") or t.endswith(".KQ"):
        return "KR"
    if t.isdigit() and len(t) == 6:
        return "KR"
    return "US"
```

테스트:
- `"005930"` → KR, `"AAPL"` → US, `"005930.KS"` → KR, `"BRK.A"` → US, `""` → US (default)

## 4. get_prices dispatch (FR-K02)

```python
def get_prices(ticker, start=None, end=None, interval="1d"):
    market = detect_market(ticker)
    if market == "KR":
        from mcp_server.tools.kr_market_data import get_kr_adapter
        df = get_kr_adapter().get_ohlcv(ticker, start=start, end=end)
        # 이미 Date/Open/High/Low/Close/Volume 반환 — 스키마 일치
        return df.reset_index() if not df.empty else pd.DataFrame()
    # 기존 yfinance path
    ...
```

캐시는 기존 `@cached(ttl=TTL.DAILY, prefix="prices")` 가 ticker 자체를 key 에 포함하므로 분기 후에도 동작.

## 5. DART 연동 (FR-K10/K11/K15)

### 라이브러리 선택
`OpenDartReader` (PyPI) 채택 — XBRL 파싱 이미 내장.
```bash
pip install OpenDartReader
```

### `mcp_server/tools/dart.py`
```python
class DartClient:
    def __init__(self):
        import OpenDartReader
        self._client = OpenDartReader(os.getenv("DART_API_KEY", ""))

    @cached(ttl=TTL.FUNDAMENTAL, prefix="dart_fin")
    def get_financials(self, ticker_6: str, year: int | None = None) -> dict:
        """ROE/ROA/EPS/매출성장 실값 (단위: 배/억원)."""
        ...

    @cached(ttl=TTL.DAILY, prefix="dart_filings")
    def get_filings(self, ticker_6: str, days: int = 30) -> list[dict]:
        """최근 공시 목록 — title, date, url."""
        ...
```

DART 의 6자리 티커는 **corp_code** 가 아닌 **stock_code** — `OpenDartReader.find_corp_code(stock_code)` 로 변환.

### `financial_factors.py` 통합 (FR-K11)
```python
def calculate_profitability(ticker, market="US"):
    if market == "KR":
        from mcp_server.tools.dart import get_dart_client
        try:
            return get_dart_client().get_financials(ticker.replace(".KS","").replace(".KQ",""))
        except Exception as e:
            logger.info("DART failed, fallback to yfinance: %s", e)
    # 기존 yfinance path
    ...
```

## 6. 한국어 뉴스 (FR-K12/K13)

### `news_search_kr.py`
소스:
- Google News RSS 한국어 (`hl=ko&gl=KR&ceid=KR:ko`)
- 네이버 금융 RSS: `https://finance.naver.com/news/news_list.naver?mode=RANK` (HTML 스크래핑 회피 위해 일단 Google News 만)

### KR 센티먼트 키워드 (`news_sentiment.py` 확장)
```python
KR_KEYWORDS = {
    "strong_positive": ["역대급", "급등", "상한가", "호재"],
    "positive":        ["매수", "상승", "개선", "성장", "호조", "실적 개선"],
    "negative":        ["하락", "악재", "부진", "실망", "감소"],
    "strong_negative": ["급락", "하한가", "우려", "손실 확대"],
}
```
기존 영어 키워드 dict 와 merge — 언어 감지 없이 substring match 로 충분.

## 7. 한국 테마 맵 (FR-K14)

### `kr_themes.py` + `data/kr_themes.json`
```json
{
  "2차전지": ["373220", "247540", "006400", "066970", "096770"],
  "원전": ["034020", "138930", "267260", "329180"],
  "AI반도체": ["000660", "005930", "042700", "058470"],
  "조선": ["009540", "010140", "042660"],
  "바이오": ["207940", "068270", "145020"],
  "방산": ["047810", "012450", "272210"],
  "로봇": ["108320", "067990", "319660"],
  "전력설비": ["015760", "034020", "267250"]
}
```
(시드 데이터 8개 테마 × 3~5 종목. 후속 확장 가능)

`propose_tickers_kr(theme)` → 이 JSON 직접 lookup.

## 8. 환율 헬퍼 (FR-K17 부분, USD 고정용 힌트)

```python
# mcp_server/tools/fx.py
@cached(ttl=TTL.DAILY, prefix="fx")
def get_rate(from_ccy="USD", to_ccy="KRW") -> float:
    import requests
    r = requests.get("https://api.exchangerate.host/latest",
                     params={"base": from_ccy, "symbols": to_ccy}, timeout=10)
    return r.json()["rates"][to_ccy]
```

엔드포인트: `/api/fx/rate?from=USD&to=KRW` — UI 입력 힌트 전용. 포트폴리오 계산 영향 없음.

## 9. API 응답 스키마 확장

### `StockComprehensive` 신규 필드
```python
class StockComprehensiveData(BaseModel):
    ticker: str
    market: Literal["KR", "US"] = "US"
    currency: Literal["KRW", "USD"] = "USD"
    name: str = ""            # 영문 또는 원어
    name_kr: str | None = None  # KR 전용 한글명
    # ... 기존 필드
```

### 신규 엔드포인트
- `GET /api/market/kr/condition` → `{condition: "bull"|"bear"|"neutral", kospi_60d_return}`
- `GET /api/market/kr/indices` → `{kospi: bar[], kosdaq: bar[], kospi200: bar[]}`
- `GET /api/market/kr/prices?ticker=005930&period=6mo` → 통합 `PriceBar[]`
- `GET /api/theme/kr/propose` → `{themes: string[]}`  (JSON 키 반환)
- `GET /api/theme/kr/tickers?theme=2차전지` → `{theme, tickers: [...], names: [...]}`
- `GET /api/dart/filings?ticker=005930&days=30` → 공시 목록
- `GET /api/dart/financials?ticker=005930` → ROE/ROA/EPS/매출성장
- `GET /api/fx/rate?from=USD&to=KRW` → `{rate, date}`

## 10. 프론트엔드 변경

### `locale.ts`
```typescript
export function formatPrice(value: number, market: "US" | "KR" = "US"): string {
  if (market === "KR") {
    return new Intl.NumberFormat("ko-KR", {
      style: "currency", currency: "KRW", maximumFractionDigits: 0,
    }).format(value);
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency", currency: "USD",
  }).format(value);
}

export function formatPercent(value: number, digits = 2): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${(value * 100).toFixed(digits)}%`;
}
```

### `MarketSelector.tsx`
3-way pill: `AUTO | US | KR`. AUTO 는 입력 티커의 `detect_market` 결과 사용.

### `/` (Market Overview) 카드
기존 4 → 6 → grid md:grid-cols-6:
- S&P 500, NASDAQ, DOW, VIX, **KOSPI (^KS11)**, **KOSDAQ (^KQ11)**

### `/stock` 변경
- 상단: `<MarketSelector>` + ticker input placeholder 동적 변경
- 가격 표시: `formatPrice(price, comprehensive.market)` 사용
- 한글명 표시: `{name_kr ?? name} ({ticker})`

### `/theme` 변경
- 탭: `US 테마` / `한국 테마`
- 한국 탭 선택 시 `/api/theme/kr/propose` 호출 → JSON 키 칩 표시

## 11. 테스트

| 파일 | 케이스 |
|---|---|
| `tests/test_kr_market.py` | `detect_market` 10케이스, `get_prices` KR 분기 (mock adapter) |
| `tests/test_dart.py` | DART 응답 파싱 fixture, `corp_code` 변환 |
| `tests/test_kr_themes.py` | JSON 로드, `propose_tickers_kr` 반환 |
| `tests/test_news_kr.py` | Google News KR RSS 파싱 (fixture) |

## 12. 의존성 업데이트

```bash
pip install pykrx FinanceDataReader OpenDartReader
```
`requirements.txt` 반영.

## 13. 환경변수

```bash
DART_API_KEY=...        # 사용자 발급 완료
# KIS_APP_KEY, KIS_APP_SECRET — 보관만, 이번 사이클 미사용
```

## 14. 구현 순서 (Do phase)

1. `detect_market` + 단위 테스트
2. `get_prices` dispatch
3. `/api/market/kr/*` 엔드포인트 + 스키마
4. `/api/stock/comprehensive` market-aware
5. 프론트 `locale.ts` + `MarketSelector` + 홈 카드
6. `/stock` 페이지 통합
7. `mcp_server/tools/dart.py` + OpenDartReader
8. `financial_factors.py` KR 분기
9. `/api/dart/*` 엔드포인트
10. `kr_themes.py` + JSON 시드 + `/api/theme/kr/*`
11. 프론트 `/theme` KR 탭
12. `news_search_kr.py` + KR 센티먼트 키워드
13. 전체 테스트 + gap analyze

## 15. Risk

동일한 리스크 표 유지 (Plan §13). 추가:
- **OpenDartReader 의 corp_code 매핑 캐시** — 첫 호출 시 공시 리스트 전체 다운로드(수 MB). 시작 시 한 번만 실행되도록 lazy singleton.
