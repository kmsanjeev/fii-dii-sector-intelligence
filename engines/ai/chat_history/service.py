from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

_SAFE_COMPONENT_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_component(value: str, *, default: str) -> str:
    cleaned = _SAFE_COMPONENT_RE.sub("_", (value or "").strip()).strip("._-")
    return cleaned[:80] or default


class ChatHistoryService:
    def __init__(self, *, storage_dir: Path | None = None):
        self._storage_dir = Path(storage_dir or cfg.VEDA_CHAT_SESSION_DIR)
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    def list_sessions(self, owner_key: str) -> list[dict[str, Any]]:
        owner_dir = self._owner_dir(owner_key)
        if not owner_dir.exists():
            return []

        sessions: list[dict[str, Any]] = []
        for path in owner_dir.glob("*.json"):
            payload = self._read_json(path)
            if payload is None or not payload.get("id"):
                continue
            sessions.append(payload)

        sessions.sort(
            key=lambda item: (
                int(item.get("updatedAt") or 0),
                int(item.get("createdAt") or 0),
            ),
            reverse=True,
        )
        return sessions

    def upsert_session(self, owner_key: str, session: dict[str, Any]) -> dict[str, Any]:
        session_id = str(session.get("id") or "").strip()
        if not session_id:
            raise ValueError("Saved chat session is missing an id.")

        now_ms = int(time.time() * 1000)
        normalized = {
            "id": session_id,
            "title": str(session.get("title") or "New Chat").strip() or "New Chat",
            "messages": list(session.get("messages") or []),
            "backendSessionId": (str(session.get("backendSessionId")).strip() if session.get("backendSessionId") else None),
            "createdAt": int(session.get("createdAt") or now_ms),
            "updatedAt": int(session.get("updatedAt") or now_ms),
        }
        self._write_json(self._session_path(owner_key, session_id), normalized)
        return normalized

    def delete_session(self, owner_key: str, session_id: str) -> bool:
        path = self._session_path(owner_key, session_id)
        if not path.exists():
            return False
        path.unlink()
        self._cleanup_owner_dir(path.parent)
        return True

    def delete_all_sessions(self, owner_key: str) -> int:
        owner_dir = self._owner_dir(owner_key)
        if not owner_dir.exists():
            return 0

        deleted = 0
        for path in owner_dir.glob("*.json"):
            path.unlink()
            deleted += 1
        self._cleanup_owner_dir(owner_dir)
        return deleted

    def _owner_dir(self, owner_key: str) -> Path:
        digest = hashlib.sha1(owner_key.encode("utf-8")).hexdigest()[:16]
        safe = _safe_component(owner_key, default="owner")
        return self._storage_dir / f"{digest}_{safe}"

    def _session_path(self, owner_key: str, session_id: str) -> Path:
        owner_dir = self._owner_dir(owner_key)
        owner_dir.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha1(session_id.encode("utf-8")).hexdigest()[:16]
        safe = _safe_component(session_id, default="session")
        return owner_dir / f"{digest}_{safe}.json"

    def _read_json(self, path: Path) -> dict[str, Any] | None:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("[VedaChatHistory] Failed reading %s: %s", path, exc)
            return None
        return payload if isinstance(payload, dict) else None

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)

    def _cleanup_owner_dir(self, owner_dir: Path) -> None:
        try:
            next(owner_dir.iterdir())
        except StopIteration:
            owner_dir.rmdir()
        except FileNotFoundError:
            return
        except OSError:
            return


_SERVICE: ChatHistoryService | None = None


def get_chat_history_service() -> ChatHistoryService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = ChatHistoryService()
    return _SERVICE
