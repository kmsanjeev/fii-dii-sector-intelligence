"""
Auth Middleware -- Phase 25
HTTP middleware that validates Bearer tokens / API keys for protected paths.
When auth is disabled (default), all requests pass through unchanged.

Also exposes FastAPI dependencies: require_auth, require_admin.
"""

import sys
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.auth.store import User, is_auth_enabled, verify_session, verify_api_key

# Paths that bypass auth even when auth is enabled
_PUBLIC = {
    "/", "/health", "/docs", "/openapi.json", "/redoc",
    "/api/auth/login", "/api/auth/setup",
}


def _is_public(path: str) -> bool:
    return path in _PUBLIC or path.startswith("/ws/")


def _resolve_user(request: Request) -> Optional[User]:
    """Extract and verify user from Authorization header or X-API-Key header."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return verify_session(auth[7:])
    api_key = request.headers.get("X-API-Key", "")
    if api_key:
        return verify_api_key(api_key)
    return None


class AuthMiddleware(BaseHTTPMiddleware):
    """Rejects unauthenticated / unauthorised requests when auth is enabled."""

    async def dispatch(self, request: Request, call_next):
        if not is_auth_enabled() or _is_public(request.url.path):
            return await call_next(request)

        user = _resolve_user(request)
        if user is None or not user.active:
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication required"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        request.state.user = user

        # analyst role: read-only
        if user.role == "analyst" and request.method not in ("GET", "HEAD", "OPTIONS"):
            return JSONResponse(
                status_code=403,
                content={"detail": "Analyst role is read-only"},
            )

        return await call_next(request)


# ── FastAPI dependencies ───────────────────────────────────────────────────────

_DEV_USER = User(id="dev", email="dev@localhost", role="admin", active=True, created_at="")


def require_auth(request: Request) -> User:
    """Dependency: authenticated user (or synthetic dev user when auth off)."""
    if not is_auth_enabled():
        return _DEV_USER
    user = getattr(request.state, "user", None) or _resolve_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def require_admin(request: Request) -> User:
    """Dependency: raises 403 unless role == admin."""
    user = require_auth(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return user
