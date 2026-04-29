"""Stock domain Pydantic schemas (FR-B08)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class FactorBreakdown(BaseModel):
    financial_score: float = 0.0
    technical_score: float = 0.0
    sentiment_score: float = 0.0
    growth_score: float = 0.0
    quality_score: float = 0.0
    valuation_score: float = 0.0


class StockRankingData(BaseModel):
    ticker: str
    composite_score: float = 0.0
    signal: str = "Hold"
    sector: str = ""
    factors: dict[str, Any] = {}
    normalized_factors: dict[str, Any] = {}
    factor_count: int = 0
    fundamentals: dict[str, Any] = {}
    interpretation: str = ""
    # FR-K06: locale-aware fields so the frontend can pick ₩ vs $ and the
    # Korean display name without running its own heuristic.
    market: str = "US"          # "US" | "KR"
    currency: str = "USD"       # "USD" | "KRW"
    name: str = ""              # primary display name (English or native)
    name_kr: str | None = None  # Korean name when known (DART / KRX)


class InvestmentSignalData(BaseModel):
    decision: str = "Hold"
    confidence: str = "Low"
    reasons: list[str] = []
    risks: list[str] = []
