"""In-memory chatbot metrics (FR-P10).

A tiny, dependency-free counter store. Not a replacement for Prometheus —
just enough to expose p50/p95 latency, tool error rate, and hop averages
through ``GET /api/chat/metrics`` so operators can see the chatbot's pulse
without trawling logs.

All public functions are safe to call from any thread (dict + deque writes
are atomic in CPython). They are intentionally fast and allocation-free in
the hot path.
"""
from __future__ import annotations

import collections
import threading
from datetime import datetime, timezone

_MAX_SAMPLES = 500


class _Store:
    __slots__ = ("lock", "requests", "hops_total", "tool_ok", "tool_err",
                 "latencies_ms", "tool_latencies_ms", "started_at", "llm_errors")

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.requests = 0
        self.hops_total = 0
        self.tool_ok = 0
        self.tool_err = 0
        self.llm_errors = 0
        self.latencies_ms: collections.deque[float] = collections.deque(maxlen=_MAX_SAMPLES)
        self.tool_latencies_ms: collections.deque[float] = collections.deque(maxlen=_MAX_SAMPLES)
        self.started_at = datetime.now(tz=timezone.utc)


_store = _Store()


def record_request(total_latency_ms: float, hops: int) -> None:
    with _store.lock:
        _store.requests += 1
        _store.hops_total += hops
        _store.latencies_ms.append(total_latency_ms)


def record_tool(ok: bool, latency_ms: float) -> None:
    with _store.lock:
        if ok:
            _store.tool_ok += 1
        else:
            _store.tool_err += 1
        _store.tool_latencies_ms.append(latency_ms)


def record_llm_error() -> None:
    with _store.lock:
        _store.llm_errors += 1


def _percentile(samples: collections.deque[float], pct: float) -> float:
    if not samples:
        return 0.0
    sorted_s = sorted(samples)
    k = max(0, min(len(sorted_s) - 1, int(round((pct / 100.0) * (len(sorted_s) - 1)))))
    return float(sorted_s[k])


def snapshot() -> dict:
    """Return a JSON-serialisable view of the current counters."""
    with _store.lock:
        lat = list(_store.latencies_ms)
        tlat = list(_store.tool_latencies_ms)
        total_tools = _store.tool_ok + _store.tool_err
        now = datetime.now(tz=timezone.utc)
        return {
            "requests": _store.requests,
            "hops_total": _store.hops_total,
            "hop_avg": (_store.hops_total / _store.requests) if _store.requests else 0.0,
            "tool_ok": _store.tool_ok,
            "tool_err": _store.tool_err,
            "tool_error_rate": (_store.tool_err / total_tools) if total_tools else 0.0,
            "llm_errors": _store.llm_errors,
            "latency_ms": {
                "p50": _percentile(collections.deque(lat), 50),
                "p95": _percentile(collections.deque(lat), 95),
                "samples": len(lat),
            },
            "tool_latency_ms": {
                "p50": _percentile(collections.deque(tlat), 50),
                "p95": _percentile(collections.deque(tlat), 95),
                "samples": len(tlat),
            },
            "uptime_sec": (now - _store.started_at).total_seconds(),
            "started_at": _store.started_at.isoformat(),
        }


def reset() -> None:
    """Test helper — wipes counters. Do not call in production paths."""
    global _store
    _store = _Store()
