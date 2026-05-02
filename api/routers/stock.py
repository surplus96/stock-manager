"""Stock domain router (FR-B07).

Routes: /api/stock/* (except analysis-report, which lives in analysis.py)
"""
from __future__ import annotations

import logging

from fastapi import APIRouter

from api.schemas.common import Envelope
from api.schemas.stock import StockRankingData, InvestmentSignalData

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/stock", tags=["stock"])


def _enrich_ranking(result: dict) -> dict:
    """Add signal and factor category scores to a ranking result dict."""
    from mcp_server.tools.factor_aggregator import FactorAggregator

    score = result.get("composite_score", 0)
    result["signal"] = FactorAggregator.get_recommendation(score)

    nf = result.get("normalized_factors", {})
    financial_keys = ["ROE", "ROA", "ROIC", "Operating_Margin", "Net_Margin",
                      "Debt_to_Equity", "Current_Ratio", "Revenue_Growth", "EPS_Growth",
                      "FCF_to_Sales", "Dividend_Yield", "Payout_Ratio"]
    technical_keys = ["RSI", "MACD_Signal", "Stochastic", "ADX", "CCI",
                      "Williams_R", "MFI", "OBV_Trend", "ATR_Ratio", "BB_Position"]
    sentiment_keys = ["News_Sentiment", "Analyst_Rating", "Short_Interest",
                      "Put_Call_Ratio", "Insider_Activity"]
    growth_keys = ["Revenue_Growth", "EPS_Growth"]
    quality_keys = ["ROE", "ROIC", "Operating_Margin", "Net_Margin"]
    value_keys = ["Debt_to_Equity", "Current_Ratio", "FCF_to_Sales"]

    def avg_score(keys):
        vals = [nf[k] for k in keys if k in nf]
        return round(sum(vals) / len(vals), 1) if vals else 50.0

    result["factors"] = {
        "financial_score": avg_score(financial_keys),
        "technical_score": avg_score(technical_keys),
        "sentiment_score": round((avg_score(sentiment_keys) - 50) / 50, 2),
        "growth_score": avg_score(growth_keys),
        "quality_score": avg_score(quality_keys),
        "valuation_score": avg_score(value_keys),
    }
    return result


def _run_factor_ranking(tickers: list) -> list:
    """Run FactorAggregator.rank_stocks and enrich results.

    When every input ticker points at the same market (all US or all KR),
    ``market=`` is forwarded to the aggregator so KR tickers go through
    the DART/PyKrx branch instead of yfinance (which 404's on ``005930``
    and similar codes). Mixed baskets default to ``"US"`` so US tickers
    still flow through yfinance; KR tickers in the mixed case fall back
    to the simple analytics path via ``FactorAggregator`` internals.
    """
    from mcp_server.tools.factor_aggregator import FactorAggregator
    from mcp_server.tools.yf_utils import detect_market

    markets = {detect_market(t) for t in tickers}
    # Unambiguous single-market basket → pin the aggregator's market.
    if markets == {"KR"}:
        mkt = "KR"
    elif markets == {"US"}:
        mkt = "US"
    else:
        mkt = "US"

    try:
        results = FactorAggregator.rank_stocks(
            tickers, market=mkt, include_sentiment=False,
        )
    except TypeError:
        # Older signature without market=
        results = FactorAggregator.rank_stocks(tickers, include_sentiment=False)
    except Exception as e:
        logger.error("FactorAggregator failed: %s", e)
        results = []

    if not results or all(r.get("composite_score", 0) == 0 for r in results):
        logger.info("FactorAggregator returned empty, falling back to simple analytics")
        from mcp_server.tools.analytics import rank_tickers_with_fundamentals
        simple = rank_tickers_with_fundamentals(tickers)
        results = [
            {
                "ticker": s.get("ticker", ""),
                "composite_score": round(s.get("score", 0) * 100, 1),
                "factor_count": 6,
                "factors": {},
                "normalized_factors": {},
                "sector": s.get("sector", ""),
            }
            for s in simple
        ]

    from concurrent.futures import ThreadPoolExecutor
    from mcp_server.tools.market_data import get_fundamentals_snapshot

    for r in results:
        _enrich_ranking(r)

    missing = [r for r in results if not r.get("sector")]
    if missing:
        def _fetch_sector(tk: str) -> tuple[str, str]:
            try:
                snap = get_fundamentals_snapshot(tk) or {}
                return tk, snap.get("sector", "") or ""
            except Exception:
                return tk, ""

        with ThreadPoolExecutor(max_workers=min(8, len(missing))) as pool:
            sector_map = dict(pool.map(_fetch_sector, [r["ticker"] for r in missing]))
        for r in missing:
            r["sector"] = sector_map.get(r["ticker"], "")

    # Annotate KR rows with the canonical Korean company name + market
    # tag so every consumer (chat artifacts, ranking table, theme panel,
    # portfolio table) can render "삼성전자 (005930)" without re-resolving.
    from mcp_server.tools.kr_ticker_resolver import code_to_name
    for r in results:
        t = r.get("ticker") or ""
        m = r.get("market") or detect_market(str(t))
        r.setdefault("market", m)
        r.setdefault("currency", "KRW" if m == "KR" else "USD")
        if m == "KR":
            nm = code_to_name(str(t))
            if nm and not r.get("name_kr"):
                r["name_kr"] = nm

    return results


@router.get("/comprehensive", response_model=Envelope[StockRankingData])
def api_stock_comprehensive(ticker: str):
    from mcp_server.tools.market_data import get_fundamentals_snapshot
    from mcp_server.tools.yf_utils import detect_market
    from mcp_server.tools.kr_ticker_resolver import resolve_korean_ticker

    # Resolve Korean names → 6-digit code first, then detect market.
    ticker = resolve_korean_ticker(ticker)
    market = detect_market(ticker)
    currency = "KRW" if market == "KR" else "USD"
    name_kr: str | None = None
    primary_name = ""

    fundamentals = get_fundamentals_snapshot(ticker)

    # FR-K06: enrich KR response with Korean display name so the UI
    # can show "삼성전자 (005930)" instead of the raw code.
    if market == "KR":
        try:
            from mcp_server.tools.kr_market_data import get_kr_adapter
            nm = get_kr_adapter().get_ticker_name(ticker)
            if nm:
                name_kr = nm
                primary_name = nm
        except Exception:  # noqa: BLE001
            pass
    if not primary_name:
        primary_name = str(fundamentals.get("shortName") or fundamentals.get("longName") or "")

    rankings = _run_factor_ranking([ticker])
    result = rankings[0] if rankings else {"ticker": ticker, "composite_score": 0}
    result["fundamentals"] = fundamentals
    score = result.get("composite_score", 0)
    signal = result.get("signal", "Hold")
    sector = result.get("sector", fundamentals.get("sector", ""))
    factors = result.get("factors", {})
    result["interpretation"] = (
        f"{ticker} ({sector}) has a composite score of {score:.1f}/100, "
        f"rated as '{signal}'. "
        f"Financial: {factors.get('financial_score', 'N/A')}, "
        f"Technical: {factors.get('technical_score', 'N/A')}, "
        f"Growth: {factors.get('growth_score', 'N/A')}, "
        f"Quality: {factors.get('quality_score', 'N/A')}."
    )
    result["market"] = market
    result["currency"] = currency
    result["name"] = primary_name
    result["name_kr"] = name_kr
    data = StockRankingData(**{k: v for k, v in result.items() if k in StockRankingData.model_fields})
    return Envelope[StockRankingData](data=data)


@router.get("/signal", response_model=Envelope[dict])
def api_stock_signal(ticker: str):
    from mcp_server.tools.kr_ticker_resolver import resolve_korean_ticker
    ticker = resolve_korean_ticker(ticker)
    rankings = _run_factor_ranking([ticker])
    if rankings:
        r = rankings[0]
        factors = r.get("factors", {})
        score = r.get("composite_score", 0)
        signal = r.get("signal", "Hold")
        data = {
            "ticker": ticker,
            "signal": signal,
            "composite_score": score,
            "reasoning": (
                f"Score {score:.1f}/100. "
                f"Financial={factors.get('financial_score', 'N/A')}, "
                f"Technical={factors.get('technical_score', 'N/A')}, "
                f"Growth={factors.get('growth_score', 'N/A')}."
            ),
        }
    else:
        data = {"ticker": ticker, "signal": "Hold", "composite_score": 0, "reasoning": ""}
    return Envelope[dict](data=data)


@router.get("/investment-signal", response_model=Envelope[InvestmentSignalData])
def api_investment_signal(ticker: str):
    """Investment signal with decision rationale and risk list."""
    from mcp_server.tools.data_integrator import get_investment_signal
    from mcp_server.tools.kr_ticker_resolver import resolve_korean_ticker
    ticker = resolve_korean_ticker(ticker)

    try:
        result = get_investment_signal(ticker)
        data = InvestmentSignalData(**{k: v for k, v in result.items() if k in InvestmentSignalData.model_fields})
    except Exception as e:
        logger.error("Investment signal failed for %s: %s", ticker, e)
        data = InvestmentSignalData(decision="Hold", confidence="Low", risks=[str(e)])
    return Envelope[InvestmentSignalData](data=data)


@router.get("/factor-interpretation", response_model=Envelope[dict])
def api_factor_interpretation(ticker: str):
    """40-factor per-category text interpretation — market-aware (FR-K01)."""
    from mcp_server.tools.kr_ticker_resolver import resolve_korean_ticker
    from mcp_server.tools.yf_utils import detect_market

    ticker = resolve_korean_ticker(ticker)
    market = detect_market(ticker)
    result: dict = {"ticker": ticker, "market": market, "financial": {}, "technical": {}, "sentiment": {}}

    try:
        from mcp_server.tools.financial_factors import FinancialFactors
        fin_factors = FinancialFactors.calculate_all(ticker, market)
        fin_interp = FinancialFactors.get_factor_interpretation(fin_factors)

        # KR — augment with KIS valuation snapshot (PER/PBR/EPS/BPS/시가총액).
        # The 20-factor calc only covers profitability/health/growth via
        # yfinance/DART; KRX special listings (REIT/ETN/0001A0 etc) come
        # back empty there even though KIS has solid valuation data, so
        # this fills the Financial Analysis card with at least the basic
        # market multiples instead of leaving it blank.
        if market == "KR":
            try:
                from mcp_server.tools import kis_market_data as _kis
                q = _kis.get_quote(ticker) or {}

                def _per_label(v: float) -> str:
                    if v <= 0: return f"적자 또는 PER 음수 ({v:.1f})"
                    if v < 10: return f"저평가 구간 (PER {v:.1f})"
                    if v < 20: return f"적정 평가 (PER {v:.1f})"
                    if v < 40: return f"성장주 평가 (PER {v:.1f})"
                    return f"고평가 (PER {v:.1f})"

                def _pbr_label(v: float) -> str:
                    if v <= 0: return f"PBR 산출 불가 ({v:.2f})"
                    if v < 1: return f"청산가치 이하 (PBR {v:.2f})"
                    if v < 2: return f"적정 (PBR {v:.2f})"
                    if v < 4: return f"성장 프리미엄 (PBR {v:.2f})"
                    return f"높은 평가 (PBR {v:.2f})"

                if q.get("per") is not None:
                    fin_factors["PER"] = q["per"]
                    fin_interp["PER"] = _per_label(float(q["per"]))
                if q.get("pbr") is not None:
                    fin_factors["PBR"] = q["pbr"]
                    fin_interp["PBR"] = _pbr_label(float(q["pbr"]))
                if q.get("eps") is not None:
                    fin_factors["EPS_KRW"] = q["eps"]
                    fin_interp["EPS"] = f"주당순이익 {float(q['eps']):,.0f}원"
                if q.get("bps") is not None:
                    fin_factors["BPS_KRW"] = q["bps"]
                    fin_interp["BPS"] = f"주당순자산 {float(q['bps']):,.0f}원"
                if q.get("market_cap") is not None:
                    fin_factors["Market_Cap_KRW"] = q["market_cap"]
                    eok = float(q["market_cap"]) / 100_000_000
                    fin_interp["시가총액"] = f"{eok:,.0f}억원"
            except Exception as e:  # noqa: BLE001
                logger.debug("KIS valuation seed failed for %s: %s", ticker, e)

        result["financial"] = {"factors": fin_factors, "interpretation": fin_interp}
    except Exception as e:
        logger.warning("Financial factors failed: %s", e)
        result["financial"] = {"error": str(e)}

    try:
        from mcp_server.tools.technical_indicators import TechnicalFactors
        # KR → PyKrx OHLCV (via market_data.get_prices); US → yfinance history.
        if market == "KR":
            from mcp_server.tools.market_data import get_prices
            df = get_prices(ticker)
        else:
            import yfinance as yf
            df = yf.Ticker(ticker).history(period="6mo")
        if df is not None and not df.empty:
            tech_factors = TechnicalFactors.calculate_all(df)
            tech_interp = TechnicalFactors.get_factor_interpretation(tech_factors)
            result["technical"] = {"factors": tech_factors, "interpretation": tech_interp}
    except Exception as e:
        logger.warning("Technical factors failed: %s", e)
        result["technical"] = {"error": str(e)}

    try:
        from mcp_server.tools.sentiment_analysis import SentimentFactors
        sent_factors = SentimentFactors.calculate_all(ticker, market, days=7)
        sent_interp = SentimentFactors.get_factor_interpretation(sent_factors)
        result["sentiment"] = {"factors": sent_factors, "interpretation": sent_interp}
    except Exception as e:
        logger.warning("Sentiment factors failed: %s", e)
        result["sentiment"] = {"error": str(e)}

    return Envelope[dict](data=result)
