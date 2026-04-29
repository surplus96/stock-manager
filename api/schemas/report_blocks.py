"""Structured analysis-report building blocks (rich-visual-reports).

Instead of returning one long Markdown string the analysis pipeline now
emits a **list of typed blocks** that the frontend can render as
discrete cards, inline charts, tables, citations, … — inspired by
Anthropic's ShowMe pattern where the answer is a composition of
purpose-built widgets rather than prose.

Every block carries a ``kind`` literal so the TypeScript mirror can be
an exhaustive discriminated union. Keep the two schemas in sync (see
``dashboard/src/lib/reportBlocks.ts``).
"""
from __future__ import annotations

from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Leaf types
# ---------------------------------------------------------------------------

Tone = Literal["positive", "negative", "neutral"]
Market = Literal["US", "KR"]


class MetricItem(BaseModel):
    label: str
    value: str
    delta: Optional[float] = None           # e.g. +0.034 → rendered as +3.4%
    tone: Optional[Tone] = None             # color hint; None → neutral
    hint: Optional[str] = None              # small subtitle (e.g. "vs last year")


class TableColumn(BaseModel):
    key: str
    label: str
    # align left for text, right for numbers; numeric columns will render with tabular-nums
    numeric: bool = False
    format: Optional[Literal["currency", "percent", "compact", "integer"]] = None


class OHLCVRow(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


class PriceBarLite(BaseModel):
    t: str        # ISO date
    c: float      # close


class NewsCitationItem(BaseModel):
    id: int
    source: str
    title: str
    date: str
    url: str = ""
    snippet: str = ""


class FactorBulletItem(BaseModel):
    name: str
    score: float      # 0-100 scale
    note: Optional[str] = None


# ---------------------------------------------------------------------------
# Block variants (discriminated by ``kind``)
# ---------------------------------------------------------------------------

class SummaryBlock(BaseModel):
    kind: Literal["summary"] = "summary"
    title: Optional[str] = None
    markdown: str
    # ids referring to NewsCitationBlock.items[i].id
    citations: list[int] = Field(default_factory=list)


class MetricCardBlock(BaseModel):
    kind: Literal["metric"] = "metric"
    label: str
    value: str
    delta: Optional[float] = None
    tone: Optional[Tone] = None
    hint: Optional[str] = None


class MetricGridBlock(BaseModel):
    kind: Literal["metric_grid"] = "metric_grid"
    items: list[MetricItem]


class FactorBulletBlock(BaseModel):
    kind: Literal["factor_bullet"] = "factor_bullet"
    factors: list[FactorBulletItem]


class NewsCitationBlock(BaseModel):
    kind: Literal["news_citation"] = "news_citation"
    items: list[NewsCitationItem]


class PriceSparkBlock(BaseModel):
    kind: Literal["price_spark"] = "price_spark"
    ticker: str
    market: Market = "US"
    series: list[PriceBarLite]


class CandlestickBlock(BaseModel):
    kind: Literal["candlestick"] = "candlestick"
    ticker: str
    market: Market = "US"
    rows: list[OHLCVRow]
    overlays: list[Literal["ma20", "ma50", "bb"]] = Field(default_factory=list)
    with_volume: bool = True


class TableBlock(BaseModel):
    kind: Literal["table"] = "table"
    columns: list[TableColumn]
    rows: list[dict[str, Any]]
    caption: Optional[str] = None


class HeatmapBlock(BaseModel):
    kind: Literal["heatmap"] = "heatmap"
    xs: list[str]
    ys: list[str]
    matrix: list[list[float]]
    scale: Literal["correlation", "heat"] = "correlation"


class SectorTreemapItem(BaseModel):
    sector: str
    weight: float
    pnl: Optional[float] = None


class SectorTreemapBlock(BaseModel):
    kind: Literal["sector_treemap"] = "sector_treemap"
    items: list[SectorTreemapItem]


class RadarMiniBlock(BaseModel):
    kind: Literal["radar_mini"] = "radar_mini"
    factors: list[FactorBulletItem]
    max: float = 100.0


class SuggestedBlock(BaseModel):
    """Follow-up question chips (Perplexity-style retention pattern, FR-PSP-F).

    Either rendered as the closing block of an analysis report (clicking
    a chip opens the question in the chat) or surfaced inline under a
    chat answer (clicking submits the chip text as the next user turn).
    """

    kind: Literal["suggested"] = "suggested"
    items: list[str] = Field(default_factory=list, max_length=8)


ReportBlock = Union[
    SummaryBlock,
    MetricCardBlock,
    MetricGridBlock,
    FactorBulletBlock,
    NewsCitationBlock,
    PriceSparkBlock,
    CandlestickBlock,
    TableBlock,
    HeatmapBlock,
    SectorTreemapBlock,
    RadarMiniBlock,
    SuggestedBlock,
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def coerce_block(obj: Any) -> Optional[ReportBlock]:
    """Best-effort coerce a dict (e.g. from LLM JSON) into a typed block.

    Returns ``None`` on failure rather than raising so one bad block in an
    LLM response doesn't take down the whole report.
    """
    if not isinstance(obj, dict):
        return None
    kind = obj.get("kind")
    registry: dict[str, type[BaseModel]] = {
        "summary": SummaryBlock,
        "metric": MetricCardBlock,
        "metric_grid": MetricGridBlock,
        "factor_bullet": FactorBulletBlock,
        "news_citation": NewsCitationBlock,
        "price_spark": PriceSparkBlock,
        "candlestick": CandlestickBlock,
        "table": TableBlock,
        "heatmap": HeatmapBlock,
        "sector_treemap": SectorTreemapBlock,
        "radar_mini": RadarMiniBlock,
        "suggested": SuggestedBlock,
    }
    cls = registry.get(str(kind)) if kind else None
    if not cls:
        return None
    try:
        return cls(**obj)  # type: ignore[return-value]
    except Exception:  # noqa: BLE001
        return None
