"""Portfolio domain Pydantic schemas (FR-B08)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class HoldingItem(BaseModel):
    ticker: str
    shares: int
    entry_price: float
    current_price: float
    market_value: float
    pnl: float
    pnl_pct: float
    signal: str = "Hold"
    composite_score: float = 0.0


class AllocationItem(BaseModel):
    name: str
    value: float


class AlertItem(BaseModel):
    ticker: str
    type: str
    message: str


class PortfolioData(BaseModel):
    total_value: float
    total_cost: float
    total_pnl: float
    cash: float
    holdings: list[HoldingItem]
    allocation: list[AllocationItem]
    health_score: float
    phase: str
    alerts: list[dict[str, Any]] = []
    insights: list[str] = []
