"""Ranking domain Pydantic schemas (FR-B08)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class RankingEntry(BaseModel):
    ticker: str
    composite_score: float = 0.0
    signal: str = "Hold"
    sector: str = ""
    factors: dict[str, Any] = {}
    normalized_factors: dict[str, Any] = {}
    factor_count: int = 0
