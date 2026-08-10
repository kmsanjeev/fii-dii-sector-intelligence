from __future__ import annotations

import json

import pytest


@pytest.fixture
def isolated_broker_storage(monkeypatch, tmp_dir):
    from engines.broker import sync_engine

    portfolio_dir = tmp_dir / "portfolio"
    auth_dir = tmp_dir / "auth"
    monkeypatch.setattr(sync_engine, "PORTFOLIO_DIR", portfolio_dir)
    monkeypatch.setattr(sync_engine, "BROKER_AUTH", portfolio_dir / "broker_auth.json")
    monkeypatch.setattr(sync_engine, "BROKER_KEY", auth_dir / "broker_credentials.key")
    monkeypatch.delenv("VEDA_BROKER_CREDENTIAL_SECRET", raising=False)
    return sync_engine


def test_broker_credentials_roundtrip_without_plaintext_persistence(isolated_broker_storage):
    isolated_broker_storage.save_credentials("dhan", "1100123456", "token-abc-123")

    creds = isolated_broker_storage.load_credentials()
    stored_text = isolated_broker_storage.BROKER_AUTH.read_text(encoding="utf-8")

    assert creds is not None
    assert creds["broker"] == "dhan"
    assert creds["client_id"] == "1100123456"
    assert creds["access_token"] == "token-abc-123"
    assert "token-abc-123" not in stored_text
    assert "1100123456" not in stored_text
    assert "ciphertext" in stored_text


def test_legacy_plaintext_broker_file_is_migrated(isolated_broker_storage):
    isolated_broker_storage.PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)
    isolated_broker_storage.BROKER_AUTH.write_text(
        json.dumps(
            {
                "broker": "dhan",
                "client_id": "2200123456",
                "access_token": "legacy-token",
                "set_at": "2026-08-10T00:00:00",
            }
        ),
        encoding="utf-8",
    )

    creds = isolated_broker_storage.load_credentials()
    migrated = json.loads(isolated_broker_storage.BROKER_AUTH.read_text(encoding="utf-8"))

    assert creds is not None
    assert creds["client_id"] == "2200123456"
    assert creds["access_token"] == "legacy-token"
    assert "ciphertext" in migrated
    assert "access_token" not in migrated
    assert migrated["client_id_mask"] == "2200****"


def test_broker_status_masks_client_id(isolated_broker_storage):
    isolated_broker_storage.save_credentials("dhan", "3300123456", "another-token")

    status = isolated_broker_storage.get_status()

    assert status["connected"] is True
    assert status["client_id"] == "3300****"
