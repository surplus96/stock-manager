"""Chat router (mcp-chatbot feature).

Exposes a tool-augmented LLM chat endpoint that orchestrates the existing
MCP analysis tools. See ``api/services/chat_service.py`` for the loop and
``api/services/chat_tools.py`` for the registry.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from api.schemas.chat import ChatRequest, ChatResponseData
from api.schemas.common import Envelope
from api.services.chat_service import get_session_history, run_chat
from api.services.chat_stream_service import run_chat_stream
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Per-route rate limit (LLM cost guard) — graceful if slowapi unavailable.
try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    _limiter: Limiter | None = Limiter(key_func=get_remote_address)
    _rate_limit = _limiter.limit("20/minute")
except ImportError:
    _limiter = None
    _rate_limit = lambda f: f  # noqa: E731

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=Envelope[ChatResponseData])
@_rate_limit
def api_chat(request: Request, body: ChatRequest):
    """Tool-augmented chat turn.

    Body::

        { "message": "AI 반도체 테마 추천해줘", "session_id": null }

    Response (Envelope[ChatResponseData])::

        { "data": { "session_id": "...", "answer": "...", "trace": [...], "hops": 2 }, ... }

    Multi-turn: pass the returned ``session_id`` back to retain history
    (30-minute TTL, in-memory).
    """
    try:
        result = run_chat(body.message, body.session_id)
    except Exception as e:  # pragma: no cover — surfaced to client
        logger.exception("chat run failed")
        raise HTTPException(status_code=500, detail=f"chat error: {e}") from e
    return Envelope[ChatResponseData](data=result)


@router.get("/stream")
@_rate_limit
async def api_chat_stream(
    request: Request,
    message: str = Query(..., min_length=1, max_length=2000),
    session_id: str | None = Query(default=None),
):
    """SSE streaming chat (mcp-chatbot-streaming).

    Response is ``text/event-stream`` with one JSON object per frame.
    See ``api/services/chat_events.py`` for the discriminated-union schema.

    The frontend should consume with ``fetch`` + ``ReadableStream`` rather
    than ``EventSource`` (query-only, no POST body needed — EventSource
    works too, but fetch gives us ``AbortController`` cancellation).
    """
    generator = run_chat_stream(message, session_id, request)
    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",  # disable proxy buffering (nginx)
        "Connection": "keep-alive",
    }
    return StreamingResponse(generator, media_type="text/event-stream", headers=headers)


@router.get("/metrics", response_model=Envelope[dict])
def api_chat_metrics():
    """FR-P10 — lightweight in-memory metrics snapshot for ops dashboards."""
    from api.services.chat_metrics import snapshot
    return Envelope[dict](data=snapshot())


@router.get("/session/{session_id}", response_model=Envelope[dict])
def api_chat_session(session_id: str):
    """Debug helper — return the transcript for an active session."""
    history = get_session_history(session_id)
    if history is None:
        raise HTTPException(status_code=404, detail="session not found or expired")
    return Envelope[dict](data={"session_id": session_id, "messages": history})
