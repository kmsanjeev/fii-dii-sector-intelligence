"""Astro-Databank sample qualification tests; no astrology execution."""

import json

import pytest

from scripts.veda_evidence_adb_sample_001 import DEFAULT_XML, build, write_artifacts


pytestmark = pytest.mark.skipif(not DEFAULT_XML.exists(), reason="official ADB sample is local-only and not committed")


def test_official_sample_counts_and_discrepancy_are_preserved():
    result = build()
    assert result["observed_records"] == 6036
    assert result["unique_record_ids"] == 6036
    assert result["ratings"]["A"] == 1155
    assert result["ratings"]["AA"] == 3820
    assert result["discrepancy_records"] == 170
    assert result["discrepancy_a_aa"] == 143


def test_birth_and_rectification_safeguards():
    result = build()
    assert result["timed_birth"] == 6036
    assert result["chart_input_complete"] == 6023
    assert result["birth_precision"] == {"UNKNOWN": 6036}
    assert result["mapping_state"] == "TIER_MAPPING_UNRESOLVED"
    assert result["rectified_keyword_candidates"] == 284
    assert result["funnel"]["veda_birth_tier_a_b"] == 0


def test_event_precision_and_two_provenance():
    result = build()
    assert result["events"]["subjects_with_events"] == 3685
    assert result["events"]["total"] == 8121
    assert result["events"]["precision"] == {"DAY": 4777, "MONTH": 531, "YEAR": 2813}
    assert result["events"]["duplicate_event_keys"] == 984
    assert result["corroboration"]["exact_confirmed"] == 5
    assert result["corroboration"]["conflicts"] == 1
    assert result["funnel"]["combined_tier_a_b_exact_day"] == 0


def test_india_power_and_governance_locks():
    result = build()
    assert result["india"] == {"subjects": 135, "a_aa": 119, "timed": 135, "potential_birth_tier_ab": 0, "day_events": 118}
    assert result["power"] == {"baseline_10_target_15": 3390, "baseline_10_target_20": 982, "baseline_10_target_25": 490, "baseline_10_target_30": 302}
    assert result["raw_data_committed"] is False
    assert result["ai_training"] is False
    assert result["scraping"] is False
    assert result["astrology_executed"] is False
    assert result["pred_m4_changed"] is False


def test_derived_artifacts_are_deterministic():
    first = json.dumps(build(), sort_keys=True)
    second = json.dumps(build(), sort_keys=True)
    assert first == second
    write_artifacts()
    assert json.loads((DEFAULT_XML.parents[5] / "docs/current-state/evidence-adb-sample-001/09_TIER_QUALIFICATION_FUNNEL.json").read_text(encoding="utf-8"))["combined_tier_a_b_exact_day"] == 0
