"""Chat domain schemas (mcp-chatbot feature).

The chatbot wraps a prompt-based tool-calling loop around the existing
MCP analysis tools so the same domain logic that powers the REST routers
(`/api/theme/*`, `/api/stock/*`, …) is reachable through natural-language
queries.

Wire format::

    POST /api/chat
        { "session_id": "...", "message": "..." }
    →
    Envelope[ChatResponseData]
        { session_id, answer, trace[], hops }
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Inbound chat turn."""

    session_id: str | None = Field(
        default=None,
        description="UUID-string. Omit to start a new conversation.",
    )
    message: str = Field(
        min_length=1,
        max_length=2000,
        description="User's natural-language query (Korean or English).",
    )


class ToolTrace(BaseModel):
    """One tool invocation surfaced to the UI for transparency."""

    tool: str
    args: dict[str, Any] = Field(default_factory=dict)
    result_summary: str = Field(
        default="",
        description="First ~200 chars or row count of the tool result.",
    )
    ok: bool = True


class ChatResponseData(BaseModel):
    session_id: str
    answer: str
    trace: list[ToolTrace] = Field(default_factory=list)
    hops: int = 0
    # FR-PSP-F — Perplexity-style follow-up chips. Empty default keeps every
    # existing client unchanged; new clients render them under the
    # assistant bubble.
    suggested: list[str] = Field(default_factory=list)
