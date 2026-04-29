"""Health + circuit-status router (FR-B07, FR-B19)."""
from __future__ import annotations

from fastapi import APIRouter

from api.schemas.common import HealthResponse
from core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    s = get_settings()
    return HealthResponse(status="ok", version="1.1.0", environment=str(s.environment))


@router.get("/health/detail")
def health_detail() -> dict:
    """Detailed health probe — includes circuit breaker status."""
    s = get_settings()
    payload: dict = {
        "status": "ok",
        "version": "1.1.0",
        "environment": str(s.environment),
        "llm_timeout_sec": s.llm_timeout_sec,
        "rate_limit_per_min": s.rate_limit_per_min,
    }
    try:
        from mcp_server.tools.resilience import get_all_circuit_status
        payload["circuits"] = get_all_circuit_status()
    except Exception:  # noqa: BLE001
        payload["circuits"] = {}
    return payload
