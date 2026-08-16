"""Source-cluster-aware ADB scale tests; no astrology or outcome selection."""

import json

import pytest

from scripts.veda_evidence_adb_scale_001 import DEFAULT_XML, build, write_artifacts


pytestmark = pytest.mark.skipif(not DEFAULT_XML.exists(), reason="official ADB sample is local-only and not committed")


def test_universe_and_stratified_sample_freeze():
    result = build()
    assert result["universe"]["subject_count"] == 4623
    assert result["universe"]["potential_tier_a"] == 4232
    assert result["universe"]["potential_tier_b"] == 233
    assert result["sample"]["subject_count"] == 400
    assert result["sample"]["cluster_counts"]["STEINBRECHER_COLLECTION"] <= 50
    assert len(result["sample"]["subject_hash"]) == 64


def test_cluster_census_and_generalization_are_outcome_blind():
    result = build()
    census = result["cluster_census"]
    assert census["largest_cluster"] == ("SY_SCHOLFIELD_SUBMISSIONS", 1470)
    assert census["unknown_cluster_records"] == 1358
    assert result["cluster_generalization"] == "IS_CLUSTER_SPECIFIC"
    assert result["source_independence"]["raw_n_suitable_as_independent_n"] is False
    assert result["source_independence"]["effective_n_or_bound"] == 27


def test_new_adjudication_and_day_event_boundary():
    result = build()
    assert result["new_results"]["verified_a_b"] == 5
    assert result["new_results"]["state_counts"]["REJECTED_PRECISION"] == 333
    assert result["combined_pool"]["subject_count"] == 114
    assert result["day_event_overlap"]["verified_subjects_with_day"] == 66
    assert result["day_event_overlap"]["total_day_events"] == 130
    assert result["day_event_overlap"]["event_status"] == "ADB_EVENT_DISCOVERY_ONLY"
    assert result["governance"]["astrology_executed"] is False
    assert result["governance"]["rag_changed"] is False


def test_scale_artifacts_are_deterministic():
    first = json.dumps(build(), sort_keys=True)
    second = json.dumps(build(), sort_keys=True)
    assert first == second
    write_artifacts()
