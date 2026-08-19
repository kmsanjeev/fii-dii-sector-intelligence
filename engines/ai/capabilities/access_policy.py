"""Single source of truth for Veda conversational capability access.

This is intentionally separate from capability maturity.  Administrators can
turn an implemented capability on or off, while source maturity and runtime
availability remain read-only facts supplied by the platform.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import RLock
from typing import Any

from engines.common import config as cfg

POLICY_VERSION = "2026-08-20"
SCHEMA_VERSION = 1
ENABLED = "ENABLED"
DISABLED = "DISABLED"
ADMIN_ONLY = "ADMIN_ONLY"


@dataclass(frozen=True)
class CapabilityDefinition:
    capability_id: str
    label: str
    description: str
    maturity: str
    answer_mode: str
    intent_types: tuple[str, ...]
    runtime_config: str | None = None
    protected: bool = False


@dataclass(frozen=True)
class CapabilityState:
    capability_id: str
    label: str
    description: str
    admin_access_state: str
    runtime_available: bool
    capability_maturity: str
    effective_access: str
    effective_answer_mode: str
    reason: str
    policy_version: str = POLICY_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_DEFINITIONS: tuple[CapabilityDefinition, ...] = (
    CapabilityDefinition("GENERAL_CHAT", "General Assistant", "Ordinary conversation and non-domain questions.", "IMPLEMENTED_VALIDATED", "FULL", ("GENERAL", "GREETING")),
    CapabilityDefinition("MARKET_INTELLIGENCE", "Market", "Market regime and institutional-flow analysis.", "IMPLEMENTED_VALIDATED", "FULL", ("MARKET",)),
    CapabilityDefinition("SECTOR_INTELLIGENCE", "Sector", "Sector rotation and sector-flow analysis.", "IMPLEMENTED_VALIDATED", "FULL", ("SECTOR",)),
    CapabilityDefinition("STOCK_INTELLIGENCE", "Stock", "Stock, technical, and F&O intelligence.", "IMPLEMENTED_VALIDATED", "FULL", ("STOCK",)),
    CapabilityDefinition("CORPORATE_INTELLIGENCE", "Corporate", "Corporate actions and company intelligence.", "IMPLEMENTED_VALIDATED", "FULL", ("CORPORATE",)),
    CapabilityDefinition("ASTROLOGY", "Astrology", "Governed AstroFinance and Jyotisha discussion.", "IMPLEMENTED_WITH_CONDITIONS", "QUALIFIED", ("ASTRO", "KUNDLI")),
    CapabilityDefinition("RESEARCH", "Research", "Explicit research and governed evidence workflows.", "IMPLEMENTED_WITH_CONDITIONS", "QUALIFIED", ("RESEARCH",), "VEDA_RESEARCH_ENABLED"),
    CapabilityDefinition("MUHURTA", "Muhurta", "Muhurta discussion and available operational activities.", "IMPLEMENTED_WITH_CONDITIONS", "QUALIFIED", ("GENERAL", "ASTRO")),
    CapabilityDefinition("ATTACHMENTS", "Attachments", "User-provided file analysis.", "IMPLEMENTED_WITH_CONDITIONS", "QUALIFIED", tuple(), "VEDA_ATTACHMENTS_ENABLED"),
    CapabilityDefinition("REVIEWED_MEMORY", "Reviewed Memory", "Reviewed knowledge save and retrieval.", "IMPLEMENTED_WITH_CONDITIONS", "QUALIFIED", tuple(), "VEDA_SAVE_TO_KNOWLEDGE_ENABLED"),
    CapabilityDefinition("MIT_REPO_INTAKE", "Repository Intake", "Reviewed MIT repository capability intake.", "IMPLEMENTED_WITH_CONDITIONS", "QUALIFIED", tuple(), "VEDA_MIT_REPO_INTAKE_ENABLED"),
    CapabilityDefinition("MCP", "MCP", "Configured external MCP server access.", "IMPLEMENTED_WITH_CONDITIONS", "DIAGNOSTIC", tuple(), "VEDA_MCP_ENABLED"),
    CapabilityDefinition("VOICE", "Voice / Interaction", "Voice input and response adaptation.", "IMPLEMENTED_WITH_CONDITIONS", "QUALIFIED", tuple()),
)
_BY_ID = {item.capability_id: item for item in _DEFINITIONS}
# A capability can expose an intent as a related subdomain (for example,
# MUHURTA also understands ASTRO/GENERAL context).  Core conversational
# routes must remain authoritative; a later optional definition must not
# silently replace GENERAL_CHAT or ASTROLOGY.
_BY_INTENT: dict[str, str] = {}
for _definition in _DEFINITIONS:
    for _intent in _definition.intent_types:
        _BY_INTENT.setdefault(_intent, _definition.capability_id)
_LOCK = RLock()


def definitions() -> list[dict[str, Any]]:
    return [asdict(item) for item in _DEFINITIONS]


def _path() -> Path:
    return Path(getattr(cfg, "VEDA_CONVERSATIONAL_ACCESS_CONFIG", cfg.VEDA_CACHE_DIR / "conversation_access.json"))


def _default_access() -> dict[str, str]:
    return {item.capability_id: ENABLED for item in _DEFINITIONS}


def _read_access() -> dict[str, str]:
    path = _path()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != SCHEMA_VERSION:
            return _default_access()
        access = _default_access()
        for key, value in dict(payload.get("access") or {}).items():
            if key in _BY_ID and value in {ENABLED, DISABLED, ADMIN_ONLY}:
                access[key] = value
        return access
    except (OSError, ValueError, TypeError):
        return _default_access()


def _write_access(access: dict[str, str]) -> None:
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": SCHEMA_VERSION, "policy_version": POLICY_VERSION, "access": access}
    fd, temp_name = tempfile.mkstemp(prefix="conversation_access_", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def _runtime_available(definition: CapabilityDefinition) -> bool:
    if not definition.runtime_config:
        return True
    return bool(getattr(cfg, definition.runtime_config, False))


def _state(definition: CapabilityDefinition, access: str) -> CapabilityState:
    runtime = _runtime_available(definition)
    if access == DISABLED:
        return CapabilityState(definition.capability_id, definition.label, definition.description, access, runtime, definition.maturity, DISABLED, "UNAVAILABLE", "Disabled by administrator")
    if access == ADMIN_ONLY:
        return CapabilityState(definition.capability_id, definition.label, definition.description, access, runtime, definition.maturity, ADMIN_ONLY, "DIAGNOSTIC", "Available only to administrators")
    if not runtime:
        return CapabilityState(definition.capability_id, definition.label, definition.description, access, False, definition.maturity, "UNAVAILABLE", "UNAVAILABLE", "Configured on, but runtime/provider is unavailable")
    return CapabilityState(definition.capability_id, definition.label, definition.description, access, True, definition.maturity, ENABLED, definition.answer_mode, "Enabled; maturity remains read-only")


def get_states() -> list[dict[str, Any]]:
    with _LOCK:
        access = _read_access()
        return [_state(item, access[item.capability_id]).to_dict() for item in _DEFINITIONS]


def get_state(capability_id: str) -> CapabilityState:
    key = str(capability_id or "").upper()
    definition = _BY_ID.get(key)
    if definition is None:
        raise KeyError(f"Unknown capability: {capability_id}")
    with _LOCK:
        return _state(definition, _read_access()[key])


def resolve_intent(intent_type: str, *, research_mode: bool = False) -> CapabilityState:
    key = "RESEARCH" if research_mode else str(intent_type or "GENERAL").upper()
    capability_id = _BY_INTENT.get(key, "GENERAL_CHAT")
    return get_state(capability_id)


def set_access(capability_id: str, state: str) -> list[dict[str, Any]]:
    key = str(capability_id or "").upper()
    if key not in _BY_ID:
        raise KeyError(f"Unknown capability: {capability_id}")
    if state not in {ENABLED, DISABLED, ADMIN_ONLY}:
        raise ValueError("state must be ENABLED, DISABLED, or ADMIN_ONLY")
    if key == "GENERAL_CHAT" and state == DISABLED:
        raise ValueError("GENERAL_CHAT cannot be disabled; protected conversational access remains available")
    with _LOCK:
        access = _read_access()
        access[key] = state
        _write_access(access)
        return get_states()


def reset_defaults() -> list[dict[str, Any]]:
    with _LOCK:
        _write_access(_default_access())
        return get_states()


def configuration() -> dict[str, Any]:
    states = get_states()
    return {"schema_version": SCHEMA_VERSION, "policy_version": POLICY_VERSION, "capabilities": states, "protected_safeguards": {"state": "ACTIVE", "configurable": False, "note": "Safety, privacy, prompt-leak, and high-stakes safeguards cannot be disabled."}}


def disabled_reply(state: CapabilityState) -> str:
    return f"The {state.label} capability is currently disabled by configuration. An administrator can enable it in Veda Configuration. Other conversational assistance remains available."


__all__ = ["ADMIN_ONLY", "DISABLED", "ENABLED", "POLICY_VERSION", "SCHEMA_VERSION", "configuration", "definitions", "disabled_reply", "get_state", "get_states", "reset_defaults", "resolve_intent", "set_access"]
