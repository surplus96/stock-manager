"""Centralized application settings (pydantic-settings).

FR-B05: PM_MCP_ROOT hardcoding removal.
FR-B14: GEMINI_MODEL naming normalization.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal


try:
    from pydantic import Field
    from pydantic_settings import BaseSettings, SettingsConfigDict
    _HAS_PYDANTIC_SETTINGS = True
except ImportError:  # pragma: no cover - fallback for environments without pydantic-settings
    _HAS_PYDANTIC_SETTINGS = False


if _HAS_PYDANTIC_SETTINGS:

    class Settings(BaseSettings):
        """Stock Manager backend settings loaded from env / .env."""

        # Paths
        pm_mcp_root: Path = Field(
            default=Path(__file__).resolve().parent.parent,
            description="Root of the PM-MCP codebase to add to sys.path",
        )

        # LLM
        gemini_api_key: str = Field(default="", description="Google AI Studio API key")
        gemini_model: str = Field(
            default="gemma-4-26b-a4b-it",
            description="Gemini/Gemma model id (formerly GEMMA_MODEL)",
        )
        llm_timeout_sec: int = Field(default=300, ge=10, le=600)

        # Security / networking
        allowed_origins: list[str] = Field(
            default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"],
            description="CORS allow_origins (comma-separated in env)",
        )
        # Dashboard Market Overview fans out ~15 parallel requests per load;
        # bumped from 60 so HMR reloads and multi-tab use don't trip the limiter.
        rate_limit_per_min: int = Field(default=240, ge=1)
        rate_limit_analysis_per_min: int = Field(default=10, ge=1)

        # Chat-bot + analysis-report shared model (FR-P01).
        # 2026-04-23: rolled back to ``gemini-2.5-flash`` after live probe
        # confirmed ``gemini-3.0-flash`` returns 404 on the v1beta endpoint
        # (model not GA on this API tier yet). Every chat call previously
        # ate a wasted round-trip + ``not found, skipping`` log line before
        # the resilient wrapper advanced to 2.5; pinning directly at 2.5
        # removes that overhead and uses 2.0 only as a 503 fallback.
        default_chat_model: str = Field(default="gemini-2.5-flash")
        chat_use_preview: bool = Field(default=False)

        # Ops
        log_level: str = Field(default="INFO")
        environment: Literal["dev", "staging", "prod"] = Field(default="dev")

        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
            case_sensitive=False,
        )

        @classmethod
        def _parse_origins(cls, raw: str | list[str]) -> list[str]:
            if isinstance(raw, list):
                return raw
            return [o.strip() for o in raw.split(",") if o.strip()]

else:  # Minimal stdlib fallback so server can still boot without pydantic-settings

    class Settings:  # type: ignore[no-redef]
        def __init__(self) -> None:
            self.pm_mcp_root = Path(os.getenv("PM_MCP_ROOT", str(Path(__file__).resolve().parent.parent)))
            self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
            self.gemini_model = os.getenv("GEMINI_MODEL", os.getenv("GEMMA_MODEL", "gemma-4-26b-a4b-it"))
            self.llm_timeout_sec = int(os.getenv("LLM_TIMEOUT_SEC", "300"))
            raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
            self.allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
            self.rate_limit_per_min = int(os.getenv("RATE_LIMIT_PER_MIN", "240"))
            self.rate_limit_analysis_per_min = int(os.getenv("RATE_LIMIT_ANALYSIS_PER_MIN", "10"))
            self.log_level = os.getenv("LOG_LEVEL", "INFO")
            self.environment = os.getenv("ENVIRONMENT", "dev")
            self.default_chat_model = os.getenv("CHAT_MODEL", "gemini-2.5-flash")
            self.chat_use_preview = os.getenv("CHAT_USE_PREVIEW", "0") in ("1", "true", "yes")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
