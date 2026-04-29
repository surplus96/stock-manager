"""Tool registry for the chat agent (mcp-chatbot).

Each entry exposes one MCP-backed analysis capability to the LLM. Tools
delegate to ``mcp_server.tools.*`` directly (in-process) so we avoid the
HTTP/MCP-stdio round-trip when the chat router and the underlying tool
both live in the same FastAPI worker.

Adding a new tool:
    1. Append a ``ToolSpec`` to ``TOOL_SPECS`` (name, description, args, fn).
    2. Make sure ``fn`` returns JSON-serialisable data (dict / list / scalars).
    3. Restart uvicorn — the system prompt is rebuilt from ``TOOL_SPECS`` on
       every request via ``build_system_prompt()``.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ToolArg:
    name: str
    type: str  # "string" | "int" | "float" | "bool"
    required: bool = True
    default: Any = None
    description: str = ""


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    args: tuple[ToolArg, ...]
    fn: Callable[..., Any]


# ---------------------------------------------------------------------------
# Tool implementations — each one takes only kwargs the LLM is allowed to set
# and returns a JSON-friendly value.
# ---------------------------------------------------------------------------

def _t_propose_themes(lookback_days: int = 7, max_themes: int = 5) -> Any:
    from mcp_server.tools.interaction import propose_themes
    return propose_themes(lookback_days=lookback_days, max_themes=max_themes)


# -----------------------------------------------------------------------------
# Locale helpers — tag every tool return with market/currency so the LLM knows
# which symbol (₩ vs $) to use when citing numbers in its final answer.
# -----------------------------------------------------------------------------

def _market_of(ticker: str) -> str:
    from mcp_server.tools.yf_utils import detect_market
    return detect_market(ticker)


def _currency_for(market: str) -> str:
    return "KRW" if market == "KR" else "USD"


def _tag_ranking_item(r: dict) -> dict:
    """Attach market/currency/name_kr to a single ranking row if absent."""
    if not isinstance(r, dict):
        return r
    t = r.get("ticker") or r.get("symbol") or ""
    m = r.get("market") or _market_of(str(t))
    r.setdefault("market", m)
    r.setdefault("currency", _currency_for(m))
    if m == "KR" and not r.get("name_kr"):
        try:
            from mcp_server.tools.kr_ticker_resolver import code_to_name
            nm = code_to_name(str(t))
            if nm:
                r["name_kr"] = nm
        except Exception:  # noqa: BLE001
            pass
    return r


def _norm_ticker_token(tok: str) -> str:
    """Normalise a single ticker token.

    * 6-digit KR codes → as-is.
    * Hangul names (e.g. "삼성전자") → resolved to 6-digit code via
      :func:`resolve_korean_ticker` so users can type company names in chat.
    * Alphabetic US tickers → uppercased.
    """
    from mcp_server.tools.kr_ticker_resolver import resolve_korean_ticker
    s = tok.strip()
    if not s:
        return s
    resolved = resolve_korean_ticker(s)
    if resolved != s:
        return resolved
    if s.isdigit() and len(s) == 6:
        return s
    return s.upper()


def _t_analyze_theme(theme: str, top_n: int = 5) -> Any:
    """Theme → tickers → factor ranking (re-uses theme router service)."""
    from mcp_server.tools.interaction import propose_tickers
    from api.routers.stock import _run_factor_ranking

    tickers = propose_tickers(theme) or []
    if not tickers:
        return {"theme": theme, "rankings": [], "note": "no tickers found"}
    rankings = [_tag_ranking_item(r) for r in _run_factor_ranking(tickers[:top_n])]
    # Single-market classification so the LLM can write the whole block in one currency.
    markets = {r.get("market") for r in rankings if r.get("market")}
    predominant = "KR" if markets == {"KR"} else "US" if markets == {"US"} else "MIXED"
    return {
        "theme": theme,
        "rankings": rankings,
        "market": predominant,
        "currency": _currency_for(predominant) if predominant != "MIXED" else "MIXED",
    }


def _t_rank_stocks(tickers: str) -> Any:
    """Comma-separated tickers → multi-factor ranking."""
    from api.routers.stock import _run_factor_ranking

    items = [_norm_ticker_token(t) for t in tickers.split(",") if t.strip()]
    if not items:
        return {"rankings": [], "note": "empty ticker list"}
    rankings = [_tag_ranking_item(r) for r in _run_factor_ranking(items)]
    markets = {r.get("market") for r in rankings if r.get("market")}
    predominant = "KR" if markets == {"KR"} else "US" if markets == {"US"} else "MIXED"
    return {
        "rankings": rankings,
        "market": predominant,
        "currency": _currency_for(predominant) if predominant != "MIXED" else "MIXED",
    }


def _t_stock_comprehensive(ticker: str) -> Any:
    """Reuse the stock router's comprehensive endpoint (in-process call).

    The router already populates ``market``/``currency``/``name_kr`` via
    FR-K06, so the LLM receives those fields directly.
    """
    from api.routers.stock import api_stock_comprehensive
    env = api_stock_comprehensive(ticker)
    result = env.data.model_dump() if hasattr(env, "data") and hasattr(env.data, "model_dump") else env
    if isinstance(result, dict):
        m = result.get("market") or _market_of(ticker)
        result.setdefault("market", m)
        result.setdefault("currency", _currency_for(m))
    return result


def _t_stock_signal(ticker: str) -> Any:
    """Reuse the stock router's investment-signal endpoint (in-process call)."""
    try:
        from api.routers.stock import api_investment_signal
        env = api_investment_signal(ticker)
        result = env.data.model_dump() if hasattr(env, "data") and hasattr(env.data, "model_dump") else env
    except Exception:
        # Fallback: factor ranking-based signal
        from api.routers.stock import api_stock_signal
        env = api_stock_signal(ticker)
        result = env.data if hasattr(env, "data") else env
        if hasattr(result, "__dict__"):
            result = result.__dict__ if not isinstance(result, dict) else result
    if isinstance(result, dict):
        m = result.get("market") or _market_of(ticker)
        result.setdefault("ticker", ticker)
        result.setdefault("market", m)
        result.setdefault("currency", _currency_for(m))
    return result


def _t_news_sentiment(tickers: str, lookback_days: int = 7) -> Any:
    from mcp_server.tools.news_sentiment import analyze_ticker_news
    items = [_norm_ticker_token(t) for t in tickers.split(",") if t.strip()]
    out: dict = {}
    for t in items:
        r = analyze_ticker_news(t, lookback_days=lookback_days)
        m = _market_of(t)
        if isinstance(r, dict):
            r.setdefault("market", m)
            r.setdefault("currency", _currency_for(m))
        out[t] = r
    return out


def _t_propose_tickers(theme: str) -> Any:
    """Direct ticker discovery for a theme — no factor ranking yet.

    Useful when the user wants to *see candidates first* before drilling
    into a full multi-factor analysis (cheaper than ``analyze_theme``).
    """
    from mcp_server.tools.interaction import propose_tickers
    tickers = propose_tickers(theme) or []
    return {"theme": theme, "tickers": tickers, "count": len(tickers)}


def _t_dip_candidates(
    theme: str | None = None,
    tickers: str | None = None,
    top_n: int = 5,
    drawdown_min: float = 0.2,
) -> Any:
    """Find dip-buy candidates — large 180D drawdown + recovering momentum.

    Either ``theme`` or ``tickers`` (comma-separated) must be provided.
    Side effects (CSV / chart rendering) are disabled via ``save=False``.
    """
    from mcp_server.pipelines.dip_candidates import run_dip_candidates

    ticker_list: list[str] | None = None
    if tickers:
        ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    if not theme and not ticker_list:
        return {"error": "either 'theme' or 'tickers' is required"}
    try:
        result = run_dip_candidates(
            theme=theme or "(custom)",
            tickers=ticker_list,
            top_n=top_n,
            drawdown_min=drawdown_min,
            save=False,
        )
        # Trim heavy fields for chat consumption (keep tickers + key scores).
        candidates = []
        for r in result.get("rows", result.get("top", [])) if isinstance(result, dict) else []:
            candidates.append({
                "ticker": r.get("ticker"),
                "score": r.get("score"),
                "drawdown180": r.get("drawdown180"),
                "mom3": r.get("mom3"),
                "mom6": r.get("mom6"),
                "pe": r.get("pe"),
                "sector": r.get("sector"),
            })
        return {"theme": theme, "top_n": top_n, "candidates": candidates or result}
    except Exception as e:  # noqa: BLE001 — surfaced to LLM
        return {"error": f"dip pipeline failed: {e}"}


def _t_watchlist_signals(top_n: int | None = None) -> Any:
    """Auto-scan: pull tickers from the persisted watchlist and rank them.

    Falls back gracefully when the watchlist file is missing/empty so the
    LLM can apologise instead of erroring out.
    """
    import json

    from api.routers.stock import _run_factor_ranking

    try:
        from mcp_server.config import WATCHLIST_PATH
    except Exception as e:
        return {"error": f"watchlist config unavailable: {e}"}

    try:
        with open(WATCHLIST_PATH, "r", encoding="utf-8") as f:
            wl = json.load(f) or {}
    except FileNotFoundError:
        return {"error": "워치리스트 파일이 없습니다. 먼저 종목을 등록하세요.", "tickers": []}
    except Exception as e:  # noqa: BLE001
        return {"error": f"watchlist load failed: {e}"}

    tickers = wl.get("tickers") if isinstance(wl, dict) else None
    if not isinstance(tickers, list) or not tickers:
        return {"error": "워치리스트가 비어 있습니다.", "tickers": []}

    cleaned = [str(t).strip().upper() for t in tickers if str(t).strip()]
    rankings = _run_factor_ranking(cleaned)
    if top_n:
        rankings = rankings[: max(1, int(top_n))]
    return {
        "watchlist_size": len(cleaned),
        "rankings": rankings,
        "themes": wl.get("themes") if isinstance(wl, dict) else None,
    }


def _t_market_condition() -> Any:
    from mcp_server.tools.ranking_engine import detect_market_condition
    from mcp_server.tools.market_data import get_prices
    from core.time import period_to_dates

    cond = detect_market_condition("SPY", lookback_days=60)
    start, end = period_to_dates("3mo")
    df = get_prices("SPY", start=start, end=end)
    spy_return = 0.0
    if len(df) >= 2:
        first = float(df.iloc[0].get("Close", df.iloc[0].get("close", 0)))
        last = float(df.iloc[-1].get("Close", df.iloc[-1].get("close", 0)))
        if first > 0:
            spy_return = (last - first) / first
    return {"condition": cond, "spy_60d_return": spy_return}


# ---------------------------------------------------------------------------
# Public registry
# ---------------------------------------------------------------------------

TOOL_SPECS: tuple[ToolSpec, ...] = (
    ToolSpec(
        name="propose_themes",
        description="최근 N일 시장 이슈를 기반으로 투자 테마(예: 'AI 반도체', '생성형 AI')를 제안한다.",
        args=(
            ToolArg("lookback_days", "int", required=False, default=7,
                    description="조회 기간(일). 기본 7."),
            ToolArg("max_themes", "int", required=False, default=5,
                    description="제안 테마 최대 개수. 기본 5."),
        ),
        fn=_t_propose_themes,
    ),
    ToolSpec(
        name="analyze_theme",
        description="특정 테마에 속한 종목들을 멀티팩터 점수로 랭킹한다.",
        args=(
            ToolArg("theme", "string", required=True, description="테마명. 예: 'AI semiconductor'"),
            ToolArg("top_n", "int", required=False, default=5, description="랭킹 상위 N개."),
        ),
        fn=_t_analyze_theme,
    ),
    ToolSpec(
        name="rank_stocks",
        description="콤마 구분 티커 리스트를 멀티팩터(재무/기술/성장/퀄리티/밸류) 점수로 랭킹한다.",
        args=(
            ToolArg("tickers", "string", required=True,
                    description="콤마 구분 티커. 예: 'AAPL,MSFT,NVDA'"),
        ),
        fn=_t_rank_stocks,
    ),
    ToolSpec(
        name="stock_comprehensive",
        description="단일 종목의 종합 분석(가격/펀더멘털/기술적 지표)을 반환한다.",
        args=(ToolArg("ticker", "string", required=True, description="단일 티커."),),
        fn=_t_stock_comprehensive,
    ),
    ToolSpec(
        name="stock_signal",
        description="단일 종목의 매수/보유/매도 시그널과 근거를 반환한다.",
        args=(ToolArg("ticker", "string", required=True, description="단일 티커."),),
        fn=_t_stock_signal,
    ),
    ToolSpec(
        name="news_sentiment",
        description="콤마 구분 티커들의 최근 N일 뉴스 센티먼트(긍정/부정/중립 분포)를 반환한다.",
        args=(
            ToolArg("tickers", "string", required=True, description="콤마 구분 티커."),
            ToolArg("lookback_days", "int", required=False, default=7, description="조회 기간(일)."),
        ),
        fn=_t_news_sentiment,
    ),
    ToolSpec(
        name="market_condition",
        description="현재 시장 국면(Bull / Bear / Neutral)과 SPY 60일 수익률을 반환한다.",
        args=(),
        fn=_t_market_condition,
    ),
    # ---- Discovery (FR-C-B09 ~ B11): cold-start 추천 보강 ----
    ToolSpec(
        name="propose_tickers",
        description="테마 키워드만 받아 후보 종목 티커 리스트를 빠르게 반환한다 (랭킹 미포함).",
        args=(
            ToolArg("theme", "string", required=True,
                    description="테마명. 예: 'AI semiconductor', '2차전지'"),
        ),
        fn=_t_propose_tickers,
    ),
    ToolSpec(
        name="dip_candidates",
        description="저점 매수(딥) 후보 발굴 — 180일 최대낙폭 + 모멘텀 회복을 본다. theme 또는 tickers 중 하나 필수.",
        args=(
            ToolArg("theme", "string", required=False, default=None,
                    description="테마명 (예: 'AI'). tickers 미지정 시 필수."),
            ToolArg("tickers", "string", required=False, default=None,
                    description="콤마 구분 티커. theme 미지정 시 필수."),
            ToolArg("top_n", "int", required=False, default=5,
                    description="상위 후보 수."),
            ToolArg("drawdown_min", "float", required=False, default=0.2,
                    description="최소 낙폭 (0.2 = -20%). 너무 강한 종목은 제외."),
        ),
        fn=_t_dip_candidates,
    ),
    ToolSpec(
        name="watchlist_signals",
        description="저장된 워치리스트의 모든 종목을 자동 스캔해 멀티팩터 점수로 랭킹한다.",
        args=(
            ToolArg("top_n", "int", required=False, default=None,
                    description="상위 N개만 반환. 미지정 시 전체."),
        ),
        fn=_t_watchlist_signals,
    ),
    # ---- 한국 주식 전용 (FR-K14/K15) ----
    ToolSpec(
        name="propose_themes_kr",
        description="한국 시장의 큐레이션된 투자 테마 목록을 반환한다 (2차전지/원전/AI반도체/조선/바이오 등).",
        args=(),
        fn=lambda: _kr_list_themes(),
    ),
    ToolSpec(
        name="analyze_theme_kr",
        description="한국 테마(예: '2차전지', 'AI반도체')의 대표 종목들을 멀티팩터 점수로 랭킹한다.",
        args=(
            ToolArg("theme", "string", required=True, description="한국 테마 이름."),
            ToolArg("top_n", "int", required=False, default=5, description="상위 N개."),
        ),
        fn=lambda theme, top_n=5: _kr_analyze_theme(theme, top_n),
    ),
    ToolSpec(
        name="dart_filings",
        description="한국 상장사의 최근 DART 공시 목록을 반환한다 (제목/일자/유형/URL).",
        args=(
            ToolArg("ticker", "string", required=True, description="6자리 KRX 코드 또는 .KS/.KQ 포함."),
            ToolArg("days", "int", required=False, default=30, description="조회 기간(일)."),
        ),
        fn=lambda ticker, days=30: _kr_dart_filings(ticker, days),
    ),
)


def _kr_list_themes() -> Any:
    from mcp_server.tools.kr_themes import list_themes
    return {"themes": list_themes()}


def _kr_analyze_theme(theme: str, top_n: int = 5) -> Any:
    from mcp_server.tools.kr_themes import propose_tickers_kr
    from api.routers.stock import _run_factor_ranking

    tickers = propose_tickers_kr(theme) or []
    if not tickers:
        return {"theme": theme, "rankings": [], "note": "테마를 찾을 수 없습니다."}
    return {"theme": theme, "rankings": _run_factor_ranking(tickers[:top_n])}


def _kr_dart_filings(ticker: str, days: int = 30) -> Any:
    from mcp_server.tools.dart import get_dart_client
    from mcp_server.tools.kr_ticker_resolver import resolve_korean_ticker
    ticker = resolve_korean_ticker(ticker)
    client = get_dart_client()
    if not client.ready:
        return {"ticker": ticker, "filings": [], "note": "DART 키 미설정"}
    return {"ticker": ticker, "filings": client.get_filings(ticker, days=days)}

TOOL_REGISTRY: dict[str, ToolSpec] = {t.name: t for t in TOOL_SPECS}


def execute_tool(name: str, args: dict[str, Any]) -> tuple[bool, Any]:
    """Run one tool. Returns ``(ok, result_or_error_string)``.

    All exceptions are caught — the LLM should see the failure and decide
    whether to retry, ask the user, or apologise. We never raise out of
    this function because that would abort the chat loop.
    """
    spec = TOOL_REGISTRY.get(name)
    if spec is None:
        return False, f"unknown tool: {name}"
    try:
        # Filter kwargs to declared args only (defensive against hallucinated keys).
        allowed = {a.name for a in spec.args}
        clean_kwargs = {k: v for k, v in args.items() if k in allowed}
        # Apply defaults for missing optional args.
        for a in spec.args:
            if not a.required and a.name not in clean_kwargs and a.default is not None:
                clean_kwargs[a.name] = a.default
        result = spec.fn(**clean_kwargs)
        return True, result
    except Exception as e:  # noqa: BLE001 — chatbot must never crash on tool error
        logger.warning("tool %s failed: %s", name, e)
        return False, f"{type(e).__name__}: {e}"


def summarize_result(result: Any, max_chars: int = 200) -> str:
    """Compact preview for the UI trace panel."""
    try:
        if isinstance(result, dict) and "rankings" in result:
            n = len(result.get("rankings") or [])
            return f"{n} rankings"
        if isinstance(result, list):
            return f"{len(result)} items"
        s = json.dumps(result, ensure_ascii=False, default=str)
    except Exception:
        s = str(result)
    return s[:max_chars] + ("…" if len(s) > max_chars else "")
