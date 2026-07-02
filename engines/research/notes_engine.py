"""
Research Notes Engine -- Phase 23
Per-symbol markdown notes with tags and star ratings.
Stored as a single JSON file: data/research/notes.json
"""

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

NOTES_DIR  = cfg.DATA_DIR / "research"
NOTES_FILE = NOTES_DIR / "notes.json"


def _load_all() -> dict:
    if not NOTES_FILE.exists():
        return {}
    try:
        with open(NOTES_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_all(notes: dict) -> None:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    tmp = NOTES_FILE.with_suffix(".tmp.json")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(notes, f, indent=2, ensure_ascii=False)
    shutil.move(str(tmp), str(NOTES_FILE))


def get(symbol: str) -> Optional[dict]:
    return _load_all().get(symbol.strip().upper())


def save(symbol: str, content: str,
         tags: list[str] = [], rating: int = 0) -> dict:
    notes = _load_all()
    sym   = symbol.strip().upper()
    now   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    existing = notes.get(sym, {})
    note = {
        "symbol":     sym,
        "content":    content,
        "tags":       [t.strip().lower() for t in tags if t.strip()],
        "rating":     max(0, min(5, int(rating))),
        "created_at": existing.get("created_at", now),
        "updated_at": now,
    }
    notes[sym] = note
    _save_all(notes)
    logger.info("[Notes] Saved note for %s (%d chars)", sym, len(content))
    return note


def delete(symbol: str) -> bool:
    notes = _load_all()
    sym   = symbol.strip().upper()
    if sym in notes:
        del notes[sym]
        _save_all(notes)
        logger.info("[Notes] Deleted note for %s", sym)
        return True
    return False


def list_index() -> list[dict]:
    """Return lightweight index of all notes (no full content)."""
    notes = _load_all()
    result = []
    for sym, note in notes.items():
        content = note.get("content", "")
        excerpt = content.replace("#", "").replace("\n", " ").strip()[:100]
        result.append({
            "symbol":     sym,
            "rating":     note.get("rating", 0),
            "tags":       note.get("tags", []),
            "updated_at": note.get("updated_at", ""),
            "excerpt":    excerpt,
        })
    return sorted(result, key=lambda x: x["updated_at"], reverse=True)
