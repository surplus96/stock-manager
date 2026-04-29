#!/usr/bin/env python3
"""기획서 PDF 생성 - Stock Manager (다이어그램 없이 텍스트 기반)"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Font ──
FONT_PATH = "/Library/Fonts/Arial Unicode.ttf"
pdfmetrics.registerFont(TTFont("KR", FONT_PATH))

# ── Colors ──
C_PRIMARY = HexColor("#1a237e")
C_ACCENT = HexColor("#2962FF")
C_DARK = HexColor("#212121")
C_GRAY = HexColor("#616161")
C_LIGHT = HexColor("#F5F7FA")
C_TH = HexColor("#1a237e")
C_STRIPE = HexColor("#EEF1F8")
C_BORDER = HexColor("#BDBDBD")

# ── Styles ──
base = getSampleStyleSheet()

def S(name, **kw):
    d = {"fontName": "KR", "textColor": C_DARK, "leading": 18}
    d.update(kw)
    return ParagraphStyle(name, parent=base["Normal"], **d)

ST_TITLE    = S("T", fontSize=28, leading=36, textColor=C_PRIMARY, alignment=TA_CENTER, spaceAfter=6)
ST_SUB      = S("Sub", fontSize=14, leading=20, textColor=C_GRAY, alignment=TA_CENTER, spaceAfter=30)
ST_H1       = S("H1", fontSize=20, leading=28, textColor=C_PRIMARY, spaceBefore=24, spaceAfter=12)
ST_H2       = S("H2", fontSize=15, leading=22, textColor=C_ACCENT, spaceBefore=18, spaceAfter=8)
ST_H3       = S("H3", fontSize=12, leading=18, textColor=C_DARK, spaceBefore=12, spaceAfter=6)
ST_P        = S("P", fontSize=10, leading=16, spaceAfter=6)
ST_BULLET   = S("BL", fontSize=10, leading=16, leftIndent=20, bulletIndent=10, spaceAfter=4)
ST_TH       = S("TH", fontSize=9, leading=13, textColor=white)
ST_TD       = S("TD", fontSize=9, leading=13)

PAGE_W, PAGE_H = A4
MARGIN = 2.2 * cm


def hf(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(C_PRIMARY)
    canvas.setLineWidth(1.5)
    canvas.line(MARGIN, PAGE_H - MARGIN + 8, PAGE_W - MARGIN, PAGE_H - MARGIN + 8)
    canvas.setFont("KR", 8)
    canvas.setFillColor(C_GRAY)
    canvas.drawString(MARGIN, PAGE_H - MARGIN + 12, "Stock Manager - AI Investment Dashboard")
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - MARGIN + 12, "Hackathon 2026")
    canvas.drawCentredString(PAGE_W / 2, 1.2 * cm, f"- {doc.page} -")
    canvas.line(MARGIN, 1.5 * cm, PAGE_W - MARGIN, 1.5 * cm)
    canvas.restoreState()


def T(headers, rows, widths=None):
    avail = PAGE_W - 2 * MARGIN
    hc = [Paragraph(f"<b>{h}</b>", ST_TH) for h in headers]
    dr = [[Paragraph(str(c), ST_TD) for c in r] for r in rows]
    data = [hc] + dr
    w = [avail * x for x in widths] if widths else [avail / len(headers)] * len(headers)
    t = Table(data, colWidths=w, repeatRows=1)
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), C_TH),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, -1), "KR"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, C_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            cmds.append(("BACKGROUND", (0, i), (-1, i), C_STRIPE))
    t.setStyle(TableStyle(cmds))
    return t


def p(text):
    return Paragraph(text, ST_P)

def b(text):
    return Paragraph(text, ST_BULLET)

def sp(n=8):
    return Spacer(1, n)

def hr():
    return HRFlowable(width="100%", thickness=1, color=C_PRIMARY, spaceAfter=12)


def build():
    out = "/Users/surplus96/projects/bio-simulagent/PM-MCP/adoring-swartz/docs/기획서_투자대시보드.pdf"
    doc = SimpleDocTemplate(out, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN + 0.5 * cm, bottomMargin=MARGIN)

    s = []

    # ══════════ COVER ══════════
    s.append(Spacer(1, 80))
    s.append(Paragraph("Stock Manager", ST_TITLE))
    s.append(Paragraph("AI 투자 분석 대시보드 서비스 기획서", ST_SUB))
    s.append(sp(20))
    s.append(HRFlowable(width="60%", thickness=2, color=C_PRIMARY, spaceAfter=20))
    s.append(sp(20))
    s.append(T(
        ["항목", "내용"],
        [
            ["서비스명", "Stock Manager - 40개 팩터 기반 AI 투자 분석 대시보드"],
            ["핵심 기술", "Skills.md 규칙 기반 자동 분석 엔진"],
            ["분석 팩터", "재무 20개 + 기술적 10개 + 감성 10개 = 40개"],
            ["시각화", "12종 차트 자동 매핑 + 6단계 투자 시그널"],
            ["대시보드", "6개 페이지 (시장/테마/종목/포트폴리오/랭킹/리포트)"],
            ["기술 스택", "Next.js 15 + Python (FastMCP) + Recharts"],
        ], [0.25, 0.75]))
    s.append(sp(40))
    s.append(Paragraph("2026. 04", S("CD", fontSize=12, alignment=TA_CENTER, textColor=C_GRAY)))
    s.append(PageBreak())

    # ══════════ TOC ══════════
    s.append(Paragraph("목차", ST_H1))
    s.append(hr())
    toc = [
        ("1. 서비스 개요", False), ("1.1 핵심 가치 및 해결 과제", True),
        ("1.2 핵심 차별점", True), ("1.3 대상 사용자", True),
        ("2. 분석 흐름 설계", False), ("2.1 전체 분석 아키텍처", True),
        ("2.2 4대 분석 파이프라인", True), ("2.3 데이터 품질 보장", True),
        ("3. 대시보드 구성", False), ("3.1 6개 페이지 구조", True),
        ("3.2 시각화 자동 매핑 체계", True),
        ("4. Skills.md 설계 방향", False), ("4.1 설계 철학", True),
        ("4.2 구성 체계 (8개 섹션)", True),
        ("5. 확장 기능 아이디어", False),
        ("6. 기술 스택", False),
        ("7. 요약", False),
    ]
    for txt, indent in toc:
        st = S("TOC", fontSize=11, leading=20, leftIndent=20 if indent else 0,
               textColor=C_GRAY if indent else C_DARK)
        s.append(Paragraph(txt, st))
    s.append(PageBreak())

    # ══════════ 1. 서비스 개요 ══════════
    s.append(Paragraph("1. 서비스 개요", ST_H1))
    s.append(hr())

    s.append(Paragraph("1.1 핵심 가치 및 해결 과제", ST_H2))
    s.append(p(
        "Stock Manager는 <b>Skills.md에 정의된 일관된 분석 규칙</b>을 기반으로, "
        "어떤 투자 데이터가 입력되든 <b>자동으로 분석, 시각화, 인사이트 생성</b>까지 "
        "완료하는 범용 금융 투자 대시보드입니다."))
    s.append(sp())
    s.append(T(
        ["기존 문제", "Stock Manager 해결 방식"],
        [
            ["데이터 구조가 매번 달라 일관된 분석이 어려움",
             "3가지 입력 형식(티커/테마/CSV) 자동 대응 + 데이터 품질 8개 항목 자동 검증"],
            ["분석 기준이 주관적이고 편향됨",
             "40개 정량 팩터 + 섹터별 동적 가중치로 객관적 스코어링"],
            ["시각화 선택에 전문 지식 필요",
             "데이터 유형에 따른 12종 차트 자동 매핑"],
            ["인사이트 해석이 어려움",
             "자연어 기반 투자 시그널 + 위험 경고 자동 생성"],
            ["분석 재현이 불가능",
             "Skills.md 규칙으로 누가 돌려도 동일한 결과"],
        ], [0.35, 0.65]))
    s.append(sp(12))

    s.append(Paragraph("1.2 핵심 차별점", ST_H2))
    s.append(b("<b>규칙 기반 범용성:</b> Skills.md 하나로 모든 분석 로직이 정의됩니다. 새로운 데이터가 들어와도 동일한 규칙으로 분석할 수 있습니다."))
    s.append(b("<b>40개 팩터 멀티 분석:</b> 재무 20개, 기술적 10개, 감성 10개 팩터를 통합 스코어링합니다. 단일 지표가 아닌 다차원 종합 분석입니다."))
    s.append(b("<b>시장 적응형 분석:</b> 강세장, 약세장, 중립에 따라 팩터 가중치가 자동 조정됩니다. 11개 섹터별 특성을 반영한 동적 가중치를 적용합니다."))
    s.append(b("<b>실행 가능한 인사이트:</b> Strong Buy에서 Strong Sell까지 6단계 시그널을 제공합니다. 포트폴리오 4단계 건강 진단과 딥 바잉 기회를 자동 탐지합니다."))
    s.append(sp(8))

    s.append(Paragraph("1.3 대상 사용자", ST_H2))
    s.append(T(
        ["사용자 유형", "활용 시나리오"],
        [
            ["개인 투자자", "보유 종목 진단, 신규 투자 후보 탐색"],
            ["투자 동호회", "테마별 종목 분석 공유, 랭킹 비교"],
            ["금융 분석가", "40개 팩터 기반 리포트 자동 생성"],
            ["핀테크 서비스", "API 연동하여 투자 분석 기능 탑재"],
        ], [0.3, 0.7]))
    s.append(PageBreak())

    # ══════════ 2. 분석 흐름 설계 ══════════
    s.append(Paragraph("2. 분석 흐름 설계", ST_H1))
    s.append(hr())

    s.append(Paragraph("2.1 전체 분석 아키텍처", ST_H2))
    s.append(p(
        "Stock Manager의 분석 시스템은 <b>4개 레이어</b>로 구성됩니다."))
    s.append(sp(4))
    s.append(p(
        "<b>첫째, 사용자 입력 레이어</b>에서 티커 직접 입력, 테마 선택, CSV 업로드의 3가지 방식으로 데이터를 받습니다."))
    s.append(p(
        "<b>둘째, 데이터 수집 레이어</b>에서 yfinance로 시장 가격 데이터를, Finnhub으로 재무 데이터를, "
        "Perplexity와 VADER로 뉴스 감성 데이터를, SEC EDGAR에서 공시 데이터를 수집합니다."))
    s.append(p(
        "<b>셋째, Skills.md 분석 엔진 레이어</b>에서 핵심 분석이 수행됩니다. "
        "먼저 데이터 품질을 8개 항목으로 검증한 후, 재무 20개, 기술적 10개, 감성 10개 팩터를 분석합니다. "
        "이후 Z-Score 정규화, 섹터별 동적 가중치, 시장 상황 보정 승수를 적용하여 복합 스코어(0~100)를 산출합니다. "
        "여기에 딥 보너스를 가산하고, 백테스트로 과거 성과를 검증합니다."))
    s.append(p(
        "<b>넷째, 출력 레이어</b>에서 6단계 투자 시그널 판정, 12종 차트 자동 매핑 시각화, "
        "자연어 인사이트 카드를 생성하여 대시보드에 렌더링합니다."))
    s.append(sp(12))

    s.append(Paragraph("2.2 4대 분석 파이프라인", ST_H2))

    # Pipeline A
    s.append(Paragraph("<b>Pipeline A: 테마 분석 (Theme Analysis)</b>", ST_H3))
    s.append(p(
        "사용자가 투자 테마 키워드(예: AI, 반도체)를 입력하면 관련 종목 발굴부터 랭킹까지 8단계로 자동 수행됩니다."))
    s.append(p(
        "먼저 테마에 매핑된 관련 ETF(예: AI는 BOTZ, AIQ)에서 상위 보유 종목을 추출하여 후보 리스트를 생성합니다. "
        "시가총액 기준으로 필터링(AI 테마는 100억 달러 이상)한 후, "
        "3개 검색 쿼리(동향, 수요, 규제)로 뉴스를 수집하고, 종목당 SEC 공시(8-K, 10-Q, 10-K) 최근 3건을 수집합니다. "
        "수집된 데이터로 40개 팩터를 스코어링하고, 딥 보너스(낙폭 + 반등 확인)를 계산한 후, "
        "종합 랭킹과 인사이트가 포함된 테마 리포트를 출력합니다."))
    s.append(sp(8))

    # Pipeline B
    s.append(Paragraph("<b>Pipeline B: 포트폴리오 진단 (Portfolio Diagnosis)</b>", ST_H3))
    s.append(p(
        "보유 종목 리스트를 입력하면 5단계로 건강 상태를 즉시 진단합니다."))
    s.append(p(
        "각 종목의 20일 모멘텀을 계산하여 4단계 Phase(Uptrend, Stable, Unstable, Critical)로 분류합니다. "
        "이후 모멘텀(1M~12M), 변동성(30일/60일), 낙폭(180일), SPY 상관계수 등 기본 메트릭을 산출하고, "
        "종목 간 90일 상관관계를 분석합니다. "
        "최종적으로 Critical 종목은 비중 축소, Uptrend 종목은 비중 확대를 제안하는 리밸런싱 리포트를 출력합니다."))
    s.append(sp(8))

    # Pipeline C
    s.append(Paragraph("<b>Pipeline C: 종합 종목 분석 (Comprehensive Analysis)</b>", ST_H3))
    s.append(p(
        "단일 종목 티커를 입력하면 재무 20개, 기술적 10개, 감성 10개 지표를 전부 분석하는 딥다이브를 수행합니다."))
    s.append(p(
        "섹터별 동적 가중치와 시장 상황 보정을 적용하여 복합 스코어를 산출하고, "
        "백테스트로 과거 성과를 시뮬레이션합니다. "
        "팩터 점수(0~3점), 백테스트 결과(0~3점), 감성 분석(0~3점)을 합산한 9점 만점 종합 판정으로 "
        "최종 투자 시그널과 자연어 인사이트를 생성합니다."))
    s.append(sp(8))

    # Pipeline D
    s.append(Paragraph("<b>Pipeline D: 딥 바잉 레이더 (Dip Buying Radar)</b>", ST_H3))
    s.append(p(
        "낙폭 과대 종목 중 반등 조짐이 보이는 역발상 매수 기회를 자동 탐지합니다."))
    s.append(p(
        "180일 고점 대비 낙폭률을 계산하고, 최근 10일 반등 모멘텀을 확인합니다. "
        "딥 보너스는 낙폭 점수의 50%와 낙폭 점수 곱하기 모멘텀 점수의 50%를 합산하여 산출합니다. "
        "30% 이상 낙폭에 10일 반등이 확인되면 최대 0.12점의 추가 점수가 부여되어, "
        "기본 복합 점수와 합산된 최종 스코어로 딥 바잉 후보를 순위화합니다."))
    s.append(sp(12))

    s.append(Paragraph("2.3 데이터 품질 보장", ST_H2))
    s.append(p(
        "모든 분석 전에 8개 항목을 자동 검증합니다. "
        "필수 컬럼(OHLC) 존재, 숫자형 타입, 날짜 연속성(3일 초과 갭 없음), "
        "결측치 1% 미만, 이상치(3시그마) 5건 미만, 제로값 없음, "
        "가격 일관성(High >= Low), 거래량 유효성을 체크합니다."))
    s.append(sp(4))
    s.append(T(
        ["품질 등급", "점수 범위", "처리"],
        [
            ["Excellent", ">= 95%", "정상 분석 진행"],
            ["Good", "85 - 95%", "정상 분석 진행"],
            ["Fair", "70 - 85%", "경고 표시 후 분석"],
            ["Poor", "50 - 70%", "자동 클리닝(결측 보간, 이상치 윈저화) 후 분석"],
            ["Critical", "< 50%", "분석 불가 안내"],
        ], [0.2, 0.2, 0.6]))
    s.append(PageBreak())

    # ══════════ 3. 대시보드 구성 ══════════
    s.append(Paragraph("3. 대시보드 구성", ST_H1))
    s.append(hr())

    s.append(Paragraph("3.1 6개 페이지 구조", ST_H2))
    s.append(T(
        ["페이지", "핵심 기능", "주요 시각화"],
        [
            ["Market Overview\n(시장 개요)",
             "시장 상황(Bull/Neutral/Bear) 진단, 주요 지수(S&P500, NASDAQ, DOW) 현황, VIX 공포 지수 표시, 트렌딩 테마 감지",
             "시장 게이지 차트, 섹터별 성과 히트맵, 지수 스파크라인"],
            ["Theme Explorer\n(테마 탐색)",
             "테마 키워드 입력으로 종목 자동 발굴, ETF 기반 후보 추천, 40개 팩터 스코어링, 감성 트렌드 추적",
             "종목 랭킹 테이블, 정규화 비교 라인 차트, 뉴스 타임라인, 딥 바잉 하이라이트"],
            ["Stock Analyzer\n(종목 분석)",
             "단일 종목 40개 팩터 종합 분석, 투자 시그널(Strong Buy~Strong Sell) 판정, 백테스트 성과 검증",
             "캔들스틱+볼린저밴드 차트, 기술적 서브플롯(RSI/MACD/ADX), 6대 팩터 레이더 차트"],
            ["Portfolio Dashboard\n(포트폴리오)",
             "보유 종목 4단계 건강 진단(Uptrend/Stable/Unstable/Critical), 상관관계 분석, 리밸런싱 제안",
             "4색 신호등 카드, 상관관계 히트맵, 포트폴리오 도넛 차트"],
            ["Ranking Engine\n(랭킹)",
             "후보 종목 비교, 팩터 가중치 커스터마이징 슬라이더, 백테스트 비교",
             "랭킹 결과 테이블(점수/시그널/팩터별), 백테스트 라인 차트"],
            ["Report Center\n(리포트)",
             "테마/포트폴리오/종합/딥 후보 4종 리포트 자동 생성, 미리보기, Markdown 및 PDF 다운로드",
             "리포트 프리뷰 패널, 다운로드 버튼"],
        ], [0.18, 0.42, 0.40]))
    s.append(sp(16))

    s.append(Paragraph("3.2 시각화 자동 매핑 체계", ST_H2))
    s.append(p(
        "Skills.md에 정의된 규칙에 따라, 분석 데이터의 유형을 판별하여 최적의 차트를 자동 선택합니다. "
        "사용자가 차트 종류를 선택할 필요 없이, 데이터가 들어오면 규칙에 맞는 차트가 자동으로 렌더링됩니다."))
    s.append(sp(4))
    s.append(T(
        ["데이터 유형", "차트 타입", "적용 페이지"],
        [
            ["단일 종목 OHLCV 가격 데이터", "캔들스틱 + 거래량 바 차트", "Stock Analyzer"],
            ["2개 이상 종목 가격 비교", "100 기준 정규화 라인 차트", "Theme Explorer, Ranking"],
            ["기술적 지표 (RSI, MACD, BB)", "멀티 서브플롯 (상/중/하 분할)", "Stock Analyzer"],
            ["포트폴리오 종목 비중", "도넛/파이 차트", "Portfolio Dashboard"],
            ["섹터별 비중 배분", "수평 바 차트", "Market Overview, Portfolio"],
            ["종목간 상관관계 매트릭스", "히트맵 (RdBu 컬러맵, -1 ~ +1)", "Portfolio Dashboard"],
            ["수익률 분포", "히스토그램 (50 bins, VaR 5% 라인)", "Ranking Engine"],
            ["벤치마크 대비 상대 강도", "듀얼 서브플롯 (종목 vs SPY)", "Stock Analyzer"],
            ["6대 팩터 스코어", "레이더(방사형) 차트", "Stock Analyzer"],
            ["종목 랭킹 점수", "수평 바 차트 (점수 내림차순)", "Theme Explorer, Ranking"],
            ["포트폴리오 건강도", "4색 신호등 카드 (초록/파랑/주황/빨강)", "Portfolio Dashboard"],
            ["시장 상황 판정", "게이지 차트 (Bull/Neutral/Bear)", "Market Overview"],
        ], [0.32, 0.36, 0.32]))
    s.append(sp(12))

    s.append(Paragraph("차트 색상 체계", ST_H3))
    s.append(T(
        ["용도", "색상코드", "적용 장면"],
        [
            ["Primary (메인)", "#2962FF", "주요 UI 요소, 강조 텍스트"],
            ["Positive (상승/긍정)", "#26A69A", "상승 추세, Buy 시그널, Uptrend"],
            ["Negative (하락/부정)", "#EF5350", "하락 추세, Sell 시그널, Critical"],
            ["Neutral (중립)", "#78909C", "변화 없음, Hold 시그널"],
            ["Secondary (보조/경고)", "#FF6D00", "경고 배너, Unstable 상태"],
        ], [0.25, 0.2, 0.55]))
    s.append(PageBreak())

    # ══════════ 4. Skills.md 설계 방향 ══════════
    s.append(Paragraph("4. Skills.md 설계 방향", ST_H1))
    s.append(hr())

    s.append(Paragraph("4.1 설계 철학", ST_H2))
    s.append(p(
        'Skills.md는 <b>"분석 규칙의 단일 진실 원천(Single Source of Truth)"</b>으로 설계했습니다. '
        "모든 분석 로직이 이 문서 하나에 정의되어 있어, 문서만 읽으면 시스템의 전체 분석 방식을 이해할 수 있습니다."))
    s.append(sp(6))
    s.append(b(
        '<b>규칙 명시성:</b> 모든 임계값, 가중치, 수식을 숫자로 명시합니다. '
        '"적절한", "높은" 같은 모호한 표현을 배제합니다. '
        '예를 들어 "RSI가 높으면 과매수"가 아니라 "RSI > 70이면 과매수"로 정의합니다.'))
    s.append(b(
        "<b>재현 가능성:</b> 같은 데이터에 같은 Skills.md를 적용하면 항상 같은 결과가 나옵니다. "
        "주관적 판단이 개입하지 않는 순수 규칙 기반 분석입니다."))
    s.append(b(
        "<b>확장 가능성:</b> 새로운 팩터를 추가할 때 기존 구조의 테이블에 행만 추가하면 됩니다. "
        "섹터별 가중치와 시장 보정 승수도 테이블로 관리하여 수정이 용이합니다."))
    s.append(b(
        "<b>범용성:</b> 특정 종목이나 시장에 종속되지 않는 범용 규칙으로 설계했습니다. "
        "미국과 한국 등 다중 시장에 대응할 수 있습니다."))
    s.append(sp(12))

    s.append(Paragraph("4.2 Skills.md 구성 체계 (8개 섹션)", ST_H2))
    s.append(p(
        "Skills.md는 대회에서 요구하는 5가지 필수 항목(데이터 분석 기준, 지표 계산 규칙, 시각화 선택 기준, "
        "리포트 구성 흐름, 인사이트 생성 규칙)을 모두 포함하며, "
        "범용성과 대시보드 자동생성을 위한 3개 섹션을 추가하여 총 8개 섹션으로 구성됩니다."))
    s.append(sp(4))
    s.append(T(
        ["섹션", "핵심 내용", "대회 평가 매핑"],
        [
            ["1. 데이터 분석 기준 정의",
             "6대 팩터 체계 정의, 11개 섹터별 동적 가중치 테이블, 3단계 시장 상황 보정 규칙(Bull/Neutral/Bear), Z-Score 정규화 4단계 절차",
             "범용성 + Skills.md 설계"],
            ["2. 투자 지표 계산 규칙",
             "재무 20개 지표(계산식+정규화 범위+해석 기준), 기술적 10개 지표(파라미터+시그널 판정), 감성 10개 지표(키워드 가중치+판정), 복합 스코어 산출식, 딥 보너스, 포트폴리오 4단계 진단, 백테스트 검증",
             "Skills.md 설계 (핵심)"],
            ["3. 시각화 선택 기준",
             "12종 데이터 유형별 차트 자동 매핑 규칙, 색상 팔레트 정의, 3단계 반응형 레이아웃 규칙(데스크톱/태블릿/모바일)",
             "대시보드 자동생성"],
            ["4. 리포트 구성 흐름",
             "테마 분석(8단계), 포트폴리오 진단(5단계), 종합 종목 분석, 딥 후보 탐색 등 4개 파이프라인 정의",
             "대시보드 자동생성"],
            ["5. 인사이트 생성 규칙",
             "9점 만점 종합 판정(팩터+백테스트+감성), 감성 모멘텀 5단계 판정, 감성 신뢰도 계산식, 트렌딩 감지 조건, 자연어 인사이트 6종 템플릿, 위험 경고 6가지 조건",
             "Skills.md 설계"],
            ["6. 데이터 품질 관리",
             "8개 자동 검증 체크, 5단계 품질 점수, 3종 자동 클리닝 규칙(결측 보간, 제로값 변환, 이상치 윈저화)",
             "범용성 (가점)"],
            ["7. 범용성 설계",
             "다중 시장 지원(US, KR), 3가지 데이터 입력 형식(티커/테마/CSV), 6단계 TTL 캐시 정책(15분~24시간)",
             "범용성 (가점)"],
            ["8. 대시보드 페이지 구성",
             "6개 페이지별 구성 요소와 배치 정의",
             "대시보드 자동생성"],
        ], [0.2, 0.5, 0.3]))
    s.append(PageBreak())

    # ══════════ 5. 확장 기능 ══════════
    s.append(Paragraph("5. 확장 기능 아이디어", ST_H1))
    s.append(hr())

    s.append(Paragraph("5.1 단기 확장 (대회 내 구현 가능)", ST_H2))
    s.append(T(
        ["기능", "설명", "가치"],
        [
            ["AI 인사이트 강화", "LLM을 활용한 자연어 분석 요약 고도화", "인사이트 품질 향상"],
            ["알림 시스템", "Critical 종목 발생 시 브라우저 알림", "즉시 대응 가능"],
            ["비교 모드", "2개 종목을 나란히 비교하는 Split View", "의사결정 지원"],
            ["다크 모드", "대시보드 다크/라이트 테마 전환", "사용성 개선"],
        ], [0.22, 0.45, 0.33]))
    s.append(sp(12))

    s.append(Paragraph("5.2 중장기 확장 (대회 후 발전 방향)", ST_H2))
    s.append(T(
        ["기능", "설명", "가치"],
        [
            ["한국 시장 완전 지원", "KRX 실시간 데이터 + 한국어 뉴스 감성 분석", "범용성 확대"],
            ["커뮤니티 랭킹", "사용자 포트폴리오 성과 공유 및 랭킹", "바이럴 효과"],
            ["자동 스케줄러", "일별/주별 자동 분석 및 리포트 이메일 발송", "분석 자동화"],
            ["Obsidian 지식 그래프", "분석 결과를 Obsidian 볼트에 자동 저장하여 종목간 관계 그래프 구축", "지식 축적"],
            ["MCP 서버 통합", "Claude AI와 대화형 자연어 분석 (예: NVDA 최근 실적 분석해줘)", "AI 통합"],
            ["멀티 에이전트 자율 분석", "시장 모니터링 에이전트가 이상 감지 후 자동으로 분석, 알림, 리포트까지 전자동 수행", "자율 분석"],
        ], [0.22, 0.48, 0.30]))
    s.append(sp(16))

    s.append(Paragraph("5.3 진화 로드맵", ST_H2))
    s.append(p(
        "<b>Phase 1 (현재):</b> Skills.md 기반 대시보드. 40개 팩터 분석과 6개 페이지 대시보드를 구축합니다."))
    s.append(p(
        "<b>Phase 2:</b> MCP 서버 통합. Claude AI와 자연어로 대화하며 분석을 수행할 수 있습니다."))
    s.append(p(
        "<b>Phase 3:</b> 멀티 에이전트 자율 분석. 시장 모니터링부터 이상 감지, 알림, 분석, 리포트까지 전자동으로 동작합니다."))
    s.append(p(
        "<b>Phase 4:</b> 글로벌 확장. 미국, 한국, 일본, 유럽 시장을 통합 분석하고 다국어 인사이트를 생성합니다."))
    s.append(PageBreak())

    # ══════════ 6. 기술 스택 ══════════
    s.append(Paragraph("6. 기술 스택", ST_H1))
    s.append(hr())
    s.append(T(
        ["영역", "기술", "선택 이유"],
        [
            ["프론트엔드", "Next.js 15 (App Router)", "SSR/SSG 지원으로 빠른 초기 로딩과 SEO 최적화"],
            ["UI 프레임워크", "shadcn/ui + Tailwind CSS", "일관된 디자인 시스템과 빠른 컴포넌트 개발"],
            ["차트 라이브러리", "Recharts + Plotly.js", "반응형 기본 차트와 고급 금융 차트(캔들스틱)"],
            ["상태 관리", "Zustand", "경량 상태 관리, 보일러플레이트 최소화"],
            ["분석 엔진", "Python (FastMCP)", "40개 팩터 계산, 백테스트 시뮬레이션 수행"],
            ["데이터 소스", "yfinance, Finnhub, Perplexity, SEC EDGAR", "가격, 재무, 뉴스, 공시 데이터 다중 소스"],
            ["캐시 시스템", "DiskCache + SQLite", "6단계 TTL 정책으로 API 호출 50% 절감"],
            ["배포", "Vercel (프론트) + Python Server (백엔드)", "프론트/백엔드 분리 배포, 안정성 확보"],
        ], [0.18, 0.35, 0.47]))
    s.append(sp(30))

    # ══════════ 7. 요약 ══════════
    s.append(Paragraph("7. 요약", ST_H1))
    s.append(hr())
    s.append(p(
        "Stock Manager는 <b>Skills.md에 정의된 40개 팩터 분석 규칙</b>을 기반으로, "
        "투자 데이터를 <b>자동 수집, 자동 분석, 자동 시각화, 자동 인사이트 생성</b>하는 "
        "<b>범용 금융 투자 대시보드</b>입니다."))
    s.append(sp(12))
    s.append(T(
        ["핵심 경쟁력", "상세 내용"],
        [
            ["Skills.md = 분석의 단일 진실 원천",
             "40개 팩터 계산 규칙, 12종 차트 매핑 규칙, 6단계 투자 시그널 판정 규칙이 모두 하나의 문서에 명시적으로 정의되어 있습니다."],
            ["범용성 = 어떤 데이터든 분석 가능",
             "티커 직접 입력, 테마 키워드, CSV 업로드 3가지 입력을 지원합니다. 미국과 한국 시장, 11개 섹터에 대응합니다."],
            ["실행 가능한 인사이트 = 판단이 아닌 행동 지침",
             "Strong Buy부터 Strong Sell까지 6단계 시그널에 자연어 설명과 위험 경고를 함께 제공하여 즉시 행동할 수 있는 인사이트를 생성합니다."],
        ], [0.35, 0.65]))

    # ══════════ BUILD ══════════
    doc.build(s, onFirstPage=hf, onLaterPages=hf)
    print(f"PDF generated: {out}")


if __name__ == "__main__":
    build()
