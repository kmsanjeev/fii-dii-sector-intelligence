from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.veda_muhurta_dedicated_classical_source_rx2_001 import (
    ARCHIVE_URL,
    BUSINESS_V3,
    EDUCATION_V3,
    OUT,
    STARTING_COMMIT,
    build,
    canonical,
    contract_hash,
    emit,
)


def _read(name: str):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def test_baseline_and_predecessor_hashes_are_explicit():
    result = build()
    assert STARTING_COMMIT == "33d9ec17938ea4ea352c6c23a21e4c17b4063dda"
    assert result["business"]["supersedes"]["legacy_v3_hash"] == BUSINESS_V3
    assert result["education"]["supersedes"]["legacy_v3_hash"] == EDUCATION_V3


def test_blocker_necessity_audit_does_not_turn_contextual_rules_into_hard_rules():
    audit = build()["blocker_audit"]
    assert audit["business"]["hard_exclusion"] is False
    assert audit["business"]["hard_requirement"] is False
    assert audit["business"]["decision"] == "NON_BLOCKING_SCOPE_GAP"
    assert audit["education"]["education_karana_source_mandatory"] is False


def test_brihat_derivation_rejects_loose_deity_equivalence():
    audit = build()["brihat"]
    assert audit["decision"] == "DERIVATION_BOUNDED_NO_LOOSE_DEITY_EQUIVALENCE"
    assert any("deity" in item.lower() for item in audit["rejected_derivations"])


def test_education_tithi_is_the_only_new_activity_tithi_predicate():
    result = build()
    education = result["education"]
    tithi = next(rule for rule in education["rules"] if rule["rule_id"] == "MUH-EDU-TITHI-VIDYARAMBHA-001")
    assert tithi["expected_set"] == [2, 3, 5, 6, 10, 11, 12]
    assert tithi["executability_state"] == "MACHINE_READY"
    assert tithi["production_activation"] is False
    assert not any(rule["rule_id"] == "MUH-BIZ-TITHI-SCOPE-GAP-001" for rule in education["rules"])


def test_business_scope_gap_and_education_karana_gap_abstain():
    result = build()
    business_gap = next(rule for rule in result["business"]["rules"] if rule["rule_id"] == "MUH-BIZ-TITHI-SCOPE-GAP-001")
    education_gap = next(rule for rule in result["education"]["rules"] if rule["rule_id"] == "MUH-EDU-KARANA-SCOPE-GAP-001")
    for rule in (business_gap, education_gap):
        assert rule["recommendation_effect"] == "ABSTAIN"
        assert rule["executability_state"] == "SOURCE_PARTIAL_NON_BLOCKING"
        assert rule["blocking_classification"] == "NON_BLOCKING_ADDITIONAL_COVERAGE"
        assert rule["hard_requirement"] is False


def test_both_v4_contracts_are_deterministic_and_engine_inactive():
    result = build()
    emit(result)
    for contract in (result["business"], result["education"]):
        assert contract["contract_hash_full"] == contract_hash(contract)
        assert contract["blocking_rule_ids"] == []
        assert contract["recommendation_engine_state"] == "MACHINE_CONTRACT_READY_WITH_NONBLOCKING_SOURCE_GAPS"
        assert contract["production_bound"] is False
    handoff = _read("14_ENGINE_HANDOFF_RX1.json")
    assert handoff["authorized"] is True
    assert handoff["state"] == "FUTURE_IMPLEMENTATION_AUTHORIZED_NOT_STARTED"


def test_source_registry_has_rights_and_ocr_uncertainty():
    result = build()
    registry = result["source_register"]
    archive = next(item for item in registry["sources"] if item["source_id"] == "VEDA-SWW-WORK-MUHURTACINTAMANI-RAMA-001")
    education = next(item for item in registry["sources"] if item["source_id"] == "VEDA-SWW-PASSAGE-MC-VIDYARAMBHA-001")
    assert archive["rights_state"] == "RESEARCH_ONLY"
    assert education["ocr_used"] is True
    assert education["ocr_verified"] == "CONDITIONAL"
    assert "raw" in registry["sources"][0]["rights_basis"] or "raw" in archive["rights_basis"]


def test_research_log_records_accessed_and_rejected_evidence():
    emit(build())
    log = _read("19_RESEARCH_LOG.json")
    assert ARCHIVE_URL in log["actual_sources_accessed"]
    assert log["rejected_or_downgraded"]
    assert log["unresolved"]


def test_no_production_side_effects_are_declared():
    result = build()
    validation = result["compatibility"]
    assert validation["education"]["decision"] == "ADMIT_TITHI_SET_ONLY"
    assert result["business"]["activity_id"] == "BUSINESS_OPENING_INAUGURATION"
    assert result["education"]["activity_id"] == "EDUCATION_COMMENCEMENT"


def test_acceptance_register_is_complete_and_no_failures():
    emit(build())
    acceptance = _read("18_FINAL_ACCEPTANCE.json")
    assert len(acceptance["criteria"]) == 118
    assert acceptance["counts"]["FAIL"] == 0
    assert acceptance["counts"]["BLOCKED"] == 0
    assert acceptance["overall"] == "PASS_WITH_CONDITION"


def test_canonical_serialization_is_stable():
    value = {"z": 1, "a": ["x", 2]}
    assert canonical(value) == '{"a":["x",2],"z":1}'
    assert hashlib.sha256(canonical(value).encode()).hexdigest() == hashlib.sha256(canonical(value).encode()).hexdigest()
