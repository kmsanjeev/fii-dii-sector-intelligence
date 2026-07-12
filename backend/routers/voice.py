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
    "hi": {"voice": "hi-IN-SwaraNeural",             "label": "Swara (Hindi)"},
    # Expressive variant discovered 2026-07-11 -- noticeably more natural
    "en": {"voice": "en-IN-NeerjaExpressiveNeural",  "label": "Neerja Expressive (Indian English)"},
    "ta": {"voice": "ta-IN-PallaviNeural",  "label": "Pallavi (Tamil)"},
    "te": {"voice": "te-IN-ShrutiNeural",   "label": "Shruti (Telugu)"},
    "bn": {"voice": "bn-IN-TanishaaNeural", "label": "Tanishaa (Bengali)"},
    "mr": {"voice": "mr-IN-AarohiNeural",   "label": "Aarohi (Marathi)"},
    "gu": {"voice": "gu-IN-DhwaniNeural",   "label": "Dhwani (Gujarati)"},
}
DEFAULT_LANG = "hi"          # per user decision 2026-07-10
# +8%: conversational pace. The original -5% made delivery drone-like
# (user feedback 2026-07-11: "easily identifiable as machine talking")
TTS_RATE     = "+8%"
MAX_TTS_CHARS = 900          # spoken summary cap -- long tables live in the chat

# Small in-memory audio cache (greetings + repeated phrases play instantly)
_tts_cache: dict[str, bytes] = {}
_TTS_CACHE_MAX = 64

# ── Conversation log (Phase V1 analytics foundation) ─────────────────────────

CHAT_LOG_DIR = cfg.DATA_DIR / "chat"
CHAT_LOG_CSV = CHAT_LOG_DIR / "conversation_log.csv"
# "symbols" (Phase V-DATA-3) added at the end so older log rows without
# this column still parse fine (pandas reads the missing trailing field
# as NaN) -- no migration needed for existing conversation_log.csv rows.
_LOG_COLS = ["ts", "session_id", "mode", "language", "wake_word_used",
             "user_message", "intent", "reply_chars", "latency_ms", "tts_voice",
             "symbols"]
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
    symbols:        list[str] = []     # Phase V-DATA-3 -- from actual tool
                                         # calls (language-agnostic), not a
                                         # regex over user_message


# "What to read vs. what to present" (user feedback: "she starts reading
# all"): a reply formatted as a bulleted/numbered list of stocks/scores is
# NOT a markdown table, so the old table-only filter let it through
# untouched -- TTS would enumerate every line. Everything from the first
# list item onward is chat-only detail; only the lead prose is spoken, with
# a short trailer telling the user the rest is in the chat.
_LIST_TRAILER: dict[str, str] = {
    "hi": "पूरी जानकारी चैट में है।",
    "en": "Full details are in the chat.",
}
_LIST_ONLY_FALLBACK: dict[str, str] = {
    "hi": "मैंने जानकारी निकाल ली है, पूरी सूची चैट में देखिए।",
    "en": "I've got the details -- check the full list in the chat.",
}

# Structural list detection (above) only catches markdown bullets/tables.
# A model can (and does, especially under the "no bullet lists" voice
# instruction) enumerate many stocks in flowing PROSE instead -- "dekhiye,
# EBGNG ka score X hai... aur CORONA ka Y hai... aur MCX..." -- which has no
# structural marker to cut on. Real backstop: cap the spoken lead to N
# sentences, always, regardless of formatting. Split only on genuine
# sentence-ending punctuation -- a decimal point inside a price/score/percent
# ("84.72", "-8%.") must never be mistaken for a sentence boundary.
MAX_SPOKEN_SENTENCES = 4


def _cap_sentences(text: str) -> tuple[str, bool]:
    """Return (capped_text, was_truncated)."""
    import re as _re
    parts = _re.split(r"(?<!\d)([.!?।])(?!\d)\s+", text)
    sentences: list[str] = []
    buf = ""
    for piece in parts:
        buf += piece
        if piece in ".!?।":
            sentences.append(buf.strip())
            buf = ""
    if buf.strip():
        sentences.append(buf.strip())
    if len(sentences) <= MAX_SPOKEN_SENTENCES:
        return text, False
    return " ".join(sentences[:MAX_SPOKEN_SENTENCES]), True


def _spoken_text(text: str, lang: str = DEFAULT_LANG) -> str:
    """Convert a chat reply into speakable text: strip markdown noise, speak
    only the lead prose (drop everything from the first list item or table
    onward -- that is chat-only detail), cap length as a backstop."""
    import re as _re
    # Defence in depth: strip leaked function-call artifacts before speaking
    text = _re.sub(r"<function[=\w\-]*>.*?</function>|<function[=\w\-]*/?>|</function>",
                   "", text or "", flags=_re.DOTALL)

    # Humanise technical tokens (V3.3): EARLY_ROTATION must be spoken as
    # "early rotation", never "early underscore rotation". Same for slashes
    # and hyphens inside identifier-like words, and symbol words.
    text = _re.sub(r"(?<=\w)[_](?=\w)", " ", text)          # snake_case -> spaces
    text = _re.sub(r"(?<=[A-Za-z])/(?=[A-Za-z])", " / ", text)  # FII/DII -> FII / DII (spoken pause)
    text = _re.sub(r"(?<=\w)-(?=\w)", " ", text)            # 52-week -> 52 week
    text = text.replace("%", " percent")
    text = text.replace("&", " and ")
    text = _re.sub(r"-{2,}|={2,}|_{2,}", " ", text)          # ruler remnants
    text = _re.sub(r"[ \t]{2,}", " ", text)   # spaces only -- newlines must survive
                                              # for the table-line filter below

    lines = []
    list_truncated = False
    for ln in text.splitlines():
        s = ln.strip()
        if not s:
            continue
        if s.startswith("|") or set(s) <= {"-", "=", "|", "+", " "}:
            list_truncated = True
            continue   # tables / rulers are never read aloud
        # Bullet/numbered list boundary -- must check BEFORE stripping "*"
        # below, since that would erase the very marker we're looking for.
        if _re.match(r"^([-*•▪‣·]|\d+[.)])\s+\S", s):
            list_truncated = True
            break   # this and every line after it is chat-only detail
        for tok in ("**", "__", "##", "#", "`", "*"):
            s = s.replace(tok, "")
        lines.append(s)
    out = " ".join(lines).strip()

    # Sentence-count backstop BEFORE the trailer decision -- catches
    # prose-enumerated replies with no structural list marker at all.
    if out:
        out, sentence_truncated = _cap_sentences(out)
        list_truncated = list_truncated or sentence_truncated

    if list_truncated:
        out = out + (" " if out else "") + (_LIST_TRAILER.get(lang, _LIST_TRAILER["en"])
                                              if out else _LIST_ONLY_FALLBACK.get(lang, _LIST_ONLY_FALLBACK["en"]))

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
    text = _spoken_text(req.text, lang)
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


def _migrate_log_schema_if_needed():
    """One-time schema migration: older conversation_log.csv rows predate
    the 'symbols' column (Phase V-DATA-3). Appending new 11-column rows
    under an old 10-column header would corrupt the file for any CSV
    reader, so if the on-disk header doesn't match _LOG_COLS, rewrite the
    whole file once with the missing column added (empty for old rows)."""
    if not CHAT_LOG_CSV.exists():
        return
    with open(CHAT_LOG_CSV, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header == _LOG_COLS:
            return   # already current
        rows = list(csv.DictReader(open(CHAT_LOG_CSV, encoding="utf-8")))
    for r in rows:
        for col in _LOG_COLS:
            r.setdefault(col, "")
    tmp = CHAT_LOG_CSV.with_suffix(".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=_LOG_COLS)
        w.writeheader()
        w.writerows(rows)
    tmp.replace(CHAT_LOG_CSV)
    logger.info("[Voice] conversation_log.csv migrated to include 'symbols' column (%d rows)", len(rows))


@router.post("/log")
def log_turn(req: LogRequest):
    """Append one conversation turn to the analytics log (CSV, atomic append)."""
    try:
        CHAT_LOG_DIR.mkdir(parents=True, exist_ok=True)
        with _log_lock:
            _migrate_log_schema_if_needed()
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
            "symbols":        ",".join(req.symbols) if req.symbols else "",
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
    """Demand analytics: prefers the V2 engine output; falls back to a live
    aggregate of the raw log."""
    import pandas as pd

    engine_csv = cfg.INTELLIGENCE_DIR / "chat_analytics.csv"
    if engine_csv.exists():
        a = pd.read_csv(engine_csv)
        if not a.empty:
            def _rows(mtype: str, limit: int = 10) -> list[dict]:
                d = a[a["metric_type"] == mtype].head(limit)
                return [{k: (None if pd.isna(v) else v) for k, v in r.items()}
                        for r in d.to_dict(orient="records")]
            summ = {r["key"]: r["count"] for _, r in a[a["metric_type"] == "SUMMARY"].iterrows()}
            return {
                "source":       "engine",
                "run_date":     str(a.iloc[0]["run_date"]),
                "summary":      summ,
                "top_intents":  _rows("INTENT"),
                "least_intents": _rows("INTENT", 999)[-5:],
                "languages":    _rows("LANGUAGE"),
                "modes":        _rows("MODE"),
                "top_symbols":  _rows("SYMBOL"),
                "by_hour_ist":  _rows("HOUR_IST", 24),
            }

    if not CHAT_LOG_CSV.exists():
        return {"source": "live", "turns": 0, "note": "no conversations logged yet"}
    df = pd.read_csv(CHAT_LOG_CSV)
    if df.empty:
        return {"source": "live", "turns": 0, "note": "no conversations logged yet"}
    return {
        "source":        "live",
        "turns":         int(len(df)),
        "sessions":      int(df["session_id"].nunique()),
        "voice_share":   round(float((df["mode"] == "voice").mean()) * 100, 1),
        "language_split": df["language"].value_counts().to_dict(),
        "top_intents":   df["intent"].value_counts().head(8).to_dict(),
        "least_intents": df["intent"].value_counts().tail(5).to_dict(),
    }
