import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/current-state/evidence-posend-design-freeze-001"
R1 = ROOT / "docs/current-state/evidence-posend-acq-r1/FINAL_MANIFEST.json"


def read(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def test_r1_hashes_and_feature_family_are_preserved():
    pilot = read("01_R1_PILOT_FREEZE.json")
    r1 = json.loads(R1.read_text(encoding="utf-8"))
    assert pilot["subjects"] == pilot["events"] == 4
    assert pilot["validation"] == 3 and pilot["holdout"] == 1
    assert pilot["feature_values_inspected"] is False
    assert pilot["holdout_opened"] is False
    assert pilot["hashes"]["birth_frame_hash"] == r1["birth_frame"]["subject_hash"]
    family = read("06_FEATURE_FAMILY_FREEZE.json")
    assert family["feature_count"] == 5
    assert family["feature_family_hash"] == "da810777ea18ff74ebcdb9b3003dd8a0b4a5b88f68cd79b0c27b569c18340297"
    assert family["changed"] == 0
    assert family["activation_accessed"] is False


def test_event_eligibility_and_control_policy_are_frozen():
    event = read("03_ELIGIBILITY_CONTRACT.json")
    policy = (OUT / "04_RISK_SET_AND_CONTROL_POLICY.md").read_text(encoding="utf-8")
    assert event["date_precision"] == "DAY for role start and role end"
    assert event["mortality_policy"] == "ROLE_END_BY_DEATH_EXCLUDED"
    assert "four deterministic interior-quantile controls" in policy
    assert "14-day pre-event exclusion" in policy


def test_r1_controls_are_valid_without_rewriting_history():
    manifest = read("FINAL_MANIFEST.json")
    assert manifest["control_policy"]["r1_validation"]["all_valid_under_protocol"] is True
    assert manifest["control_policy"]["r1_validation"]["invalid_controls"] == []
    assert manifest["control_policy"]["future_controls_per_event"] == 4
    assert manifest["control_policy"]["r1_historical_controls_per_event"] == 2


def test_power_is_matched_scenario_only_and_r1_is_not_powered():
    power = read("09_MATCHED_POWER_MODEL.json")
    assert power["primary_controls_per_event"] == 4
    assert power["r1_powered"] is False
    assert power["r1_suitable_for_effect_estimation"] is False
    assert len(power["scenarios"]) == 27
    assert all(row["method"].startswith("MATCHED_RISK_SET") for row in power["scenarios"])
    assert all(row["approximate_independent_event_subjects"] > 0 for row in power["scenarios"])


def test_synthetic_simulation_is_not_real_r1_data():
    sim = read("17_SYNTHETIC_POWER_SIMULATION.json")
    assert sim["status"] == "PASS"
    assert sim["real_r1_subject_ids_used"] is False
    assert sim["real_r1_feature_values_used"] is False
    assert sim["astrology_used"] is False
    assert len(sim["results"]) == 3


def test_protocol_hash_and_safety_state():
    protocol = read("14_PROTOCOL_HASH.json")
    manifest = read("FINAL_MANIFEST.json")
    assert protocol["protocol_id"] == "POSEND_FORMAL_ROLE_END_PROTOCOL"
    assert protocol["protocol_version"] == "v1"
    assert len(protocol["protocol_hash"]) == 64
    assert manifest["protocol_hash"] == protocol["protocol_hash"]
    assert manifest["safety"]["astrology"] == "NO"
    assert manifest["safety"]["feature_scoring"] == "NO"
    assert manifest["safety"]["ml"] == "LOCKED"
    assert manifest["safety"]["subject_data_added_to_rag"] is False
    assert manifest["next_programme_started"] is False


def test_source_diversity_and_holdout_gates():
    manifest = read("FINAL_MANIFEST.json")
    diversity = manifest["source_diversity"]
    assert diversity["r1_birth_clusters"] == 1
    assert diversity["confirmatory_single_birth_cluster_allowed"] is False
    assert diversity["future_confirmatory_gate"]["minimum_independent_birth_source_clusters"] == 2
    assert manifest["r2_protocol"]["status"] == "NOT_STARTED"


def test_design_freeze_script_has_no_calculation_or_result_reader_dependency():
    source = (ROOT / "scripts/veda_evidence_posend_design_freeze_001.py").read_text(encoding="utf-8")
    forbidden = (
        "KundliEngine", "astro_engine", "swisseph", "pyswisseph",
        "calculate_d1", "feature_activation_files", "holdout_results",
        "association_results", "sklearn", "scikit-learn",
    )
    assert all(token not in source for token in forbidden)
