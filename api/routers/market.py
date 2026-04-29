"""Market domain router (FR-B07).

Routes: /api/market/*
"""
from __future__ import annotations

from fastapi import APIRouter

from api.schemas.common import Envelope
from api.schemas.market import (
    KRConditionData,
    KRIndicesData,
    MarketConditionData,
    MarketPricesData,
)
from core.time import period_to_dates as _period_to_dates
from mcp_server.tools.yf_utils import detect_market

router = APIRouter(prefix="/api/market", tags=["market"])


def _df_to_rows(df) -> list[dict]:
    """Uniform OHLCV row dict for JSON — accepts pykrx or yfinance DataFrames."""
    rows: list[dict] = []
    if df is None or getattr(df, "empty", True):
        return rows
    for row in df.to_dict(orient="records"):
        d: dict = {}
        for col, val in row.items():
            key = str(col).lower()
            if hasattr(val, "isoformat"):
                d[key] = val.isoformat()[:10]
            elif isinstance(val, (int, float)):
                d[key] = float(val)
            else:
                try:
                    d[key] = float(val)
                except (TypeError, ValueError):
                    d[key] = str(val)
        rows.append(d)
    return rows


@router.get("/condition", response_model=Envelope[MarketConditionData])
def api_market_condition():
    from mcp_server.tools.ranking_engine import detect_market_condition
    from mcp_server.tools.market_data import get_prices

    condition = detect_market_condition("SPY", lookback_days=60)
    start, end = _period_to_dates("3mo")
    df = get_prices("SPY", start=start, end=end)
    spy_return = 0.0
    if len(df) >= 2:
        first_close = float(df.iloc[0].get("Close", df.iloc[0].get("close", 0)))
        last_close = float(df.iloc[-1].get("Close", df.iloc[-1].get("close", 0)))
        if first_close > 0:
            spy_return = (last_close - first_close) / first_close
    data = MarketConditionData(condition=condition, spy_60d_return=spy_return)
    return Envelope[MarketConditionData](data=data)


@router.get("/prices", response_model=Envelope[MarketPricesData])
def api_market_prices(ticker: str, period: str = "6mo", interval: str = "1d"):
    from mcp_server.tools.market_data import get_prices
    from mcp_server.tools.kr_ticker_resolver import resolve_korean_ticker

    ticker = resolve_korean_ticker(ticker)
    start, end = _period_to_dates(period)
    df = get_prices(ticker, start=start, end=end, interval=interval)
    rows = _df_to_rows(df)
    market = detect_market(ticker)
    currency = "KRW" if market == "KR" else "USD"
    data = MarketPricesData(
        ticker=ticker, count=len(rows), data=rows, market=market, currency=currency,
    )
    return Envelope[MarketPricesData](data=data)


# ---------------------------------------------------------------------------
# Korean market (FR-K03/K04/K05)
# ---------------------------------------------------------------------------

@router.get("/kr/condition", response_model=Envelope[KRConditionData])
def api_market_kr_condition():
    """KOSPI 60-day return → bull/bear/neutral."""
    from mcp_server.tools.market_data import get_prices

    start, end = _period_to_dates("3mo")
    df = get_prices("^KS11", start=start, end=end)  # yfinance KOSPI index code
    kospi_return = 0.0
    if df is not None and not df.empty:
        close_col = "Close" if "Close" in df.columns else "close"
        if close_col in df.columns and len(df) >= 2:
            first = float(df.iloc[0][close_col] or 0)
            last = float(df.iloc[-1][close_col] or 0)
            if first > 0:
                kospi_return = (last - first) / first
    condition = "bull" if kospi_return >= 0.05 else "bear" if kospi_return <= -0.05 else "neutral"
    return Envelope[KRConditionData](
        data=KRConditionData(condition=condition, kospi_60d_return=kospi_return)
    )


@router.get("/kr/indices", response_model=Envelope[KRIndicesData])
def api_market_kr_indices(period: str = "3mo"):
    """KOSPI / KOSDAQ / KOSPI200 snapshot — OHLCV rows."""
    from mcp_server.tools.market_data import get_prices

    start, end = _period_to_dates(period)
    out = {}
    for key, sym in (("kospi", "^KS11"), ("kosdaq", "^KQ11"), ("kospi200", "^KS200")):
        df = get_prices(sym, start=start, end=end)
        out[key] = _df_to_rows(df)
    return Envelope[KRIndicesData](data=KRIndicesData(**out))


@router.get("/kr/prices", response_model=Envelope[MarketPricesData])
def api_market_kr_prices(ticker: str, period: str = "6mo"):
    """Explicit KR-market prices endpoint (kept even though `/prices`
    auto-dispatches, for API clarity)."""
    from mcp_server.tools.market_data import get_prices

    start, end = _period_to_dates(period)
    df = get_prices(ticker, start=start, end=end)
    rows = _df_to_rows(df)
    return Envelope[MarketPricesData](
        data=MarketPricesData(
            ticker=ticker, count=len(rows), data=rows, market="KR", currency="KRW",
        )
    )
