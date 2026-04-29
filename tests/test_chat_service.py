"""Unit tests for chat parser + tool dispatch (no LLM, no network)."""
from __future__ import annotations

import pytest

from api.services.chat_service import build_system_prompt, parse_tool_call
from api.services.chat_tools import (
    TOOL_REGISTRY,
    execute_tool,
    summarize_result,
)


# ---- parse_tool_call ----

def test_parse_tool_call_plain_json():
    txt = '{"tool": "rank_stocks", "args": {"tickers": "AAPL,MSFT"}}'
    out = parse_tool_call(txt)
    assert out == {"tool": "rank_stocks", "args": {"tickers": "AAPL,MSFT"}}


def test_parse_tool_call_with_code_fence():
    txt = '```json\n{"tool": "market_condition", "args": {}}\n```'
    out = parse_tool_call(txt)
    assert out == {"tool": "market_condition", "args": {}}


def test_parse_tool_call_returns_none_for_prose():
    assert parse_tool_call("AAPL은 매수 의견입니다. ROE 30% 수준.") is None


def test_parse_tool_call_returns_none_for_invalid_json():
    assert parse_tool_call('{"tool": broken json') is None


def test_parse_tool_call_missing_args_defaults_to_empty():
    out = parse_tool_call('{"tool": "market_condition"}')
    assert out == {"tool": "market_condition", "args": {}}


# ---- system prompt ----

def test_system_prompt_lists_all_tools():
    prompt = build_system_prompt()
    for name in TOOL_REGISTRY.keys():
        assert name in prompt
    assert "JSON" in prompt
    assert "한국어" in prompt


# ---- tool dispatch ----

def test_execute_tool_unknown_returns_error():
    ok, msg = execute_tool("nonexistent_tool", {})
    assert ok is False
    assert "unknown tool" in msg


def test_execute_tool_filters_unknown_kwargs():
    """Hallucinated kwargs must not crash the dispatch."""
    # market_condition takes no args; LLM passes garbage → ignored
    ok, _ = execute_tool("market_condition", {"foo": "bar", "baz": 1})
    # ok may be True or False depending on whether yfinance is reachable;
    # the important contract is that it does not raise TypeError.
    assert ok in (True, False)


# ---- summarize_result ----

def test_summarize_rankings():
    out = summarize_result({"rankings": [{"a": 1}, {"a": 2}]})
    assert out == "2 rankings"


def test_summarize_list():
    out = summarize_result(["x", "y", "z"])
    assert out == "3 items"


def test_summarize_truncates_long_string():
    big = {"data": "x" * 1000}
    out = summarize_result(big, max_chars=50)
    assert len(out) <= 51 + 1  # 50 + ellipsis
    assert out.endswith("…")


# ---- Discovery tools (FR-C-B09 ~ B11) ----

def test_discovery_tools_registered():
    """Cold-start recommendation tools must appear in the registry."""
    for name in ("propose_tickers", "dip_candidates", "watchlist_signals"):
        assert name in TOOL_REGISTRY, f"missing tool: {name}"


def test_discovery_tools_in_system_prompt():
    """The LLM must see the discovery tools to be able to call them."""
    prompt = build_system_prompt()
    assert "propose_tickers" in prompt
    assert "dip_candidates" in prompt
    assert "watchlist_signals" in prompt


def test_dip_candidates_requires_theme_or_tickers():
    """Without inputs the tool must return a clear error, not raise."""
    ok, result = execute_tool("dip_candidates", {})
    assert ok is True  # execute_tool succeeds; the *payload* signals the issue
    assert isinstance(result, dict)
    assert "error" in result


def test_is_transient_detects_503():
    from api.services.chat_service import _is_transient_upstream_error
    assert _is_transient_upstream_error(Exception("503 Server Error: Service Unavailable")) is True
    assert _is_transient_upstream_error(Exception("429 Too Many Requests")) is True
    assert _is_transient_upstream_error(Exception("Connection reset by peer")) is True
    assert _is_transient_upstream_error(ValueError("bad payload")) is False


def test_friendly_llm_error_for_503():
    from api.services.chat_service import _friendly_llm_error
    msg = _friendly_llm_error(Exception("503 Server Error: Service Unavailable"))
    assert "일시적으로" in msg
    assert "GEMINI_MODEL" in msg


def test_friendly_llm_error_for_other():
    from api.services.chat_service import _friendly_llm_error
    msg = _friendly_llm_error(ValueError("bad payload"))
    assert "LLM 호출 실패" in msg
    assert "bad payload" in msg


def test_watchlist_signals_handles_missing_file():
    """When watchlist file is absent or empty, return error payload not raise."""
    ok, result = execute_tool("watchlist_signals", {})
    assert ok is True
    assert isinstance(result, dict)
    # Either gives an error or returns rankings — never crash.
    assert "error" in result or "rankings" in result
