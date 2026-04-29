"""Market domain Pydantic schemas (FR-B08)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class MarketConditionData(BaseModel):
    condition: str
    spy_60d_return: float


class PriceRow(BaseModel):
    date: str = ""
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0


class MarketPricesData(BaseModel):
    ticker: str
    count: int
    data: list[dict[str, Any]]
    # FR-K02: market tag so the frontend can pick locale / currency without
    # re-running its own ticker heuristic. "US" remains the default for
    # every pre-KR integration caller.
    market: str = "US"
    currency: str = "USD"


class KRConditionData(BaseModel):
    """FR-K03 — KOSPI-based bull/bear signal (mirror of MarketConditionData)."""
    condition: str
    kospi_60d_return: float


class KRIndicesData(BaseModel):
    """FR-K04 — snapshot of the three headline Korean indices."""
    kospi: list[dict[str, Any]] = []
    kosdaq: list[dict[str, Any]] = []
    kospi200: list[dict[str, Any]] = []
