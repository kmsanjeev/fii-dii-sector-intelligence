from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest


@pytest.fixture
def isolated_auth_store(monkeypatch, tmp_dir):
    from backend.auth import store

    auth_dir = tmp_dir / "auth"
    monkeypatch.setattr(store, "AUTH_DIR", auth_dir)
    monkeypatch.setattr(store, "DB_PATH", auth_dir / "users.db")
    monkeypatch.setattr(store, "CFG_PATH", auth_dir / "auth_config.json")
    for name in ["VEDA_RUNTIME_ENV", "ENVIRONMENT", "VEDA_AUTH_ENABLED", "ADMIN_EMAIL", "ADMIN_PASSWORD"]:
        monkeypatch.delenv(name, raising=False)
    return store


def _make_auth_client() -> TestClient:
    from backend.auth import router as auth_router
    from backend.auth.middleware import AuthMiddleware

    app = FastAPI()
    app.add_middleware(AuthMiddleware)

    @app.get("/private")
    def private():
        return {"ok": True}

    @app.get("/health")
    def health():
        return {"status": "ok"}

    app.include_router(auth_router.router)
    return TestClient(app)


def test_validate_runtime_auth_policy_requires_auth_in_production(monkeypatch, isolated_auth_store):
    isolated_auth_store.init_db()
    isolated_auth_store.save_auth_config({"enabled": False})
    monkeypatch.setenv("VEDA_RUNTIME_ENV", "production")
    monkeypatch.delenv("VEDA_AUTH_ENABLED", raising=False)

    with pytest.raises(RuntimeError, match="requires authentication"):
        isolated_auth_store.validate_runtime_auth_policy()


def test_bootstrap_admin_skips_without_env_credentials_in_local(monkeypatch, isolated_auth_store):
    isolated_auth_store.save_auth_config({"enabled": True})
    monkeypatch.setenv("VEDA_RUNTIME_ENV", "local")
    monkeypatch.setenv("VEDA_AUTH_ENABLED", "true")

    isolated_auth_store.bootstrap_admin()

    assert isolated_auth_store.user_count() == 0


def test_bootstrap_admin_creates_first_admin_from_env(monkeypatch, isolated_auth_store):
    isolated_auth_store.save_auth_config({"enabled": True})
    monkeypatch.setenv("VEDA_RUNTIME_ENV", "production")
    monkeypatch.setenv("VEDA_AUTH_ENABLED", "true")
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "StrongAdmin123")

    isolated_auth_store.bootstrap_admin()

    assert isolated_auth_store.user_count() == 1
    admin = isolated_auth_store.get_user_by_email("admin@example.com")
    assert admin is not None
    assert admin.role == "admin"
    isolated_auth_store.validate_runtime_auth_policy()


def test_setup_is_disabled_in_production(monkeypatch, isolated_auth_store):
    isolated_auth_store.init_db()
    monkeypatch.setenv("VEDA_RUNTIME_ENV", "production")
    monkeypatch.setenv("VEDA_AUTH_ENABLED", "true")

    client = _make_auth_client()
    response = client.post("/api/auth/setup", json={"email": "admin@example.com", "password": "StrongAdmin123"})

    assert response.status_code == 403
    assert "disabled" in response.json()["detail"]


def test_setup_enforces_password_policy(monkeypatch, isolated_auth_store):
    isolated_auth_store.init_db()
    monkeypatch.setenv("VEDA_RUNTIME_ENV", "local")

    client = _make_auth_client()
    response = client.post("/api/auth/setup", json={"email": "admin@example.com", "password": "weakpass"})

    assert response.status_code == 400
    assert "at least 12 characters" in response.json()["detail"]


def test_auth_disabled_mode_blocks_non_loopback_requests(monkeypatch, isolated_auth_store):
    isolated_auth_store.init_db()
    monkeypatch.setenv("VEDA_RUNTIME_ENV", "local")

    from backend.auth import middleware as auth_middleware

    monkeypatch.setattr(auth_middleware, "_is_loopback_request", lambda request: False)
    client = _make_auth_client()

    assert client.get("/health").status_code == 200
    response = client.get("/private")
    assert response.status_code == 403
    assert "loopback" in response.json()["detail"].lower()
