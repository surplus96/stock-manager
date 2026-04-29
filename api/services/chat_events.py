"""Chat streaming event schema (mcp-chatbot-streaming).

The SSE wire format is one JSON object per frame::

    data: {"type": "tool_call", "tool": "analyze_theme", "args": {...}, "hop": 1}

    data: {"type": "token", "text": "AI 반도체 테마는..."}

    data: {"type": "done", "hops": 2, "session_id": "uuid"}

A single ``data:`` field (no ``event:`` line) keeps the JS parser trivial
and mirrors a TypeScript discriminated union on the frontend. Every event
carries a ``type`` field so the consumer can branch without cross-
referencing HTTP event names.
"""
from __future__ import annotations

import json
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field


class ToolCallEvent(BaseModel):
    type: Literal["tool_call"] = "tool_call"
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)
    hop: int


class ToolResultEvent(BaseModel):
    type: Literal["tool_result"] = "tool_result"
    tool: str
    ok: bool
    summary: str
    ms: int
    hop: int
    # rich-visual-reports FR-R-B06: structured artifact (report blocks) so
    # the chat UI can render tables / mini-radars / candlesticks instead of
    # the raw summary string. Optional — if missing, clients fall back to
    # the summary.
    artifact: Optional[list[dict[str, Any]]] = None


class TokenEvent(BaseModel):
    type: Literal["token"] = "token"
    text: str


class DoneEvent(BaseModel):
    type: Literal["done"] = "done"
    hops: int
    session_id: str
    # FR-PSP-F — follow-up chips for Perplexity-style retention. Empty
    # default means existing clients ignore the field.
    suggested: list[str] = Field(default_factory=list)


class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    message: str
    retriable: bool = False


ChatEvent = Union[ToolCallEvent, ToolResultEvent, TokenEvent, DoneEvent, ErrorEvent]


def serialize_event(event: ChatEvent) -> bytes:
    """Encode one event as a single SSE frame (``data: <json>\\n\\n``)."""
    body = event.model_dump_json()
    return f"data: {body}\n\n".encode("utf-8")


def parse_event(line: str) -> dict[str, Any] | None:
    """Best-effort decoder used by tests. ``None`` on malformed frames."""
    if not line.startswith("data: "):
        return None
    payload = line[len("data: "):].strip()
    try:
        obj = json.loads(payload)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        return None
