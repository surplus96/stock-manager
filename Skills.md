# Skills.md - Stock Manager Analysis Engine

> 금융 투자 데이터를 자동 분석하고, 데이터 유형에 맞는 시각화를 선택하며, 실행 가능한 투자 인사이트를 생성하는 범용 분석 규칙 문서

---

## 1. 데이터 분석 기준 정의

### 1.1 6대 분석 팩터 체계

모든 투자 종목은 다음 6개 팩터로 정량 평가한다.

| 팩터 | 설명 | 방향 | 기본 가중치 |
|------|------|------|-------------|
| Growth | 매출/이익 성장률 | 높을수록 좋음 | 0.22 |
| Profitability | 수익성 지표 (ROE, 마진) | 높을수록 좋음 | 0.22 |
| Valuation | 밸류에이션 (PE, PB) | 낮을수록 좋음 | 0.20 |
| Quality | 재무 건전성 + 이벤트 반영 | 높을수록 좋음 | 0.18 |
| Momentum | 가격 모멘텀 (1M~12M) | 높을수록 좋음 | 0.12 |
| Volatility | 변동성 리스크 | 낮을수록 좋음 | 0.06 |

### 1.2 섹터별 동적 가중치

섹터 특성에 따라 팩터 가중치를 차등 적용한다. 성장주 섹터는 Growth에, 가치주 섹터는 Valuation에 높은 가중치를 부여한다.

| 섹터 | Growth | Profit | Value | Quality | Mom | Vol |
|------|--------|--------|-------|---------|-----|-----|
| Technology | 0.30 | 0.20 | 0.15 | 0.15 | 0.15 | 0.05 |
| Healthcare | 0.28 | 0.22 | 0.18 | 0.17 | 0.10 | 0.05 |
| Financial Services | 0.18 | 0.25 | 0.22 | 0.20 | 0.10 | 0.05 |
| Consumer Defensive | 0.15 | 0.25 | 0.25 | 0.20 | 0.10 | 0.05 |
| Energy | 0.15 | 0.25 | 0.25 | 0.15 | 0.15 | 0.05 |
| Utilities | 0.10 | 0.25 | 0.30 | 0.20 | 0.08 | 0.07 |
| Real Estate | 0.15 | 0.23 | 0.27 | 0.18 | 0.10 | 0.07 |
| Industrials | 0.22 | 0.23 | 0.20 | 0.18 | 0.12 | 0.05 |
| Comm Services | 0.28 | 0.22 | 0.18 | 0.15 | 0.12 | 0.05 |
| Consumer Cyclical | 0.25 | 0.22 | 0.18 | 0.15 | 0.15 | 0.05 |
| Basic Materials | 0.18 | 0.22 | 0.22 | 0.18 | 0.15 | 0.05 |

### 1.3 시장 상황 반영 규칙

SPY의 60일 수익률로 시장 상황을 판정하고, 팩터 가중치에 보정 승수를 적용한다.

| 시장 상황 | 판정 기준 | Growth | Profit | Value | Quality | Mom | Vol |
|-----------|-----------|--------|--------|-------|---------|-----|-----|
| **강세장** (Bull) | 60일 수익률 > +10% | x1.2 | x1.0 | x0.8 | x0.9 | x1.3 | x0.7 |
| **약세장** (Bear) | 60일 수익률 < -10% | x0.8 | x1.2 | x1.3 | x1.2 | x0.7 | x1.3 |
| **중립** (Neutral) | -10% ~ +10% | x1.0 | x1.0 | x1.0 | x1.0 | x1.0 | x1.0 |

> 최종 팩터 가중치 = 섹터 가중치 x 시장 보정 승수 (정규화 후 합산 = 1.0)

### 1.4 Z-Score 정규화 규칙

모든 팩터 원시값은 Z-Score로 정규화한 후 0~1 스케일로 변환한다.

```
1. 윈저화: 상하위 5% 극단값 클리핑
2. Z-Score 계산: z = (value - mean) / std
3. 0~1 매핑: score = clip((z + 3) / 6, 0, 1)
4. 방향 보정: "낮을수록 좋음" 지표는 score = 1.0 - score
```

---

## 2. 투자 지표 계산 규칙

### 2.1 재무 팩터 (20개 지표)

#### 수익성 지표 (Profitability) - 5개

| 지표 | 계산식 | 정규화 범위 | 해석 기준 |
|------|--------|------------|-----------|
| ROE | 당기순이익 / 자기자본 | (0, 0.3) | > 15% 우수, 10-15% 양호, < 10% 저조 |
| ROA | 당기순이익 / 총자산 | (0, 0.2) | > 10% 우수, 5-10% 양호 |
| ROIC | NOPAT / 투하자본 | (0, 0.25) | NOPAT = 영업이익 x (1 - 0.21) |
| 영업이익률 | 영업이익 / 매출 | (0, 0.4) | > 20% 우수, 10-20% 양호, < 0% 적자 |
| 순이익률 | 당기순이익 / 매출 | (0, 0.3) | 양(+)이면 흑자 기업 |

#### 재무 건전성 (Financial Health) - 5개

| 지표 | 계산식 | 정규화 범위 | 방향 | 해석 기준 |
|------|--------|------------|------|-----------|
| 부채비율 | 총부채 / 자기자본 | (0, 2.0) | 낮을수록 | < 0.5 매우 건전, 0.5-1.0 건전, > 2.0 고위험 |
| 유동비율 | 유동자산 / 유동부채 | (1.0, 3.0) | 높을수록 | > 2.0 우수, 1.0-1.5 적정, < 1.0 위험 |
| 당좌비율 | (유동자산 - 재고) / 유동부채 | (0.5, 2.5) | 높을수록 | 재고 제외한 단기 지급능력 |
| 이자보상배율 | EBIT / 이자비용 | (0, 50) | 높을수록 | 이자 지급 여력 |
| 부채자산비율 | 총부채 / 총자산 | (0, 0.7) | 낮을수록 | 자산 대비 부채 비중 |

#### 효율성 지표 (Efficiency) - 5개

| 지표 | 계산식 | 정규화 범위 | 방향 |
|------|--------|------------|------|
| 자산회전율 | 매출 / 총자산 | (0, 3.0) | 높을수록 |
| 재고회전율 | 매출원가 / 재고 | (0, 20) | 높을수록 |
| 매출채권회전율 | 매출 / 매출채권 | (0, 20) | 높을수록 |
| 운전자본회전율 | 매출 / 순운전자본 | (0, 10) | 높을수록 |
| FCF/매출비율 | 잉여현금흐름 / 매출 | (0, 0.3) | 높을수록 |

#### 배당 지표 (Dividend) - 3개

| 지표 | 정규화 범위 | 방향 | 비고 |
|------|------------|------|------|
| 배당수익률 | (0, 0.08) | 높을수록 | 연 배당 / 주가 |
| 배당성향 | (0, 1.0) | 최적 40-60% | 너무 높으면 지속 불가 |
| 배당성장률 | (-0.2, 0.3) | 높을수록 | 전년 대비 증감 |

#### 성장 지표 (Growth) - 2개

| 지표 | 정규화 범위 | 방향 |
|------|------------|------|
| 매출 성장률 | (-0.2, 0.5) | 높을수록 |
| EPS 성장률 | (-0.3, 0.6) | 높을수록 |

### 2.2 기술적 지표 (Technical) - 10개

#### 계산 파라미터

| 지표 | 기간 | 파라미터 | 정규화 범위 |
|------|------|----------|------------|
| RSI | 14일 | - | (0, 100), 최적 30-70 |
| MACD | Fast 12, Slow 26, Signal 9 | - | (-10, 10) |
| Stochastic | 14일 | Smooth 3 | (0, 100), 최적 30-70 |
| Williams %R | 14일 | - | (-100, 0), 최적 -50~-30 |
| CCI | 20일 | - | (-300, 300), 최적 0 근방 |
| ADX | 14일 | - | (0, 100) |
| Bollinger Width | 20일, 2σ | - | (0, 50), 낮을수록 |
| ATR | 14일 | - | (0, 50), 낮을수록 |
| MA Cross | Short 20, Long 50 | 정규화 % 차이 | (-20, 20) |
| 거래량 비율 | 20일 평균 대비 | - | (0, 5), 최적 1.0 근방 |

#### 기술적 시그널 판정 규칙

```
RSI:
  > 70 → 과매수 (Overbought)
  < 30 → 과매도 (Oversold)
  30-70 → 중립

MACD:
  > 0 → 상승 추세 (Bullish)
  < 0 → 하락 추세 (Bearish)

MA Cross (이동평균 교차):
  > +1% → 강한 골든크로스 (Strong Golden Cross)
  0% ~ +1% → 골든크로스
  -1% ~ 0% → 데드크로스
  < -1% → 강한 데드크로스 (Strong Death Cross)

ADX (추세 강도):
  > 25 → 강한 추세 (Strong Trend)
  20-25 → 추세 형성 중 (Trending)
  < 20 → 추세 없음 (No Trend)
```

### 2.3 감성 팩터 (Sentiment) - 10개

#### 뉴스 감성 분석

VADER 기반 감성 점수에 금융 키워드 임팩트 가중치를 적용한다.

**키워드 감성 가중치 체계:**

| 등급 | 점수 | 키워드 예시 |
|------|------|------------|
| Strong Positive | +0.9 | surge, soar, skyrocket, breakthrough, record high, beat expectations, all-time high |
| Positive | +0.6 | gain, rise, growth, profit, bullish, recovery, momentum, partnership, innovation |
| Weak Positive | +0.3 | steady, stable, maintain, in-line, meet expectations, potential |
| Neutral | 0.0 | announce, report, update, plan, schedule, appoint |
| Weak Negative | -0.3 | concern, caution, uncertainty, headwind, underperform, volatile |
| Negative | -0.6 | drop, fall, decline, loss, layoff, downgrade, disappointing |
| Strong Negative | -0.9 | crash, plunge, collapse, crisis, bankruptcy, fraud, scandal, sec probe |

**뉴스 임팩트 레벨:**

| 레벨 | 가중치 | 키워드 |
|------|--------|--------|
| High Impact | x1.0 | earnings, revenue, guidance, FDA, merger, acquisition, IPO, SEC, bankruptcy |
| Medium Impact | x0.7 | analyst, rating, upgrade, downgrade, price target, contract, product launch |
| Low Impact | x0.4 | conference, interview, opinion, speculation, rumor |

#### 감성 지표 목록

| 지표 | 범위 | 방향 | 판정 기준 |
|------|------|------|-----------|
| 뉴스 감성 점수 | (-1, 1) | 높을수록 | > 0.2 긍정, < -0.2 부정 |
| 뉴스 볼륨 | (0, 100) | 높을수록 | > 50 매우높음, 20-50 높음, 10-20 보통, < 10 낮음 |
| 감성 표준편차 | (0, 0.5) | 낮을수록 | 의견 일치도 |
| SEC 공시 감성 | (-1, 1) | 높을수록 | 공시 문서 분석 |
| Put/Call 비율 | (0.5, 2.0) | 최적 1.0 | > 1.0 약세 심리, < 0.7 강세 심리 |
| VIX 수준 | (10, 50) | 낮을수록 | > 30 공포, 20-30 경계, < 20 안정 |
| 공매도 비율 | (0, 20) | 낮을수록 | > 10% 매우높음, 5-10% 높음, 2-5% 보통 |
| 애널리스트 평점 | (1, 5) | 높을수록 | 4.5+ Strong Buy, 3.5-4.5 Buy, 2.5-3.5 Hold |
| 목표가 괴리율 | (-50, 100) | 높을수록 | > 20% 높은 업사이드, 0-10% 제한적 |
| 감성 모멘텀 | (-1, 1) | 높을수록 | 최근 30% 기사 vs 이전 70% 기사 비교 |

### 2.4 복합 스코어 계산

#### 카테고리 가중치 (최종 합산)

```
재무 팩터 (40%):
  - 수익성: 15%
  - 건전성: 10%
  - 효율성: 8%
  - 배당: 4%
  - 성장: 3%

기술적 팩터: 30%
감성 팩터: 30%
```

#### 최종 복합 점수 → 투자 시그널 매핑

| 복합 점수 | 시그널 | 대시보드 표시 |
|-----------|--------|--------------|
| >= 75 | **Strong Buy** | 진한 초록 + 이중 상향 화살표 |
| 65 - 74 | **Buy** | 초록 + 상향 화살표 |
| 55 - 64 | **Hold** | 노랑 + 수평 화살표 |
| 45 - 54 | **Neutral** | 회색 + 대시 |
| 35 - 44 | **Sell** | 주황 + 하향 화살표 |
| < 35 | **Strong Sell** | 빨강 + 이중 하향 화살표 |

### 2.5 딥 보너스 알고리즘 (Dip Bonus)

낙폭 과대 종목 중 반등 모멘텀이 확인된 종목에 추가 점수를 부여한다.

```
기본 파라미터:
  lookback = 180일
  dip_weight = 0.12 (기본 가중치)

계산식:
  recent_high = max(종가[최근 180일])
  drawdown = (recent_high - 현재가) / recent_high
  dd_score = min(drawdown / 0.30, 1.0)

  ret10 = 최근 10일 수익률
  mom_score = clip((ret10 + 0.05) / 0.10, 0, 1)

  dip_bonus = 0.5 x dd_score + 0.5 x (dd_score x mom_score)

최종 점수 = 기본 복합점수 + (dip_weight x dip_bonus)
```

> 의미: 30% 이상 낙폭 + 10일 반등 확인 시 최대 0.12점 추가

### 2.6 포트폴리오 4단계 진단 (Phase Evaluation)

보유 종목을 20일 모멘텀 기반으로 4단계로 진단한다.

| 단계 | 조건 (20일 수익률) | 대시보드 색상 | 조치 |
|------|-------------------|-------------|------|
| **Uptrend** (상승) | > +10% | 초록 | 보유 유지 또는 추가 매수 검토 |
| **Stable** (안정) | +2% ~ +10% | 파랑 | 현 상태 유지 |
| **Unstable** (불안정) | -5% ~ +2% | 주황 | 주의 관찰, 비중 축소 검토 |
| **Critical** (적신호) | < -5% | 빨강 | 즉시 정밀 분석 필요, 손절 검토 |

### 2.7 모멘텀 지표 계산

| 지표 | 계산 기간 | 설명 |
|------|-----------|------|
| mom_1m | 21 거래일 | 단기 모멘텀 |
| mom_3m | 63 거래일 | 중기 모멘텀 |
| mom_6m | 126 거래일 | 중장기 모멘텀 |
| mom_12m | 252 거래일 | 장기 모멘텀 |
| mom_20d | 20 거래일 | 포트폴리오 진단용 |

**모멘텀 복합 점수:**
```
momentum_score = mom_1m x 0.4 + mom_3m x 0.3 + mom_6m x 0.2 + mom_12m x 0.1
```

### 2.8 백테스트 검증 규칙

분석 결과의 유효성을 과거 데이터로 검증한다.

```
기본 파라미터:
  리밸런싱 주기: 30일
  매수 임계점: 복합점수 >= 60
  매도 임계점: 복합점수 <= 40
  초기 자본: $10,000

성과 지표:
  - 총 수익률 = (최종 자산 - 초기 자본) / 초기 자본 x 100%
  - CAGR = ((최종 / 초기) ^ (1/연수) - 1) x 100%
  - 최대 낙폭 (MDD) = 고점 대비 최저점 하락률
  - 샤프 비율 = 평균 수익률 / 수익률 표준편차
  - 승률 = 수익 거래 수 / 총 거래 수 x 100%
  - 손익비 = 평균 수익 / |평균 손실|
```

---

## 3. 시각화 선택 기준

### 3.1 데이터 유형 → 차트 타입 자동 매핑

분석 데이터의 유형에 따라 최적의 차트를 자동 선택한다.

| 데이터 유형 | 차트 타입 | 선택 조건 |
|------------|-----------|-----------|
| 단일 종목 OHLCV | **캔들스틱 + 거래량** | 가격 시계열 데이터가 OHLCV 형태일 때 |
| 다중 종목 가격 비교 | **정규화 라인 차트** | 2개 이상 종목을 100 기준 정규화 비교 |
| 기술적 지표 | **멀티 서브플롯** | RSI(상단), MACD(중단), 가격+BB(하단) |
| 포트폴리오 구성 | **도넛/파이 차트** | 종목별 비중 표시 |
| 섹터 배분 | **수평 바 차트** | 섹터별 % 비중 |
| 종목간 상관관계 | **히트맵** | RdBu_r 컬러맵, -1~+1 스케일 |
| 수익률 분포 | **히스토그램** | 50 bins, VaR 5% 라인 표시 |
| 상대 강도 | **듀얼 서브플롯** | vs 벤치마크(SPY) 비교 |
| 팩터 스코어 | **레이더(방사형) 차트** | 6대 팩터를 육각형으로 표시 |
| 종목 랭킹 | **수평 바 차트 + 점수** | 복합점수 기준 내림차순 |
| 포트폴리오 건강도 | **신호등 카드** | 4단계 색상 (초록/파랑/주황/빨강) |
| 시장 상황 | **게이지 차트** | Bull/Neutral/Bear 3단계 표시 |

### 3.2 차트 기본 설정

```
색상 팔레트:
  primary: #2962FF (메인 파란색)
  secondary: #FF6D00 (보조 주황색)
  positive: #26A69A (상승/긍정)
  negative: #EF5350 (하락/부정)
  neutral: #78909C (중립)
  background: #FFFFFF
  grid: #E0E0E0

기본 차트 파라미터:
  캔들스틱 이동평균: [20일, 50일, 200일]
  볼린저 밴드: 20일, 2σ
  RSI 기준선: 30 (과매도), 70 (과매수)
  기본 조회 기간: 6개월
  비교 차트 정규화 기준: 100
```

### 3.3 반응형 레이아웃 규칙

```
데스크톱 (>= 1280px):
  - 대시보드 그리드: 3열
  - 메인 차트: 2열 차지
  - 사이드 패널: 1열

태블릿 (768px - 1279px):
  - 대시보드 그리드: 2열
  - 메인 차트: 2열 차지 (full width)

모바일 (< 768px):
  - 대시보드 그리드: 1열
  - 차트 스와이프 네비게이션
```

---

## 4. 리포트 구성 흐름

### 4.1 테마 분석 파이프라인

사용자가 투자 테마(예: AI, 반도체)를 입력하면 자동으로 전체 분석이 진행된다.

```
[입력: 테마명, 후보 종목]
       │
       ├── Step 1. 뉴스 수집
       │   └── 3개 쿼리 x 5개 결과 (테마 동향, 수요, 규제)
       │
       ├── Step 2. SEC 공시 수집
       │   └── 종목당 8-K, 10-Q, 10-K 최근 3건
       │
       ├── Step 3. 재무 데이터 수집
       │   └── 20개 지표 (수익성, 건전성, 효율성, 배당, 성장)
       │
       ├── Step 4. 기술적 분석
       │   └── 10개 지표 (RSI, MACD, BB, ADX 등)
       │
       ├── Step 5. 감성 분석
       │   └── 뉴스 감성 + 키워드 임팩트 + 모멘텀
       │
       ├── Step 6. 40개 팩터 복합 스코어링
       │   └── 섹터 가중치 x 시장 보정 x Z-Score
       │
       ├── Step 7. 딥 보너스 적용
       │   └── 낙폭 과대 + 반등 모멘텀 확인
       │
       ├── Step 8. 랭킹 & 투자 시그널 생성
       │   └── Strong Buy ~ Strong Sell 판정
       │
       └── [출력: 테마 리포트]
            ├── 시장 동향 요약
            ├── 종목별 스코어카드
            ├── 랭킹 테이블
            ├── 인사이트 카드
            └── 시각화 차트 세트
```

#### 테마별 기본 설정

| 테마 | 참조 ETF | 최소 시가총액 | 최대 후보 |
|------|----------|-------------|-----------|
| AI | BOTZ, AIQ | $10B | 15 |
| Semiconductor | SMH, SOXX | $5B | 12 |
| Cloud | CLOU, WCLD | $5B | 12 |
| Cybersecurity | HACK, CIBR | $3B | 10 |
| Biotech | XBI, IBB | $2B | 12 |
| 기타 | - | $1B | 10 |

### 4.2 포트폴리오 진단 파이프라인

```
[입력: 보유 종목 리스트]
       │
       ├── Step 1. 각 종목 20일 모멘텀 계산
       │
       ├── Step 2. 4단계 Phase 분류
       │   └── Uptrend / Stable / Unstable / Critical
       │
       ├── Step 3. 기본 메트릭 계산
       │   └── 모멘텀(1M~12M), 변동성(30D/60D), 낙폭(180D), SPY 상관
       │
       ├── Step 4. 상관관계 분석
       │   └── 종목간 90일 상관계수 히트맵
       │
       ├── Step 5. 리밸런싱 제안
       │   └── Critical 종목 비중 축소, Uptrend 종목 비중 확대
       │
       └── [출력: 포트폴리오 진단 리포트]
            ├── 전체 건강도 요약 (신호등)
            ├── 종목별 Phase 카드
            ├── 상관관계 히트맵
            └── 리밸런싱 제안
```

### 4.3 종합 종목 분석 파이프라인

```
[입력: 단일 종목 티커]
       │
       ├── 재무 분석 (20개 지표)
       ├── 기술적 분석 (10개 지표)
       ├── 감성 분석 (10개 지표)
       ├── 백테스트 검증
       │
       └── [출력: 종합 분석 리포트]
            ├── 복합 점수 & 투자 시그널
            ├── 6대 팩터 레이더 차트
            ├── 기술적 지표 멀티 서브플롯
            ├── 감성 트렌드
            └── 백테스트 성과
```

### 4.4 딥 후보 탐색 파이프라인

```
[입력: 테마 또는 종목 리스트]
       │
       ├── Step 1. 180일 낙폭 계산
       ├── Step 2. 10일 반등 모멘텀 확인
       ├── Step 3. 딥 보너스 스코어링
       ├── Step 4. 복합 점수 + 딥 보너스 합산
       │
       └── [출력: 딥 바잉 후보 리스트]
            ├── 낙폭률 & 반등률 테이블
            ├── 딥 보너스 점수 순위
            └── 매수 타이밍 시그널
```

---

## 5. 인사이트 생성 규칙

### 5.1 투자 시그널 종합 판정

팩터 점수, 백테스트 결과, 감성 분석을 종합하여 최종 투자 판정을 생성한다.

```
포인트 시스템 (총 9점 만점):

[팩터 점수] (0~3점)
  복합점수 >= 70 → 3점
  복합점수 60-69 → 2점
  복합점수 < 60 → 1점

[백테스트 결과] (0~3점)
  수익률 > 20% → 3점
  수익률 10-20% → 2점
  수익률 0-10% → 1점
  수익률 < 0% → 0점

[감성 분석] (0~3점)
  트렌딩 + 긍정 → 3점
  긍정 → 2점
  중립 → 1점
  부정 → 0점
  감성 모멘텀 양(+) → +0.5 보너스
  감성 모멘텀 음(-) → -0.5 페널티

최종 판정:
  >= 7점 + 저위험 → BUY (매수 추천)
  >= 5점 + 저위험 → WATCH (관심 종목)
  >= 4점 → HOLD (보유 유지)
  < 4점 → AVOID (회피)
```

### 5.2 감성 모멘텀 판정

뉴스 기사의 시간 흐름에 따른 감성 변화를 추적한다.

```
recent_sentiment = 평균(최근 30% 기사)
earlier_sentiment = 평균(이전 70% 기사)
momentum = recent_sentiment - earlier_sentiment

판정:
  > +0.15 → Strong Positive (감성 급격 개선)
  +0.05 ~ +0.15 → Positive (감성 개선)
  -0.05 ~ +0.05 → Stable (감성 변화 없음)
  -0.15 ~ -0.05 → Negative (감성 악화)
  < -0.15 → Strong Negative (감성 급격 악화)
```

### 5.3 감성 신뢰도 (Confidence Score)

```
volume_score = min(뉴스 건수 / 20, 1.0)
consistency_score = max(0, 1 - 감성_표준편차)
confidence = volume_score x 0.6 + consistency_score x 0.4

레벨:
  > 0.7 → High (충분한 데이터 + 일관된 의견)
  0.4-0.7 → Medium
  < 0.4 → Low (데이터 부족 또는 의견 분산)
```

### 5.4 트렌딩 감지

```
trending = (뉴스 건수 > 10) AND (감성 점수 > 0.2) AND (감성 모멘텀 > 0)
```

> 3가지 조건 모두 충족 시 해당 테마/종목이 "트렌딩" 상태로 판정

### 5.5 자연어 인사이트 생성 템플릿

각 분석 결과를 사용자가 이해하기 쉬운 자연어로 변환한다.

#### 투자 시그널 인사이트

```
Strong Buy:
  "[종목명]은(는) 재무 건전성과 성장성이 우수하며, 기술적 지표와 시장 감성 모두
   긍정적입니다. 적극 매수를 검토할 수 있습니다."

Buy:
  "[종목명]은(는) 대부분의 분석 지표에서 양호한 신호를 보이고 있습니다.
   매수 관심 종목으로 추가할 수 있습니다."

Hold:
  "[종목명]은(는) 현재 특별한 매수/매도 시그널이 없습니다.
   기존 보유 시 유지, 신규 진입은 추가 관찰 후 판단하세요."

Sell:
  "[종목명]은(는) 여러 지표에서 약세 신호가 감지됩니다.
   비중 축소를 검토하고, 손절 기준을 재점검하세요."

Strong Sell:
  "[종목명]은(는) 재무, 기술적, 감성 분석 모두에서 부정적 신호가 강합니다.
   즉시 포지션 정리를 검토하세요."
```

#### 포트폴리오 건강도 인사이트

```
Uptrend:
  "강한 상승 추세입니다. 현재 포지션을 유지하며, 목표가 도달 시 분할 익절을 고려하세요."

Stable:
  "안정적인 흐름입니다. 특별한 조치 없이 보유를 유지하세요."

Unstable:
  "주의가 필요합니다. 추가 하락 시 손절 기준을 미리 설정하고, 비중 축소를 검토하세요."

Critical:
  "경고: 상당한 하락이 진행 중입니다. 즉시 해당 종목의 정밀 분석을 수행하고,
   손절 여부를 결정하세요."
```

#### 딥 바잉 인사이트

```
높은 딥 보너스 (> 0.08):
  "[종목명]이(가) 고점 대비 [X]% 하락한 상태에서 최근 반등 조짐을 보이고 있습니다.
   역발상 매수 기회가 될 수 있으나, 추가 하락 리스크도 존재합니다."

낮은 딥 보너스 (< 0.04):
  "[종목명]의 낙폭이 크지 않거나 반등 모멘텀이 부족합니다.
   딥 바잉 매력은 제한적입니다."
```

### 5.6 위험 경고 조건 & 표시

다음 조건 중 하나라도 해당하면 대시보드에 경고 배너를 표시한다.

| 조건 | 경고 레벨 | 경고 문구 |
|------|----------|-----------|
| VIX > 30 | HIGH | "시장 공포 지수가 높습니다. 신규 진입에 주의하세요." |
| 종목 MDD > 30% | HIGH | "최대 낙폭이 30%를 초과했습니다. 손절 기준을 재점검하세요." |
| 부채비율 > 2.0 | MEDIUM | "부채 수준이 높습니다. 재무 건전성을 확인하세요." |
| RSI > 80 | MEDIUM | "과매수 구간입니다. 단기 조정 가능성에 유의하세요." |
| 공매도 비율 > 10% | MEDIUM | "공매도 비율이 높습니다. 하방 압력에 주의하세요." |
| 데이터 품질 < 70% | LOW | "데이터 품질이 낮습니다. 분석 결과의 신뢰도가 제한될 수 있습니다." |

---

## 6. 데이터 품질 관리

### 6.1 데이터 검증 규칙 (8개 체크)

| 체크 항목 | 통과 기준 |
|-----------|-----------|
| 필수 컬럼 존재 | Open, High, Low, Close 필수 |
| 데이터 타입 | 가격 컬럼 모두 숫자형 |
| 날짜 연속성 | 3일 초과 갭 없음 (주말 제외) |
| 결측치 | 가격 컬럼 NaN < 1% |
| 이상치 | 3σ 이상 이상치 < 5건 |
| 제로값 | OHLC에 0 없음 |
| 가격 일관성 | High >= Low, High >= Open/Close |
| 거래량 | 음수 없음, 0인 날 < 20% |

### 6.2 데이터 품질 점수

```
quality_score = (통과 체크 수 / 전체 체크 수) x 100%

등급:
  >= 95% → Excellent
  85-95% → Good
  70-85% → Fair (경고 표시)
  50-70% → Poor (분석 제한)
  < 50% → Critical (분석 불가)
```

### 6.3 자동 데이터 클리닝

```
결측치: Forward Fill → Backward Fill
제로값: NaN 변환 후 Forward Fill
이상치: ±3σ 범위로 윈저화 클리핑
```

---

## 7. 범용성 설계

### 7.1 다중 시장 지원

| 시장 | 티커 형식 | 통화 | 거래 시간 | 데이터 소스 |
|------|----------|------|-----------|------------|
| 미국 (US) | AAPL, MSFT | USD ($) | 09:30-16:00 ET | yfinance, Finnhub, Alpha Vantage, Google News RSS |
| 한국 (KR) | 005930 / 005930.KS (KOSPI) / 247540.KQ (KOSDAQ) / "삼성전자" | KRW (₩) | 09:00-15:30 KST | PyKrx (OHLCV), DART OPEN API (재무), Google News KR RSS |

#### 7.1.0 KOSPI vs KOSDAQ 자동 분류 (`kr_market_lookup`)

PyKrx 의 시장 리스트 엔드포인트가 2026-04 KRX-side 변경으로 깨진 이후
`mcp_server/tools/kr_market_lookup.py` 의 3-tier 분류기가 yfinance 의
정확한 suffix (`.KS` vs `.KQ`) 를 결정한다.

```
1. Seed JSON (mcp_server/data/kr_kosdaq_codes.json, ~90개) — 인기
   KOSDAQ 코드 즉시 매핑 (오프라인, 0 네트워크)
2. yfinance probe — 시드에 없으면 .KS → 실패 시 .KQ 시도, 결과 캐시
3. Default .KS — 둘 다 실패 시 (PyKrx OHLCV 경로는 suffix 무관하게 OK)
```

영향: `247540` (에코프로BM), `086520` (에코프로) 등 KOSDAQ 종목이
이전엔 `.KS` 로 매핑되어 yfinance 404 → 분석 빈 응답이었으나, 이제
정확히 `.KQ` 매핑되어 정상 분석됨.

#### 7.1.1 시장 자동 분류 규칙 (`detect_market`)

입력 티커 문자열을 아래 우선순위로 판정한다.

```
1. Hangul 포함 ([가-힣]) → KR  (예: "삼성전자")
2. .KS / .KQ 접미 → KR         (예: "005930.KS")
3. 6자리 숫자 → KR             (예: "005930")
4. 그 외 (알파벳, BRK.A 등) → US (default)
```

#### 7.1.2 한국 기업명 ↔ 6자리 코드 양방향 Resolver

**`resolve_korean_ticker(query)`** — 한글명 → 6자리 코드 (3-tier):

```
Step 1. 시드 딕셔너리 (~45개 대형주, 오프라인 즉시)
        "삼성전자" → "005930", "SK하이닉스" → "000660",
        "LG에너지솔루션" → "373220", "에코프로비엠" → "247540" 등

Step 2. 전체 PyKrx 인덱스 (첫 요청 시 lazy build, 24h 캐시)
        KOSPI + KOSDAQ ~2,600 종목 name → code 맵

Step 3. Prefix / Substring fallback
        "삼성" → "005930" (best-effort 매칭)

이미 코드/접미 형태이거나 US 티커면 입력 그대로 passthrough (멱등).
```

**`code_to_name(code)`** — 6자리 코드 → 한글명 (역방향, 동일 3-tier):
시드 dict 의 inverse map → 캐시된 PyKrx 인덱스 → `KoreanMarketAdapter.get_ticker_name`. 알 수 없으면 `None`.

**`label_kr_ticker(code)`** — `"한글명 (코드)"` 표준 포맷터:
```
"005930"  → "삼성전자 (005930)"
"247540"  → "에코프로비엠 (247540)"
"AAPL"    → "AAPL"   (US 는 코드만)
"999999"  → "999999" (이름 모르면 코드만)
```

#### 7.1.2.1 양방향 매칭이 적용된 라우터/페이지

API 응답에 자동으로 `name_kr` / `market` / `currency` 가 enrichment 되어
프론트가 별도 client-side resolver 없이 dual label 을 렌더한다.

| API/도구 | enrichment |
|---|---|
| `/api/stock/comprehensive`, `/signal`, `/investment-signal`, `/factor-interpretation` | `name_kr` 헤더 + 모든 KR 행 |
| `/api/ranking/stocks` | basket 의 모든 한글명 입력 → 코드 변환 + 응답 행마다 `name_kr` |
| `/api/portfolio/comprehensive` | holdings 파싱 시 한글명 token 수용 (`삼성전자:10@70000`), 행마다 `name_kr` |
| `/api/dart/filings`, `/api/dart/financials` | 응답에 `name_kr` |
| `/api/news/sentiment`, `/api/news/timeline` | 응답에 `name_kr` |
| `/api/theme/kr/tickers` | 코드 + `names` 배열 |
| 챗봇 `_tag_ranking_item` | tool_result artifact 의 ranking 행에 `name_kr` |
| `report_builder.rankings_to_table` | KR 종목 포함 시 "이름" 컬럼 자동 추가 |

프론트엔드 dual-label 렌더 (단일 표준 포맷):
```
삼성전자 (005930)        ← /ranking, /portfolio, /theme 테이블
에코프로비엠 (247540)     ← /chat ArtifactPanel 테이블
✓ 삼성전자 (005930)      ← /stock 검색 후 입력창 옆 배지
```

`dashboard/src/lib/locale.ts::formatKrTickerLabel(ticker, name?)` 가
모든 페이지에서 동일하게 사용된다.

#### 7.1.3 통화 표기 강제 규칙 (UI + LLM)

모든 가격/시가총액 수치는 시장 태그에 따라 포맷을 자동 전환한다.

| 시장 | 통화 | 포맷 예시 | 자리수 |
|------|------|----------|--------|
| KR | KRW | `₩214,500`, `₩400조` | 소수 없음, 천 단위 콤마 |
| US | USD | `$190.12`, `$3.2T` | 소수 2자리 |

LLM 시스템 프롬프트에도 명시:
- 도구 결과의 `market`/`currency` 필드 확인 → 해당 통화 기호 사용
- 한국 종목과 미국 종목 혼용 시 종목별로 해당 통화 (혼용 금지)
- 한국 종목은 한글명 + 6자리 코드 병기 (예: "삼성전자(005930)")
- 점수/수익률 등 **단위 없는 값은 통화 기호 붙이지 않음**

#### 7.1.4 KR 전용 데이터 경로 분기

`data_integrator` 와 팩터 계산 파이프라인은 `detect_market` 결과에 따라
분기한다. Alpha Vantage / Finnhub 은 한국 상장사를 커버하지 않으므로
KR 경로에서는 절대 호출하지 않는다.

```
기술적 지표: KR → PyKrx OHLCV + TechnicalFactors.calculate_all (로컬)
             US → Alpha Vantage (getRSI/getMACD/getBBANDS)
재무 지표:   KR → DART OPEN API (K-IFRS: ROE/ROA/Operating/Net/Revenue_Growth)
                  + PyKrx fundamental (PER/PBR/EPS)
             US → Finnhub basic_financials
뉴스 감성:   KR → news_search_kr (Google News KR RSS, 한글명 쿼리)
                  + 한국어 감성 키워드 확장
             US → Finnhub company news (fallback Google News EN)
시장 국면:   KR → KOSPI 60D 수익률 (임계 ±5%)
             US → SPY 60D 수익률 (임계 ±10%, 섹션 1.3)
```

#### 7.1.5 한국 테마 맵 (`mcp_server/data/kr_themes.json`)

미국 테마는 ETF Top Holdings 로 자동 발굴하지만, 한국은 ETF 커버리지가 낮고
테마 분류 관행이 다르므로 **큐레이션된 JSON 맵** (18개 테마 × 3~5 종목)
을 사용한다. 예:

```
2차전지:   373220(LG엔솔) · 247540(에코프로BM) · 006400(삼성SDI) · 066970 · 096770
원전:     034020(두산에너빌) · 138930 · 267260 · 329180
AI반도체:  000660(SK하이닉스) · 005930(삼성전자) · 042700(한미반도체) · 058470(리노공업)
조선:     009540(HD현대조선) · 010140(삼성중공업) · 042660(한화오션) · 077970
바이오:   207940(삼성바이오) · 068270(셀트리온) · 145020 · 326030
방산:     047810(한국항공우주) · 012450(한화에어로) · 272210 · 064350
로봇, 전력설비, 자동차, 반도체장비, 자율주행, 게임, 엔터, 리츠, 화장품, 음식료, 건설 …
```

추가/수정은 JSON 파일만 편집하면 즉시 반영된다 (일일 캐시).

#### 7.1.6 한국 뉴스 감성 키워드 (`news_sentiment` 확장)

영어 VADER 사전 위에 한국어 금융 어휘를 병합 (substring 매칭).

| 등급 | 한국어 키워드 |
|------|--------------|
| Strong Positive | 역대급, 급등, 상한가, 신고가 |
| Positive | 매수, 상승, 개선, 성장, 호조, 실적 개선, 호재 |
| Weak Positive | 유지, 안정, 예상 부합 |
| Negative | 하락, 악재, 부진, 실망, 감소, 하향 |
| Strong Negative | 급락, 하한가, 우려, 손실 확대, 폭락 |

**`SentimentFactors.analyze_news_sentiment(ticker, days, market)`** 도
KR 분기 — KR 티커는 `KoreanMarketAdapter.get_ticker_name` 으로 회사명을
조회해 `hl=ko&gl=KR&ceid=KR:ko` Google News RSS 로 검색. URL 은 `urllib.parse.quote()` 로 인코딩되어 `326030 stock` 처럼 raw space 가 포함된 쿼리도 안전.

### 7.2 데이터 입력 형식

3가지 입력 방식을 지원하여 다양한 데이터 구조에 대응한다.

```
1. 티커 직접 입력: "AAPL, MSFT, GOOGL"
   → 실시간 API로 데이터 자동 수집

2. 테마 입력: "AI", "semiconductor"
   → ETF 기반 자동 종목 추천 후 분석

3. CSV 업로드:
   → 필수 컬럼: Date, Close (최소)
   → 선택 컬럼: Open, High, Low, Volume
   → 자동 데이터 검증 후 분석 진행
```

### 7.3 캐시 정책

분석 성능 최적화를 위한 6단계 TTL 캐시를 적용한다.

| 데이터 유형 | TTL | 설명 |
|------------|-----|------|
| 실시간 가격 | 15분 | 장중 데이터 |
| 기술적 지표 | 4시간 | 일중 변동 반영 |
| 뉴스/감성 | 1시간 | 뉴스 업데이트 주기 |
| 재무 데이터 | 24시간 | 분기별 변동 |
| SEC 공시 | 24시간 | 공시 발생 빈도 |
| 메트릭/랭킹 | 4시간 | 재계산 주기 |

---

## 8. 대시보드 페이지 구성

### 8.1 Market Overview (시장 개요)

```
구성 요소:
  - 시장 상황 게이지 (Bull / Neutral / Bear)
  - 주요 지수 카드 (S&P 500, NASDAQ, DOW)
  - VIX 공포 지수 표시
  - 섹터별 성과 히트맵
```

### 8.2 Theme Explorer (테마 탐색)

```
구성 요소:
  - 테마 선택 (AI, 반도체, 클라우드 등) / 직접 입력
  - 테마 인사이트 추천 카드
  - 종목 랭킹 테이블 (점수, 시그널, 재무/기술/퀄리티 점수, 섹터)
  - [하단] LLM 테마 분석 리포트 (AI 요약 + 관련 뉴스 + 핵심 근거)
```

### 8.3 Stock Analyzer (종목 분석)

```
구성 요소:
  - 종목 검색 / 입력
  - 투자 시그널 카드 (Strong Buy ~ Strong Sell) + 복합점수
  - 6대 팩터 레이더 차트
  - 투자 판단 근거 카드 (매수 이유 + 리스크 평가)
  - 팩터 해석 3열 그리드 (재무 / 기술적 / 감성 분석 텍스트)
  - 핵심 펀더멘털 요약 (P/E, ROE, 매출성장률 등)
  - 6개월 가격 차트 (AreaChart)
  - [하단] LLM 종합 분석 리포트 (AI 요약 + 관련 뉴스 + 핵심 근거)
```

### 8.4 Portfolio Dashboard (포트폴리오)

```
구성 요소:
  - 보유 종목 입력 (TICKER:수량@매입가 형식)
  - 4단계 건강도 요약 카드 (총 자산, 총 손익, 건강도, Phase)
  - 보유 종목 분석 테이블 (주수, 매입/현재가, P&L, 점수, 시그널)
  - 포트폴리오 구성 도넛 차트
  - 종목별 P&L 수평 바 차트
  - 리스크 경고 / 긍정 시그널 카드
  - [하단] LLM 포트폴리오 진단 리포트 (AI 요약 + 관련 뉴스 + 핵심 근거)
```

### 8.5 Ranking Engine (랭킹)

```
구성 요소:
  - 후보 종목 입력 (쉼표 구분)
  - 랭킹 인사이트 요약 카드
  - 랭킹 결과 테이블 (순위, 점수, 시그널, 재무/기술/성장/퀄리티 점수, 섹터)
  - [하단] LLM 랭킹 분석 리포트 (AI 요약 + 핵심 근거)
```

### 8.6 LLM 종합 분석 리포트 (각 페이지 하단)

각 분석 페이지(종목/포트폴리오/테마/랭킹) 하단에 AI 기반 종합 분석 리포트 섹션이 포함된다.
사용자가 "리포트 생성" 버튼을 클릭하면 LLM이 수집된 데이터를 종합하여 한국어 리포트를 생성한다.

```
LLM 엔진: Google AI Studio - Gemini 3.1 Flash-Lite Preview
타임아웃: 300초 (5분)
응답 언어: 한국어 (전문 용어 한국어+영문 병기)

리포트 구성:
  1. AI 종합 분석 요약
     - ## 종합 요약: 투자의견/점수/핵심 판단
     - ## 핵심 근거: 펀더멘털, 밸류에이션, 뉴스 인용
     - ## 리스크 및 우려사항: 기술적 약세, 변동성, 구조적 리스크
     - ## 결론: 투자 전략, 진입/퇴출 조건

  2. 관련 뉴스 & 이벤트
     - 최근 7일 뉴스 5건 (제목 + 출처 + 날짜 + 링크 + 요약)
     - Google News RSS 폴백 지원
     - HTML 태그 자동 제거

  3. 핵심 근거 데이터
     - 주요 지표 key-value 요약 (종합점수, 시그널, P/E, ROE 등)

프롬프트 구조:
  - System: 시니어 금융 애널리스트 역할, 4섹션 구조, 뉴스 인용 규칙
  - User: 구조화된 데이터 블록 (■ 기호) + 뉴스 snippet 포함
  - 뉴스 인용 지시: "~에 따르면(출처)" 형태로 자연스럽게 인용
```

#### 페이지별 리포트 API

| 페이지 | API 엔드포인트 | 데이터 소스 |
|--------|---------------|------------|
| 종목 분석 | `/api/stock/analysis-report` | 팩터 점수 + 투자 시그널 + 재무/기술 해석 + 뉴스 + 센티먼트 |
| 포트폴리오 | `/api/portfolio/analysis-report` | 포트폴리오 현황 + 보유 종목 분석 + 경고 + 뉴스 |
| 테마 | `/api/theme/analysis-report` | 테마 랭킹 + 종목별 점수 + 매수 시그널 + 뉴스 |
| 랭킹 | `/api/ranking/analysis-report` | 비교 랭킹 + 팩터별 점수 + 매수/매도 시그널 |

---

## 9. AI 챗봇 (Conversational Analyst)

### 9.1 챗봇 개요

`/chat` 페이지는 PM-MCP 분석 도구를 **자연어로 질의**할 수 있는 대화형
인터페이스다. LLM 이 사용자 질문을 읽고 적절한 도구를 자동 호출하여
답변하는 **tool-augmented generation** 패턴을 사용한다.

### 9.2 도구 레지스트리 (13개)

| 범주 | 도구 | 용도 |
|---|---|---|
| 시장 | `market_condition` | Bull/Bear/Neutral + SPY 60D 수익률 |
| 종목 | `stock_comprehensive`, `stock_signal` | 단일 종목 종합 분석·시그널 (KR/US 자동) |
| 랭킹 | `rank_stocks`, `analyze_theme` | 멀티팩터 랭킹, 테마 기반 발굴 |
| Discovery | `propose_themes`, `propose_tickers`, `dip_candidates`, `watchlist_signals` | cold-start 추천 |
| 뉴스 | `news_sentiment` | 티커별 센티먼트 (KR/US) |
| **KR 전용** | `propose_themes_kr`, `analyze_theme_kr`, `dart_filings` | 한국 테마 + 공시 |

### 9.3 Tool-calling 프로토콜

네이티브 function calling 대신 **JSON 한 줄 contract** 사용 (Gemma 계열
호환). LLM 이 도구가 필요하면 답변 첫 줄에 다음 형식으로 출력한다.

```
{"tool": "도구이름", "args": {"key": "value"}}
```

백엔드가 파싱 → 실행 → 결과를 다음 턴 transcript 에 주입 → 다시 LLM 호출.
최대 5 hop, 초과 시 강제 종료.

### 9.4 세션 메모리

- in-memory dict, 30 분 TTL, lazy GC
- 20 turn rolling window (프롬프트 비대화 방지)
- `session_id` 를 클라이언트가 보관해 다중 턴 이어 질의

### 9.5 스트리밍 (SSE)

`GET /api/chat/stream` 은 `text/event-stream` 으로 5종 이벤트를 발행한다.

| 이벤트 | 필드 | 타이밍 |
|---|---|---|
| `tool_call` | tool, args, hop | LLM 이 도구 호출 결심한 직후 |
| `tool_result` | tool, ok, summary, ms, hop | 도구 실행 완료 |
| `token` | text | 최종 답변 청크 (typewriter) |
| `done` | hops, session_id | 턴 종료 |
| `error` | message, retriable | 예외 (503 등) |

클라이언트는 `fetch` + `ReadableStream` + `AbortController` 로 소비.
첫 이벤트 도달 전 실패 시 비-스트리밍 `POST /api/chat` 으로 자동 fallback.

### 9.6 LLM 신뢰성 전략 (`call_llm_resilient`)

| 실패 유형 | 처리 |
|---|---|
| 5xx / timeout / connection | 같은 모델로 지수 백오프 재시도 (기본 3회) |
| **429 (rate limit)** | **같은 모델 재시도 금지** → 즉시 fallback 모델 전환 + circuit reset |
| **404 (모델 없음)** | 해당 모델 skip → 다음 fallback 시도 |
| 인증/스키마 오류 | 즉시 raise (retry 무의미) |

모델 체인 (`GEMINI_FALLBACK_MODELS` env, 2026-04-23 갱신):
```
gemini-2.5-flash → gemini-2.0-flash → gemini-2.0-flash-lite → gemini-2.5-flash-lite → gemini-1.5-flash-latest
```

챗봇 + 분석 리포트는 `settings.default_chat_model = gemini-3.0-flash`
(2026-04-23 신규 기본) 에 고정되고 preview/experimental 모델은
`CHAT_USE_PREVIEW=1` 로 opt-in. 3.0 이 rate-limit 또는 일시 장애 시
위 chain 으로 자동 강등.

### 9.7 관측성 (`/api/chat/metrics`)

thread-safe 카운터로 p50/p95 레이턴시, tool_ok/tool_err, tool_error_rate,
llm_errors, hop_avg, uptime 반환. Prometheus 전 단계의 경량 스냅샷.

### 9.8 프론트 구조 (mcp-chatbot-ux)

2-pane analyst workbench (Perplexity Finance + Claude.ai Artifacts + Linear 벤치마크):
- **ChatHeader**: Model Selector + ⌘K + New Chat + Theme Toggle + Session badge
- **ConversationPane**: user / assistant / error 버블, Markdown, BlinkingCaret
- **ArtifactPanel**: tool 결과 tabbed 렌더 (RankingsTable, MarketGaugeMini, NewsListPanel)
  — `P1 placeholder` (summary-only), 후속 사이클에서 구조화 데이터 확장 예정
- **CommandPalette**: 네이티브 `<dialog>`, ↑↓/Enter/Esc, quick-start 필터
- **ThemeToggle**: `<html data-theme>` + localStorage 영속

### 9.9 LLM 출력 토큰 한도

`LLM_MAX_OUTPUT_TOKENS_DEFAULT = 8192` (env override 가능). 한국어 마크다운
분석 리포트가 중간에 잘리지 않도록 이전 2048 → 8192 로 상향.
`finishReason == "MAX_TOKENS"` 감지 시 warning 로그로 truncation 명시적 알림.

---

## 10. 로드맵 진행 현황 (2026-04-23)

### 10.1 완료 (archived)

| Feature | Phase | Match Rate | 아카이브 |
|---|---|---|---|
| backend-quality-upgrade | archived | 91% | `docs/archive/2026-04/backend-quality-upgrade/` |
| frontend-quality-upgrade | archived | 90% | `docs/archive/2026-04/frontend-quality-upgrade/` |
| mcp-chatbot | archived | 91% | `docs/archive/2026-04/mcp-chatbot/` |
| mcp-chatbot-streaming | archived | 98% | `docs/archive/2026-04/mcp-chatbot-streaming/` |
| mcp-chatbot-performance | archived | 92% | `docs/archive/2026-04/mcp-chatbot-performance/` |
| mcp-chatbot-ux | archived | 94% | `docs/archive/2026-04/mcp-chatbot-ux/` |
| **rich-visual-reports** | **archived** | **92%** | `docs/archive/2026-04/rich-visual-reports/` |

### 10.2 진행 중 (do)

| Feature | 상태 |
|---|---|
| kr-stock-integration (P1+P2) | 코어 + DART + KR 테마 + 한국 뉴스 + KOSDAQ 분류 + 양방향 매칭 모두 구현 완료. 운영 가동 중. 최종 archive 대기 |

### 10.3 운영성 핫픽스 (포스트-rich-visual-reports, archived 외부)

| 변경 | 효과 |
|---|---|
| KOSDAQ classifier (`kr_market_lookup`) | `247540` 등 KOSDAQ 종목 정상 분석 가능 |
| KR sentiment URL 인코딩 + 한국어 RSS 분기 | KR 티커 sentiment 0건 → 90+ articles |
| 한글명 ↔ 코드 양방향 매칭 + dual label | 모든 라우터/페이지에서 `삼성전자 (005930)` 통일 표시 |
| Default LLM `gemini-3.0-flash` | 챗봇/리포트 모두 최신 Flash 사용 + 2.x chain fallback |

### 10.4 계획 (기록만)

| Feature | 예상 범위 |
|---|---|
| kr-stock-integration P3 | KIS 실시간 호가, 멀티통화 포트폴리오, 거래시간 감지, 외국인/기관 수급 |
| chart-polish | 차트 mode 탭, dashed grid, 반응형 axis, skeleton chart |
| a11y-audit | axe-core 자동화 |
| mcp-chatbot-v2 integration | streaming/performance/ux/rich-visual-reports 통합 릴리스 브랜치 |

---

## 11. Rich Visual Reports (Block-based UI)

ShowMe 스타일의 구조화된 답변 시스템. LLM 이 prose 마크다운 대신
**블록 배열 JSON** 을 반환하고 프론트가 dispatcher 로 카드/차트/표로
분해 렌더한다. 분석 리포트 + 챗봇 도구 결과 모두 적용.

### 11.1 11종 ReportBlock 스키마

| kind | 용도 | 데이터 출처 |
|---|---|---|
| `summary` | 제목 + Markdown 본문 + `[1][2]` 인용 | LLM JSON output |
| `metric` / `metric_grid` | BigNumber 카드 (label / value / delta / tone) | 결정론적 builder |
| `factor_bullet` | 6대 팩터 점수 막대 + 해석 한 줄 | LLM JSON output |
| `news_citation` | 번호 bubble + 제목 + 출처 + URL | search_news |
| `price_spark` | 미니 area chart + delta % | get_prices |
| **`candlestick`** | 거래량 overlay + MA20/MA50 | PyKrx/yfinance OHLCV |
| `table` | sortable headless, tabular-nums, format(currency/percent/compact/integer) | 다양 |
| `heatmap` | CSS-grid (correlation/heat 스케일) | 상관관계 |
| `sector_treemap` | flex squarified, PnL tint | 섹터 배분 |
| `radar_mini` | 6 팩터 RadarChart, tick 제거 | 팩터 점수 |

Python: `api/schemas/report_blocks.py` (Pydantic discriminated union).
TS mirror: `dashboard/src/lib/reportBlocks.ts`.

### 11.2 Deterministic-first 정책

수치는 코드, 해석만 LLM:

```python
# api/services/report_builder.py
blocks = [
    build_stock_metric_grid(ticker, ranking, fundamentals, market),
    *build_price_blocks(ticker, df, market),       # price_spark + candlestick
    build_news_citation(news_items),
    build_radar_mini(factors),
]
# LLM 은 summary + factor_bullet 만 추가 (call_llm_json)
llm_blocks = parse_llm_blocks(llm_raw)
blocks.extend(b.model_dump() for b in llm_blocks)
```

### 11.3 LLM JSON 파서 — 3-strategy fallback

```python
# api/services/report_builder.py::parse_llm_blocks
1. json.loads(전체)         → 파싱 성공 시 coerce_block list
2. 첫 [..마지막 ] 추출 후 parse  → balanced bracket 회수
3. SummaryBlock(markdown=raw)   → prose fallback (회귀 0)
```

LLM 이 schema 안 지켜도 사용자에게는 항상 prose 답이 보장됨.

### 11.4 차트 팔레트 (CSS 토큰)

`globals.css`:
```css
:root            { --chart-grid:#e2e8f0; --chart-axis:#64748b;
                   --chart-pos:#10b981; --chart-neg:#ef4444; ... }
html[data-theme="dark"] { /* 동일 키, 다크 변형 */ }
```

모든 차트 컴포넌트가 `var(--chart-...)` 참조 → `<html data-theme>`
swap 시 즉시 반영, 별도 React state 없음.

### 11.5 `CandlestickBlock` — 의존성 0

Recharts ComposedChart + 커스텀 `CandleShape` (wick + body SVG, ~50줄):
- `TradingView`/`lightweight-charts` 같은 외부 라이브러리 도입 회피 (+40KB gzip 절감)
- volume sub-series + MA20/MA50 라인 overlay
- `var(--chart-pos/neg)` 다크모드 자동 swap

### 11.6 챗봇 artifact 통합

`ToolResultEvent.artifact?: list[ReportBlock]` — `rank_stocks` /
`analyze_theme` / `watchlist_signals` / `stock_comprehensive` 등 도구
결과를 `[TableBlock, RadarMiniBlock]` 으로 자동 변환 → `ArtifactPanel`
(또는 chat 페이지의 인라인 BlockRenderer) 가 즉시 렌더.

KR 종목이 ranking 에 포함되면 `TableBlock.columns` 에 "이름" 컬럼이
자동 추가되어 한글명도 표시 (`rankings_to_table`).

### 11.7 framer-motion stagger

`Motion.tsx` — `FadeIn`, `Stagger`, `StaggerItem` + `useReducedMotion`.
`prefers-reduced-motion` 사용자에게 자동으로 애니메이션 비활성화 (a11y).
`MetricGridBlock`, `BlockList` 가 stagger 적용해 부드럽게 mount.
