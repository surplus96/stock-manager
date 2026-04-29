"""Application-wide constants (FR-B11).

Magic numbers extracted from inline usage across routers/services/tools.
"""
from __future__ import annotations

# --- LLM / analysis ---
ANALYSIS_NEWS_LOOKBACK_DAYS: int = 7
ANALYSIS_NEWS_MAX_RESULTS: int = 5
ANALYSIS_SENTIMENT_LOOKBACK_DAYS: int = 7
ANALYSIS_PRICE_PERIOD_SHORT: str = "3mo"
ANALYSIS_PRICE_PERIOD_LONG: str = "6mo"

# --- Report limits ---
REPORT_NEWS_ITEMS_IN_SUMMARY: int = 5
REPORT_FINANCIAL_INTERPRETATIONS_MAX: int = 8
REPORT_TECHNICAL_INTERPRETATIONS_MAX: int = 6

# --- Cache / timeouts (also used in routers) ---
DEFAULT_CACHE_TTL_SEC: int = 300
NEWS_SEARCH_DEFAULT_MAX: int = 10

# --- Thread pool for parallel data collection ---
LLM_PARALLEL_MAX_WORKERS: int = 6

# --- API versioning ---
API_ENVELOPE_VERSION: str = "v1"
