from __future__ import annotations

from pathlib import Path

from scripts.veda_muhurta_electional_contract_remediation_rx1_001 import (
    CORE_HASHES,
    OUT,
    T2_HASHES,
    T3_HASHES,
    activity_next_contracts,
    blocker_necessity_reaudit,
    build,
    core_binding_register,
    final_acceptance,
    predecessor_register,
    source_count_audit,
)


def test_predecessor_and_core_hashes_are_preserved():
    predecessor = predecessor_register()
    assert all(row["contract_preserved"] and row["machine_preserved"] for row in predecessor["activities"].values())
    bindings = core_binding_register()
    assert bindings["lagna"]["hash"] == CORE_HASHES["MUHURTA_LAGNA_SIGN"]
    assert bindings["godhuli"]["hash"] == CORE_HASHES["GODHULI"]
    assert T2_HASHES["HOUSE_CONSTRUCTION_COMMENCEMENT_CONTRACT"]
    assert T3_HASHES["MARRIAGE_CONTRACT"]


def test_blocker_necessity_reaudit_does_not_promote_unsupported_semantics():
    rows = blocker_necessity_reaudit()["activities"]
    for activity in rows:
        assert rows[activity]["result"] == "CONTRACT_BLOCKED"
        assert rows[activity]["lagna_semantics"]["current"] == "BLOCKING_SOURCE_MANDATORY"
        assert rows[activity]["planetary_semantics"]["current"] == "BLOCKING_SOURCE_MANDATORY"
    assert rows["HOUSE_ENTRY_OR_GRIHA_PRAVESHA"]["context"]["first_occupancy"]["state"] == "NONBLOCKING_CONTEXT_GAP"
    assert rows["MARRIAGE_CEREMONY_TIMING"]["godhuli"]["current"] == "NONBLOCKING_ADDITIONAL_COVERAGE"


def test_no_v2_or_production_handoff_is_created():
    contracts = activity_next_contracts()
    assert all(row["v2_created"] is False and row["v2_hash"] is None for row in contracts.values())
    result = build()
    assert result["handoff"]["engine_handoff"] == "NOT_AUTHORIZED"
    assert result["handoff"]["machine_ready_activities"] == []


def test_source_count_root_cause_is_explicit():
    audit = source_count_audit()
    assert audit["observed_source_count"] == 14
    assert audit["authoritative_architecture_count"] == 14
    assert audit["stale_test_expectation_before"] == 13
    assert audit["classification"] == "STALE_TEST_INVARIANT"
    assert "VEDA-SRC-000014" in audit["source_ids"]


def test_output_registers_are_json_and_scope_safe():
    build()
    assert (OUT / "18_FINAL_ACCEPTANCE.md").exists()
    acceptance = final_acceptance()
    assert acceptance["overall"] == "PASS_WITH_CONDITION"
    assert acceptance["counts"]["FAIL"] == 0
    text = "\n".join(path.read_text(encoding="utf-8") for path in OUT.iterdir() if path.is_file())
    for forbidden in ("ELECTIONAL_SCORE", "GOOD_LAGNA", "GOOD_PLANET_CONFIGURATION"):
        assert forbidden not in text
