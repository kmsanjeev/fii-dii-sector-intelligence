import json
from pathlib import Path

from scripts.veda_emp_feature_001 import build_artifacts


ROOT = Path(__file__).resolve().parents[1]


def test_feature_registry_contracts_and_reachability_are_deterministic():
    first = build_artifacts()
    second = build_artifacts()
    assert first == second
    contracts = first["registry"]["features"]
    assert len(contracts) == 5
    assert len({item["feature_id"] for item in contracts}) == 5
    assert all(item["hash"] for item in contracts)
    for fixture in first["reachability"]["fixtures"]:
        assert fixture["positive"] is not None
        assert fixture["negative"] is not None


def test_prevalence_is_outcome_free_and_study_reports_every_feature():
    result = build_artifacts()
    prevalence = result["prevalence"]
    study = result["study"]
    assert prevalence["population_id"] == "VEDA-POP-OGDB-001"
    assert prevalence["outcome_free"] is True
    assert all(row["outcome_join_performed"] is False for row in prevalence["features"])
    assert study["all_prespecified_features_reported"] is True
    assert study["event_family"] == "POSITION_START"
    assert study["event_count"] == 6
    assert study["subject_count"] == 3
    assert all(row["result"] == "INSUFFICIENT_SAMPLE" for row in study["features"])


def test_empirical_results_do_not_change_source_or_production_status():
    result = build_artifacts()
    assert all(item["source_status"] == "PLATFORM_SYNTHESIS" for item in result["registry"]["features"])
    assert all(item["production_status"] == "INACTIVE" for item in result["registry"]["features"])
    assert result["manifest"]["pred_m4"] == "INSUFFICIENT_SAMPLE"
    assert result["manifest"]["production_changed"] is False
    assert result["manifest"]["rag_changed"] is False
