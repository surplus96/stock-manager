"""Server bootstrap smoke tests (FR-B24).

Assert:
- App object is importable
- 8 OpenAPI tags are present
- CORS middleware is registered
"""
from __future__ import annotations

import pytest


def test_app_importable() -> None:
    from api.server import app
    assert app is not None
    assert app.title == "Stock Manager API"


def test_openapi_tags_count() -> None:
    from api.server import app, OPENAPI_TAGS
    assert len(OPENAPI_TAGS) >= 8, f"Expected >=8 tags, got {len(OPENAPI_TAGS)}"
    tag_names = {t["name"] for t in OPENAPI_TAGS}
    required = {"health", "market", "stock", "portfolio", "ranking", "theme", "analysis", "news"}
    missing = required - tag_names
    assert not missing, f"Missing tags: {missing}"


def test_cors_middleware_registered() -> None:
    from fastapi.middleware.cors import CORSMiddleware
    from api.server import app

    middleware_types = [type(m.cls) if hasattr(m, "cls") else type(m) for m in app.user_middleware]
    # CORSMiddleware is added via add_middleware so it shows up in user_middleware
    cors_found = any(
        "CORSMiddleware" in str(m) for m in app.user_middleware
    )
    assert cors_found, f"CORSMiddleware not found in middleware stack: {app.user_middleware}"


def test_routers_mounted() -> None:
    """Verify domain router prefixes appear in app routes."""
    from api.server import app

    route_paths = [str(r.path) for r in app.routes if hasattr(r, "path")]
    prefixes_expected = ["/api/market/", "/api/stock/", "/api/portfolio/", "/api/news/"]
    for prefix in prefixes_expected:
        found = any(p.startswith(prefix) for p in route_paths)
        assert found, f"No route with prefix '{prefix}' found. Routes: {route_paths[:20]}"
