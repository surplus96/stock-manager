"""Analysis-report Pydantic schemas (FR-B08, rich-visual-reports FR-R-B01)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class NewsItem(BaseModel):
    title: str = ""
    source: str = ""
    date: str = ""
    url: str = ""
    snippet: str = ""


class StockAnalysisReport(BaseModel):
    ticker: str
    summary: str = ""
    sections: dict[str, Any] = Field(default_factory=dict)
    news: list[NewsItem] = Field(default_factory=list)
    evidence: dict[str, str] = Field(default_factory=dict)
    # rich-visual-reports: structured block array. Consumers that don't
    # know about blocks keep using ``summary`` as before (fallback).
    blocks: list[dict[str, Any]] = Field(default_factory=list)
