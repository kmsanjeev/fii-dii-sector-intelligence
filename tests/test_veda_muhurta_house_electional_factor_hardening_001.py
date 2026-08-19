from __future__ import annotations

import json

from scripts.veda_muhurta_house_electional_factor_hardening_001 import (
    OUT,
    RASHIS,
    build_bundle,
    digest,
    lagna_factor_contract,
)


def test_t2_contracts_are_preserved_and_hash_verified():
    bundle = build_bundle()
    assert bundle["t2_reconciliation"]["all_hashes_match"] is True
    assert bundle["t2_reconciliation"]["supersession_created"] is False


def test_lagna_factor_reuses_canonical_calculation_with_conditions():
    bundle = build_bundle()
    factor = bundle["lagna_factor"]
    assert factor["factor_id"] == "MUHURTA_LAGNA_SIGN"
    assert factor["canonical_enum"] == RASHIS
    assert len(factor["canonical_enum"]) == 12
    assert factor["validation_state"] == "INTERNAL_CALCULATION_VALIDATED_WITH_CONDITIONS"
    assert factor["new_calculation_created"] is False
    assert factor["boundary_policy"]["classification"] == "BOUNDARY_POLICY_REQUIRED"


def test_source_semantics_and_planetary_context_remain_partial():
    bundle = build_bundle()
    assert bundle["lagna_source_semantics"]["machine_semantics_decision"] == "SOURCE_PARTIAL"
    assert bundle["planetary_dependencies"]["machine_state"] == "PLANETARY_DEPENDENCY_PARTIAL"
    assert bundle["planetary_dependencies"]["dependency_states"]["aspect"] == "AVAILABLE_BUT_NOT_GOVERNED_FOR_MUHURTA"
    assert bundle["planetary_dependencies"]["dependency_states"]["benefic_malefic_classification"] == "SOURCE_SEMANTICS_UNRESOLVED"


def test_griha_context_requires_source_bounded_fields_and_abstains_on_missing():
    context = build_bundle()["context_schema"]
    assert context["source_context"]["construction_state"]["status"] == "REQUIRED"
    assert context["source_context"]["puja_completed"]["status"] == "REQUIRED"
    assert context["source_context"]["first_occupancy"]["status"] == "SOURCE_VARIANT"
    assert context["missing_required_policy"] == "ABSTAIN"
    assert context["invalid_or_unknown_policy"] == "FAIL_CLOSED"


def test_both_machine_contracts_remain_partial_and_nonproduction():
    bundle = build_bundle()
    for contract in bundle["machine_contracts"].values():
        assert contract["machine_state"] == "MACHINE_PARTIAL"
        assert contract["production_activation"] is False
        assert contract["no_runtime_registration"] is True
        assert contract["no_numeric_score"] is True
        assert any(item["state"] == "NOT_BOUND" for item in contract["declarative_predicates"])


def test_lagna_exhaustive_synthetic_matrix_and_abstention():
    validation = build_bundle()["synthetic_validation"]
    assert validation["lagna_sign_cases_per_activity"] == 12
    assert validation["case_count"] == 34
    assert validation["all_nonproduction"] is True
    assert all(row["expected"] in {"ABSTAIN", "ABSTAIN_SOURCE_SEMANTICS_UNRESOLVED"} for row in validation["rows"])


def test_window_and_handoff_are_not_falsely_ready():
    bundle = build_bundle()
    assert bundle["handoff"]["generated"] is False
    assert bundle["handoff"]["machine_ready_activities"] == []
    assert bundle["window_readiness"]["fixed_sampling_introduced"] is False
    assert all(item["single_candidate"] == "NOT_READY" for item in bundle["window_readiness"].values() if isinstance(item, dict))


def test_generated_artifacts_match_deterministic_contract_payload():
    assert json.loads((OUT / "03_LAGNA_FACTOR_CONTRACT.json").read_text(encoding="utf-8")) == lagna_factor_contract()
    assert digest(lagna_factor_contract()) == digest(json.loads((OUT / "03_LAGNA_FACTOR_CONTRACT.json").read_text(encoding="utf-8")))
    assert json.loads((OUT / "15_ENGINE_HANDOFF_T2_RX.json").read_text(encoding="utf-8"))["machine_ready_activities"] == []
