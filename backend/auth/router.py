"""
Auth Router -- Phase 25
Handles login, logout, user management, API key management, and auth config.
"""

import sys
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.auth import store
from backend.auth.middleware import require_admin, require_auth
from backend.auth.store import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── Request models ─────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email:    str
    password: str


class SetupRequest(BaseModel):
    email:    str
    password: str


class CreateUserRequest(BaseModel):
    email:    str
    password: str
    role:     str = "analyst"   # admin | analyst | trader


class UpdateUserRequest(BaseModel):
    role:   Optional[str]  = None
    active: Optional[bool] = None


class ChangePasswordRequest(BaseModel):
    new_password: str


class CreateApiKeyRequest(BaseModel):
    name: str


class AuthConfigUpdate(BaseModel):
    enabled:            Optional[bool] = None
    token_expiry_days:  Optional[int]  = None


# ── Helpers ────────────────────────────────────────────────────────────────────

def _user_dict(u: User) -> dict:
    return {"id": u.id, "email": u.email, "role": u.role,
            "active": u.active, "created_at": u.created_at}


def _token_from_request(request: Request) -> Optional[str]:
    auth = request.headers.get("Authorization", "")
    return auth[7:] if auth.startswith("Bearer ") else None


# ── Auth endpoints ─────────────────────────────────────────────────────────────

@router.post("/setup")
def setup(req: SetupRequest):
    """
    First-run only: creates the admin account and enables auth.
    Rejected if any users already exist.
    """
    store.init_db()
    if store.user_count() > 0:
        raise HTTPException(status_code=409, detail="Setup already complete -- users exist")
    if not req.email or not req.password:
        raise HTTPException(status_code=400, detail="Email and password required")
    user  = store.create_user(req.email, req.password, role="admin")
    store.save_auth_config({"enabled": True})
    token = store.create_session(user.id)
    return {"token": token, "user": _user_dict(user), "message": "Admin created. Auth is now enabled."}


@router.post("/login")
def login(req: LoginRequest):
    store.init_db()
    user = store.authenticate(req.email, req.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = store.create_session(user.id)
    return {"token": token, "user": _user_dict(user)}


@router.post("/logout")
def logout(request: Request):
    token = _token_from_request(request)
    if token:
        store.revoke_session(token)
    return {"message": "Logged out"}


@router.get("/me")
def me(request: Request):
    """Returns current user if auth is enabled + logged in, or null if auth is off."""
    if not store.is_auth_enabled():
        return {"enabled": False, "user": None}
    from backend.auth.middleware import _resolve_user
    user = getattr(request.state, "user", None) or _resolve_user(request)
    if user is None:
        return {"enabled": True, "user": None}
    return {"enabled": True, "user": _user_dict(user)}


@router.put("/me/password")
def change_password(req: ChangePasswordRequest, current_user: User = Depends(require_auth)):
    if not req.new_password or len(req.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    store.change_password(current_user.id, req.new_password)
    return {"message": "Password updated"}


# ── Auth config ────────────────────────────────────────────────────────────────

@router.get("/config")
def get_auth_config(current_user: User = Depends(require_admin)):
    return store.load_auth_config()


@router.put("/config")
def update_auth_config(req: AuthConfigUpdate, current_user: User = Depends(require_admin)):
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    return store.save_auth_config(updates)


# ── User management (admin) ────────────────────────────────────────────────────

@router.get("/users")
def list_users(current_user: User = Depends(require_admin)):
    return {"users": [_user_dict(u) for u in store.list_users()]}


@router.post("/users")
def create_user(req: CreateUserRequest, current_user: User = Depends(require_admin)):
    if store.get_user_by_email(req.email):
        raise HTTPException(status_code=409, detail=f"User {req.email} already exists")
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if req.role not in ("admin", "analyst", "trader"):
        raise HTTPException(status_code=400, detail="Role must be admin, analyst, or trader")
    user = store.create_user(req.email, req.password, req.role)
    return _user_dict(user)


@router.put("/users/{user_id}")
def update_user(user_id: str, req: UpdateUserRequest, current_user: User = Depends(require_admin)):
    if req.role and req.role not in ("admin", "analyst", "trader"):
        raise HTTPException(status_code=400, detail="Invalid role")
    # Prevent admin from deactivating themselves
    if user_id == current_user.id and req.active is False:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    user = store.update_user(user_id, role=req.role, active=req.active)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_dict(user)


@router.delete("/users/{user_id}")
def deactivate_user(user_id: str, current_user: User = Depends(require_admin)):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    user = store.update_user(user_id, active=False)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"User {user.email} deactivated"}


# ── API keys ───────────────────────────────────────────────────────────────────

@router.get("/api-keys")
def list_api_keys(current_user: User = Depends(require_auth)):
    keys = store.list_api_keys(current_user.id)
    return {"keys": [
        {"id": k.id, "name": k.name, "key_prefix": k.key_prefix,
         "created_at": k.created_at, "last_used_at": k.last_used_at}
        for k in keys
    ]}


@router.post("/api-keys")
def create_api_key(req: CreateApiKeyRequest, current_user: User = Depends(require_auth)):
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="Key name required")
    raw_key, meta = store.create_api_key(current_user.id, req.name.strip())
    return {
        "key": raw_key,   # shown ONCE
        "id":  meta.id,
        "name": meta.name,
        "key_prefix": meta.key_prefix,
        "message": "Store this key now -- it will not be shown again.",
    }


@router.delete("/api-keys/{key_id}")
def revoke_api_key(key_id: str, current_user: User = Depends(require_auth)):
    if not store.revoke_api_key(key_id, current_user.id):
        raise HTTPException(status_code=404, detail="API key not found")
    return {"message": f"API key {key_id} revoked"}
