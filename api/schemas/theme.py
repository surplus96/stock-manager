"""Theme domain Pydantic schemas (FR-B08)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ThemeProposal(BaseModel):
    themes: list[str] = []


class ThemeAnalysisData(BaseModel):
    theme: str
    rankings: list[dict[str, Any]] = []
    recommendation: str = ""
