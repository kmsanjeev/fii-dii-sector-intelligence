"""Focused governance tests for the POSEND R2 frame activity."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import scripts.veda_evidence_posend_r2_frame_001 as activity


def test_parent_and_frozen_contracts_are_preserved():
    result = activity.build()
    assert result["parent_commit"] == activity.PARENT_COMMIT
    assert result["baseline"]["r1_events"] == 4
    assert result["baseline"]["r1_validation"] == 3
    assert result["baseline"]["r1_holdout"] == 1
    assert result["baseline"]["r1_holdout_opened"] is False
    assert result["baseline"]["protocol_hash"] == activity.PROTOCOL_HASH
    assert result["baseline"]["feature_family_hash"] == activity.FEATURE_HASH


def test_current_frame_is_exhausted_and_not_reused_as_new_r2():
    result = activity.build()
    exhaustion = result["exhaustion"]
    frame = result["current_frame"]
    assert exhaustion["candidates_screened"] == 114
    assert exhaustion["search_exhausted"] == 107
    assert exhaustion["eligible_exact_day"] == 4
    assert exhaustion["risk_interval_ready"] == 4
    assert exhaustion["current_frame_exhausted"] is True
    assert frame["new_unique_subjects_for_r2"] == 0
    assert frame["overlap_with_r1"] == 114


def test_inventory_separates_benchmark_ogdb_synthetic_and_provider_gates():
    result = activity.build()
    by_id = {row["frame_id"]: row for row in result["inventory"]}
    assert "CALCULATION_BENCHMARK_ONLY" in by_id["CALC-SILVER-109"]["classification"]
    assert "MECHANICS_PREVALENCE_ONLY" in by_id["OGDB-TIMED-POPULATION-1000"]["classification"]
    assert "SYNTHETIC_ONLY" in by_id["CONSENT-SYNTHETIC-25"]["classification"]
    assert "PROVIDER_ACCESS_GATED" in by_id["ADB-FORMAL-ACCESS-PREPARED"]["classification"]


def test_prescreen_policy_is_birth_first_and_outcome_blind():
    policy = activity.build()["prescreen_policy"]
    assert policy["event_first_construction"] is False
    assert policy["outcome_selected_frame"] is False
    assert policy["feature_values_used"] is False
    assert "event outcome or event availability" in policy["forbidden_before_event_lookup"]
    assert len(policy["policy_hash"]) == 64


def test_r2_is_blocked_without_fabricating_a_candidate_frame():
    result = activity.build()
    frame = result["r2_frame"]
    assert result["decision"] == "R2_FRAME_BLOCKED_FORMAL_ACCESS_REQUIRED"
    assert frame["acquisition_ready"] is False
    assert frame["candidate_universe_frozen"] is False
    assert frame["new_unique_subjects"] == 0
    assert frame["event_acquisition_performed"] is False
    assert result["formal_access"]["submitted"] is False


def test_source_diversity_gate_is_explicit():
    result = activity.build()
    scale = result["yield_and_scale"]
    assert scale["current_birth_clusters_for_r1_events"] == 1
    assert scale["current_event_clusters_for_r1_events"] == 3
    assert scale["source_diversity_minimum_birth_clusters"] == 2
    assert scale["source_diversity_minimum_event_clusters"] == 2
    assert result["r2_frame"]["birth_source_clusters"] == 0


def test_planning_yields_are_deterministic_and_non_predictive():
    first = activity.build()
    second = activity.build()
    assert first["hashes"]["result_hash"] == second["hashes"]["result_hash"]
    assert first["yield_and_scale"]["planning_only"] is True
    assert all(row["planning_only"] and row["not_a_prediction"] for row in first["yield_and_scale"]["scenarios"])


def test_no_raw_provider_data_is_read_or_written_by_generated_manifest():
    result = activity.build()
    assert result["governance"]["raw_provider_data_committed"] is False
    assert result["governance"]["new_provider_calls"] == 0
    manifest_text = json.dumps(result, sort_keys=True).lower()
    assert "astrology" in manifest_text
    assert "feature_values_used" in manifest_text
    assert result["governance"]["astrology"] is False
    assert result["governance"]["ml"] is False
    assert result["governance"]["pred_m4"] == "UNCHANGED"


def test_written_artifacts_are_canonical_json(tmp_path, monkeypatch):
    monkeypatch.setattr(activity, "OUT", tmp_path)
    activity.write()
    files = sorted(tmp_path.iterdir())
    assert len(files) == 16
    for path in files:
        if path.suffix == ".json":
            json.loads(path.read_text(encoding="utf-8"))
