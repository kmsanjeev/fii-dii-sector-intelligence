"""Provider-local Dhan authentication and secure token lifecycle.

This module is intentionally outside VEDA Core.  Credentials and tokens are
stored only in the OS credential manager through ``keyring``; validation state
is non-secret metadata in the ignored intraday data directory.
"""

from __future__ import annotations

import getpass
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests

from engines.common import config as cfg

try:
    import keyring
except ImportError:  # pragma: no cover - dependency is declared in requirements
    keyring = None

try:
    import pyotp
except ImportError:  # pragma: no cover - dependency is declared in requirements
    pyotp = None


AUTH_SERVICE = "veda.fii.dhan"
TOKEN_URL = "https://auth.dhan.co/app/generateAccessToken"
PROFILE_URL = "https://api.dhan.co/v2/profile"
STATE_PATH = cfg.DATA_DIR / "intraday" / "provider_state.json"
TOKEN_REFRESH_MARGIN = timedelta(minutes=2)


class DhanAuthError(RuntimeError):
    """Safe provider authentication failure with a stable code."""

    def __init__(self, code: str, *, status_code: int | None = None):
        super().__init__(code)
        self.code = code
        self.status_code = status_code


@dataclass(frozen=True, slots=True)
class DhanCredentialMetadata:
    client_id: str
    pin: str
    totp_seed: str


@dataclass(frozen=True, slots=True)
class DhanToken:
    access_token: str
    expires_at: datetime


class SecureCredentialStore:
    """Small keyring wrapper that fails closed when no secure backend exists."""

    def __init__(self, service: str = AUTH_SERVICE):
        self.service = service

    def _backend(self) -> Any:
        if keyring is None:
            raise DhanAuthError("SECURE_CREDENTIAL_STORE_UNAVAILABLE")
        backend = keyring.get_keyring()
        if getattr(backend, "priority", 0) <= 0:
            raise DhanAuthError("SECURE_CREDENTIAL_STORE_UNAVAILABLE")
        return backend

    def get(self, name: str) -> dict[str, Any] | None:
        self._backend()
        raw = keyring.get_password(self.service, name)
        if not raw:
            return None
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise DhanAuthError("SECURE_CREDENTIAL_STORE_CORRUPT") from exc
        return value if isinstance(value, dict) else None

    def put(self, name: str, value: dict[str, Any]) -> None:
        self._backend()
        keyring.set_password(self.service, name, json.dumps(value, sort_keys=True))

    def delete(self, name: str) -> None:
        self._backend()
        try:
            keyring.delete_password(self.service, name)
        except keyring.errors.PasswordDeleteError:
            pass


class DhanAuthManager:
    """Authenticate Dhan using TOTP, reuse valid tokens and refresh on demand."""

    def __init__(self, store: SecureCredentialStore | None = None, http: Any = requests):
        self.store = store or SecureCredentialStore()
        self.http = http

    @staticmethod
    def _validate_credentials(client_id: str, pin: str, totp_seed: str) -> None:
        if not client_id or not pin or not totp_seed:
            raise DhanAuthError("SECURE_CREDENTIAL_ENROLLMENT_REQUIRED")
        if not pin.isdigit() or len(pin) != 6:
            raise DhanAuthError("INVALID_DHAN_PIN_FORMAT")
        if pyotp is None:
            raise DhanAuthError("PYOTP_DEPENDENCY_REQUIRED")
        try:
            pyotp.TOTP(totp_seed).now()
        except Exception as exc:
            raise DhanAuthError("INVALID_TOTP_SEED") from exc

    @classmethod
    def from_environment(cls) -> "DhanAuthManager":
        manager = cls()
        try:
            enrolled = bool(manager.store.get("credentials"))
        except DhanAuthError:
            enrolled = False
        if not enrolled and all(os.getenv(name, "").strip() for name in ("DHAN_CLIENT_ID", "DHAN_PIN", "DHAN_TOTP_SECRET")):
            manager.enroll(
                os.environ["DHAN_CLIENT_ID"].strip(),
                os.environ["DHAN_PIN"].strip(),
                os.environ["DHAN_TOTP_SECRET"].strip(),
            )
        return manager

    def enroll(self, client_id: str, pin: str, totp_seed: str) -> None:
        self._validate_credentials(client_id, pin, totp_seed)
        self.store.put("credentials", {"client_id": client_id, "pin": pin, "totp_seed": totp_seed})
        # An enrolled credential set invalidates any previous token.
        try:
            self.store.delete("token")
        except AttributeError:
            pass

    def enroll_interactive(self) -> None:
        self.enroll(
            getpass.getpass("Dhan client ID: ").strip(),
            getpass.getpass("Dhan PIN (not echoed): ").strip(),
            getpass.getpass("Dhan TOTP seed (not echoed): ").strip(),
        )

    def has_credentials(self) -> bool:
        try:
            if self.store.get("credentials"):
                return True
        except DhanAuthError:
            return False
        return all(os.getenv(name, "").strip() for name in ("DHAN_CLIENT_ID", "DHAN_PIN", "DHAN_TOTP_SECRET"))

    def _credentials(self) -> DhanCredentialMetadata:
        try:
            stored = self.store.get("credentials")
        except DhanAuthError:
            stored = None
        if stored:
            return DhanCredentialMetadata(str(stored["client_id"]), str(stored["pin"]), str(stored["totp_seed"]))
        values = {name: os.getenv(name, "").strip() for name in ("DHAN_CLIENT_ID", "DHAN_PIN", "DHAN_TOTP_SECRET")}
        if all(values.values()):
            self._validate_credentials(values["DHAN_CLIENT_ID"], values["DHAN_PIN"], values["DHAN_TOTP_SECRET"])
            return DhanCredentialMetadata(values["DHAN_CLIENT_ID"], values["DHAN_PIN"], values["DHAN_TOTP_SECRET"])
        raise DhanAuthError("SECURE_CREDENTIAL_ENROLLMENT_REQUIRED")

    @staticmethod
    def _parse_expiry(value: str) -> datetime:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.replace(tzinfo=parsed.tzinfo or timezone.utc)

    def _cached_token(self) -> DhanToken | None:
        try:
            stored = self.store.get("token")
        except DhanAuthError:
            return None
        if not stored or not stored.get("access_token") or not stored.get("expires_at"):
            return None
        try:
            token = DhanToken(str(stored["access_token"]), self._parse_expiry(str(stored["expires_at"])))
        except (TypeError, ValueError):
            return None
        return token if token.expires_at > datetime.now(timezone.utc) + TOKEN_REFRESH_MARGIN else None

    def ensure_valid_token(self) -> DhanToken:
        cached = self._cached_token()
        if cached:
            return cached
        credentials = self._credentials()
        assert pyotp is not None
        response = self.http.post(
            TOKEN_URL,
            params={
                "dhanClientId": credentials.client_id,
                "pin": credentials.pin,
                "totp": pyotp.TOTP(credentials.totp_seed).now(),
            },
            timeout=20,
        )
        try:
            payload = response.json()
        except ValueError as exc:
            raise DhanAuthError("AUTH_RESPONSE_NOT_JSON", status_code=response.status_code) from exc
        if response.status_code != 200 or not isinstance(payload, dict) or not payload.get("accessToken"):
            raise DhanAuthError(
                str(payload.get("errorCode") or payload.get("errorType") or "AUTH_FAILED"),
                status_code=response.status_code,
            )
        try:
            token = DhanToken(str(payload["accessToken"]), self._parse_expiry(str(payload["expiryTime"])))
        except (KeyError, TypeError, ValueError) as exc:
            raise DhanAuthError("AUTH_EXPIRY_INVALID", status_code=response.status_code) from exc
        self.store.put("token", {"access_token": token.access_token, "expires_at": token.expires_at.isoformat()})
        return token

    def profile(self) -> dict[str, Any]:
        token = self.ensure_valid_token()
        response = self.http.get(PROFILE_URL, headers={"access-token": token.access_token}, timeout=20)
        try:
            payload = response.json()
        except ValueError as exc:
            raise DhanAuthError("PROFILE_RESPONSE_NOT_JSON", status_code=response.status_code) from exc
        if response.status_code != 200 or not isinstance(payload, dict):
            raise DhanAuthError("PROFILE_FAILED", status_code=response.status_code)
        return {
            "http_status": response.status_code,
            "dhan_client_id_present": bool(payload.get("dhanClientId")),
            "token_validity_present": bool(payload.get("tokenValidity")),
            "active_segment": str(payload.get("activeSegment") or ""),
            "data_plan": str(payload.get("dataPlan") or "UNKNOWN"),
            "data_validity": str(payload.get("dataValidity") or ""),
            "ddpi": str(payload.get("ddpi") or ""),
        }

    @staticmethod
    def read_validation_state() -> dict[str, Any]:
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    @staticmethod
    def write_validation_state(state: dict[str, Any]) -> None:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        temp = STATE_PATH.with_suffix(".tmp")
        temp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
        temp.replace(STATE_PATH)
