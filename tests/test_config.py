"""Smoke tests for core.config (FR-B24)."""
from __future__ import annotations

import importlib
import os

import pytest


def _reload_config():
    import core.config as cfg
    importlib.reload(cfg)
    cfg.get_settings.cache_clear()  # type: ignore[attr-defined]
    return cfg


def test_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for k in ("ALLOWED_ORIGINS", "RATE_LIMIT_PER_MIN", "LLM_TIMEOUT_SEC", "GEMINI_MODEL"):
        monkeypatch.delenv(k, raising=False)
    cfg = _reload_config()
    s = cfg.get_settings()
    assert s.llm_timeout_sec >= 10
    assert s.rate_limit_per_min >= 1
    assert isinstance(s.allowed_origins, list)
    assert s.allowed_origins, "default origins must be non-empty"


def test_settings_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_TIMEOUT_SEC", "120")
    monkeypatch.setenv("RATE_LIMIT_PER_MIN", "30")
    cfg = _reload_config()
    s = cfg.get_settings()
    assert s.llm_timeout_sec == 120
    assert s.rate_limit_per_min == 30


def test_settings_is_singleton() -> None:
    from core.config import get_settings
    assert get_settings() is get_settings()
