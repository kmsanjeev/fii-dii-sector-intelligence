"""
Voice Router -- Phase V1 (Veda / Adya voice assistant)

POST /api/voice/tts       text + language -> streamed MP3 (edge-tts neural voices)
GET  /api/voice/voices    voice casting per language (for the settings picker)
POST /api/voice/log       append a conversation turn to the analytics log
GET  /api/voice/analytics quick aggregate of the conversation log

Voice casting (design doc docs/modules/VOICE_PLATFORM.md):
  hi -> hi-IN-SwaraNeural   (sweet, clear -- the default Hindi Veda)
  en -> en-IN-NeerjaNeural  (polished, professional Indian English)
Rate -5%% for precision; small in-memory cache so greetings play instantly.
"""

from __future__ import annotations

import csv
import hashlib
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/voice", tags=["voice"])

# ── Voice casting ─────────────────────────────────────────────────────────────

VOICES: dict[str, dict] = {
    "hi": {"voice": "hi-IN-SwaraNeural",    "label": "Swara (Hindi)"},
    "en": {"voice": "en-IN-NeerjaNeural",   "label": "Neerja (Indian English)"},
    "ta": {"voice": "ta-IN-PallaviNeural",  "label": "Pallavi (Tamil)"},
    "te": {"voice": "te-IN-ShrutiNeural",   "label": "Shruti (Telugu)"},
    "bn": {"voice": "bn-IN-TanishaaNeural", "label": "Tanishaa (Bengali)"},
    "mr": {"voice": "mr-IN-AarohiNeural",   "label": "Aarohi (Marathi)"},
    "gu": {"voice": "gu-IN-DhwaniNeural",   "label": "Dhwani (Gujarati)"},
}
DEFAULT_LANG = "hi"          # per user decision 2026-07-10
TTS_RATE     = "-5%"         # slightly slower = precise, confident delivery
MAX_TTS_CHARS = 900          # spoken summary cap -- long tables live in the chat

# Small in-memory audio cache (greetings + repeated phrases play instantly)
_tts_cache: dict[str, bytes] = {}
_TTS_CACHE_MAX = 64

# ── Conversation log (Phase V1 analytics foundation) ─────────────────────────

CHAT_LOG_DIR = cfg.DATA_DIR / "chat"
CHAT_LOG_CSV = CHAT_LOG_DIR / "conversation_log.csv"
_LOG_COLS = ["ts", "session_id", "mode", "language", "wake_word_used",
             "user_message", "intent", "reply_chars", "latency_ms", "tts_voice"]
_log_lock = threading.Lock()


class TTSRequest(BaseModel):
    text: str
    language: str = DEFAULT_LANG


class LogRequest(BaseModel):
    session_id:     str
    mode:           str = "text"       # voice | text
    language:       str = DEFAULT_LANG
    wake_word_used: bool = False
    user_message:   str = ""
    intent:         str = ""
    reply_chars:    int = 0
    latency_ms:     int = 0
    tts_voice:      str = ""


def _spoken_text(text: str) -> str:
    """Convert a chat reply into speakable text: strip markdown noise,
    drop table blocks, cap length (long detail stays in the chat)."""
    lines = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s:
            continue
        if s.startswith("|") or set(s) <= {"-", "=", "|", "+", " "}:
            continue   # tables / rulers are never read aloud
        for tok in ("**", "__", "##", "#", "`", "*"):
            s = s.replace(tok, "")
        lines.append(s)
    out = " ".join(lines)
    if len(out) > MAX_TTS_CHARS:
        cut = out[:MAX_TTS_CHARS]
        # end on a sentence boundary when possible
        for stop in (". ", "? ", "! ", "| "):
            i = cut.rfind(stop)
            if i > MAX_TTS_CHARS // 2:
                cut = cut[: i + 1]
                break
        out = cut
    return out.strip()


@router.post("/tts")
async def tts(req: TTSRequest):
    """Text -> MP3 via edge-tts. Cached responses return instantly."""
    try:
        import edge_tts
    except ImportError:
        raise HTTPException(status_code=503,
                            detail="edge-tts not installed: py -3.11 -m pip install edge-tts")

    lang = req.language if req.language in VOICES else DEFAULT_LANG
    voice = VOICES[lang]["voice"]
    text = _spoken_text(req.text)
    if not text:
        raise HTTPException(status_code=400, detail="Nothing speakable in the text")

    key = hashlib.sha1(f"{voice}|{TTS_RATE}|{text}".encode("utf-8")).hexdigest()
    if key in _tts_cache:
        return Response(content=_tts_cache[key], media_type="audio/mpeg",
                        headers={"X-Voice": voice, "X-Cache": "hit"})

    async def _generate() -> AsyncGenerator[bytes, None]:
        buf = bytearray()
        try:
            communicate = edge_tts.Communicate(text, voice, rate=TTS_RATE)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buf.extend(chunk["data"])
                    yield bytes(chunk["data"])
        except Exception as e:
            logger.error("[Voice] TTS stream failed (%s): %s", voice, e)
            return
        # cache complete utterances (bounded)
        if buf and len(_tts_cache) < _TTS_CACHE_MAX:
            _tts_cache[key] = bytes(buf)

    return StreamingResponse(_generate(), media_type="audio/mpeg",
                             headers={"X-Voice": voice, "X-Cache": "miss"})


@router.get("/voices")
def list_voices():
    """Available voice casting per language + defaults for the settings UI."""
    return {
        "default_language": DEFAULT_LANG,
        "wake_words": ["veda", "adya"],
        "voices": [{"language": k, **v} for k, v in VOICES.items()],
    }


@router.post("/log")
def log_turn(req: LogRequest):
    """Append one conversation turn to the analytics log (CSV, atomic append)."""
    try:
        CHAT_LOG_DIR.mkdir(parents=True, exist_ok=True)
        row = {
            "ts":             datetime.now(timezone.utc).isoformat(),
            "session_id":     req.session_id,
            "mode":           req.mode if req.mode in ("voice", "text") else "text",
            "language":       req.language,
            "wake_word_used": req.wake_word_used,
            "user_message":   req.user_message[:500],
            "intent":         req.intent,
            "reply_chars":    req.reply_chars,
            "latency_ms":     req.latency_ms,
            "tts_voice":      req.tts_voice,
        }
        with _log_lock:
            new_file = not CHAT_LOG_CSV.exists()
            with open(CHAT_LOG_CSV, "a", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=_LOG_COLS)
                if new_file:
                    w.writeheader()
                w.writerow(row)
        return {"logged": True}
    except Exception as e:
        logger.error("[Voice] log failed: %s", e)
        return {"logged": False, "error": str(e)}


@router.get("/analytics")
def quick_analytics():
    """Lightweight aggregate of the conversation log (full engine lands in V2)."""
    import pandas as pd
    if not CHAT_LOG_CSV.exists():
        return {"turns": 0, "note": "no conversations logged yet"}
    df = pd.read_csv(CHAT_LOG_CSV)
    if df.empty:
        return {"turns": 0, "note": "no conversations logged yet"}
    top_intents = df["intent"].value_counts().head(8).to_dict()
    return {
        "turns":         int(len(df)),
        "sessions":      int(df["session_id"].nunique()),
        "voice_share":   round(float((df["mode"] == "voice").mean()) * 100, 1),
        "language_split": df["language"].value_counts().to_dict(),
        "top_intents":   top_intents,
        "least_intents": df["intent"].value_counts().tail(5).to_dict(),
    }
