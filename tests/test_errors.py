"""Smoke tests for core.errors exception handlers (FR-B24)."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.errors import (
    AppError,
    NotFoundError,
    UpstreamError,
    ValidationAppError,
    install_exception_handlers,
)


def _make_app() -> FastAPI:
    app = FastAPI()
    install_exception_handlers(app)

    @app.get("/boom-app")
    def _boom_app() -> dict:
        raise AppError("generic app error")

    @app.get("/boom-404")
    def _boom_404() -> dict:
        raise NotFoundError("missing thing")

    @app.get("/boom-validation")
    def _boom_val() -> dict:
        raise ValidationAppError("bad field", details={"field": "ticker"})

    @app.get("/boom-upstream")
    def _boom_up() -> dict:
        raise UpstreamError("gateway down")

    @app.get("/boom-unknown")
    def _boom_unknown() -> dict:
        raise RuntimeError("unexpected")

    return app


def test_app_error_envelope() -> None:
    client = TestClient(_make_app())
    r = client.get("/boom-app")
    assert r.status_code == 500
    body = r.json()
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert body["error"]["message"] == "generic app error"


def test_not_found_error() -> None:
    r = TestClient(_make_app()).get("/boom-404")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


def test_validation_error_details() -> None:
    r = TestClient(_make_app()).get("/boom-validation")
    assert r.status_code == 400
    body = r.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["details"] == {"field": "ticker"}


def test_upstream_error() -> None:
    r = TestClient(_make_app()).get("/boom-upstream")
    assert r.status_code == 502
    assert r.json()["error"]["code"] == "UPSTREAM_ERROR"


def test_fallback_handler_hides_internals() -> None:
    client = TestClient(_make_app(), raise_server_exceptions=False)
    r = client.get("/boom-unknown")
    assert r.status_code == 500
    assert r.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "unexpected" not in r.text  # message must not leak
