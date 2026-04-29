"""TestClient tests for health router (FR-B24).

Asserts /health and /health/detail return expected shapes.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from api.server import app
    return TestClient(app, raise_server_exceptions=False)


def test_health_ok(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_health_detail_ok(client: TestClient) -> None:
    resp = client.get("/health/detail")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "environment" in data
    # circuit key present (may be empty dict if resilience unavailable)
    assert "circuits" in data


def test_health_has_version_field(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("version") is not None
