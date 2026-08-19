"""
Voice Router -- Phase V1 (Veda / Adya voice assistant)

POST /api/voice/tts       text + language -> streamed MP3 (edge-tts neural voices)
GET  /api/voice/voices    voice casting per language (for the settings picker)
POST /api/voice/log       append a conversation turn to the analytics log
GET  /api/voice/analytics quick aggregate of the conversation log

Voice casting (design doc docs/modules/VOICE_PLATFORM.md):
  hi -> hi-IN-SwaraNeural   (sweet, clear -- the default Hindi Veda)
  en -> en-IN-NeerjaNeural  (polished, professional Indian English)
Per-voice rate: hi -10% (clarity), en +5% (lively Indian English, Alexa-like), others -5%.
Small in-memory cache so greetings play instantly.
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

# rate is per-voice (user feedback 2026-08-08 — "sweet and polite" reset):
#   hi/Swara  -8%:  Swara is already the sweetest Hindi neural voice; -10% was
#                   dragging, -8% keeps her warm and clear without the lag.
#   en/Neerja   0%: +5% made her sound rushed/Alexa-like; 0% is her natural,
#                   polite register — best for a courteous relationship-manager
#                   tone the user asked for.
#   other Indian languages: -5% (conservative default, unchanged).
VOICES: dict[str, dict] = {
    "hi": {"voice": "hi-IN-SwaraNeural",    "label": "Swara (Hindi)",            "rate": "-8%"},
    "en": {"voice": "en-IN-NeerjaNeural",   "label": "Neerja (Indian English)",  "rate": "+10%"},
    "ta": {"voice": "ta-IN-PallaviNeural",  "label": "Pallavi (Tamil)",          "rate": "-5%"},
    "te": {"voice": "te-IN-ShrutiNeural",   "label": "Shruti (Telugu)",          "rate": "-5%"},
    "bn": {"voice": "bn-IN-TanishaaNeural", "label": "Tanishaa (Bengali)",       "rate": "-5%"},
    "mr": {"voice": "mr-IN-AarohiNeural",   "label": "Aarohi (Marathi)",         "rate": "-5%"},
    "gu": {"voice": "gu-IN-DhwaniNeural",   "label": "Dhwani (Gujarati)",        "rate": "-5%"},
}
DEFAULT_LANG = "hi"          # per user decision 2026-07-10
MAX_TTS_CHARS = 1500         # spoken summary cap -- long tables live in the chat

# Small in-memory audio cache (greetings + repeated phrases play instantly)
_tts_cache: dict[str, bytes] = {}
_TTS_CACHE_MAX = 128  # doubled: warmup pre-fills greetings + common phrases

# Greetings / pleasantries pre-synthesised on startup so the FIRST spoken turn
# is instant (no edge-tts cold-call latency). These are the phrases Veda says
# most often, so caching them pays off immediately on every backend restart.
# Keys are the speakable (post-_spoken_text) text; the cache key hashes
# voice+rate+text exactly like the live path, so a warm entry is a guaranteed
# cache HIT at request time.
_TTS_WARMUP_PHRASES: dict[str, list[str]] = {
    "hi": [
        "Namaste! Main Veda hoon. Aapko kya jaanna hai?",
        "Haan, bataiye.",
        "Ji haan, main sun rahi hoon.",
        "Kya main aage bataoon?",
        "Aur kuch jaanna hai?",
        "Dhanyavaad! Koi aur sawal ho to poochiyega.",
        "Main samajh gayi. Aur bataiye.",
        "Theek hai, main check karti hoon.",
    ],
    "en": [
        "Hello, I'm Veda. What would you like to know?",
        "Yes, please go ahead.",
        "Of course, I'm listening.",
        "Would you like me to continue?",
        "Anything else you'd like to know?",
        "Thank you! Do let me know if there's anything else.",
        "I understand. Please go on.",
        "Sure, let me check that for you.",
    ],
}


async def validate_voices_on_startup() -> None:
    """Validate all VOICES entries against the installed edge-tts voice list.
    Runs in background so it never blocks backend startup.
    """
    import asyncio

    async def _validate_and_warm():
        try:
            import edge_tts
        except ImportError:
            logger.warning("[Voice] edge-tts not installed — voice ID validation skipped")
            return
        try:
            voice_list = await edge_tts.list_voices()
            available  = {v["ShortName"] for v in voice_list}
            invalid    = 0
            for lang_key, entry in VOICES.items():
                if entry["voice"] not in available:
                    logger.warning(
                        "[Voice] Unrecognised voice ID '%s' for lang '%s' — check VOICES dict",
                        entry["voice"], lang_key,
                    )
                    invalid += 1
            if invalid == 0:
                logger.info("[Voice] All %d configured voices validated OK", len(VOICES))
        except Exception as e:
            logger.warning("[Voice] Voice ID validation failed (edge-tts list_voices error): %s", e)
        # Warm the TTS cache with common greetings/phrases so the first spoken
        # turn is instant (no cold edge-tts latency on every backend restart).
        await _warm_tts_cache()

    # Fire-and-forget: don't block backend startup on network calls to edge-tts
    asyncio.get_event_loop().create_task(_validate_and_warm())


async def _warm_tts_cache() -> None:
    """Pre-synthesise and cache the most common spoken phrases.
    Runs once on backend startup; doubles the cache size so we don't evict
    real utterances later. Silent no-op if edge-tts is unavailable.
    """
    try:
        import edge_tts
    except ImportError:
        return
    # Pre-generate for each configured language
    for lang, phrases in _TTS_WARMUP_PHRASES.items():
        if lang not in VOICES:
            continue
        voice = VOICES[lang]["voice"]
        rate  = VOICES[lang]["rate"]
        for text in phrases:
            # The text is already in "spoken" form, so we cache it as-is
            key = hashlib.sha1(f"{voice}|{rate}|{text}".encode("utf-8")).hexdigest()
            if key in _tts_cache:
                continue
            try:
                communicate = edge_tts.Communicate(text, voice, rate=rate)
                buf = bytearray()
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        buf.extend(chunk["data"])
                if buf and len(_tts_cache) < _TTS_CACHE_MAX:
                    _tts_cache[key] = bytes(buf)
            except Exception as e:
                logger.debug("[Voice] Warmup skipped for '%s' (%s): %s", text, voice, e)
    logger.info("[Voice] TTS cache warmed with %d common phrases", len(_tts_cache))


# ── Conversation log (Phase V1 analytics foundation) ─────────────────────────

CHAT_LOG_DIR = cfg.DATA_DIR / "chat"
CHAT_LOG_CSV = CHAT_LOG_DIR / "conversation_log.csv"
# "symbols" (Phase V-DATA-3) and "flag_reason" (compliance addendum
# follow-up) added at the end so older log rows without these columns
# still parse fine (pandas reads a missing trailing field as NaN) -- no
# migration needed for existing conversation_log.csv rows.
_LOG_COLS = ["ts", "session_id", "mode", "language", "wake_word_used",
             "user_message", "intent", "reply_chars", "latency_ms", "tts_voice",
             "symbols", "flag_reason", "research_requested", "research_used",
             "research_provider", "research_reason"]
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
    flag_reason:    Optional[str] = None  # "refused" | "prompt_leak" | None
                                            # (engines/ai/chatbot/safety.py)
    research_requested: bool = False
    research_used:      bool = False
    research_provider:  str = ""
    research_reason:    Optional[str] = None


# "What to read vs. what to present" (user feedback: "she starts reading
# all"): a reply formatted as a bulleted/numbered list of stocks/scores is
# NOT a markdown table, so the old table-only filter let it through
# untouched -- TTS would enumerate every line. Everything from the first
# list item onward is chat-only detail; only the lead prose is spoken.
#
# V4 rewrite (user feedback: a flat "full details are in the chat" reads
# like a hang-up, not a handoff -- "gives a cheated feeling"). The trailer
# is now a genuine offer/question, matching the customer-support voice
# persona in chat_engine.py's _VOICE_ADDENDUM (which also now instructs the
# model to ask this itself before handing off to a table). This is only a
# FALLBACK for when the model's own spoken lead didn't already end in a
# question -- see the trailing "?" check in _spoken_text() below, which
# skips this to avoid asking twice.
_LIST_TRAILER: dict[str, str] = {
    "hi": "क्या मैं पूरी जानकारी बताऊं, या इतना काफी है?",
    "en": "Would you like me to go through the rest, or does this cover it?",
}
_LIST_ONLY_FALLBACK: dict[str, str] = {
    "hi": "मैंने पूरी जानकारी निकाल ली है -- क्या मैं इसे पढ़कर सुनाऊं, या चैट में देखना ठीक रहेगा?",
    "en": "I've pulled up the details -- would you like me to read them out, or is checking the chat fine?",
}

# Structural list detection (above) only catches markdown bullets/tables.
# A model can (and does, especially under the "no bullet lists" voice
# instruction) enumerate many stocks in flowing PROSE instead -- "dekhiye,
# EBGNG ka score X hai... aur CORONA ka Y hai... aur MCX..." -- which has no
# structural marker to cut on. Real backstop: cap the spoken lead to N
# sentences, always, regardless of formatting. Split only on genuine
# sentence-ending punctuation -- a decimal point inside a price/score/percent
# ("84.72", "-8%.") must never be mistaken for a sentence boundary.
# 5, not 4 (V4): the voice persona now asks a closing "want the rest?"
# question as part of its own spoken lead (chat_engine.py _VOICE_ADDENDUM)
# -- that question needs a slot of its own, on top of the actual answer,
# or the cap would truncate the model mid-offer.
MAX_SPOKEN_SENTENCES = 8


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
        # Strip ALL asterisks for output -- edge-tts speaks lone "*"
        # as "tarankan" (Hindi) / "asterisk" (English). Bold markers (**) and
        # italic markers (*) must both be silently dropped, never spoken.
        s = s.replace("*", "")
        for tok in ("**", "__", "##", "#", "`"):
            s = s.replace(tok, "")
        lines.append(s)
    out = " ".join(lines).strip()

    # Sentence-count backstop BEFORE the trailer decision -- catches
    # prose-enumerated replies with no structural list marker at all.
    if out:
        out, sentence_truncated = _cap_sentences(out)
        list_truncated = list_truncated or sentence_truncated

    # The voice persona is now instructed to ask its own "want the rest?"
    # question before handing off to a table (chat_engine.py). If it
    # already did -- the spoken lead ends in a question mark -- appending
    # the mechanical trailer on top would ask twice back to back, which
    # sounds worse than the original hang-up this was meant to fix. Only
    # append the fallback offer when the model's own lead did NOT already
    # end with one (covers models that ignore the instruction).
    already_asked = bool(out) and out.rstrip()[-1:] in ("?", "？")
    if list_truncated and not already_asked:
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
    from engines.ai.capabilities import CapabilityAccessError, require_capability_access
    try:
        require_capability_access("VOICE")
    except CapabilityAccessError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    try:
        import edge_tts
    except ImportError:
        raise HTTPException(status_code=503,
                            detail="edge-tts not installed: py -3.11 -m pip install edge-tts")

    lang = req.language if req.language in VOICES else DEFAULT_LANG
    voice = VOICES[lang]["voice"]
    text = _spoken_text(req.text, lang)
    logger.info("[TTS] lang=%s voice=%s input_len=%d output_len=%d text_preview=%r",
                lang, voice, len(req.text or ""), len(text or ""), (text or "")[:120])
    # Fallback: if _spoken_text stripped everything (all bullets/tables),
    # use the raw text truncated to MAX_TTS_CHARS so the user still hears something
    if not text and req.text:
        text = req.text[:MAX_TTS_CHARS]
        logger.warning("[TTS] _spoken_text returned empty, using raw text (truncated to %d chars)", MAX_TTS_CHARS)
    if not text:
        raise HTTPException(status_code=400, detail="Nothing speakable in the text")

    rate = VOICES[lang]["rate"]
    key = hashlib.sha1(f"{voice}|{rate}|{text}".encode("utf-8")).hexdigest()
    if key in _tts_cache:
        return Response(content=_tts_cache[key], media_type="audio/mpeg",
                        headers={"X-Voice": voice, "X-Cache": "hit"})

    async def _generate() -> AsyncGenerator[bytes, None]:
        buf = bytearray()
        try:
            communicate = edge_tts.Communicate(text, voice, rate=rate)
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
    the latest analytics columns. Appending new rows
    under an old header would corrupt the file for any CSV
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
    logger.info("[Voice] conversation_log.csv migrated to current schema (%d rows)", len(rows))


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
            "flag_reason":    req.flag_reason or "",
            "research_requested": "1" if req.research_requested else "0",
            "research_used":      "1" if req.research_used else "0",
            "research_provider":  req.research_provider,
            "research_reason":    req.research_reason or "",
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
    research_used = df.get("research_used")
    if research_used is not None:
        research_share = round(float(research_used.astype(str).isin(["1", "true", "True"]).mean()) * 100, 1)
    else:
        research_share = 0.0
    return {
        "source":        "live",
        "turns":         int(len(df)),
        "sessions":      int(df["session_id"].nunique()),
        "voice_share":   round(float((df["mode"] == "voice").mean()) * 100, 1),
        "research_share": research_share,
        "language_split": df["language"].value_counts().to_dict(),
        "top_intents":   df["intent"].value_counts().head(8).to_dict(),
        "least_intents": df["intent"].value_counts().tail(5).to_dict(),
    }
