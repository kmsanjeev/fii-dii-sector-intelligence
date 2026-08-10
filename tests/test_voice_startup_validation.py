"""Tests for validate_voices_on_startup() in backend/routers/voice.py."""
import asyncio
import logging
import sys
import types
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.routers.voice import VOICES, validate_voices_on_startup


def _run(coro):
    """Run an async coroutine synchronously (compatible with Python 3.10+)."""
    return asyncio.run(coro)


def test_all_valid_voices_logs_no_warning(caplog):
    """All VOICES IDs present → no warning logged."""
    all_short_names = [entry["voice"] for entry in VOICES.values()]
    fake_voice_list = [{"ShortName": sn} for sn in all_short_names]

    fake_edge_tts = types.ModuleType("edge_tts")

    async def fake_list_voices():
        return fake_voice_list

    fake_edge_tts.list_voices = fake_list_voices

    original = sys.modules.get("edge_tts")
    sys.modules["edge_tts"] = fake_edge_tts
    try:
        with caplog.at_level(logging.WARNING, logger="backend.routers.voice"):
            _run(validate_voices_on_startup())
        voice_warnings = [
            r for r in caplog.records
            if r.levelno >= logging.WARNING and "Unrecognised voice ID" in r.message
        ]
        assert len(voice_warnings) == 0
    finally:
        if original is None:
            sys.modules.pop("edge_tts", None)
        else:
            sys.modules["edge_tts"] = original


def test_invalid_voice_id_logs_warning(caplog):
    """An unrecognised voice ID → WARNING logged with lang key and voice ID."""
    # Fake list that omits hi-IN-SwaraNeural
    fake_voice_list = [
        {"ShortName": "en-IN-NeerjaNeural"},
        {"ShortName": "ta-IN-PallaviNeural"},
        {"ShortName": "te-IN-ShrutiNeural"},
        {"ShortName": "bn-IN-TanishaaNeural"},
        {"ShortName": "mr-IN-AarohiNeural"},
        {"ShortName": "gu-IN-DhwaniNeural"},
    ]

    fake_edge_tts = types.ModuleType("edge_tts")

    async def fake_list_voices():
        return fake_voice_list

    fake_edge_tts.list_voices = fake_list_voices

    original = sys.modules.get("edge_tts")
    sys.modules["edge_tts"] = fake_edge_tts
    try:
        with caplog.at_level(logging.WARNING, logger="backend.routers.voice"):
            _run(validate_voices_on_startup())
        voice_warnings = [
            r for r in caplog.records
            if r.levelno >= logging.WARNING and "Unrecognised voice ID" in r.message
        ]
        assert len(voice_warnings) >= 1
        combined = " ".join(r.message for r in voice_warnings)
        assert "hi-IN-SwaraNeural" in combined
    finally:
        if original is None:
            sys.modules.pop("edge_tts", None)
        else:
            sys.modules["edge_tts"] = original


def test_startup_validation_handles_list_voices_error(caplog):
    """list_voices() raises → warning logged, no crash."""
    fake_edge_tts = types.ModuleType("edge_tts")

    async def fake_list_voices():
        raise RuntimeError("network error")

    fake_edge_tts.list_voices = fake_list_voices

    original = sys.modules.get("edge_tts")
    sys.modules["edge_tts"] = fake_edge_tts
    try:
        with caplog.at_level(logging.WARNING, logger="backend.routers.voice"):
            _run(validate_voices_on_startup())   # must not raise
        any_warning = any(r.levelno >= logging.WARNING for r in caplog.records)
        assert any_warning
    finally:
        if original is None:
            sys.modules.pop("edge_tts", None)
        else:
            sys.modules["edge_tts"] = original
