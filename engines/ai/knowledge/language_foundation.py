"""Deterministic LANG-002 presentation and translation-governance foundation.

This module is deliberately presentation-only. Canonical Jyotisha IDs, source
metadata, trust states, calculations, and business rules are never localized.
No provider call or free-text machine translation is used at runtime.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any, Mapping


LANGUAGE_FOUNDATION_VERSION = "LANG-002-1.0.0"
CANONICAL_LOCALE = "en"
LANGUAGE_TARGET_STATUS = "HINDI_LOCALE_REVIEW_CANDIDATE_READY"
_ROOT = Path(__file__).resolve().parents[3]
_REGISTRY_PATH = _ROOT / "data" / "veda" / "localization" / "canonical_term_registry.json"
_LOCALE_DIR = _ROOT / "data" / "veda" / "localization" / "locales"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_term_registry() -> dict[str, Any]:
    """Load the governed presentation vocabulary without changing ontology data."""
    return _read_json(_REGISTRY_PATH)


def available_locales() -> tuple[str, ...]:
    return tuple(sorted(path.stem for path in _LOCALE_DIR.glob("*.json")))


def _normalize(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().casefold())


def _locale_chain(locale: str) -> tuple[str, ...]:
    requested = _normalize(locale).replace("_", "-") or CANONICAL_LOCALE
    chain = [requested]
    if "-" in requested:
        chain.append(requested.split("-", 1)[0])
    if CANONICAL_LOCALE not in chain:
        chain.append(CANONICAL_LOCALE)
    return tuple(dict.fromkeys(chain))


def _load_locale_exact(locale: str) -> dict[str, Any] | None:
    path = _LOCALE_DIR / f"{locale}.json"
    return _read_json(path) if path.is_file() else None


def load_locale(locale: str = CANONICAL_LOCALE) -> dict[str, Any]:
    """Return the first available locale in requested -> parent -> English order."""
    for candidate in _locale_chain(locale):
        loaded = _load_locale_exact(candidate)
        if loaded is not None:
            return loaded
    raise FileNotFoundError("The canonical English locale pack is missing")


def _term_maps(locale: str = CANONICAL_LOCALE) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    terms = load_term_registry()["terms"]
    by_id = {item["canonical_id"]: item for item in terms}
    aliases: dict[str, str] = {}
    for item in terms:
        aliases[_normalize(item["canonical_id"])] = item["canonical_id"]
        aliases[_normalize(item["english"])] = item["canonical_id"]
        for alias in item.get("aliases", []):
            aliases[_normalize(alias)] = item["canonical_id"]
    for candidate in _locale_chain(locale):
        locale_pack = _load_locale_exact(candidate)
        if locale_pack is None:
            continue
        for alias, canonical_id in locale_pack.get("aliases", {}).items():
            if canonical_id in by_id:
                aliases[_normalize(alias)] = canonical_id
    return by_id, aliases


def canonicalize_term(value: str, locale: str = CANONICAL_LOCALE) -> str | None:
    """Resolve a controlled term ID or alias to one canonical ID."""
    return _term_maps(locale)[1].get(_normalize(value))


def _resolve_locale(locale: str) -> tuple[dict[str, Any], str, bool]:
    requested = _normalize(locale).replace("_", "-") or CANONICAL_LOCALE
    for candidate in _locale_chain(requested):
        loaded = _load_locale_exact(candidate)
        if loaded is not None:
            return loaded, candidate, candidate != requested
    raise FileNotFoundError("The canonical English locale pack is missing")


def render_term(value: str, locale: str = CANONICAL_LOCALE) -> dict[str, Any]:
    """Render a controlled vocabulary item while preserving its canonical ID."""
    by_id, aliases = _term_maps(locale)
    canonical_id = value if value in by_id else aliases.get(_normalize(value))
    if canonical_id is None:
        return {"canonical_id": value, "text": None, "status": "MISSING_CANONICAL_TERM", "review_state": "REVIEW_PENDING"}
    registry_item = copy.deepcopy(by_id[canonical_id])
    locale_pack, locale_used, fallback_used = _resolve_locale(locale)
    has_locale_term = canonical_id in locale_pack.get("terms", {}) or locale_used == CANONICAL_LOCALE
    text = locale_pack.get("terms", {}).get(canonical_id, registry_item["english"])
    return {
        "canonical_id": canonical_id,
        "text": text,
        "locale_requested": _normalize(locale).replace("_", "-") or CANONICAL_LOCALE,
        "locale_used": locale_used,
        "fallback_used": fallback_used or not has_locale_term,
        "status": "AVAILABLE",
        "review_state": locale_pack.get("review_state", "REVIEW_PENDING"),
        "term_class": registry_item["term_class"],
        "knowledge_zone": registry_item.get("knowledge_zone", "PRESENTATION_ONLY"),
        "sanskrit": registry_item.get("sanskrit"),
        "transliteration": registry_item.get("transliteration"),
        "transliteration_status": registry_item.get("transliteration_status", "NOT_RECORDED"),
    }


def render_message(message_id: str, locale: str = CANONICAL_LOCALE, *, variables: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Render a governed presentation message; never invent a missing string."""
    locale_pack, locale_used, fallback_used = _resolve_locale(locale)
    messages = locale_pack.get("messages", {})
    text = messages.get(message_id)
    if text is None:
        english = _load_locale_exact(CANONICAL_LOCALE) or {}
        text = english.get("messages", {}).get(message_id)
        fallback_used = True
    if text is None:
        return {"message_id": message_id, "text": None, "status": "MISSING_TRANSLATION", "review_state": "REVIEW_PENDING"}
    if variables:
        text = text.format_map({key: str(value) for key, value in variables.items()})
    return {
        "message_id": message_id,
        "text": text,
        "locale_requested": _normalize(locale).replace("_", "-") or CANONICAL_LOCALE,
        "locale_used": locale_used,
        "fallback_used": fallback_used,
        "status": locale_pack.get("status", "REVIEW_PENDING"),
        "review_state": locale_pack.get("review_state", "REVIEW_PENDING"),
    }


def render_source_citation(citation: Mapping[str, Any], locale: str = CANONICAL_LOCALE) -> dict[str, Any]:
    """Add presentation text without dropping source identity or trust metadata."""
    result = copy.deepcopy(dict(citation))
    result["source_label"] = render_message("GOVERNANCE.SOURCE_CITATION", locale)
    return result


def render_structured(fact_payload: Mapping[str, Any], locale: str = CANONICAL_LOCALE) -> dict[str, Any]:
    """Return canonical facts separately from optional display fields."""
    canonical = copy.deepcopy(dict(fact_payload))
    display = copy.deepcopy(canonical)
    for key, value in canonical.items():
        if key.endswith("_id") and isinstance(value, str):
            rendered = render_term(value, locale)
            if rendered["status"] == "AVAILABLE":
                display[f"{key[:-3]}_display"] = rendered["text"]
        elif key == "status" and isinstance(value, str):
            message_id = f"STATUS.{value}"
            rendered = render_message(message_id, locale)
            if rendered["text"] is not None:
                display["status_display"] = rendered["text"]
    return {"fact_payload": canonical, "display": display, "locale": _normalize(locale) or CANONICAL_LOCALE}


def render_interpretation(text: str, locale: str = CANONICAL_LOCALE, *, status: str, source_metadata: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Keep free-text interpretation canonical until a reviewed translation exists."""
    result = {"text": str(text), "locale": CANONICAL_LOCALE, "translation_state": "CANONICAL_TEXT_ONLY", "status": status}
    if source_metadata:
        result["source_metadata"] = copy.deepcopy(dict(source_metadata))
    if _normalize(locale) not in {CANONICAL_LOCALE, ""}:
        result["requested_locale"] = _normalize(locale)
        result["translation_note"] = render_message("SAFETY.MISSING_TRANSLATION", locale)
    return result


def validate_epistemic_preservation(source_text: str, rendered_text: str) -> dict[str, Any]:
    """Conservative English safety checks for high-risk qualifiers and negation."""
    source = _normalize(source_text)
    rendered = _normalize(rendered_text)
    required = []
    if "may indicate" in source:
        required.append(("may indicate", "QUALIFIER"))
    for phrase in ("research-only", "not validated", "not authorized", "no predictive claim", "not proven"):
        if phrase in source:
            required.append((phrase, "NEGATION_OR_STATUS"))
    failures = [phrase for phrase, _ in required if phrase not in rendered]
    return {"passed": not failures, "required_phrases": [phrase for phrase, _ in required], "missing_phrases": failures}


def coverage_report(locale: str = CANONICAL_LOCALE) -> dict[str, Any]:
    """Report coverage without calling fallback complete translation."""
    registry = load_term_registry()["terms"]
    locale_pack = _load_locale_exact(_normalize(locale).replace("_", "-"))
    english = _load_locale_exact(CANONICAL_LOCALE) or {}
    message_ids = set(english.get("messages", {}))
    term_ids = {item["canonical_id"] for item in registry}
    if locale_pack is None:
        translated = 0
        missing = len(message_ids) + len(term_ids)
        fallback = missing
        status = "UNIMPLEMENTED_LOCALE"
        classification = "UNIMPLEMENTED_LOCALE"
        counts = {}
    else:
        translated_terms = len(term_ids) if _normalize(locale) == CANONICAL_LOCALE else len(set(locale_pack.get("terms", {})) & term_ids)
        translated = len(set(locale_pack.get("messages", {})) & message_ids) + translated_terms
        total = len(message_ids) + len(term_ids)
        missing = total - translated
        fallback = 0
        status = locale_pack.get("status", "REVIEW_PENDING")
        classification = locale_pack.get("classification", status)
        counts = locale_pack.get("review_counts", {})
    total = len(message_ids) + len(term_ids)
    canonical_baseline = classification == "CANONICAL_BASELINE"
    return {
        "locale": _normalize(locale).replace("_", "-") or CANONICAL_LOCALE,
        "total_keys": total,
        "translated": translated,
        "missing": missing,
        "fallback_used": fallback,
        "coverage": round(translated / total, 4) if total else 1.0,
        "status": status,
        "classification": classification,
        "human_reviewed": int(counts.get("HUMAN_REVIEWED", 0)),
        "machine_draft": int(counts.get("MACHINE_DRAFT", 0)) if not canonical_baseline else 0,
        "source_reviewed": int(counts.get("SOURCE_REVIEWED", 0)),
        "approved_presentation": int(counts.get("APPROVED_PRESENTATION", 0)),
        "review_pending": int(counts.get("REVIEW_PENDING", total)),
    }


def serialize_unicode(payload: Any) -> str:
    """Stable UTF-8 JSON for API/storage boundaries."""
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "CANONICAL_LOCALE", "LANGUAGE_FOUNDATION_VERSION", "LANGUAGE_TARGET_STATUS",
    "available_locales", "canonicalize_term", "coverage_report", "load_locale",
    "load_term_registry", "render_interpretation", "render_message",
    "render_source_citation", "render_structured", "render_term",
    "serialize_unicode", "validate_epistemic_preservation",
]
