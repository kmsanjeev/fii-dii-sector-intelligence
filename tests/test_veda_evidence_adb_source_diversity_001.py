"""Bounded unknown-source diversity audit tests; no astrology or raw-data export."""

from scripts.veda_evidence_adb_source_diversity_001 import build, select_sample
from scripts.veda_evidence_adb_sample_001 import DEFAULT_XML


def test_unknown_universe_and_denominators_are_frozen():
    result = build(DEFAULT_XML)
    assert result["unknown_universe"]["subject_count"] == 1358
    assert result["cluster_denominators"]["full_candidate_universe"] == 4623
    assert result["cluster_denominators"]["identified_cluster_records"] == 3265
    assert result["cluster_denominators"]["top5_share_identified"] <= 1


def test_resolution_keeps_levels_and_does_not_overclaim_original_independence():
    result = build(DEFAULT_XML)
    resolution = result["resolution"]
    assert resolution["resolved_records"] + resolution["unresolved_records"] + resolution["unsupported_records"] == 1358
    assert result["source_graph"]["edges"].find("not treated as original-document independence") >= 0
    assert result["verified_pool"]["combined_verified"] == 114


def test_sample_cap_and_no_previous_overlap():
    result = build(DEFAULT_XML)
    sample = result["sample"]
    assert sample["subject_count"] == 240
    assert sample["previous_overlap"] == 0
    assert sample["single_cluster_maximum"] <= 20
    assert sample["india_subjects"] > 0


def test_adjudication_and_governance_boundaries():
    result = build(DEFAULT_XML)
    assert result["adjudication"]["total_verified_a_b"] == 0
    assert result["adjudication"]["source_diverse_yield_state"] == "SOURCE_DIVERSE_YIELD_NEGLIGIBLE"
    assert result["day_event_overlap"]["event_status"] == "ADB_EVENT_DISCOVERY_ONLY"
    assert result["power"]["predictive_study_ready"] is False
    assert result["governance"]["astrology_executed"] is False
    assert result["governance"]["raw_data_committed"] is False
    assert result["stop_go"]["further_generic_free_sample_adjudication_authorized"] is False


def test_source_diversity_is_deterministic():
    first = build(DEFAULT_XML)
    second = build(DEFAULT_XML)
    assert first == second
