"""Analysis-report router (FR-B07, FR-B04).

Routes:
  /api/stock/analysis-report
  /api/portfolio/analysis-report
  /api/theme/analysis-report

FR-B04: @limiter.limit applied — 10/minute per IP (settings.rate_limit_analysis_per_min).
"""
from __future__ import annotations

import logging
import re

from fastapi import APIRouter, Request

from api.schemas.common import Envelope
from api.schemas.analysis import StockAnalysisReport, NewsItem
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# FR-B04: per-route rate-limit decorator (graceful degradation if slowapi absent)
try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    _limiter: Limiter | None = Limiter(key_func=get_remote_address)
    _RATE_LIMIT = f"{settings.rate_limit_analysis_per_min}/minute"
    _rate_limit = _limiter.limit(_RATE_LIMIT)
except ImportError:
    _limiter = None
    _rate_limit = lambda f: f  # noqa: E731 — identity decorator

router = APIRouter(tags=["analysis"])


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _strip_html(text: str) -> str:
    import re as _re
    if not text:
        return ""
    text = _re.sub(r"<[^>]+>", "", text)
    text = _re.sub(r"&nbsp;", " ", text)
    text = _re.sub(r"&amp;", "&", text)
    text = _re.sub(r"&lt;", "<", text)
    text = _re.sub(r"&gt;", ">", text)
    text = _re.sub(r"&quot;", '"', text)
    text = _re.sub(r"&#\d+;", "", text)
    text = _re.sub(r"\s+", " ", text).strip()
    return text


def _extract_news_items(news_result) -> list:
    items = []
    if isinstance(news_result, list):
        for entry in news_result:
            if isinstance(entry, dict) and "hits" in entry:
                items.extend(entry["hits"])
            elif isinstance(entry, dict) and "title" in entry:
                items.append(entry)
    elif isinstance(news_result, dict):
        items = news_result.get("hits", news_result.get("items", news_result.get("results", [])))
    for item in items:
        if isinstance(item, dict):
            for field in ("title", "snippet", "source"):
                if item.get(field) and isinstance(item[field], str):
                    item[field] = _strip_html(item[field])
    return items


def _llm_summarize(prompt_data: str, context: str) -> str:
    """Generate an LLM-backed analysis summary.

    Routes through ``call_llm_resilient`` (FR-P05) so preview-model 503s
    automatically cycle through the ``GEMINI_FALLBACK_MODELS`` chain and
    retry a few times before giving up — matches the robustness the
    chatbot path got, since preview models (e.g.
    ``gemini-3.1-flash-lite-preview``) are frequently throttled.

    The primary model is deliberately ``settings.default_chat_model``
    (stable) rather than the analysis-specific ``GEMINI_MODEL`` so that
    analysis reports enjoy the same stability guarantee as the chatbot.
    Override with ``CHAT_MODEL`` env var if you want to pin a different
    model for analysis routes without touching ``GEMINI_MODEL``.
    """
    try:
        from mcp_server.tools.llm import call_llm_resilient
        system = (
            "당신은 시니어 금융 애널리스트입니다. 투자 리서치 리포트를 한국어로 작성하세요.\n\n"
            "## 작성 규칙\n"
            "1. 전문 용어는 한국어+영문 병기: 예) '자기자본이익률(ROE) 17.4%', '데드 크로스(Death Cross)'\n"
            "2. 반드시 구체적 수치를 인용하며, 해석과 함께 제시할 것\n"
            "3. '최근 뉴스' 데이터가 있으면 관련 기사 내용을 분석 근거로 자연스럽게 인용할 것\n"
            "4. 300~500 단어, 간결하고 명확하게\n\n"
            "## 필수 섹션 구조\n"
            "## 종합 요약\n"
            "투자의견/점수/핵심 한 줄 판단을 먼저 제시\n\n"
            "## 핵심 근거\n"
            "펀더멘털 강점, 밸류에이션, 센티먼트 등 매수/보유 근거를 수치와 함께 정리.\n\n"
            "## 리스크 및 우려사항\n"
            "기술적 약세, 변동성, 구조적 리스크 등을 구체적 지표와 함께 설명\n\n"
            "## 결론\n"
            "최종 투자 전략(진입 시점, 조건부 매수/매도 기준)을 명확히 제시"
        )
        return call_llm_resilient(
            system,
            prompt_data,
            model=settings.default_chat_model,
            temperature=0.3,
        )
    except Exception as e:
        logger.warning("LLM summary failed: %s", e)
        return ""


def _run_factor_ranking(tickers: list) -> list:
    from api.routers.stock import _run_factor_ranking as _rfr
    return _rfr(tickers)


# ---------------------------------------------------------------------------
# Routes (FR-B04: 10/minute rate limit on analysis endpoints)
# ---------------------------------------------------------------------------

@router.get("/api/stock/analysis-report", response_model=Envelope[StockAnalysisReport])
@_rate_limit
def api_stock_analysis_report(request: Request, ticker: str):
    """Comprehensive analysis report: LLM summary + news + fundamentals + technicals."""
    report: dict = {"ticker": ticker, "sections": {}}

    rankings = _run_factor_ranking([ticker])
    rank_data = rankings[0] if rankings else {}
    score = rank_data.get("composite_score", 0)
    signal = rank_data.get("signal", "Hold")
    factors = rank_data.get("factors", {})
    sector = rank_data.get("sector", "")

    from api.services.stock_report import collect_stock_analysis_inputs
    collected = collect_stock_analysis_inputs(ticker)
    invest_signal = collected.get("invest_signal", {}) or {}
    fin_interp = collected.get("fin_interp", {}) or {}
    tech_interp = collected.get("tech_interp", {}) or {}
    raw_news = collected.get("news_items", []) or []
    sentiment_data = collected.get("sentiment", {}) or {}
    fundamentals = collected.get("fundamentals", {}) or {}

    try:
        news_items = _extract_news_items({"items": raw_news} if isinstance(raw_news, list) else raw_news)
    except Exception:
        news_items = raw_news if isinstance(raw_news, list) else []

    report["sections"]["score"] = {
        "composite_score": score,
        "signal": signal,
        "factors": factors,
        "factor_count": rank_data.get("factor_count", 0),
    }
    report["sections"]["investment_signal"] = invest_signal
    report["sections"]["financial"] = {
        "interpretation": fin_interp,
        "fundamentals": {
            k: v for k, v in fundamentals.items()
            if k in ("pe", "pb", "eps", "returnOnEquity", "profitMargins",
                     "revenueGrowth", "market_cap", "sector", "industry")
        },
    }
    report["sections"]["technical"] = {"interpretation": tech_interp}
    report["sections"]["news"] = [
        {"title": n.get("title", ""), "source": n.get("source", ""), "date": n.get("published", n.get("date", ""))}
        for n in news_items[:5]
    ]
    report["sections"]["sentiment"] = {
        "overall": sentiment_data.get("overall", sentiment_data.get("sentiment_label", "")),
        "score": sentiment_data.get("sentiment_score", sentiment_data.get("score", 0)),
        "investment_signal": sentiment_data.get("investment_signal", ""),
    }

    news_for_prompt = "\n".join([
        f"- [{n.get('source','?')}] \"{n.get('title','')}\" — {n.get('snippet','내용 없음')[:150]}"
        for n in news_items[:5]
    ]) or "최근 관련 뉴스 없음"

    prompt = f"""[투자 리서치 리포트] {ticker} ({sector})

■ 종합점수: {score:.1f}/100 | 시그널: {signal}
■ 팩터: 재무 {factors.get('financial_score','N/A')}, 기술적 {factors.get('technical_score','N/A')}, 성장 {factors.get('growth_score','N/A')}, 퀄리티 {factors.get('quality_score','N/A')}, 밸류 {factors.get('valuation_score','N/A')}

■ 투자판단: {invest_signal.get('decision','N/A')} (신뢰도: {invest_signal.get('confidence','N/A')})
  - 매수근거: {'; '.join(invest_signal.get('reasons', [])) or 'N/A'}
  - 리스크: {'; '.join(invest_signal.get('risks', [])) or 'N/A'}

■ 재무 지표:
  P/E {fundamentals.get('pe','N/A')} | ROE {fundamentals.get('returnOnEquity','N/A')} | 매출성장 {fundamentals.get('revenueGrowth','N/A')} | 이익률 {fundamentals.get('profitMargins','N/A')}
{chr(10).join(f'  - {k}: {v}' for k, v in list(fin_interp.items())[:8])}

■ 기술적 분석:
{chr(10).join(f'  - {k}: {v}' for k, v in list(tech_interp.items())[:6])}

■ 뉴스 센티먼트: {sentiment_data.get('overall', sentiment_data.get('sentiment_label', 'N/A'))} (점수: {sentiment_data.get('sentiment_score', 'N/A')})

■ 최근 주요 뉴스:
{news_for_prompt}

위 데이터를 종합하여 투자 리포트를 작성하세요.
"""
    summary = _llm_summarize(prompt, f"{ticker} 종목 분석")

    # rich-visual-reports — build deterministic structured blocks from the
    # collected data, then let the LLM contribute a summary + factor bullets
    # that reference the news citations. Any failure falls back to the
    # legacy prose summary which the frontend still renders via <Markdown/>.
    from api.services.report_builder import (
        build_news_citation,
        build_price_blocks,
        build_radar_mini,
        build_stock_metric_grid,
        parse_llm_blocks,
    )
    from api.schemas.report_blocks import FactorBulletBlock, FactorBulletItem, SummaryBlock
    from mcp_server.tools.market_data import get_prices
    from mcp_server.tools.yf_utils import detect_market

    market = detect_market(ticker)
    blocks: list[dict] = []
    try:
        blocks.append(build_stock_metric_grid(ticker, rank_data, fundamentals, market).model_dump())
        for b in build_price_blocks(ticker, get_prices(ticker), market):
            blocks.append(b.model_dump())
        news_block = build_news_citation(news_items)
        if news_block:
            blocks.append(news_block.model_dump())
        radar = build_radar_mini(factors)
        if radar:
            blocks.append(radar.model_dump())
    except Exception as e:  # noqa: BLE001
        logger.warning("structured block build failed for %s: %s", ticker, e)

    # Ask LLM for interpretive blocks (summary + factor bullets) — structured.
    try:
        from mcp_server.tools.llm import call_llm_json
        json_system = (
            "당신은 시니어 금융 애널리스트입니다. 아래 데이터를 읽고 **JSON 배열만** "
            "출력하세요 (prose 금지).\n"
            "스키마 (FR-PSP-F: suggested 블록 추가):\n"
            "[{\"kind\":\"summary\",\"title\":\"투자 의견\",\"markdown\":\"...[1] 참조...\","
            "\"citations\":[1,2]},\n"
            " {\"kind\":\"factor_bullet\",\"factors\":[{\"name\":\"Financial\",\"score\":72,"
            "\"note\":\"ROE 우수\"},{\"name\":\"Technical\",\"score\":45,\"note\":\"모멘텀 약화\"}, ...6개]},\n"
            " {\"kind\":\"suggested\",\"items\":[\"이 종목의 경쟁사와 비교해 줘\",\"분기 실적 추이는?\",\"리스크 시나리오 더 자세히\"]}]\n"
            "규칙: KR 종목이면 ₩, US 는 $. 점수/팩터 값은 통화기호 없이. 인용은 citations 배열에 id(1-5)로.\n"
            "suggested.items 는 3~5개, 각 50자 이내, 사용자가 자연스럽게 이어서 물을 만한 후속 질문."
        )
        raw = call_llm_json(json_system, prompt, model=settings.default_chat_model, temperature=0.1)
        llm_blocks = parse_llm_blocks(raw)
        for lb in llm_blocks:
            blocks.append(lb.model_dump())
    except Exception as e:  # noqa: BLE001
        logger.warning("LLM JSON blocks failed for %s: %s", ticker, e)
        if summary:
            blocks.append(SummaryBlock(markdown=summary).model_dump())

    news_out = [
        NewsItem(
            title=n.get("title", ""),
            source=n.get("source", ""),
            date=n.get("published", n.get("date", "")),
            url=n.get("url", ""),
            snippet=n.get("snippet", ""),
        )
        for n in news_items[:5]
    ]

    evidence: dict[str, str] = {}
    evidence["종합점수"] = f"{score:.1f}/100"
    evidence["시그널"] = signal
    evidence["섹터"] = sector or "N/A"
    if factors.get("financial_score") is not None:
        evidence["재무점수"] = f"{factors['financial_score']:.0f}"
    if factors.get("technical_score") is not None:
        evidence["기술점수"] = f"{factors['technical_score']:.0f}"
    if fundamentals.get("pe"):
        evidence["P/E 비율"] = f"{fundamentals['pe']:.1f}"
    if fundamentals.get("returnOnEquity"):
        evidence["자기자본이익률(ROE)"] = f"{fundamentals['returnOnEquity']*100:.1f}%"
    sent_label = sentiment_data.get("overall", sentiment_data.get("sentiment_label", ""))
    if sent_label:
        evidence["뉴스 센티먼트"] = sent_label

    data = StockAnalysisReport(
        ticker=ticker,
        summary=summary,
        blocks=blocks,
        sections=report["sections"],
        news=news_out,
        evidence=evidence,
    )
    return Envelope[StockAnalysisReport](data=data)


@router.get("/api/portfolio/analysis-report", response_model=Envelope[dict])
@_rate_limit
def api_portfolio_analysis_report(request: Request, holdings: str, cash: float = 0):
    """Portfolio comprehensive diagnostic report."""
    from api.routers.portfolio import api_portfolio_comprehensive

    portfolio_env = api_portfolio_comprehensive(holdings, cash)
    portfolio = portfolio_env.data.model_dump() if hasattr(portfolio_env, "data") else {}

    holdings_list = portfolio.get("holdings", [])
    tickers = [h["ticker"] for h in holdings_list]

    news_items: list = []
    try:
        from mcp_server.tools.news_search import search_news
        queries = [f"{t} stock" for t in tickers[:3]]
        news_result = search_news(queries, lookback_days=7, max_results=5)
        news_items = _extract_news_items(news_result)
    except Exception:
        pass

    holdings_text = "\n".join([
        f"- {h['ticker']}: {h['shares']}주, 매입가 ${h['entry_price']}, "
        f"현재가 ${h['current_price']}, 수익률 {h['pnl_pct']:.1f}%, "
        f"점수 {h.get('composite_score', 0):.0f}, 시그널 {h.get('signal', 'N/A')}"
        for h in holdings_list
    ])
    alerts_text = "\n".join([f"- [{a['type']}] {a['message']}" for a in portfolio.get("alerts", [])])
    news_for_prompt = "\n".join([
        f"- [{n.get('source','?')}] \"{n.get('title','')}\" — {n.get('snippet','')[:150]}"
        for n in news_items[:5]
    ]) or "최근 관련 뉴스 없음"

    prompt = f"""[포트폴리오 종합 진단 리포트]

■ 포트폴리오 현황:
  총 자산: ${portfolio['total_value']:,.0f} | 총 손익: ${portfolio['total_pnl']:,.0f}
  건강도: {portfolio['health_score']}/100 | 단계: {portfolio['phase']} | 현금: ${portfolio['cash']:,.0f}

■ 보유 종목:
{holdings_text}

■ 경고: {alerts_text or '없음'}

■ 최근 주요 뉴스:
{news_for_prompt}

위 데이터를 종합하여 포트폴리오 진단 리포트를 작성하세요.
개별 종목 분석, 분산투자 적정성, 리스크 경고, 실행 가능한 리밸런싱 추천을 포함하세요.
"""

    evidence = {
        "총 자산": f"${portfolio['total_value']:,.0f}",
        "총 손익": f"${portfolio['total_pnl']:,.0f}",
        "건강도 점수": f"{portfolio['health_score']:.0f}/100",
        "단계": portfolio.get("phase", "N/A"),
        "보유 종목수": str(len(holdings_list)),
        "현금": f"${portfolio['cash']:,.0f}",
    }
    news_out = [
        {"title": n.get("title", ""), "source": n.get("source", ""),
         "date": n.get("published", n.get("date", "")),
         "url": n.get("url", ""), "snippet": n.get("snippet", "")}
        for n in news_items[:5]
    ]
    result = {
        "portfolio": portfolio,
        "news": news_out,
        "evidence": evidence,
        "summary": _llm_summarize(prompt, "포트폴리오 분석"),
    }
    return Envelope[dict](data=result)


@router.get("/api/theme/analysis-report", response_model=Envelope[dict])
@_rate_limit
def api_theme_analysis_report(request: Request, theme: str, top_n: int = 5):
    """Theme comprehensive analysis report."""
    from api.routers.theme import api_theme_analyze

    theme_env = api_theme_analyze(theme, top_n)
    theme_data = theme_env.data.model_dump() if hasattr(theme_env, "data") else {}
    rankings = theme_data.get("rankings", [])

    news_items: list = []
    try:
        from mcp_server.tools.news_search import search_news
        news_result = search_news(
            [f"{theme} investment", f"{theme} market trend"], lookback_days=7, max_results=5
        )
        news_items = _extract_news_items(news_result)
    except Exception:
        pass

    stocks_text = "\n".join([
        f"- #{i+1} {r['ticker']}: 점수 {r.get('composite_score',0):.1f}, 시그널 {r.get('signal','N/A')}, "
        f"재무 {r.get('factors',{}).get('financial_score','N/A')}, "
        f"기술적 {r.get('factors',{}).get('technical_score','N/A')}, "
        f"섹터 {r.get('sector','N/A')}"
        for i, r in enumerate(rankings)
    ])
    news_for_prompt = "\n".join([
        f"- [{n.get('source','?')}] \"{n.get('title','')}\" — {n.get('snippet','')[:150]}"
        for n in news_items[:5]
    ]) or "최근 관련 뉴스 없음"

    avg_score = sum(r.get("composite_score", 0) for r in rankings) / max(len(rankings), 1)
    buys = [r["ticker"] for r in rankings if r.get("signal") in ("Strong Buy", "Buy")]

    prompt = f"""[테마 투자 분석 리포트] '{theme}'

■ 테마 요약: 분석 {len(rankings)}개 종목 | 평균 점수 {avg_score:.1f}/100
■ 매수 시그널: {', '.join(buys) if buys else '없음'}

■ 종목 랭킹:
{stocks_text}

■ 최근 주요 뉴스:
{news_for_prompt}

위 데이터를 종합하여 테마 분석 리포트를 작성하세요.
"""

    evidence = {
        "테마": theme,
        "분석 종목수": str(len(rankings)),
        "평균 점수": f"{avg_score:.1f}/100",
        "매수 시그널": ", ".join(buys) if buys else "없음",
    }
    if rankings:
        evidence["최우선 추천"] = f"{rankings[0]['ticker']} ({rankings[0].get('composite_score',0):.1f})"

    news_out = [
        {"title": n.get("title", ""), "source": n.get("source", ""),
         "date": n.get("published", n.get("date", "")),
         "url": n.get("url", ""), "snippet": n.get("snippet", "")}
        for n in news_items[:5]
    ]
    result = {
        "theme": theme,
        "rankings": rankings,
        "news": news_out,
        "recommendation": theme_data.get("recommendation", ""),
        "evidence": evidence,
        "summary": _llm_summarize(prompt, f"{theme} 테마 분석"),
    }
    return Envelope[dict](data=result)
