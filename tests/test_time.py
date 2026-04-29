"""Smoke tests for core.time helpers (FR-B23/B24)."""
from __future__ import annotations

from datetime import datetime, timezone

from core.time import period_to_dates, to_utc, utcnow


def test_utcnow_is_aware() -> None:
    now = utcnow()
    assert now.tzinfo is not None
    assert now.utcoffset() == timezone.utc.utcoffset(now)


def test_to_utc_attaches_tz() -> None:
    naive = datetime(2026, 1, 1, 12, 0, 0)
    assert to_utc(naive).tzinfo == timezone.utc


def test_period_to_dates_shape() -> None:
    start, end = period_to_dates("3mo")
    assert len(start) == 10 and len(end) == 10
    assert start < end
