"""
Stock Manager - FastAPI Backend
PM-MCP 도구를 REST API로 노출

Phase 1 하드닝 적용:
- FR-B01: CORS allow_origins를 환경변수 기반 허용 목록으로 제한
- FR-B04: slowapi Rate Limit — analysis 라우트에 10/minute 적용
- FR-B05: PM_MCP_ROOT 하드코딩 제거 (env / core.config)
- FR-B06: 전역 예외 핸들러 + RequestId 미들웨어
- FR-B07: 도메인별 라우터 분리 (market/stock/portfolio/ranking/theme/analysis/news)
- FR-B08: Pydantic response_model + Envelope[T] 적용
- FR-B12: structlog 스타일 구조적 로깅 (request_id)
"""
from __future__ import annotations
import sys
import os
from pathlib import Path

# Load .env from worktree root (contains API keys) — must happen before core/config import
from dotenv import load_dotenv
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(_env_path):
    load_dotenv(_env_path, override=True)

# FR-B05: PM_MCP_ROOT is resolved via core.config (env-backed, no hardcoded path).
_REPO_ROOT = Path(__file__).resolve().parent.parent
PM_MCP_ROOT = os.environ.get("PM_MCP_ROOT") or str(_REPO_ROOT)
sys.path.insert(0, PM_MCP_ROOT)
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from core.config import get_settings
from core.logging import configure_logging, get_logger
from core.errors import install_exception_handlers
from core.middleware import RequestIdMiddleware

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)

# Silence pykrx's noisy "Logging error … not all arguments converted" stack
# traces. Upstream calls ``logging.info(args, kwargs)`` at the *module*
# level (pykrx/website/comm/util.py:19) — that goes through the ROOT logger,
# not ``pykrx.*``, so a level bump on the named logger does nothing. We
# install a path-based filter on root that drops any record originating
# from that exact file. The underlying KRX hiccup ("Expecting value …") is
# handled gracefully downstream by kr_market_data's empty-frame fallback.
logging.getLogger("pykrx").setLevel(logging.WARNING)
logging.getLogger("pykrx.website").setLevel(logging.WARNING)


class _DropPyKrxLoggingBug(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        path = getattr(record, "pathname", "") or ""
        return "pykrx/website/comm/util.py" not in path


logging.getLogger().addFilter(_DropPyKrxLoggingBug())

# FR-B04: Rate limiting via slowapi (optional dependency — graceful degradation)
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    _limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[f"{settings.rate_limit_per_min}/minute"],
    )
    _RATE_LIMIT_AVAILABLE = True
except ImportError:  # pragma: no cover
    _limiter = None
    _RATE_LIMIT_AVAILABLE = False
    logger.warning("slowapi not installed; rate limiting disabled. `pip install slowapi` to enable.")

OPENAPI_TAGS = [
    {"name": "health", "description": "Liveness, readiness, circuit-breaker status"},
    {"name": "market", "description": "Market condition, prices, and snapshots"},
    {"name": "stock", "description": "Single-ticker analysis, technicals, fundamentals"},
    {"name": "portfolio", "description": "Portfolio CRUD, PnL, evaluation"},
    {"name": "ranking", "description": "Multi-factor ranking engine"},
    {"name": "theme", "description": "Market theme proposal & exploration"},
    {"name": "analysis", "description": "LLM-backed comprehensive analysis reports"},
    {"name": "news", "description": "News search & sentiment"},
    {"name": "chat", "description": "Tool-augmented LLM chatbot for theme/stock recommendations"},
    {"name": "dart", "description": "DART OPEN API — Korean corporate filings & K-IFRS financials"},
]

app = FastAPI(
    title="Stock Manager API",
    version="1.1.0",
    description=(
        "REST facade over PM-MCP tools. "
        "Envelope-style success responses (`{data, generated_at, version}`) and "
        "unified error envelope (`{error: {code, message, request_id, details}}`)."
    ),
    openapi_tags=OPENAPI_TAGS,
    contact={"name": "Stock Manager", "url": "https://example.com"},
)

# Middleware order: RequestId (outer) -> CORS -> RateLimit
app.add_middleware(RequestIdMiddleware)

# FR-B01: CORS restricted to allow_origins list; credentials only if not wildcard
_origins = settings.allowed_origins
_allow_creds = True if _origins and "*" not in _origins else False
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=_allow_creds,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# FR-B06: Unified exception handlers (AppError / ValidationError / HTTPException / fallback)
install_exception_handlers(app)

if _RATE_LIMIT_AVAILABLE:
    app.state.limiter = _limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------------------------------------------------------------------------
# FR-B07: Mount domain routers
# ---------------------------------------------------------------------------

try:
    from api.routers.health import router as health_router
    app.include_router(health_router, prefix="")
except Exception as _e:
    logger.warning("health router not mounted: %s", _e)

try:
    from api.routers.market import router as market_router
    app.include_router(market_router)
except Exception as _e:
    logger.warning("market router not mounted: %s", _e)

try:
    from api.routers.stock import router as stock_router
    app.include_router(stock_router)
except Exception as _e:
    logger.warning("stock router not mounted: %s", _e)

try:
    from api.routers.portfolio import router as portfolio_router
    app.include_router(portfolio_router)
except Exception as _e:
    logger.warning("portfolio router not mounted: %s", _e)

try:
    from api.routers.ranking import router as ranking_router
    app.include_router(ranking_router)
except Exception as _e:
    logger.warning("ranking router not mounted: %s", _e)

try:
    from api.routers.theme import router as theme_router
    app.include_router(theme_router)
except Exception as _e:
    logger.warning("theme router not mounted: %s", _e)

try:
    from api.routers.news import router as news_router
    app.include_router(news_router)
except Exception as _e:
    logger.warning("news router not mounted: %s", _e)

try:
    from api.routers.chat import router as chat_router
    app.include_router(chat_router)
except Exception as _e:
    logger.warning("chat router not mounted: %s", _e)

try:
    from api.routers.dart import router as dart_router
    app.include_router(dart_router)
except Exception as _e:
    logger.warning("dart router not mounted: %s", _e)

try:
    from api.routers.analysis import router as analysis_router
    app.include_router(analysis_router)
except Exception as _e:
    logger.warning("analysis router not mounted: %s", _e)


# ---------------------------------------------------------------------------
# Remaining inline routes (not yet extracted to domain routers)
# ---------------------------------------------------------------------------

@app.get("/api/technical/analyze", tags=["stock"])
def api_technical_analyze(ticker: str):
    from mcp_server.tools.alpha_vantage import get_technical_summary
    return get_technical_summary(ticker)


@app.get("/api/finnhub/summary", tags=["stock"])
def api_finnhub_summary(ticker: str):
    from mcp_server.tools.finnhub_api import get_finnhub_summary
    return get_finnhub_summary(ticker)


@app.get("/api/ranking/analysis-report", tags=["analysis"])
def api_ranking_analysis_report(tickers: str):
    """Ranking comprehensive analysis report."""
    from api.routers.stock import _run_factor_ranking

    ticker_list = [t.strip() for t in tickers.split(",") if t.strip()]
    rankings = _run_factor_ranking(ticker_list)

    stocks_text = "\n".join([
        f"- #{i+1} {r['ticker']}: 점수 {r.get('composite_score',0):.1f}, 시그널 {r.get('signal','N/A')}, "
        f"재무 {r.get('factors',{}).get('financial_score','N/A')}, "
        f"기술적 {r.get('factors',{}).get('technical_score','N/A')}, "
        f"성장 {r.get('factors',{}).get('growth_score','N/A')}, "
        f"퀄리티 {r.get('factors',{}).get('quality_score','N/A')}, "
        f"섹터 {r.get('sector','N/A')}"
        for i, r in enumerate(rankings)
    ])

    avg = sum(r.get("composite_score", 0) for r in rankings) / max(len(rankings), 1)
    top = rankings[0] if rankings else {}
    buys = [r["ticker"] for r in rankings if r.get("signal") in ("Strong Buy", "Buy")]
    sells = [r["ticker"] for r in rankings if r.get("signal") in ("Sell", "Strong Sell")]

    prompt = f"""[종목 비교 랭킹 리포트]

■ 비교 종목: {', '.join(ticker_list)}
■ 평균 점수: {avg:.1f}/100
■ 최우선 추천: {top.get('ticker','N/A')} ({top.get('composite_score',0):.1f})
■ 매수 시그널: {', '.join(buys) if buys else '없음'}
■ 매도 시그널: {', '.join(sells) if sells else '없음'}

■ 상세 랭킹:
{stocks_text}

위 데이터를 종합하여 비교 분석, 1위 종목의 강점, 주의 종목과 이유, 섹터 분석, 각 종목별 투자 추천을 제공하세요.
"""

    try:
        # FR-P05: route through resilient helper so 503 from preview models
        # falls back to GEMINI_FALLBACK_MODELS automatically.
        from mcp_server.tools.llm import call_llm_resilient
        system = (
            "당신은 시니어 금융 애널리스트입니다. 투자 리서치 리포트를 한국어로 작성하세요."
        )
        summary = call_llm_resilient(
            system, prompt, model=settings.default_chat_model, temperature=0.3,
        )
    except Exception as e:
        logger.warning("LLM summary failed: %s", e)
        summary = ""

    evidence = {
        "비교 종목수": str(len(rankings)),
        "평균 점수": f"{avg:.1f}/100",
        "최우선 추천": f"{top.get('ticker','N/A')} ({top.get('composite_score',0):.1f})",
        "매수 시그널": ", ".join(buys) if buys else "없음",
        "매도 시그널": ", ".join(sells) if sells else "없음",
    }
    return {
        "rankings": rankings,
        "evidence": evidence,
        "summary": summary,
    }


@app.get("/api/health", tags=["health"])
def api_health():
    return {"status": "ok", "service": "Stock Manager API"}


@app.get("/api/circuit/status", tags=["health"])
def api_circuit_status():
    from mcp_server.tools.resilience import get_all_circuit_status
    return get_all_circuit_status()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
