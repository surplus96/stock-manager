"""Unit tests for chat_events + chat_stream_service.

LLM and tool execution are stubbed so tests run offline.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest

from api.services import chat_stream_service as css
from api.services.chat_events import (
    DoneEvent,
    ErrorEvent,
    TokenEvent,
    ToolCallEvent,
    ToolResultEvent,
    parse_event,
    serialize_event,
)


# ---------- serialize_event / parse_event ----------

@pytest.mark.parametrize("event, expected_type", [
    (ToolCallEvent(tool="rank_stocks", args={"tickers": "AAPL"}, hop=1), "tool_call"),
    (ToolResultEvent(tool="rank_stocks", ok=True, summary="3 rankings", ms=120, hop=1), "tool_result"),
    (TokenEvent(text="안녕하세요"), "token"),
    (DoneEvent(hops=2, session_id="abc"), "done"),
    (ErrorEvent(message="fail", retriable=True), "error"),
])
def test_serialize_event_roundtrip(event, expected_type):
    frame = serialize_event(event)
    assert isinstance(frame, bytes)
    assert frame.startswith(b"data: ")
    assert frame.endswith(b"\n\n")
    line = frame.decode("utf-8").split("\n")[0]
    obj = parse_event(line)
    assert obj is not None
    assert obj["type"] == expected_type


def test_parse_event_rejects_non_data_line():
    assert parse_event("event: token") is None
    assert parse_event("") is None
    assert parse_event("data: not json") is None


# ---------- run_chat_stream with stubs ----------

class _FakeRequest:
    """Drop-in substitute for ``fastapi.Request`` — needs ``is_disconnected`` and ``headers``."""

    def __init__(self, disconnect_after: int | None = None, request_id: str | None = None):
        self._calls = 0
        self._limit = disconnect_after
        self.headers = {"x-request-id": request_id} if request_id else {}

    async def is_disconnected(self) -> bool:
        self._calls += 1
        if self._limit is not None and self._calls > self._limit:
            return True
        return False


def _collect(gen) -> list[dict[str, Any]]:
    """Drain an async generator of SSE frames into a list of parsed events."""

    async def _drain():
        events: list[dict[str, Any]] = []
        async for frame in gen:
            line = frame.decode("utf-8").split("\n")[0]
            obj = parse_event(line)
            if obj is not None:
                events.append(obj)
        return events

    return asyncio.run(_drain())


def test_stream_final_answer_only(monkeypatch):
    """LLM returns prose straight away → one or more token events + done."""

    async def fake_iter(system, prompt):
        for chunk in ["AAPL은 ", "매수 의견입니다. ", "ROE 30%."]:
            yield chunk

    monkeypatch.setattr(css, "_iter_llm_stream", fake_iter)

    req = _FakeRequest()
    events = _collect(css.run_chat_stream("AAPL 어때?", None, req))

    types = [e["type"] for e in events]
    # We accept either a batched token (if detection threshold fired) or
    # multiple — the contract is: at least one token before done.
    assert "token" in types
    assert types[-1] == "done"
    # The concatenated token text should match the full LLM output.
    answer = "".join(e["text"] for e in events if e["type"] == "token")
    assert "AAPL" in answer and "ROE" in answer


def test_stream_tool_call_then_answer(monkeypatch):
    """First LLM turn yields JSON tool call → tool dispatch → second LLM turn yields answer."""

    turns = [
        ['{"tool": "market_condition", "args": {}}'],  # turn 1: tool call
        ["시장은 ", "강세입니다."],                      # turn 2: final answer
    ]
    turn_idx = {"i": 0}

    async def fake_iter(system, prompt):
        chunks = turns[turn_idx["i"]]
        turn_idx["i"] += 1
        for c in chunks:
            yield c

    def fake_execute(name, args):
        assert name == "market_condition"
        return True, {"condition": "bull", "spy_60d_return": 0.05}

    monkeypatch.setattr(css, "_iter_llm_stream", fake_iter)
    monkeypatch.setattr(css, "execute_tool", fake_execute)

    events = _collect(css.run_chat_stream("지금 시장 어때?", None, _FakeRequest()))
    types = [e["type"] for e in events]

    assert "tool_call" in types
    tc = next(e for e in events if e["type"] == "tool_call")
    assert tc["tool"] == "market_condition"
    assert tc["hop"] == 1

    assert "tool_result" in types
    tr = next(e for e in events if e["type"] == "tool_result")
    assert tr["ok"] is True
    assert tr["hop"] == 1

    assert types[-1] == "done"
    final = "".join(e["text"] for e in events if e["type"] == "token")
    assert "강세" in final


def test_stream_cancellation_on_disconnect(monkeypatch):
    """When the client disconnects mid-stream the generator returns early."""

    async def fake_iter(system, prompt):
        for c in ["a", "b", "c", "d"]:
            yield c

    monkeypatch.setattr(css, "_iter_llm_stream", fake_iter)

    # Disconnect after the first disconnect check (outer loop entry).
    events = _collect(css.run_chat_stream("hi", None, _FakeRequest(disconnect_after=0)))
    # No done / no error is acceptable — the generator simply returns.
    assert all(e["type"] != "done" for e in events)


def test_stream_emits_request_id_comment(monkeypatch):
    """Design §9 — first SSE frame should carry the request id as a comment."""

    async def fake_iter(system, prompt):
        yield "ok"

    monkeypatch.setattr(css, "_iter_llm_stream", fake_iter)

    async def _drain():
        frames: list[bytes] = []
        async for f in css.run_chat_stream("hi", None, _FakeRequest(request_id="req-XYZ")):
            frames.append(f)
        return frames

    frames = asyncio.run(_drain())
    assert frames[0].startswith(b": req-id=req-XYZ")


def test_stream_llm_error_emits_error_event(monkeypatch):
    async def fake_iter(system, prompt):
        raise RuntimeError("503 Server Error: Service Unavailable")
        yield  # pragma: no cover — unreachable, keeps it a generator

    monkeypatch.setattr(css, "_iter_llm_stream", fake_iter)

    events = _collect(css.run_chat_stream("hi", None, _FakeRequest()))
    assert events[-1]["type"] == "error"
    assert events[-1]["retriable"] is True
    assert "일시적으로" in events[-1]["message"]  # friendly 503 copy
