from __future__ import annotations

import json

from scripts.veda_muhurta_electional_core_primitives_001 import (
    OUT,
    T2_HASHES,
    T3_HASHES,
    build_bundle,
    digest,
    lagna_factor_contract,
    lagna_rashi_from_longitude,
    write_artifacts,
)
from scripts.veda_muhurta_house_electional_factor_hardening_001 import build_bundle as build_t2_bundle


def test_lagna_factor_reuses_canonical_path_and_abstains_at_boundary():
    factor = build_bundle()["lagna_factor"]
    assert factor["calculation_source"].endswith("KundliEngine._ascendant")
    assert factor["method"] == "SWISS_HOUSES_W_PLUS_EXPLICIT_LAHIRI_SUBTRACTION"
    assert factor["maturity"] == "LAGNA_FACTOR_READY_WITH_BOUNDARY_ABSTENTION"
    assert factor["boundary_policy"]["classification"] == "LAGNA_BOUNDARY_AMBIGUOUS"
    assert "GOOD_LAGNA" in factor["semantic_limit"]


def test_all_twelve_rashi_mapping_and_wrap():
    assert [lagna_rashi_from_longitude(index * 30.0) for index in range(12)] == build_bundle()["lagna_factor"]["canonical_enum"]
    assert lagna_rashi_from_longitude(360.0) == "ARIES"
    assert lagna_rashi_from_longitude(-0.1) == "PISCES"


def test_lagna_transition_diagnostic_covers_all_boundaries_deterministically():
    validation = build_bundle()["lagna_transition_validation"]
    assert validation["production_registered"] is False
    assert validation["fixed_grid_final_boundaries"] is False
    assert len(validation["rows"]) == 12
    assert all(row["status"] == "PASS" for row in validation["rows"])
    assert validation["determinism_hash"] == digest(validation["rows"])


def test_planetary_facts_are_separate_from_advisory_semantics():
    bundle = build_bundle()
    inventory = bundle["planetary_inventory"]
    assert inventory["new_ephemeris"] is False
    assert "GOOD_PLANETS" in inventory["not_bound"]
    assert bundle["planetary_contracts"]["PLANET_HOUSE_FROM_LAGNA"]["advisory_semantics"] == "SOURCE_PARTIAL; ACTIVITY_SPECIFIC_RULE_REQUIRED"


def test_godhuli_does_not_become_a_sunset_timestamp_or_advisory_rule():
    bundle = build_bundle()
    audit = bundle["godhuli_audit"]
    contract = bundle["godhuli_contract"]
    assert audit["instant_or_interval"].startswith("UNRESOLVED")
    assert contract["interval_status"] == "NOT_VALIDATED"
    assert contract["candidate_evaluation"] == "ABSTAIN_SOURCE_INTERVAL_UNRESOLVED"
    assert contract["advisory_effect"] == "NONE_IN_FACTOR_LAYER"


def test_t2_t3_hashes_and_no_production_binding():
    bundle = build_bundle()
    assert bundle["preserved_hashes"]["t2"] == T2_HASHES
    assert bundle["preserved_hashes"]["t3"] == T3_HASHES
    t3_marriage = json.loads((OUT.parent / "muhurta-activity-expansion-t3-001" / "07_SELECTED_ACTIVITY_A_RULE_CONTRACT.json").read_text(encoding="utf-8"))
    t3_machine = json.loads((OUT.parent / "muhurta-activity-expansion-t3-001" / "08_SELECTED_ACTIVITY_A_MACHINE_CONTRACT.json").read_text(encoding="utf-8"))
    t2_reconciliation = build_t2_bundle()["t2_reconciliation"]
    assert t2_reconciliation["all_hashes_match"] is True
    assert t3_marriage["contract_hash"] == T3_HASHES["MARRIAGE_CONTRACT"]
    assert t3_machine["machine_hash"] == T3_HASHES["MARRIAGE_MACHINE"]
    assert bundle["machine_bindings"]["production_bindings"] == []
    assert bundle["capability_register"]["no_production_activity_registration"] is True


def test_no_generic_scoring_or_personal_bala_activation():
    bundle = build_bundle()
    assert bundle["machine_bindings"]["new_operator_implementation"] is False
    assert "numeric electional score" in bundle["machine_bindings"]["forbidden"]
    assert bundle["parallel_state"]["Personal Tara/Chandra Bala"] == "diagnostic-only; production inactive"


def test_generated_artifacts_match_deterministic_payload():
    write_artifacts()
    assert json.loads((OUT / "04_LAGNA_FACTOR_CONTRACT.json").read_text(encoding="utf-8")) == lagna_factor_contract()
    assert lagna_factor_contract()["hash"] == json.loads((OUT / "04_LAGNA_FACTOR_CONTRACT.json").read_text(encoding="utf-8"))["hash"]
    acceptance = json.loads((OUT / "21_ACCEPTANCE_REGISTER.json").read_text(encoding="utf-8"))
    assert len(acceptance) == 26
    assert not {row["status"] for row in acceptance}.intersection({"FAIL", "BLOCKED"})
