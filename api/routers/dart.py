"""DART router — domestic filings + financials (FR-K10/K15).

All endpoints degrade gracefully: if ``DART_API_KEY`` is missing or
``OpenDartReader`` is not installed, they return an empty payload with
a short note rather than a 5xx. This mirrors the behaviour in
``mcp_server.tools.dart.DartClient``.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter

from api.schemas.common import Envelope

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dart", tags=["dart"])


@router.get("/filings", response_model=Envelope[dict])
def api_dart_filings(ticker: str, days: int = 30, limit: int = 20):
    """Recent filings from DART for a Korean stock code or company name."""
    from mcp_server.tools.dart import get_dart_client
    from mcp_server.tools.kr_ticker_resolver import code_to_name, resolve_korean_ticker

    ticker = resolve_korean_ticker(ticker)
    name_kr = code_to_name(ticker)
    client = get_dart_client()
    if not client.ready:
        return Envelope[dict](data={
            "ticker": ticker, "name_kr": name_kr,
            "count": 0, "filings": [],
            "note": "DART_API_KEY missing or OpenDartReader not installed",
        })
    filings = client.get_filings(ticker, days=days, limit=limit)
    return Envelope[dict](data={
        "ticker": ticker, "name_kr": name_kr,
        "count": len(filings), "filings": filings,
    })


@router.get("/financials", response_model=Envelope[dict])
def api_dart_financials(ticker: str, year: int | None = None):
    """Annual K-IFRS financial ratios (ROE/ROA/Operating_Margin/…)."""
    from mcp_server.tools.dart import get_dart_client
    from mcp_server.tools.kr_ticker_resolver import code_to_name, resolve_korean_ticker

    ticker = resolve_korean_ticker(ticker)
    name_kr = code_to_name(ticker)
    client = get_dart_client()
    if not client.ready:
        return Envelope[dict](data={
            "ticker": ticker, "name_kr": name_kr,
            "financials": {},
            "note": "DART_API_KEY missing or OpenDartReader not installed",
        })
    return Envelope[dict](data={
        "ticker": ticker, "name_kr": name_kr,
        "financials": client.get_financials(ticker, year=year),
    })
