# Stock Manager — AI Portfolio Analyst

**Demo**: <!-- DEMO_URL --> _(배포 후 갱신 예정)_
**License**: [MIT](LICENSE) · **Third-party notices**: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)

> 한국·미국 주식을 자연어로 분석·랭킹·리포팅해 주는 AI 포트폴리오 매니저.
> Next.js 대시보드 + FastAPI 백엔드 + Gemini LLM + MCP 툴 레지스트리 통합.

---

## For Reviewers (심사자용)

- **공개 데모 URL** 한 곳만 열어서 모든 기능을 그대로 체험할 수 있습니다.
- **별도의 API 키 입력은 필요 없습니다.** 외부 API(Google Gemini, DART, KRX, yfinance)는 모두 서버사이드 환경변수로 호출되며, 프론트엔드는 자체 백엔드만 호출합니다.
- 심사 기간 동안 데모 URL이 살아있도록 유지합니다.
- 라이선스/저작권: 본 저장소는 [MIT](LICENSE) 라이선스이며, 사용된 모든 의존성·폰트·아이콘의 라이선스 출처는 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)에 정리되어 있습니다. 이미지·차트 자산은 모두 공개 데이터로 코드가 직접 생성한 것이며 외부 저작물 도용은 없습니다.

---

## 개요
MCP 서버 기반 펀드 매니저 에이전트. 뉴스·재무·공시 데이터를 수집/요약/지식화하고, 후보군 랭킹과 리포트를 생성합니다. 웹 대시보드(채팅 + 분석 리포트)와 Claude 호스트앱(MCP) 양쪽에서 동일한 백엔드 도구를 호출합니다.
- 타겟: 한국·미국 주식 (3-tier 한국 코드 분류, KOSPI/KOSDAQ 자동 판별)
- 인터페이스: 웹 대시보드 (Next.js 16) · Claude 호스트앱 (MCP 연동)

### 주요 프로세스
- 신규 투자 진행 프로세스:
  1. 전반적 시장/섹터/기업 동향 파악
  2. 사용자에게 종목 카테고리 추천
  3. 사용자 지정 종목·테마 정밀 파악
  4. 후보 기업/종목 리스트업 및 데이터 수집
  5. 분석·평가·랭킹 및 리포트 작성(예상 이익률·근거)
  6. 옵시디언으로 문서화·시각화·지식 그래프 활용
- 보유 종목 진단/알림 프로세스:
  1. 보유 종목 진단 및 페이즈(상승/유지/불안정/적신호) 알림
  2. 적신호 단계 시 정밀 분석 및 대응 제안

### 아키텍처 요약
- Claude 호스트앱 + MCP 서버(도구 제공)
- 데이터 소스:
  - 뉴스/동향: Perplexity MCP
  - 시세/재무: yfinance(우선), Alpha Vantage/Finnhub/Polygon.io(확장)
  - 공시/실적: SEC EDGAR API
- 분석/랭킹: 팩터 + 이벤트/모멘텀/리스크 스코어
- 스토리지: SQLite 캐시/운영, 옵시디언 Markdown, (선택) Neo4j
- 스케줄링: APScheduler (데일리/주간 잡)

### 사용 라이브러리
- 핵심: fastapi(선택), pydantic, requests, pandas, numpy, yfinance, python-dateutil, APScheduler, jinja2, diskcache, tqdm
- 선택: alpha_vantage, sec-api 또는 직접 EDGAR, ta, vectorbt, neo4j(옵션), langchain-core, pyyaml, markdownify

### 핵심 MCP 도구(엔드포인트)
- market_data.get_prices(ticker, start, end, interval)
- market_data.get_fundamentals(ticker)
- news.search(query|tickers, lookback)
- filings.fetch(ticker, form, lookback)
- analytics.rank(candidates, criteria?)
- portfolio.evaluate(holdings)
- reports.generate(type, payload)
- obsidian.write(note_path, content, links)

### Claude 자연어 예시 프롬프트
- 테마 리포트: "AI 테마 주간 리포트 만들어줘. 티커는 AAPL, MSFT, NVDA 사용해."
  - 내부 호출: `create_theme_report(theme='AI', tickers_csv='AAPL,MSFT,NVDA')`
- 포트폴리오 페이즈: "내 보유종목 AAPL, MSFT, NVDA의 페이즈 리포트 만들어줘."
  - 내부 호출: `create_portfolio_phase_report(tickers_csv='AAPL,MSFT,NVDA')`
- 뉴스: "최근 일주일 AI 칩과 클라우드 성장 관련 뉴스 5개만 요약해줘."
  - 내부 호출: `news_search(queries=['AI chips','cloud growth'], lookback_days=7, max_results=5)`
- 공시: "AAPL의 최근 10-Q/8-K 3건 보여줘."
  - 내부 호출: `filings_fetch_recent(ticker='AAPL', forms=['10-Q','8-K'], limit=3)`

---

## 로컬 실행

```bash
# 1. 환경 변수 설정
cp .env.example .env
#   GEMINI_API_KEY (https://aistudio.google.com/apikey) 만 채워 넣으면 기본 동작

# 2. 백엔드 (FastAPI, http://localhost:8000)
pip install -r requirements.txt
uvicorn api.server:app --reload

# 3. 프론트엔드 (Next.js 16, http://localhost:3000)
cd dashboard
npm install
npm run dev
```

## 라이선스 / 저작권

- 본 저장소 코드: [MIT License](LICENSE)
- 의존성 라이선스 전체 목록: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
- 폰트: Source Serif 4 (SIL Open Font License 1.1)
- 아이콘: lucide-react (ISC)
- 외부 데이터: Google Gemini, DART, KRX, Yahoo Finance — 각 서비스 약관 준수, 비상업적 연구 목적
