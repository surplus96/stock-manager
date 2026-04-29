"""Streaming chat orchestration (mcp-chatbot-streaming).

Turns the tool-calling loop from ``chat_service.run_chat`` into an
``AsyncIterator[bytes]`` that emits SSE frames. Re-uses:

    * ``build_system_prompt`` / ``build_transcript`` from chat_service
    * ``_get_or_create_session`` for session memory + TTL
    * ``parse_tool_call`` for JSON tool-call detection
    * ``execute_tool`` + ``summarize_result`` for dispatch

Event order per turn::

    tool_call      (0..MAX_HOPS times, interleaved with)
    tool_result
    ...
    token          (one or many, final answer chunks)
    done

Cancellation: the generator checks ``await request.is_disconnected()``
between hops and between streamed chunks. When the client disconnects the
generator returns early and the session transcript is NOT updated with a
partial answer.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import AsyncIterator

from fastapi import Request

from api.services import chat_metrics
from api.services.chat_events import (
    ChatEvent,
    DoneEvent,
    ErrorEvent,
    TokenEvent,
    ToolCallEvent,
    ToolResultEvent,
    serialize_event,
)
from api.services.chat_service import (
    MAX_HOPS,
    _friendly_llm_error,
    _get_or_create_session,
    build_system_prompt,
    build_transcript,
    parse_tool_call,
)
from api.services.chat_tools import execute_tool, summarize_result

logger = logging.getLogger(__name__)

# How many characters to buffer before deciding "this is an answer, not a
# tool call" and flipping to token-streaming mode. A valid JSON tool call
# is always <<512 chars in practice.
_TOOL_DETECT_THRESHOLD = 512


def _artifact_from_tool_result(tool: str, result: Any) -> list[dict] | None:
    """Convert a tool's return value into ``ReportBlock`` dicts when we can.

    Only a handful of tools benefit from structured rendering; everything
    else falls through to None and the summary string does the job.
    """
    try:
        from api.services.report_builder import rankings_to_table, build_radar_mini

        blocks: list[dict] = []
        if tool in ("rank_stocks", "analyze_theme", "analyze_theme_kr", "watchlist_signals"):
            rankings = None
            if isinstance(result, dict):
                rankings = result.get("rankings")
            if isinstance(rankings, list) and rankings:
                blocks.append(rankings_to_table(rankings).model_dump())
                # Radar of the top entry (most informative at a glance).
                top_factors = (rankings[0] or {}).get("factors") or {}
                radar = build_radar_mini(top_factors)
                if radar:
                    blocks.append(radar.model_dump())
        elif tool == "stock_comprehensive" and isinstance(result, dict):
            from api.services.report_builder import build_radar_mini
            factors = (result.get("factors") or {})
            radar = build_radar_mini(factors)
            if radar:
                blocks.append(radar.model_dump())
        return blocks or None
    except Exception:  # noqa: BLE001
        return None


async def _sleep(ms: float) -> None:
    await asyncio.sleep(ms / 1000.0)


async def _iter_llm_stream(system: str, prompt: str):
    """Async wrapper over the blocking ``_call_gemma_stream`` generator.

    The underlying Gemini SSE consumer uses ``requests``, which is blocking;
    we run each ``next(gen)`` in a threadpool so the event loop stays
    responsive for disconnect polling. FR-P01: pin chat requests to
    ``settings.default_chat_model`` so preview models on ``GEMINI_MODEL``
    don't leak into the chat experience.
    """
    from mcp_server.tools.llm import _call_gemma_stream
    from core.config import get_settings

    loop = asyncio.get_running_loop()
    gen = _call_gemma_stream(system, prompt, model=get_settings().default_chat_model)

    def _next():
        try:
            return next(gen)
        except StopIteration:
            return None

    while True:
        chunk = await loop.run_in_executor(None, _next)
        if chunk is None:
            return
        yield chunk


async def run_chat_stream(
    message: str, session_id: str | None, request: Request
) -> AsyncIterator[bytes]:
    sid, sess = _get_or_create_session(session_id)
    sess.messages.append({"role": "user", "content": message})

    system = build_system_prompt()
    hops = 0
    final_answer_parts: list[str] = []
    t_request_start = time.monotonic()

    # Per design §9 — emit a leading SSE comment carrying the request id
    # for log correlation. Comments start with ":" and are ignored by SSE
    # parsers (including our own ``sseClient.ts``).
    req_id = request.headers.get("x-request-id") if hasattr(request, "headers") else None
    if not req_id and hasattr(request, "state"):
        req_id = getattr(request.state, "request_id", None)
    if req_id:
        yield f": req-id={req_id}\n\n".encode("utf-8")

    async def emit(ev: ChatEvent) -> bytes:
        return serialize_event(ev)

    # Outer loop — repeated hops until we commit to a final answer
    for _ in range(MAX_HOPS + 1):
        if await request.is_disconnected():
            return

        prompt = build_transcript(sess.messages, "")
        buffer = ""
        decided_answer = False
        tool_call_detected: dict | None = None

        try:
            async for chunk in _iter_llm_stream(system, prompt):
                if await request.is_disconnected():
                    return

                buffer += chunk

                if not decided_answer and tool_call_detected is None:
                    # Try to detect a tool call early. ``parse_tool_call``
                    # is tolerant of incomplete input; it returns None
                    # until we have a full balanced JSON object.
                    maybe = parse_tool_call(buffer)
                    if maybe is not None:
                        tool_call_detected = maybe
                        break  # stop streaming; dispatch tool
                    if len(buffer) >= _TOOL_DETECT_THRESHOLD and not buffer.lstrip().startswith("{"):
                        # Definitely not a tool call — flush what we have
                        # as tokens and keep going in answer mode.
                        decided_answer = True
                        yield await emit(TokenEvent(text=buffer))
                        final_answer_parts.append(buffer)
                        buffer = ""
                        continue

                if decided_answer:
                    # Answer mode — forward each chunk immediately.
                    yield await emit(TokenEvent(text=chunk))
                    final_answer_parts.append(chunk)

        except Exception as e:  # noqa: BLE001
            logger.warning("LLM stream failed: %s", e)
            yield await emit(ErrorEvent(
                message=_friendly_llm_error(e),
                retriable=True,
            ))
            return

        # End of stream — decide what to do with the buffer.
        if tool_call_detected is not None:
            if hops >= MAX_HOPS:
                yield await emit(ErrorEvent(
                    message="도구 호출 한도(5회)에 도달했습니다. 질문을 좁혀서 다시 시도해 주세요.",
                    retriable=False,
                ))
                return
            hops += 1
            call = tool_call_detected
            yield await emit(ToolCallEvent(tool=call["tool"], args=call["args"], hop=hops))

            if await request.is_disconnected():
                return

            start = time.monotonic()
            ok, result = await asyncio.get_running_loop().run_in_executor(
                None, execute_tool, call["tool"], call["args"]
            )
            ms = int((time.monotonic() - start) * 1000)
            chat_metrics.record_tool(ok, ms)
            logger.info(
                "chat.stream.hop session=%s hop=%d tool=%s ok=%s latency_ms=%d",
                sid, hops, call["tool"], ok, ms,
            )
            summary = summarize_result(result) if ok else f"ERROR: {result}"
            # rich-visual-reports: turn ranking/theme results into a
            # structured artifact so ArtifactPanel can render a sortable
            # table + radar instead of a bare summary string.
            artifact = _artifact_from_tool_result(call["tool"], result) if ok else None
            yield await emit(ToolResultEvent(
                tool=call["tool"], ok=ok, summary=summary, ms=ms, hop=hops,
                artifact=artifact,
            ))

            # Feed observation back to the model transcript and loop again.
            observation = json.dumps(
                {"tool": call["tool"], "ok": ok, "result": result},
                ensure_ascii=False,
                default=str,
            )
            if len(observation) > 8000:
                observation = observation[:8000] + " …(truncated)"
            sess.messages.append({"role": "tool", "content": observation})
            continue

        # No tool call — commit buffer as the final answer.
        if buffer and not decided_answer:
            yield await emit(TokenEvent(text=buffer))
            final_answer_parts.append(buffer)

        final_answer = "".join(final_answer_parts).strip() or "(빈 응답)"
        # FR-PSP-F — strip the trailing <<SUGGEST>>[...] marker before we
        # commit the answer to session history; surface chips on DoneEvent.
        from api.services.chat_service import split_suggested_marker
        clean_answer, suggested = split_suggested_marker(final_answer)
        sess.messages.append({"role": "assistant", "content": clean_answer})
        total_ms = (time.monotonic() - t_request_start) * 1000
        chat_metrics.record_request(total_ms, hops)
        yield await emit(DoneEvent(hops=hops, session_id=sid, suggested=suggested))
        return

    # Fell out of the loop without committing — hop limit reached.
    yield await emit(ErrorEvent(
        message="도구 호출 한도에 도달해 응답을 완성할 수 없었습니다.",
        retriable=False,
    ))
