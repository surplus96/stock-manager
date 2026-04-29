"""Theme domain router (FR-B07).

Routes: /api/theme/* (except analysis-report, which lives in analysis.py)
"""
from __future__ import annotations

from fastapi import APIRouter

from api.schemas.common import Envelope
from api.schemas.theme import ThemeAnalysisData

router = APIRouter(prefix="/api/theme", tags=["theme"])


def _run_factor_ranking(tickers: list) -> list:
    from api.routers.stock import _run_factor_ranking as _rfr
    return _rfr(tickers)


@router.get("/propose", response_model=Envelope[dict])
def api_theme_propose(lookback_days: int = 7, max_themes: int = 5):
    from mcp_server.tools.interaction import propose_themes
    data = propose_themes(lookback_days=lookback_days, max_themes=max_themes)
    return Envelope[dict](data=data if isinstance(data, dict) else {"themes": data})


@router.get("/explore", response_model=Envelope[dict])
def api_theme_explore(theme: str, lookback_days: int = 7):
    from mcp_server.tools.interaction import explore_theme
    data = explore_theme(theme, lookback_days=lookback_days)
    return Envelope[dict](data=data if isinstance(data, dict) else {"result": data})


@router.get("/tickers", response_model=Envelope[list])
def api_theme_tickers(theme: str):
    from mcp_server.tools.interaction import propose_tickers
    data = propose_tickers(theme)
    return Envelope[list](data=data if isinstance(data, list) else [])


# ---------------------------------------------------------------------------
# Korean themes (FR-K14) — hand-curated map in mcp_server/data/kr_themes.json
# ---------------------------------------------------------------------------

@router.get("/kr/propose", response_model=Envelope[dict])
def api_theme_kr_propose():
    """List the available Korean theme labels."""
    from mcp_server.tools.kr_themes import list_themes
    return Envelope[dict](data={"themes": list_themes()})


@router.get("/kr/tickers", response_model=Envelope[dict])
def api_theme_kr_tickers(theme: str):
    """Anchor tickers for a Korean theme (6-digit KRX codes)."""
    from mcp_server.tools.kr_themes import propose_tickers_kr

    tickers = propose_tickers_kr(theme)
    names: list[str] = []
    if tickers:
        try:
            from mcp_server.tools.kr_market_data import get_kr_adapter
            adapter = get_kr_adapter()
            names = [adapter.get_ticker_name(t) or "" for t in tickers]
        except Exception:  # noqa: BLE001
            names = ["" for _ in tickers]
    return Envelope[dict](data={"theme": theme, "tickers": tickers, "names": names})


@router.get("/kr/analyze", response_model=Envelope[ThemeAnalysisData])
def api_theme_kr_analyze(theme: str, top_n: int = 5):
    """KR-theme factor ranking — mirrors `/api/theme/analyze` but uses the
    curated Korean ticker map rather than ``propose_tickers``."""
    from mcp_server.tools.kr_themes import propose_tickers_kr

    tickers = propose_tickers_kr(theme)
    if not tickers:
        data = ThemeAnalysisData(theme=theme, rankings=[], recommendation="No tickers found")
        return Envelope[ThemeAnalysisData](data=data)

    rankings = _run_factor_ranking(tickers[:top_n])
    if rankings:
        top = rankings[0]
        avg_score = sum(r.get("composite_score", 0) for r in rankings) / len(rankings)
        strong = [r["ticker"] for r in rankings if r.get("signal") in ("Strong Buy", "Buy")]
        recommendation = (
            f"Theme '{theme}': 평균 점수 {avg_score:.1f}/100, 최우선 {top['ticker']} "
            f"({top.get('composite_score', 0):.1f}, {top.get('signal', 'Hold')})."
        )
        if strong:
            recommendation += f" 매수 시그널: {', '.join(strong)}."
    else:
        recommendation = f"No data available for theme '{theme}'."
    data = ThemeAnalysisData(theme=theme, rankings=rankings, recommendation=recommendation)
    return Envelope[ThemeAnalysisData](data=data)


@router.get("/analyze", response_model=Envelope[ThemeAnalysisData])
def api_theme_analyze(theme: str, top_n: int = 5):
    """Theme analysis — factor-based ranking + recommendation text."""
    from mcp_server.tools.interaction import propose_tickers

    tickers = propose_tickers(theme)
    if not tickers:
        data = ThemeAnalysisData(theme=theme, rankings=[], recommendation="No tickers found")
        return Envelope[ThemeAnalysisData](data=data)

    rankings = _run_factor_ranking(tickers[:top_n])

    if rankings:
        top = rankings[0]
        avg_score = sum(r.get("composite_score", 0) for r in rankings) / len(rankings)
        strong_buys = [r["ticker"] for r in rankings if r.get("signal") in ("Strong Buy", "Buy")]
        recommendation = (
            f"Theme '{theme}': Average score {avg_score:.1f}/100. "
            f"Top pick: {top['ticker']} ({top.get('composite_score', 0):.1f}, {top.get('signal', 'Hold')}). "
        )
        if strong_buys:
            recommendation += f"Buy signals: {', '.join(strong_buys)}. "
        else:
            recommendation += "No strong buy signals currently. "
    else:
        recommendation = f"No data available for theme '{theme}'."

    data = ThemeAnalysisData(theme=theme, rankings=rankings, recommendation=recommendation)
    return Envelope[ThemeAnalysisData](data=data)
