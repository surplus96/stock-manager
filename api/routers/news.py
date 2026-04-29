"""News domain router (FR-B07).

Routes: /api/news/*
"""
from __future__ import annotations

import logging

from fastapi import APIRouter

from api.schemas.common import Envelope

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/search", response_model=Envelope[dict])
def api_news_search(queries: str, lookback_days: int = 7, max_results: int = 10):
    from mcp_server.tools.news_search import search_news

    q_list = [q.strip() for q in queries.split(",") if q.strip()]
    result = search_news(q_list, lookback_days=lookback_days, max_results=max_results)
    data = result if isinstance(result, dict) else {"results": result}
    return Envelope[dict](data=data)


@router.get("/sentiment", response_model=Envelope[dict])
def api_news_sentiment(tickers: str, lookback_days: int = 7):
    from mcp_server.tools.news_sentiment import analyze_ticker_news
    from mcp_server.tools.kr_ticker_resolver import code_to_name, resolve_korean_ticker

    ticker_list = [t.strip() for t in tickers.split(",") if t.strip()]
    results: dict = {}
    for raw in ticker_list:
        t = resolve_korean_ticker(raw)
        try:
            r = analyze_ticker_news(t, lookback_days=lookback_days)
            if isinstance(r, dict):
                nm = code_to_name(t)
                if nm:
                    r.setdefault("name_kr", nm)
            results[t] = r
        except Exception as e:
            results[t] = {"error": str(e)}
    return Envelope[dict](data=results)


@router.get("/timeline", response_model=Envelope[dict])
def api_news_timeline(ticker: str, lookback_days: int = 14):
    from mcp_server.tools.news_sentiment import analyze_ticker_news
    from mcp_server.tools.kr_ticker_resolver import code_to_name, resolve_korean_ticker

    ticker = resolve_korean_ticker(ticker)
    result = analyze_ticker_news(ticker, lookback_days=lookback_days)
    data = result if isinstance(result, dict) else {"result": result}
    if isinstance(data, dict):
        nm = code_to_name(ticker)
        if nm:
            data.setdefault("name_kr", nm)
        data.setdefault("ticker", ticker)
    return Envelope[dict](data=data)
