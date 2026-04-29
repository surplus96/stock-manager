"""Smoke tests verifying Envelope shape across domain routers (FR-B24, FR-B08).

Each test mocks the underlying data-fetching calls so the suite runs offline
without real API keys.
"""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _assert_envelope(body: dict) -> None:
    """Assert success envelope shape {data, generated_at, version}."""
    assert "data" in body, f"'data' key missing from: {body}"
    assert "generated_at" in body, f"'generated_at' key missing from: {body}"
    assert "version" in body, f"'version' key missing from: {body}"


@pytest.fixture(scope="module")
def client():
    from api.server import app
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Market router
# ---------------------------------------------------------------------------

def test_market_condition_envelope(client: TestClient) -> None:
    with (
        patch("mcp_server.tools.ranking_engine.detect_market_condition", return_value="Bull"),
        patch("mcp_server.tools.market_data.get_prices", return_value=MagicMock(
            empty=False,
            __len__=lambda s: 2,
            iloc=MagicMock(
                __getitem__=lambda s, i: {"Close": 100.0 if i == 0 else 110.0}
            ),
        )),
    ):
        resp = client.get("/api/market/condition")
    assert resp.status_code == 200
    _assert_envelope(resp.json())


def test_market_prices_envelope(client: TestClient) -> None:
    import pandas as pd

    df = pd.DataFrame([{"Close": 150.0, "Volume": 1000000}])
    df.index = pd.to_datetime(["2026-04-01"])

    with patch("mcp_server.tools.market_data.get_prices", return_value=df):
        resp = client.get("/api/market/prices?ticker=AAPL")
    assert resp.status_code == 200
    _assert_envelope(resp.json())


# ---------------------------------------------------------------------------
# Stock router
# ---------------------------------------------------------------------------

_FAKE_RANKING = [{
    "ticker": "AAPL",
    "composite_score": 72.5,
    "signal": "Buy",
    "sector": "Technology",
    "factors": {"financial_score": 70.0, "technical_score": 65.0,
                 "sentiment_score": 0.2, "growth_score": 68.0,
                 "quality_score": 71.0, "valuation_score": 60.0},
    "normalized_factors": {},
    "factor_count": 40,
    "fundamentals": {},
    "interpretation": "",
}]


def test_stock_signal_envelope(client: TestClient) -> None:
    with patch("api.routers.stock._run_factor_ranking", return_value=_FAKE_RANKING):
        resp = client.get("/api/stock/signal?ticker=AAPL")
    assert resp.status_code == 200
    _assert_envelope(resp.json())
    inner = resp.json()["data"]
    assert inner["signal"] == "Buy"


def test_stock_investment_signal_envelope(client: TestClient) -> None:
    with patch("mcp_server.tools.data_integrator.get_investment_signal", return_value={
        "decision": "Buy",
        "confidence": "High",
        "reasons": ["Strong ROE"],
        "risks": [],
    }):
        resp = client.get("/api/stock/investment-signal?ticker=AAPL")
    assert resp.status_code == 200
    _assert_envelope(resp.json())


# ---------------------------------------------------------------------------
# Portfolio router
# ---------------------------------------------------------------------------

def test_portfolio_comprehensive_envelope(client: TestClient) -> None:
    import pandas as pd

    df = pd.DataFrame([{"Close": 180.0}])

    with (
        patch("api.routers.stock._run_factor_ranking", return_value=_FAKE_RANKING),
        patch("mcp_server.tools.market_data.get_prices", return_value=df),
    ):
        resp = client.get("/api/portfolio/comprehensive?holdings=AAPL:10@150")
    assert resp.status_code == 200
    _assert_envelope(resp.json())
    data = resp.json()["data"]
    assert "holdings" in data
    assert "total_value" in data


# ---------------------------------------------------------------------------
# News router
# ---------------------------------------------------------------------------

def test_news_search_envelope(client: TestClient) -> None:
    with patch("mcp_server.tools.news_search.search_news", return_value={"results": []}):
        resp = client.get("/api/news/search?queries=AAPL")
    assert resp.status_code == 200
    _assert_envelope(resp.json())


def test_news_sentiment_envelope(client: TestClient) -> None:
    with patch("mcp_server.tools.news_sentiment.analyze_ticker_news", return_value={"sentiment_label": "Positive"}):
        resp = client.get("/api/news/sentiment?tickers=AAPL")
    assert resp.status_code == 200
    _assert_envelope(resp.json())
