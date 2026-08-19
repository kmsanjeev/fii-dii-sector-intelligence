from __future__ import annotations

import json
from pathlib import Path

from scripts.veda_muhurta_activity_expansion_t2_001 import (
    COMPLETED,
    OUT,
    SELECTED,
    build_bundle,
    digest,
    machine_payload,
    contract_payload,
)


def test_t1_inventory_is_reused_and_completed_activities_are_excluded():
    bundle = build_bundle()
    assert bundle["inventory"]["original_candidates"] == 9
    assert len(bundle["inventory"]["remaining"]) == 7
    assert not COMPLETED.intersection({row["activity_id"] for row in bundle["inventory"]["remaining"]})
    assert bundle["inventory"]["selected"] == SELECTED
    assert bundle["inventory"]["numeric_readiness_score"] is False


def test_t2_selection_is_deterministic_and_machine_partial():
    first = build_bundle()
    second = build_bundle()
    assert first == second
    assert first["handoff"]["machine_ready_activities"] == []
    assert all(item["machine_state"] == "MACHINE_PARTIAL" for item in first["machines"].values())


def test_contract_and_machine_hashes_are_stable_and_lineage_bound():
    bundle = build_bundle()
    for activity_id in SELECTED:
        contract = bundle["contracts"][activity_id]
        machine = bundle["machines"][activity_id]
        assert contract["contract_hash"] == digest(contract_payload(activity_id))
        assert machine["machine_hash"] == digest(machine_payload(activity_id))
        assert contract["production_bound"] is False
        assert machine["production_activation"] is False
        assert machine["source_assertion_ids"]
        assert all(predicate["missing_value_policy"] == "ABSTAIN" for predicate in machine["predicates"])


def test_synthetic_dry_runs_never_claim_production_support():
    bundle = build_bundle()
    assert len(bundle["dry_runs"]) == 6
    assert all(item["expected"] == "ABSTAIN_MISSING_ELECTIONAL_FACTORS" for item in bundle["dry_runs"])
    assert all(item["production"] is False for item in bundle["dry_runs"])


def test_generated_contract_files_are_distinct_and_valid():
    expected = {
        "06_SELECTED_ACTIVITY_A_RULE_CONTRACT.json": "HOUSE_CONSTRUCTION_COMMENCEMENT",
        "07_SELECTED_ACTIVITY_A_MACHINE_CONTRACT.json": "HOUSE_CONSTRUCTION_COMMENCEMENT",
        "09_SELECTED_ACTIVITY_B_RULE_CONTRACT.json": "HOUSE_ENTRY_OR_GRIHA_PRAVESHA",
        "10_SELECTED_ACTIVITY_B_MACHINE_CONTRACT.json": "HOUSE_ENTRY_OR_GRIHA_PRAVESHA",
    }
    for filename, activity_id in expected.items():
        payload = json.loads((OUT / filename).read_text(encoding="utf-8"))
        assert payload["activity_id"] == activity_id
    assert json.loads((OUT / "15_ENGINE_HANDOFF_T2.json").read_text(encoding="utf-8"))["machine_ready_activities"] == []


def test_no_production_engine_registration_is_created():
    bundle = build_bundle()
    assert bundle["baseline"]["production_activation"] is False
    assert bundle["handoff"]["production_activation"] is False
    assert not any("recommend" in key.lower() for key in bundle["handoff"])
