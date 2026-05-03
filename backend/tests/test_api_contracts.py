"""Golden-path API contracts: auth middleware, request IDs, error shape."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.subject_service import SubjectService


@pytest.fixture(autouse=True)
def reset_openapi_schema():
    app.openapi_schema = None
    yield
    app.openapi_schema = None


@pytest.fixture
def no_api_key(monkeypatch):
    import app.config as cfg

    monkeypatch.setattr(cfg.settings, "afe_api_key", "")


@pytest.fixture
def with_api_key(monkeypatch):
    import app.config as cfg

    monkeypatch.setattr(cfg.settings, "afe_api_key", "contract-test-secret")


def test_health_ok_and_skips_api_key(with_api_key):
    with TestClient(app, raise_server_exceptions=True) as client:
        res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "healthy"}
    assert res.headers.get("X-Request-ID")


def test_root_without_key_returns_401_when_api_key_configured(with_api_key):
    with TestClient(app, raise_server_exceptions=True) as client:
        res = client.get("/")
    assert res.status_code == 401
    body = res.json()
    assert body["detail"] == "Invalid or missing API key"
    assert body.get("request_id")


def test_root_with_valid_key_returns_200(with_api_key):
    with TestClient(app, raise_server_exceptions=True) as client:
        res = client.get("/", headers={"X-API-Key": "contract-test-secret"})
    assert res.status_code == 200
    assert res.json()["status"] == "running"


def test_list_subjects_contract(no_api_key):
    with TestClient(app, raise_server_exceptions=True) as client:
        res = client.get("/api/subjects")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_openapi_includes_api_key_scheme_when_configured(with_api_key):
    with TestClient(app, raise_server_exceptions=True) as client:
        res = client.get(
            "/openapi.json",
            headers={"X-API-Key": "contract-test-secret"},
        )
    assert res.status_code == 200
    spec = res.json()
    assert "ApiKeyAuth" in spec["components"]["securitySchemes"]
    assert spec["components"]["securitySchemes"]["ApiKeyAuth"]["in"] == "header"


def test_unhandled_exception_body_is_sanitized(no_api_key, monkeypatch):
    def boom(self):
        raise RuntimeError("do-not-leak-this-secret")

    monkeypatch.setattr(SubjectService, "list_subjects", boom)

    with TestClient(app, raise_server_exceptions=False) as client:
        res = client.get("/api/subjects")

    assert res.status_code == 500
    body = res.json()
    assert body["detail"] == "Internal server error"
    assert "do-not-leak" not in res.text
    assert body.get("request_id")
