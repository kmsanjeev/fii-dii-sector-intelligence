"""Focused regression tests for VEDA Muhurta activity expansion T3."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.veda_muhurta_activity_expansion_t3_001 import (
    COMPLETED,
    HOUSE_ACTIVITIES,
    HOUSE_EXPECTED,
    SELECTED,
    build_bundle,
    canonical,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/current-state/muhurta-activity-expansion-t3-001"


def _digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest().upper()


def test_inventory_reuses_and_excludes_authoritative_scopes():
    bundle = build_bundle()
    remaining = {row["activity_id"] for row in bundle["inventory"]["remaining"]}
    assert len(remaining) == 7
    assert not remaining.intersection(COMPLETED)
    assert remaining.intersection(HOUSE_ACTIVITIES) == HOUSE_ACTIVITIES
    assert not set(SELECTED).intersection(HOUSE_ACTIVITIES)
    assert SELECTED == ["MARRIAGE_CEREMONY_TIMING"]
    assert bundle["inventory"]["numeric_readiness_score"] is False


def test_house_lane_hashes_and_freeze_are_preserved():
    bundle = build_bundle()
    for activity_id, expected in HOUSE_EXPECTED.items():
        row = bundle["house_lane_freeze"][activity_id]
        assert row["contract_hash"] == expected["contract_hash"]
        assert row["machine_hash"] == expected["machine_hash"]
        assert row["frozen"] is True
        assert row["reopen_trigger"] == "REOPEN_ON_NEW_ELECTIONAL_SOURCE_EVIDENCE"


def test_marriage_contract_has_complete_machine_metadata_but_remains_partial():
    bundle = build_bundle()
    contract = bundle["selected"]["rule_contract"]
    machine = bundle["selected"]["machine_contract"]
    assert contract["readiness"] == "SOURCE_CONTRACT_READY_MACHINE_PARTIAL"
    assert contract["production_bound"] is False
    assert machine["machine_state"] == "SOURCE_CONTRACT_READY_MACHINE_PARTIAL"
    assert machine["production_activation"] is False
    assert machine["no_runtime_registration"] is True
    assert machine["no_numeric_score"] is True
    for predicate in machine["predicates"]:
        assert predicate["factor_id"]
        assert predicate["evaluator_id"]
        assert predicate["operator"]
        assert "missing_value_policy" in predicate
        assert "recommendation_effect" in predicate
        assert "source_assertion_ids" in predicate


def test_variant_and_safety_boundaries_are_explicit():
    bundle = build_bundle()
    contract = bundle["selected"]["rule_contract"]
    assert "NO_PARTNER_MATCHING" in contract["context_rules"]
    assert "NO_SHOULD_MARRY_DECISION" in contract["context_rules"]
    assert "MARRIAGE_OUTCOME_OR_DURATION_GUARANTEE" in contract["hard_exclusions"]
    assert "GODHULI_OVERRIDE_SCOPE_VARIANT" in contract["variants"]
    assert bundle["handoff"]["machine_ready_activities"] == []


def test_dry_runs_cover_scope_missing_context_and_trace():
    cases = {row["case"]: row for row in build_bundle()["dry_runs"]}
    assert set(cases) == {
        "supporting_godhuli_context",
        "nonmatching_context",
        "missing_factor",
        "scope_mismatch",
        "required_context_missing",
        "variant_isolation",
        "source_trace",
    }
    assert cases["scope_mismatch"]["expected"] == "ABSTAIN_ACTIVITY_SCOPE_MISMATCH"
    assert cases["missing_factor"]["expected"] == "ABSTAIN_MISSING_ELECTIONAL_FACTORS"
    assert all(row["production"] is False for row in cases.values())


def test_source_lineage_and_rights_are_recorded():
    source = build_bundle()["source_research"]
    assert source["lineage"] == "MACHINE PREDICATE -> RULE -> ASSERTION -> PASSAGE -> EDITION -> WITNESS -> WORK"
    assert len(source["accepted_witnesses"]) == 3
    assert all(item["url"].startswith("https://") for item in source["accepted_witnesses"])
    assert source["ocr_used"] is False
    assert any("ocr" in item["claim"].lower() for item in source["downgraded_or_rejected"])


def test_contract_and_machine_hashes_are_self_consistent():
    bundle = build_bundle()
    contract = dict(bundle["selected"]["rule_contract"])
    machine = dict(bundle["selected"]["machine_contract"])
    contract_hash = contract.pop("contract_hash")
    machine_hash = machine.pop("machine_hash")
    assert contract_hash == _digest(contract)
    assert machine_hash == _digest(machine)


def test_written_bundle_is_deterministic_and_no_selected_b_exists():
    expected = json.loads((OUT / "07_SELECTED_ACTIVITY_A_RULE_CONTRACT.json").read_text(encoding="utf-8"))
    assert expected["activity_id"] == "MARRIAGE_CEREMONY_TIMING"
    assert not (OUT / "09_SELECTED_ACTIVITY_B_RULE_CONTRACT.json").exists()
    assert not (OUT / "10_SELECTED_ACTIVITY_B_MACHINE_CONTRACT.json").exists()
    assert json.loads((OUT / "16_ENGINE_HANDOFF_T3.json").read_text(encoding="utf-8"))["machine_ready_activities"] == []
