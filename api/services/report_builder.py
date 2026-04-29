"""Build structured ``ReportBlock`` arrays from collected analysis data
(rich-visual-reports).

Deterministic blocks (metric grid, price spark, candlestick, news
citations, radar) are produced from raw data **before** the LLM runs.
The LLM is then asked to add ``summary`` + ``factor_bullet`` blocks
that reference the citations — keeping the interpretive part in natural
language while the quantitative parts stay reliable and cheap.
"""
from __future__ import annotations

import logging
from typing import Any, Iterable

from api.schemas.report_blocks import (
    CandlestickBlock,
    FactorBulletBlock,
    FactorBulletItem,
    MetricGridBlock,
    MetricItem,
    NewsCitationBlock,
    NewsCitationItem,
    OHLCVRow,
    PriceBarLite,
    PriceSparkBlock,
    RadarMiniBlock,
    ReportBlock,
    SectorTreemapBlock,
    SectorTreemapItem,
    SummaryBlock,
    TableBlock,
    TableColumn,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Metric grid helpers
# ---------------------------------------------------------------------------

def _fmt_currency(value: float | None, market: str) -> str:
    if value is None:
        return "—"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "—"
    if market == "KR":
        if abs(v) >= 1_000_000_000_000:
            return f"₩{v / 1_000_000_000_000:.1f}조"
        if abs(v) >= 100_000_000:
            return f"₩{v / 100_000_000:.0f}억"
        return f"₩{v:,.0f}"
    # USD
    if abs(v) >= 1_000_000_000:
        return f"${v / 1_000_000_000:.1f}B"
    if abs(v) >= 1_000_000:
        return f"${v / 1_000_000:.1f}M"
    return f"${v:,.2f}"


def _fmt_percent(value: float | None, digits: int = 1) -> str:
    if value is None:
        return "—"
    try:
        return f"{float(value) * 100:+.{digits}f}%"
    except (TypeError, ValueError):
        return "—"


def _signal_tone(signal: str | None) -> str:
    s = (signal or "").lower()
    if "buy" in s:
        return "positive"
    if "sell" in s:
        return "negative"
    return "neutral"


def build_stock_metric_grid(
    ticker: str,
    ranking: dict[str, Any],
    fundamentals: dict[str, Any],
    market: str,
) -> MetricGridBlock:
    items: list[MetricItem] = []
    score = ranking.get("composite_score", 0)
    signal = ranking.get("signal", "Hold")
    items.append(MetricItem(
        label="종합 점수", value=f"{float(score or 0):.1f}",
        tone=_signal_tone(signal), hint="0-100",
    ))
    items.append(MetricItem(
        label="투자 시그널", value=str(signal), tone=_signal_tone(signal),
    ))
    factors = ranking.get("factors") or {}
    if factors.get("financial_score") is not None:
        items.append(MetricItem(
            label="재무 점수", value=f"{float(factors['financial_score']):.0f}",
            hint="재무 건전성",
        ))
    if factors.get("technical_score") is not None:
        items.append(MetricItem(
            label="기술 점수", value=f"{float(factors['technical_score']):.0f}",
            hint="모멘텀/추세",
        ))
    if fundamentals.get("pe") is not None:
        items.append(MetricItem(label="P/E", value=f"{float(fundamentals['pe']):.1f}"))
    if fundamentals.get("returnOnEquity") is not None:
        items.append(MetricItem(
            label="ROE", value=_fmt_percent(float(fundamentals["returnOnEquity"]), 1),
            tone="positive" if float(fundamentals["returnOnEquity"]) > 0.12 else "neutral",
        ))
    if fundamentals.get("market_cap") is not None:
        items.append(MetricItem(
            label="시가총액", value=_fmt_currency(float(fundamentals["market_cap"]), market),
        ))
    if fundamentals.get("revenueGrowth") is not None:
        items.append(MetricItem(
            label="매출 성장", value=_fmt_percent(float(fundamentals["revenueGrowth"]), 1),
            tone="positive" if float(fundamentals["revenueGrowth"]) > 0 else "negative",
        ))
    return MetricGridBlock(items=items[:8])


# ---------------------------------------------------------------------------
# Price / OHLCV blocks
# ---------------------------------------------------------------------------

def _prices_to_lite(df, limit: int = 180) -> list[PriceBarLite]:
    out: list[PriceBarLite] = []
    if df is None or getattr(df, "empty", True):
        return out
    rows = df.tail(limit).to_dict(orient="records")
    for r in rows:
        date = r.get("Date") or r.get("date")
        close = r.get("Close") or r.get("close")
        if date is None or close is None:
            continue
        out.append(PriceBarLite(
            t=date.isoformat()[:10] if hasattr(date, "isoformat") else str(date)[:10],
            c=float(close),
        ))
    return out


def _prices_to_ohlcv(df, limit: int = 180) -> list[OHLCVRow]:
    out: list[OHLCVRow] = []
    if df is None or getattr(df, "empty", True):
        return out
    rows = df.tail(limit).to_dict(orient="records")
    for r in rows:
        try:
            date = r.get("Date") or r.get("date")
            out.append(OHLCVRow(
                date=date.isoformat()[:10] if hasattr(date, "isoformat") else str(date)[:10],
                open=float(r.get("Open") or r.get("open") or 0),
                high=float(r.get("High") or r.get("high") or 0),
                low=float(r.get("Low") or r.get("low") or 0),
                close=float(r.get("Close") or r.get("close") or 0),
                volume=float(r.get("Volume") or r.get("volume") or 0),
            ))
        except Exception:  # noqa: BLE001
            continue
    return out


def build_price_blocks(ticker: str, df, market: str) -> list[ReportBlock]:
    blocks: list[ReportBlock] = []
    spark = _prices_to_lite(df, limit=120)
    if spark:
        blocks.append(PriceSparkBlock(ticker=ticker, market=market, series=spark))
    ohlcv = _prices_to_ohlcv(df, limit=180)
    if ohlcv:
        blocks.append(CandlestickBlock(
            ticker=ticker, market=market, rows=ohlcv,
            overlays=["ma20", "ma50"], with_volume=True,
        ))
    return blocks


# ---------------------------------------------------------------------------
# News + radar
# ---------------------------------------------------------------------------

def build_news_citation(items: Iterable[dict[str, Any]], limit: int = 5) -> NewsCitationBlock | None:
    cits: list[NewsCitationItem] = []
    for i, it in enumerate(list(items)[:limit], start=1):
        if not isinstance(it, dict):
            continue
        cits.append(NewsCitationItem(
            id=i,
            source=str(it.get("source") or "")[:60],
            title=str(it.get("title") or "")[:200],
            date=str(it.get("published") or it.get("date") or "")[:10],
            url=str(it.get("url") or ""),
            snippet=str(it.get("snippet") or "")[:240],
        ))
    return NewsCitationBlock(items=cits) if cits else None


def build_radar_mini(factors: dict[str, Any]) -> RadarMiniBlock | None:
    """Map the 6 canonical factor buckets into a mini radar."""
    wanted = [
        ("financial_score", "Financial"),
        ("technical_score", "Technical"),
        ("sentiment_score", "Sentiment"),
        ("growth_score", "Growth"),
        ("quality_score", "Quality"),
        ("valuation_score", "Valuation"),
    ]
    points: list[FactorBulletItem] = []
    for key, label in wanted:
        v = factors.get(key)
        if v is None:
            continue
        try:
            points.append(FactorBulletItem(name=label, score=float(v)))
        except Exception:  # noqa: BLE001
            continue
    return RadarMiniBlock(factors=points) if points else None


# ---------------------------------------------------------------------------
# Table helpers (for rankings / portfolio / theme)
# ---------------------------------------------------------------------------

def rankings_to_table(rankings: list[dict[str, Any]]) -> TableBlock:
    """Build the artifact-panel table for a ranking response.

    When any row carries a Korean ``name_kr``, an extra ``name`` column
    is shown so the user sees ``삼성전자`` next to ``005930`` — the same
    "기업명 ↔ 코드" pairing the rest of the dashboard uses.
    """
    has_kr_name = any(isinstance(r, dict) and r.get("name_kr") for r in rankings)
    columns: list[TableColumn] = [
        TableColumn(key="rank", label="#", numeric=True, format="integer"),
        TableColumn(key="ticker", label="티커"),
    ]
    if has_kr_name:
        columns.append(TableColumn(key="name", label="이름"))
    columns.extend([
        TableColumn(key="score", label="점수", numeric=True),
        TableColumn(key="signal", label="시그널"),
        TableColumn(key="sector", label="섹터"),
    ])
    rows: list[dict[str, Any]] = []
    for i, r in enumerate(rankings[:20], start=1):
        row = {
            "rank": i,
            "ticker": r.get("ticker", ""),
            "score": round(float(r.get("composite_score", 0)), 1),
            "signal": r.get("signal", "Hold"),
            "sector": r.get("sector", ""),
        }
        if has_kr_name:
            row["name"] = r.get("name_kr") or ""
        rows.append(row)
    return TableBlock(columns=columns, rows=rows, caption="Multi-factor ranking")


def sectors_to_treemap(sectors: list[dict[str, Any]]) -> SectorTreemapBlock | None:
    items: list[SectorTreemapItem] = []
    for r in sectors:
        try:
            items.append(SectorTreemapItem(
                sector=str(r.get("sector") or r.get("name") or "Other"),
                weight=float(r.get("weight") or r.get("pct") or 0),
                pnl=float(r["pnl"]) if "pnl" in r and r["pnl"] is not None else None,
            ))
        except Exception:  # noqa: BLE001
            continue
    return SectorTreemapBlock(items=items) if items else None


# ---------------------------------------------------------------------------
# LLM JSON blocks — parse with fallback
# ---------------------------------------------------------------------------

def parse_llm_blocks(raw: str) -> list[ReportBlock]:
    """Extract a ``list[ReportBlock]`` from an LLM response.

    The prompt asks for a JSON array. We try three strategies:
      1. Parse the whole response as JSON.
      2. Extract the first balanced ``[...]`` substring and parse.
      3. Give up and return a single SummaryBlock wrapping the raw prose.
    """
    import json
    from api.schemas.report_blocks import coerce_block

    def _coerce_list(obj: Any) -> list[ReportBlock]:
        if not isinstance(obj, list):
            return []
        out: list[ReportBlock] = []
        for entry in obj:
            b = coerce_block(entry)
            if b is not None:
                out.append(b)
        return out

    if not raw or not raw.strip():
        return []
    txt = raw.strip()

    # Strip markdown code fences if the model wrapped the JSON.
    if txt.startswith("```"):
        import re as _re
        txt = _re.sub(r"^```(?:json)?\s*", "", txt)
        txt = _re.sub(r"\s*```\s*$", "", txt)

    # Strategy 1: whole-response JSON.
    try:
        parsed = json.loads(txt)
        blocks = _coerce_list(parsed)
        if blocks:
            return blocks
    except json.JSONDecodeError:
        pass

    # Strategy 2: find balanced brackets.
    start = txt.find("[")
    end = txt.rfind("]")
    if start >= 0 and end > start:
        try:
            parsed = json.loads(txt[start : end + 1])
            blocks = _coerce_list(parsed)
            if blocks:
                return blocks
        except json.JSONDecodeError:
            pass

    # Strategy 3: prose fallback — wrap in one summary block.
    return [SummaryBlock(markdown=raw.strip())]
