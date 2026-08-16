import json
from pathlib import Path

from scripts.veda_emp_feature_002 import build


ROOT = Path(__file__).resolve().parents[1]


def test_feature_hashes_and_independence_are_frozen():
    first = build()
    second = build()
    assert first == second
    freeze = first["freeze"]
    assert len(freeze["subjects"]) == 20
    assert len(freeze["validation_subjects"]) == 14
    assert len(freeze["holdout_subjects"]) == 6
    assert freeze["prior_subject_overlap"] == []
    assert len(freeze["feature_hashes"]) == 5
    assert freeze["holdout_masked_before_validation"] is True


def test_all_frozen_features_report_replication_result_and_controls():
    output = build()
    assert len(output["features"]) == 5
    for feature in output["features"]:
        assert feature["source_status_unchanged"] is True
        assert feature["production_status"] == "INACTIVE"
        assert feature["validation"]["subjects"] == 14
        assert feature["holdout"]["subjects"] == 6
        assert len(feature["combined"]["rows"]) == 20
        assert feature["state"] == "REPLICATED_NO_ASSOCIATION"
        assert feature["event_shuffled"]["seed"] >= 20260816
        assert feature["event_shuffled"]["iterations"] == 2000
        assert feature["subject_event_permutation"]["iterations"] == 2000


def test_replication_safety_states_remain_unchanged():
    manifest = build()["manifest"]
    assert manifest["feature_hashes_verified"] is True
    assert manifest["prior_subject_overlap"] == 0
    assert manifest["feature_based_acquisition"] is False
    assert manifest["holdout_leakage"] is False
    assert manifest["promising_features"] == []
    assert manifest["pred_m4"] == "INSUFFICIENT_SAMPLE"
    assert manifest["production_changed"] is False
    assert manifest["approved_core_changed"] is False
    assert manifest["rag_changed"] is False
