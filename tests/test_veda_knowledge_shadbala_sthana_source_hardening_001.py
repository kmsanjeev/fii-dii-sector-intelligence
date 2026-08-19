"""Focused validation for the Sthana Bala source-hardening activity."""

import json
from pathlib import Path

from scripts.veda_knowledge_shadbala_sthana_source_hardening_001 import (
    OUT,
    build_result,
    emit,
)


def test_sthana_inventory_is_claim_level_and_non_production():
    result = build_result()
    assert result["production_change"] is False
    assert [row["component"] for row in result["components"]] == ["UCHCHA", "SAPTAVARGAJA", "OJHAYUGMA", "KENDRADI", "DREKKANA"]
    assert result["runtime_inventory"]["subcomponents_present"] == {
        "UCHCHA": True,
        "SAPTAVARGAJA": False,
        "OJHAYUGMA": True,
        "KENDRADI": True,
        "DREKKANA": False,
    }


def test_source_and_runtime_boundaries_are_separate():
    rows = {row["component"]: row for row in build_result()["components"]}
    assert rows["UCHCHA"]["runtime_classification"] == "NORMALIZATION_EQUIVALENT"
    assert rows["SAPTAVARGAJA"]["runtime_classification"] == "ABSENT"
    assert rows["OJHAYUGMA"]["runtime_classification"] == "SIMPLIFIED_IMPLEMENTATION"
    assert rows["KENDRADI"]["readiness"] == "REMEDIATION_READY"
    assert rows["DREKKANA"]["readiness"] == "NOT_IMPLEMENTED_NOT_JUSTIFIED"
    assert build_result()["aggregate"]["status"] == "COMPONENT_LEVEL_ONLY"


def test_no_oracle_is_created_from_incomplete_source():
    result = build_result()
    assert result["oracle_status"]["independent_oracles"] == 0
    assert result["oracle_status"]["external_numerical_validation"] == "UNAVAILABLE"


def test_parallel_state_and_approved_core_are_preserved():
    governance = build_result()["governance"]
    assert governance["approved_core_before"] == governance["approved_core_after"] == 17
    assert governance["rag_documents_before"] == governance["rag_documents_after"] == 1205
    assert all(governance[name] is False for name in ("naisargika_changed", "dig_changed", "aggregate_changed", "kala_changed", "cheshta_changed", "drik_changed"))


def test_emitted_package_is_deterministic_and_acceptance_has_no_failures():
    result = build_result()
    emit(result)
    first = {path.name: path.read_bytes() for path in OUT.iterdir() if path.is_file()}
    emit(result)
    second = {path.name: path.read_bytes() for path in OUT.iterdir() if path.is_file()}
    assert first == second
    acceptance = json.loads((OUT / "15_FINAL_ACCEPTANCE.json").read_text(encoding="utf-8"))
    assert acceptance["fail"] == 0
    assert acceptance["blocked"] == 0
    assert acceptance["overall"] == "PASS_WITH_CONDITION"
