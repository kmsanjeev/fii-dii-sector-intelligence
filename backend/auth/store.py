"""
Auth Store -- Phase 25
SQLite-backed user, session, and API key management.
Zero external dependencies -- stdlib only (sqlite3, hashlib, secrets, hmac).

Schema:
  users     (id, email, password_hash, salt, role, active, created_at)
  sessions  (token, user_id, created_at, expires_at)
  api_keys  (id, user_id, name, key_prefix, key_hash, created_at, last_used_at, active)
"""

import hashlib
import hmac
import json
import secrets
import shutil
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

_ROOT = Path(__file__).resolve().parents[2]

import sys
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

AUTH_DIR          = cfg.DATA_DIR / "auth"
DB_PATH           = AUTH_DIR / "users.db"
CFG_PATH          = AUTH_DIR / "auth_config.json"
TOKEN_EXPIRY_DAYS = 7
API_KEY_PREFIX    = "cfip_"

_DEFAULT_CFG = {"enabled": False, "token_expiry_days": TOKEN_EXPIRY_DAYS}


# ── Config ────────────────────────────────────────────────────────────────────

def load_auth_config() -> dict:
    if CFG_PATH.exists():
        try:
            with open(CFG_PATH, encoding="utf-8") as f:
                return {**_DEFAULT_CFG, **json.load(f)}
        except Exception:
            pass
    return _DEFAULT_CFG.copy()


def save_auth_config(updates: dict) -> dict:
    data = load_auth_config()
    data.update(updates)
    AUTH_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CFG_PATH.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    shutil.move(str(tmp), str(CFG_PATH))
    return data


def is_auth_enabled() -> bool:
    return bool(load_auth_config().get("enabled", False))


# ── DB ─────────────────────────────────────────────────────────────────────────

def _conn() -> sqlite3.Connection:
    AUTH_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def init_db() -> None:
    with _conn() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            TEXT PRIMARY KEY,
                email         TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt          TEXT NOT NULL,
                role          TEXT NOT NULL DEFAULT 'analyst',
                active        INTEGER NOT NULL DEFAULT 1,
                created_at    TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token      TEXT PRIMARY KEY,
                user_id    TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS api_keys (
                id           TEXT PRIMARY KEY,
                user_id      TEXT NOT NULL,
                name         TEXT NOT NULL,
                key_prefix   TEXT NOT NULL,
                key_hash     TEXT NOT NULL,
                created_at   TEXT NOT NULL,
                last_used_at TEXT,
                active       INTEGER NOT NULL DEFAULT 1
            );
        """)
    logger.info("[Auth] DB ready at %s", DB_PATH)


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class User:
    id:         str
    email:      str
    role:       str    # admin | analyst | trader
    active:     bool
    created_at: str


@dataclass
class ApiKeyMeta:
    id:           str
    user_id:      str
    name:         str
    key_prefix:   str
    created_at:   str
    last_used_at: Optional[str]
    active:       bool


# ── Password helpers ──────────────────────────────────────────────────────────

def _hash_pw(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return h.hex(), salt


def _verify_pw(password: str, pw_hash: str, salt: str) -> bool:
    expected, _ = _hash_pw(password, salt)
    return hmac.compare_digest(expected, pw_hash)


# ── Users ─────────────────────────────────────────────────────────────────────

def _to_user(row) -> User:
    return User(id=row["id"], email=row["email"], role=row["role"],
                active=bool(row["active"]), created_at=row["created_at"])


def user_count() -> int:
    with _conn() as con:
        return con.execute("SELECT COUNT(*) FROM users").fetchone()[0]


def create_user(email: str, password: str, role: str = "analyst") -> User:
    uid  = str(uuid.uuid4())
    now  = datetime.now(timezone.utc).isoformat()
    ph, salt = _hash_pw(password)
    with _conn() as con:
        con.execute(
            "INSERT INTO users (id, email, password_hash, salt, role, active, created_at) VALUES (?,?,?,?,?,1,?)",
            (uid, email.lower().strip(), ph, salt, role, now),
        )
    logger.info("[Auth] User created: %s (%s)", email, role)
    return User(id=uid, email=email.lower().strip(), role=role, active=True, created_at=now)


def get_user_by_id(uid: str) -> Optional[User]:
    with _conn() as con:
        row = con.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
    return _to_user(row) if row else None


def get_user_by_email(email: str) -> Optional[User]:
    with _conn() as con:
        row = con.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),)).fetchone()
    return _to_user(row) if row else None


def list_users() -> list[User]:
    with _conn() as con:
        rows = con.execute("SELECT * FROM users ORDER BY created_at").fetchall()
    return [_to_user(r) for r in rows]


def update_user(uid: str, role: Optional[str] = None, active: Optional[bool] = None) -> Optional[User]:
    with _conn() as con:
        if role is not None:
            con.execute("UPDATE users SET role = ? WHERE id = ?", (role, uid))
        if active is not None:
            con.execute("UPDATE users SET active = ? WHERE id = ?", (1 if active else 0, uid))
    return get_user_by_id(uid)


def change_password(uid: str, new_password: str) -> None:
    ph, salt = _hash_pw(new_password)
    with _conn() as con:
        con.execute("UPDATE users SET password_hash = ?, salt = ? WHERE id = ?", (ph, salt, uid))


def authenticate(email: str, password: str) -> Optional[User]:
    with _conn() as con:
        row = con.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),)).fetchone()
    if not row or not row["active"]:
        return None
    return _to_user(row) if _verify_pw(password, row["password_hash"], row["salt"]) else None


# ── Sessions ──────────────────────────────────────────────────────────────────

def create_session(uid: str) -> str:
    token       = secrets.token_urlsafe(32)
    now         = datetime.now(timezone.utc)
    expiry_days = int(load_auth_config().get("token_expiry_days", TOKEN_EXPIRY_DAYS))
    expires_at  = (now + timedelta(days=expiry_days)).isoformat()
    with _conn() as con:
        con.execute(
            "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?,?,?,?)",
            (token, uid, now.isoformat(), expires_at),
        )
    return token


def verify_session(token: str) -> Optional[User]:
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as con:
        row = con.execute(
            "SELECT user_id FROM sessions WHERE token = ? AND expires_at > ?",
            (token, now),
        ).fetchone()
    return get_user_by_id(row["user_id"]) if row else None


def revoke_session(token: str) -> None:
    with _conn() as con:
        con.execute("DELETE FROM sessions WHERE token = ?", (token,))


def purge_expired_sessions() -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as con:
        con.execute("DELETE FROM sessions WHERE expires_at <= ?", (now,))


# ── API keys ──────────────────────────────────────────────────────────────────

def create_api_key(uid: str, name: str) -> tuple[str, ApiKeyMeta]:
    """Returns (full_key, meta). full_key is shown ONCE — only its hash is stored."""
    key_id   = str(uuid.uuid4())[:8].upper()
    raw_key  = API_KEY_PREFIX + secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    prefix   = raw_key[:12]      # e.g. "cfip_xKj7Qm"
    now      = datetime.now(timezone.utc).isoformat()
    with _conn() as con:
        con.execute(
            "INSERT INTO api_keys (id, user_id, name, key_prefix, key_hash, created_at, active) VALUES (?,?,?,?,?,?,1)",
            (key_id, uid, name, prefix, key_hash, now),
        )
    meta = ApiKeyMeta(id=key_id, user_id=uid, name=name, key_prefix=prefix,
                      created_at=now, last_used_at=None, active=True)
    logger.info("[Auth] API key created for user %s: %s (%s)", uid, key_id, name)
    return raw_key, meta


def verify_api_key(raw_key: str) -> Optional[User]:
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    with _conn() as con:
        row = con.execute(
            "SELECT user_id FROM api_keys WHERE key_hash = ? AND active = 1",
            (key_hash,),
        ).fetchone()
        if row:
            con.execute(
                "UPDATE api_keys SET last_used_at = ? WHERE key_hash = ?",
                (datetime.now(timezone.utc).isoformat(), key_hash),
            )
    return get_user_by_id(row["user_id"]) if row else None


def list_api_keys(uid: str) -> list[ApiKeyMeta]:
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM api_keys WHERE user_id = ? AND active = 1 ORDER BY created_at",
            (uid,),
        ).fetchall()
    return [ApiKeyMeta(id=r["id"], user_id=r["user_id"], name=r["name"],
                       key_prefix=r["key_prefix"], created_at=r["created_at"],
                       last_used_at=r["last_used_at"], active=bool(r["active"]))
            for r in rows]


def revoke_api_key(key_id: str, uid: str) -> bool:
    with _conn() as con:
        cur = con.execute(
            "UPDATE api_keys SET active = 0 WHERE id = ? AND user_id = ?",
            (key_id, uid),
        )
    return cur.rowcount > 0


# ── Bootstrap ──────────────────────────────────────────────────────────────────

def bootstrap_admin() -> None:
    """
    Create first admin user from env vars if auth is enabled and no users exist.
    Env vars: ADMIN_EMAIL (default: admin@localhost), ADMIN_PASSWORD (default: admin123)
    Logs a warning if using default credentials.
    """
    import os
    if not is_auth_enabled():
        return
    init_db()
    if user_count() > 0:
        return
    email    = os.environ.get("ADMIN_EMAIL",    "admin@localhost")
    password = os.environ.get("ADMIN_PASSWORD", "admin123")
    if password == "admin123":
        logger.warning(
            "[Auth] BOOTSTRAP: creating admin with default password 'admin123'. "
            "Set ADMIN_EMAIL and ADMIN_PASSWORD env vars before enabling auth in production."
        )
    create_user(email, password, role="admin")
    logger.info("[Auth] Admin bootstrapped: %s", email)
