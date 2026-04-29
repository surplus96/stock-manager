"""News domain Pydantic schemas (FR-B08)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class NewsSearchData(BaseModel):
    results: list[dict[str, Any]] = []


class NewsSentimentData(BaseModel):
    results: dict[str, Any] = {}
