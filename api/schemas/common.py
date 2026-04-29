"""Common Pydantic schemas (FR-B08, FR-B16).

Envelope and error body used by routers to standardize response shape.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from api.constants import API_ENVELOPE_VERSION

T = TypeVar("T")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ApiErrorBody(BaseModel):
    code: str
    message: str
    request_id: str
    details: dict[str, Any] = Field(default_factory=dict)


class ApiErrorEnvelope(BaseModel):
    error: ApiErrorBody


class Envelope(BaseModel, Generic[T]):
    """Unified response envelope.

    Usage::

        return Envelope[MyPayload](data=payload)
    """

    data: T
    generated_at: datetime = Field(default_factory=utcnow)
    version: str = API_ENVELOPE_VERSION


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.1.0"
    environment: str = "dev"
