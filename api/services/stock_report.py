"""Stock analysis report service — parallel data collection (FR-B09, FR-B15).

The legacy endpoint ``api_stock_analysis_report`` runs 6 independent I/O-bound
blocks sequentially. This service fans them out onto a thread pool and
composes the report from the aggregated results, cutting p95 latency
significantly for the LLM-powered report endpoint.
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from api.constants import (
    ANALYSIS_NEWS_LOOKBACK_DAYS,
    ANALYSIS_NEWS_MAX_RESULTS,
    ANALYSIS_PRICE_PERIOD_LONG,
    ANALYSIS_SENTIMENT_LOOKBACK_DAYS,
    LLM_PARALLEL_MAX_WORKERS,
)

logger = logging.getLogger(__name__)


# ---- individual collectors (each isolated try/except, safe defaults) ----

def _collect_invest_signal(ticker: str) -> dict[str, Any]:
    try:
        from mcp_server.tools.data_integrator import get_investment_signal
        return get_investment_signal(ticker) or {}
    except Exception as e:  # noqa: BLE001
        logger.info("invest_signal failed for %s: %s", ticker, e)
        return {}


def _collect_financial_interp(ticker: str) -> dict[str, Any]:
    try:
        from mcp_server.tools.financial_factors import FinancialFactors
        ff = FinancialFactors.calculate_all(ticker, "US")
        return FinancialFactors.get_factor_interpretation(ff) or {}
    except Exception as e:  # noqa: BLE001
        logger.info("financial_interp failed for %s: %s", ticker, e)
        return {}


def _collect_technical_interp(ticker: str) -> dict[str, Any]:
    try:
        from mcp_server.tools.technical_indicators import TechnicalFactors
        import yfinance as yf
        df = yf.Ticker(ticker).history(period=ANALYSIS_PRICE_PERIOD_LONG)
        if df.empty:
            return {}
        tf = TechnicalFactors.calculate_all(df)
        return TechnicalFactors.get_factor_interpretation(tf) or {}
    except Exception as e:  # noqa: BLE001
        logger.info("technical_interp failed for %s: %s", ticker, e)
        return {}


def _collect_news(ticker: str) -> list[dict[str, Any]]:
    """Fetch and **flatten** news articles for a ticker.

    ``search_news`` returns one of:
      * ``[{"query": str, "hits": [article, ...]}, ...]``  ← multi-query shape
      * ``{"results": [{"query": ..., "hits": [...]}, ...]}``
      * ``{"items" | "articles" | "data" | "news": [article, ...]}``

    All shapes are flattened to a plain ``list[dict]`` where each entry has
    at least one of ``title`` / ``url`` so downstream code can render it.
    Previously this function returned the unflattened wrapper (``[{query,hits}]``),
    which surfaced in the UI as a single empty-string news card.
    """
    try:
        # FR-K12: 한국 티커면 한국어 RSS + 종목명 기반 쿼리로 교체
        from mcp_server.tools.yf_utils import detect_market
        if detect_market(ticker) == "KR":
            from mcp_server.tools.news_search_kr import search_news_kr
            query = ticker
            try:
                from mcp_server.tools.kr_market_data import get_kr_adapter
                nm = get_kr_adapter().get_ticker_name(ticker) or ""
                if nm:
                    query = nm
            except Exception:  # noqa: BLE001
                pass
            result = search_news_kr(
                [query],
                lookback_days=ANALYSIS_NEWS_LOOKBACK_DAYS,
                max_results=ANALYSIS_NEWS_MAX_RESULTS,
            )
        else:
            from mcp_server.tools.news_search import search_news
            result = search_news(
                [f"{ticker} stock"],
                lookback_days=ANALYSIS_NEWS_LOOKBACK_DAYS,
                max_results=ANALYSIS_NEWS_MAX_RESULTS,
            )

        def _flatten_query_list(entries: list) -> list[dict[str, Any]]:
            out: list[dict[str, Any]] = []
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                if isinstance(entry.get("hits"), list):
                    out.extend(h for h in entry["hits"] if isinstance(h, dict))
                elif entry.get("title") or entry.get("url"):
                    out.append(entry)
            return out

        if isinstance(result, list):
            return _flatten_query_list(result)
        if isinstance(result, dict):
            if isinstance(result.get("results"), list):
                return _flatten_query_list(result["results"])
            for key in ("items", "articles", "data", "news"):
                items = result.get(key)
                if isinstance(items, list):
                    return [h for h in items if isinstance(h, dict)]
        return []
    except Exception as e:  # noqa: BLE001
        logger.info("news collect failed for %s: %s", ticker, e)
        return []


def _collect_sentiment(ticker: str) -> dict[str, Any]:
    try:
        from mcp_server.tools.news_sentiment import analyze_ticker_news
        return analyze_ticker_news(ticker, lookback_days=ANALYSIS_SENTIMENT_LOOKBACK_DAYS) or {}
    except Exception as e:  # noqa: BLE001
        logger.info("sentiment failed for %s: %s", ticker, e)
        return {}


def _collect_fundamentals(ticker: str) -> dict[str, Any]:
    try:
        from mcp_server.tools.market_data import get_fundamentals_snapshot
        return get_fundamentals_snapshot(ticker) or {}
    except Exception as e:  # noqa: BLE001
        logger.info("fundamentals failed for %s: %s", ticker, e)
        return {}


# ---- public entry point ----

def collect_stock_analysis_inputs(ticker: str) -> dict[str, Any]:
    """Run all 6 data collectors in parallel and return the aggregated inputs.

    Returns a dict with keys:
        invest_signal, fin_interp, tech_interp, news_items, sentiment, fundamentals
    """
    tasks: dict[str, Callable[[], Any]] = {
        "invest_signal": lambda: _collect_invest_signal(ticker),
        "fin_interp": lambda: _collect_financial_interp(ticker),
        "tech_interp": lambda: _collect_technical_interp(ticker),
        "news_items": lambda: _collect_news(ticker),
        "sentiment": lambda: _collect_sentiment(ticker),
        "fundamentals": lambda: _collect_fundamentals(ticker),
    }
    results: dict[str, Any] = {}
    with ThreadPoolExecutor(max_workers=LLM_PARALLEL_MAX_WORKERS) as pool:
        futures = {pool.submit(fn): key for key, fn in tasks.items()}
        for fut in futures:
            key = futures[fut]
            try:
                results[key] = fut.result()
            except Exception as e:  # noqa: BLE001
                logger.warning("collector %s raised: %s", key, e)
                results[key] = [] if key == "news_items" else {}
    return results
