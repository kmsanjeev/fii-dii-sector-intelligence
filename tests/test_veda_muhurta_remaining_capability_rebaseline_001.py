from __future__ import annotations

from scripts.veda_muhurta_remaining_capability_rebaseline_001 import (
    FROZEN_ELECTIONAL,
    OPERATIONAL,
    OUT,
    REMAINING,
    CORE_HASHES,
    acceptance,
    build,
    canonical_inventory,
    gate,
    frozen_register,
    operational_register,
    selection_decision,
)


def test_inventory_reconciles_operational_frozen_and_remaining_without_duplicates():
    inventory = canonical_inventory()
    ids = [row["activity_id"] for row in inventory["activities"]]
    assert len(ids) == len(set(ids))
    assert inventory["remaining_count"] == 4
    assert inventory["operational_excluded_from_selection"] == OPERATIONAL
    assert inventory["frozen_excluded_from_selection"] == FROZEN_ELECTIONAL
    assert inventory["remaining_candidates"] == REMAINING


def test_operational_register_and_frozen_backlog_are_preserved():
    operational = operational_register()
    assert operational["count"] == 4
    assert all(row["runtime_state"] == "OPERATIONAL" for row in operational["activities"])
    frozen = frozen_register()
    assert [row["activity_id"] for row in frozen["activities"]] == FROZEN_ELECTIONAL
    assert frozen["electional_core"]["lagna_hash"] == CORE_HASHES["MUHURTA_LAGNA_SIGN"]
    assert frozen["electional_core"]["godhuli_hash"] == CORE_HASHES["GODHULI"]


def test_all_remaining_candidates_fail_executability_gate_without_calculation_only_failure():
    result = gate()
    assert result["passing_candidates"] == []
    assert result["failing_source_semantics"] == REMAINING
    assert result["failing_calculation_only"] == []
    assert result["engineering_only_blockers"] == []
    assert result["selection_allowed"] is False


def test_zero_selection_is_deterministic_and_creates_no_contracts():
    decision = selection_decision()
    assert decision["selected"] == []
    assert decision["forced_selection"] is False
    assert decision["new_contracts_created"] == []
    assert decision["no_empty_engine_programme"] is True


def test_build_freezes_expansion_and_preserves_parallel_state():
    result = build()
    assert result["stop"]["decision"] == "FREEZE_MUHURTA_ACTIVITY_EXPANSION_PENDING_NEW_EVIDENCE"
    assert result["handoff"]["runtime_programme_authorized"] is False
    assert result["parallel"]["Approved_Core_before"] == 17
    assert result["parallel"]["Approved_Core_after"] == 17
    assert result["parallel"]["RAG"] == "UNCHANGED"
    assert result["lane"]["not_started"] is True
    assert (OUT / "17_FINAL_ACCEPTANCE.md").exists()


def test_acceptance_is_conditioned_without_failure():
    final = acceptance()
    assert final["decision"] == "MUHURTA_REBASELINE_ACTIVITY_EXPANSION_FREEZE_NEW_EVIDENCE_REQUIRED"
    assert final["counts"]["FAIL"] == 0
    assert final["counts"]["BLOCKED"] == 0
