"""Portfolio domain router (FR-B07).

Routes: /api/portfolio/* (except analysis-report, which lives in analysis.py)
"""
from __future__ import annotations

import logging
import re

from fastapi import APIRouter

from api.schemas.common import Envelope
from api.schemas.portfolio import PortfolioData
from core.time import period_to_dates as _period_to_dates

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


def _run_factor_ranking(tickers: list) -> list:
    """Thin import wrapper — delegates to stock router helper to avoid duplication."""
    from api.routers.stock import _run_factor_ranking as _rfr
    return _rfr(tickers)


@router.get("/comprehensive", response_model=Envelope[PortfolioData])
def api_portfolio_comprehensive(holdings: str, cash: float = 0):
    """Parse holdings like 'AAPL:10@150, MSFT:5@400' and analyze."""
    from mcp_server.tools.market_data import get_prices

    from mcp_server.tools.kr_ticker_resolver import resolve_korean_ticker

    parsed = []
    for item in holdings.split(","):
        item = item.strip()
        # ``\w`` matches Hangul under Python's default Unicode mode, so
        # a holding like ``삼성전자:10@70000`` parses; we then run the
        # token through ``resolve_korean_ticker`` to canonicalise it to
        # the 6-digit code that downstream APIs expect.
        m = re.match(r"([\w.가-힣]+):(\d+)@([\d.]+)", item)
        if m:
            parsed.append({
                "ticker": resolve_korean_ticker(m.group(1)),
                "shares": int(m.group(2)),
                "entry_price": float(m.group(3)),
            })

    if not parsed:
        return Envelope[PortfolioData](data=PortfolioData(
            total_value=0, total_cost=0, total_pnl=0, cash=cash,
            holdings=[], allocation=[], health_score=0, phase="Unknown",
        ))

    tickers = [p["ticker"] for p in parsed]
    rankings = _run_factor_ranking(tickers)
    ranking_map = {r["ticker"]: r for r in rankings} if rankings else {}

    holdings_result = []
    total_value = cash
    total_cost = 0.0

    for p in parsed:
        t = p["ticker"]
        start, end = _period_to_dates("1mo")
        df = get_prices(t, start=start, end=end)
        current_price = 0.0
        if not df.empty:
            last_row = df.iloc[-1]
            current_price = float(last_row.get("Close", last_row.get("close", 0)))

        market_value = current_price * p["shares"]
        cost_basis = p["entry_price"] * p["shares"]
        pnl = market_value - cost_basis
        pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0

        total_value += market_value
        total_cost += cost_basis

        r = ranking_map.get(t, {})
        # `_run_factor_ranking` already enriches KR rows with name_kr /
        # market / currency, but pull them through explicitly so the
        # holdings table in the dashboard can render "삼성전자 (005930)"
        # without re-running the resolver client-side.
        holdings_result.append({
            "ticker": t,
            "name_kr": r.get("name_kr"),
            "market": r.get("market"),
            "currency": r.get("currency"),
            "shares": p["shares"],
            "entry_price": p["entry_price"],
            "current_price": round(current_price, 2),
            "market_value": round(market_value, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "signal": r.get("signal", "Hold"),
            "composite_score": r.get("composite_score", 0),
        })

    total_pnl = total_value - total_cost - cash

    allocations = []
    for h in holdings_result:
        weight = (h["market_value"] / total_value * 100) if total_value > 0 else 0
        allocations.append({"name": h["ticker"], "value": round(weight, 2)})
    if cash > 0 and total_value > 0:
        allocations.append({"name": "Cash", "value": round(cash / total_value * 100, 2)})

    alerts = []
    insights = []
    for h in holdings_result:
        if h["pnl_pct"] < -10:
            alerts.append({"ticker": h["ticker"], "type": "loss",
                           "message": f"{h['ticker']}: {h['pnl_pct']:.1f}% loss — consider stop-loss review"})
        if h.get("signal") in ("Sell", "Strong Sell"):
            alerts.append({"ticker": h["ticker"], "type": "signal",
                           "message": f"{h['ticker']}: rated '{h['signal']}' — monitor closely"})
        if h.get("signal") in ("Strong Buy", "Buy") and h["pnl_pct"] > 0:
            insights.append(f"{h['ticker']}: positive trend, rated '{h['signal']}' — momentum intact")
        if h.get("composite_score", 0) < 40:
            alerts.append({"ticker": h["ticker"], "type": "weak",
                           "message": f"{h['ticker']}: low score ({h['composite_score']:.0f}) — underperforming"})

    health = round(sum(h["composite_score"] for h in holdings_result) / max(len(holdings_result), 1), 1)
    phase = "Uptrend" if health >= 65 else "Stable" if health >= 50 else "Unstable" if health >= 35 else "Critical"

    data = PortfolioData(
        total_value=round(total_value, 2),
        total_cost=round(total_cost, 2),
        total_pnl=round(total_pnl, 2),
        cash=cash,
        holdings=holdings_result,  # type: ignore[arg-type]
        allocation=allocations,  # type: ignore[arg-type]
        health_score=health,
        phase=phase,
        alerts=alerts,
        insights=insights,
    )
    return Envelope[PortfolioData](data=data)
