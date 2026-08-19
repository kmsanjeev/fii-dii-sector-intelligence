"""Focused tests for VEDA-MUHURTA-TITHI-KARANA-SOURCE-HARDENING-RX1-001."""

import json
from pathlib import Path

from scripts.veda_muhurta_tithi_karana_source_hardening_rx1_001 import (
    BUSINESS_V3,
    EDUCATION_V3,
    build,
    emit,
)


def test_remaining_blockers_are_not_silently_promoted():
    result = build()
    assert result["decision"] == "MUHURTA_BLOCKING_SEMANTICS_PARTIAL"
    assert result["business_ready"] is False
    assert result["education_ready"] is False
    assert result["business_tithi"]["machine_predicate"] is None
    assert result["education_tithi"]["machine_predicate"] is None
    assert result["education_karana"]["machine_predicate"] is None


def test_business_vara_yoga_is_explicitly_non_blocking_unresolved():
    result = build()
    audit = result["business_vara_yoga"]
    assert audit["decision"] == "NON_BLOCKING_UNRESOLVED"
    assert audit["current_effect"] == "ABSTAIN"
    assert audit["blocking_classification"] == "NON_BLOCKING_UNRESOLVED"


def test_frozen_v3_hashes_are_preserved():
    result = build()
    assert result["hashes_preserved"] is True
    assert result["computed_hashes"]["business_v3"] == BUSINESS_V3
    assert result["computed_hashes"]["education_v3"] == EDUCATION_V3


def test_no_v4_or_engine_handoff_is_created():
    result = build()
    assert result["engine_handoff_created"] is False
    assert result["rx1_authorized"] is False


def test_artifacts_are_deterministic():
    emit(build())
    first = {p.name: p.read_bytes() for p in Path("docs/current-state/muhurta-tithi-karana-source-hardening-rx1-001").iterdir()}
    emit(build())
    second = {p.name: p.read_bytes() for p in Path("docs/current-state/muhurta-tithi-karana-source-hardening-rx1-001").iterdir()}
    assert first == second
    acceptance = json.loads(Path("docs/current-state/muhurta-tithi-karana-source-hardening-rx1-001/13_FINAL_ACCEPTANCE.json").read_text(encoding="utf-8"))
    assert acceptance["contracts_preserved"] is True
