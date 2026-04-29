"""Ranking domain router (FR-B07).

Routes: /api/ranking/*
"""
from __future__ import annotations

from fastapi import APIRouter

from api.schemas.common import Envelope

router = APIRouter(prefix="/api/ranking", tags=["ranking"])


def _run_factor_ranking(tickers: list) -> list:
    from api.routers.stock import _run_factor_ranking as _rfr
    return _rfr(tickers)


def _enrich_kr_names(rows: list[dict]) -> list[dict]:
    """Attach ``name_kr`` to every KR ticker row in a ranking response."""
    from mcp_server.tools.kr_ticker_resolver import code_to_name
    from mcp_server.tools.yf_utils import detect_market

    for r in rows:
        if not isinstance(r, dict):
            continue
        t = r.get("ticker") or r.get("symbol") or ""
        market = r.get("market") or detect_market(str(t))
        r.setdefault("market", market)
        r.setdefault("currency", "KRW" if market == "KR" else "USD")
        if market == "KR":
            nm = code_to_name(str(t))
            if nm and not r.get("name_kr"):
                r["name_kr"] = nm
    return rows


@router.get("/stocks", response_model=Envelope[list])
def api_rank_stocks(tickers: str):
    """Rank a comma-separated ticker basket. Hangul names get resolved to
    6-digit codes upfront so a basket like ``"AAPL, 삼성전자, 247540"`` works.
    Each KR row is enriched with ``name_kr`` for the frontend label.
    """
    from mcp_server.tools.kr_ticker_resolver import resolve_korean_ticker

    ticker_list = [resolve_korean_ticker(t.strip()) for t in tickers.split(",") if t.strip()]
    data = _enrich_kr_names(_run_factor_ranking(ticker_list))
    return Envelope[list](data=data)
