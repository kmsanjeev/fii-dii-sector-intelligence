import json
from pathlib import Path

from scripts.veda_emp_feature_003 import OUT, POPULATION_HASH, build


def test_new_event_family_and_feature_family_are_frozen():
    result = build()
    assert result["event_family_selection"]["selected"] == "POSITION_END"
    assert result["feature_family_id"] == "VEDA_EMP_FEATURE_FAMILY_POSITION_END_V1"
    assert len(result["contracts"]) == 5
    assert len({x["hash"] for x in result["contracts"]}) == 5
    assert result["prevalence"]["population_hash"] == POPULATION_HASH
    assert result["prevalence"]["outcome_free"] is True


def test_independent_cohort_gate_and_position_start_closure_are_preserved():
    result = build()
    assert result["primary_cohort"]["eligible_subjects"] == 0
    assert result["primary_cohort"]["status"] == "BLOCKED_INSUFFICIENT_INDEPENDENT_EVENT_COHORT"
    assert result["legacy_secondary_cohort"]["subjects"] == 4
    assert result["legacy_secondary_cohort"]["events"] == 7
    assert result["position_start_closure"]["F001_F005"] == "REPLICATED_NO_ASSOCIATION_PRESERVED"
    assert result["position_start_closure"]["reopened"] is False


def test_outputs_are_written_and_safety_states_are_unchanged():
    for name in [
        "01_EVENT_FAMILY_SELECTION.json",
        "02_FEATURE_FAMILY_REGISTRY.json",
        "03_OUTCOME_FREE_PREVALENCE.json",
        "04_LEGACY_SECONDARY_COHORT.json",
        "05_FINAL_MANIFEST.json",
    ]:
        assert (OUT / name).exists()
    manifest = json.loads((OUT / "05_FINAL_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["production_changed"] is False
    assert manifest["approved_core_changed"] is False
    assert manifest["rag_changed"] is False
    assert manifest["ml_used"] is False
    assert manifest["composition_used"] is False
    assert manifest["pred_m4"] == "INSUFFICIENT_SAMPLE"
