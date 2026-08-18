"""Focused feature-blind controls for the POSITION_END redesign."""

import hashlib
import json

from scripts.veda_evidence_posend_rebaseline_001 import OUT, build, digest, write


def test_cohort_freeze_and_split_are_preserved():
    result = build()
    freeze = result["cohort_freeze"]
    assert freeze["subjects"] == 20
    assert freeze["events"] == 20
    assert freeze["validation_subjects"] == 14
    assert freeze["holdout_subjects"] == 6
    assert freeze["holdout_protected"] is True
    assert freeze["validation_subject_hash"] == digest(sorted(__import__("json").loads((OUT.parent / "emp-posend-acq-001/02_COHORT_FREEZE.json").read_text())["validation_subjects"]))
    assert freeze["holdout_subject_hash"] == digest(sorted(__import__("json").loads((OUT.parent / "emp-posend-acq-001/02_COHORT_FREEZE.json").read_text())["holdout_subjects"]))


def test_precision_ontology_and_provenance_do_not_upgrade_events():
    result = build()
    assert result["date_precision"]["before"] == {"DAY": 0, "MONTH": 0, "YEAR": 20, "UNKNOWN": 0}
    assert result["date_precision"]["after_recovery"]["DAY"] == 0
    assert result["date_precision"]["after_recovery"]["MONTH"] == 0
    assert result["date_precision"]["synthetic_dates_created"] == 0
    assert result["date_precision"]["conflicted"] == 1
    assert result["event_provenance"]["birth_event_provenance_separated"] is True
    assert result["event_provenance"]["outcome_leakage"] == "NO_EVIDENCE_OF_OUTCOME_LEAKAGE"
    assert {row["event_subtype_governed"] for row in result["event_provenance"]["records"]} == {"CAREER_END_INFERRED"}


def test_readiness_and_safety_block_premature_scoring():
    result = build()
    assert result["study_decision"]["decision"] == "POSEND_EXPLORATORY_ONLY_REACQUIRE_REQUIRED"
    assert result["power"]["day_eligible_n"] == 0
    assert result["power"]["month_secondary_n"] == 0
    assert result["power"]["year_exploratory_n"] == 20
    assert result["power"]["confirmatory_powered"] is False
    assert result["safety"]["feature_scoring"] is False
    assert result["safety"]["astrology_calculation"] is False
    assert result["safety"]["ml"] == "LOCKED"
    assert result["safety"]["rag_changed"] is False


def test_feature_metadata_is_frozen_without_activation_access():
    result = build()
    family = result["feature_family"]
    assert family["feature_family_id"] == "VEDA_EMP_FEATURE_FAMILY_POSITION_END_V1"
    assert family["feature_family_version"] == "1.0.0"
    assert family["feature_family_hash"] == "da810777ea18ff74ebcdb9b3003dd8a0b4a5b88f68cd79b0c27b569c18340297"
    assert family["feature_count"] == 5
    assert family["feature_changes"] == 0
    assert family["activation_inspected"] is False
    assert all(contract["activation_inspected"] is False for contract in family["contracts"])


def test_generated_json_is_deterministic_and_has_no_scoring_fields():
    first = write()
    snapshot_one = {path.name: path.read_bytes() for path in OUT.glob("*.json")}
    second = write()
    snapshot_two = {path.name: path.read_bytes() for path in OUT.glob("*.json")}
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert snapshot_one == snapshot_two
    forbidden = {"effect_size", "odds_ratio", "p_value", "auc", "precision", "recall", "permutation_score"}
    for path in OUT.glob("*.json"):
        parsed = json.loads(path.read_text(encoding="utf-8"))
        assert not forbidden.intersection(parsed)
