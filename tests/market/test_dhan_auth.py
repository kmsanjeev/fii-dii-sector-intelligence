from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pyotp

from engines.providers.dhan_auth import DhanAuthError, DhanAuthManager


class MemoryStore:
    def __init__(self):
        self.values = {}

    def get(self, name):
        return self.values.get(name)

    def put(self, name, value):
        self.values[name] = value

    def delete(self, name):
        self.values.pop(name, None)


class Response:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload


class FakeHTTP:
    def __init__(self):
        self.post_calls = 0
        self.get_calls = 0

    def post(self, url, *, params, timeout):
        self.post_calls += 1
        assert params["pin"] == "123456"
        assert len(params["totp"]) == 6
        return Response({"accessToken": "token-only-in-test", "expiryTime": "2099-01-01T00:00:00+00:00"})

    def get(self, url, *, headers, timeout):
        self.get_calls += 1
        assert "access-token" in headers
        return Response({"dhanClientId": "1000000001", "tokenValidity": "2099", "dataPlan": "Active", "activeSegment": "E, D"})


def test_totp_token_is_cached_and_profile_is_sanitized(monkeypatch) -> None:
    store = MemoryStore()
    http = FakeHTTP()
    manager = DhanAuthManager(store=store, http=http)
    manager.enroll("1000000001", "123456", pyotp.random_base32())
    token = manager.ensure_valid_token()
    assert token.access_token == "token-only-in-test"
    assert manager.ensure_valid_token().access_token == token.access_token
    assert http.post_calls == 1
    assert manager.profile()["data_plan"] == "Active"
    assert http.get_calls == 1


def test_missing_secure_enrollment_is_explicit(monkeypatch) -> None:
    monkeypatch.delenv("DHAN_CLIENT_ID", raising=False)
    monkeypatch.delenv("DHAN_PIN", raising=False)
    monkeypatch.delenv("DHAN_TOTP_SECRET", raising=False)
    manager = DhanAuthManager(store=MemoryStore(), http=FakeHTTP())
    try:
        manager.ensure_valid_token()
    except DhanAuthError as exc:
        assert exc.code == "SECURE_CREDENTIAL_ENROLLMENT_REQUIRED"
    else:
        raise AssertionError("missing enrollment must fail closed")


def test_cached_token_expiry_is_checked() -> None:
    store = MemoryStore()
    store.put("token", {"access_token": "expired", "expires_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()})
    manager = DhanAuthManager(store=store, http=FakeHTTP())
    assert manager._cached_token() is None
