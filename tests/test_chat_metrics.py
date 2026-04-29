"""Unit tests for chat_metrics + resilient LLM helper relocation (FR-P05/P10)."""
from __future__ import annotations

import pytest

from api.services import chat_metrics


@pytest.fixture(autouse=True)
def _reset_metrics():
    chat_metrics.reset()
    yield
    chat_metrics.reset()


def test_metrics_snapshot_initial_state():
    snap = chat_metrics.snapshot()
    assert snap["requests"] == 0
    assert snap["tool_ok"] == 0
    assert snap["tool_err"] == 0
    assert snap["hop_avg"] == 0.0
    assert snap["latency_ms"]["p50"] == 0.0
    assert "uptime_sec" in snap


def test_metrics_records_requests_and_percentiles():
    for ms in (100, 200, 300, 400, 500):
        chat_metrics.record_request(ms, hops=1)
    snap = chat_metrics.snapshot()
    assert snap["requests"] == 5
    assert snap["hops_total"] == 5
    assert snap["hop_avg"] == 1.0
    # p50 should be near the median (~300), p95 near the top (~500)
    assert 200 <= snap["latency_ms"]["p50"] <= 400
    assert snap["latency_ms"]["p95"] >= 400


def test_metrics_tool_success_and_error_rate():
    for _ in range(7):
        chat_metrics.record_tool(True, 50)
    for _ in range(3):
        chat_metrics.record_tool(False, 80)
    snap = chat_metrics.snapshot()
    assert snap["tool_ok"] == 7
    assert snap["tool_err"] == 3
    assert snap["tool_error_rate"] == pytest.approx(0.3, abs=1e-6)


def test_metrics_llm_errors_separately_tracked():
    chat_metrics.record_llm_error()
    chat_metrics.record_llm_error()
    assert chat_metrics.snapshot()["llm_errors"] == 2


# ---- FR-P05: call_llm_resilient moved to llm.py ----

def test_call_llm_resilient_is_exported_from_llm():
    """Anyone importing from ``mcp_server.tools.llm`` should get the helper."""
    from mcp_server.tools.llm import call_llm_resilient, is_transient_upstream_error
    assert callable(call_llm_resilient)
    assert callable(is_transient_upstream_error)


def test_call_llm_resilient_raises_non_transient_immediately(monkeypatch):
    """Auth errors must not be retried / fallen back on."""
    from mcp_server.tools import llm as llm_mod

    call_count = {"n": 0}

    def fake_call(system, user, temperature=0.2, model=None, **kwargs):
        call_count["n"] += 1
        raise ValueError("API key invalid")  # not transient

    # call_llm_resilient now drives `_call_gemma_no_retry` directly so we
    # don't double-burn quota on top of the tenacity decorator.
    monkeypatch.setattr(llm_mod, "_call_gemma_no_retry", fake_call)
    with pytest.raises(ValueError):
        llm_mod.call_llm_resilient("s", "u", model="x", fallback_models=["y", "z"])
    assert call_count["n"] == 1  # no retries, no fallback


def test_call_llm_resilient_falls_back_to_next_model(monkeypatch):
    """503 on primary should cycle to the next model in the chain."""
    from mcp_server.tools import llm as llm_mod

    tried: list[str] = []

    def fake_call(system, user, temperature=0.2, model=None, **kwargs):
        tried.append(model or "")
        if model == "primary":
            raise RuntimeError("503 Service Unavailable")
        return f"answer from {model}"

    # Shorten retry budget so the test isn't slow.
    monkeypatch.setattr(llm_mod, "_LLM_INNER_RETRIES", 0)
    monkeypatch.setattr(llm_mod, "_LLM_RETRY_BACKOFF_SEC", 0.0)
    monkeypatch.setattr(llm_mod, "_call_gemma_no_retry", fake_call)

    out = llm_mod.call_llm_resilient(
        "s", "u", model="primary", fallback_models=["secondary"],
    )
    assert out == "answer from secondary"
    assert tried == ["primary", "secondary"]


def test_call_llm_resilient_skips_same_model_retry_on_429(monkeypatch):
    """429 should advance to the next fallback without re-hitting primary."""
    from mcp_server.tools import llm as llm_mod

    tried: list[str] = []

    def fake_call(system, user, temperature=0.2, model=None, **kwargs):
        tried.append(model or "")
        if model == "primary":
            raise RuntimeError("429 Too Many Requests")
        return f"answer from {model}"

    monkeypatch.setattr(llm_mod, "_LLM_INNER_RETRIES", 3)  # would normally retry
    monkeypatch.setattr(llm_mod, "_LLM_RETRY_BACKOFF_SEC", 0.0)
    monkeypatch.setattr(llm_mod, "_call_gemma_no_retry", fake_call)

    out = llm_mod.call_llm_resilient(
        "s", "u", model="primary", fallback_models=["secondary"],
    )
    assert out == "answer from secondary"
    # primary tried once, secondary once — no same-model retries
    assert tried == ["primary", "secondary"]
