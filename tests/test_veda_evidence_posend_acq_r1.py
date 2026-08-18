import hashlib
import json
from pathlib import Path

from scripts.veda_evidence_posend_acq_r1 import (
    EVENTS,
    FEATURE_FAMILY_HASH,
    FRAME_IDS,
    build,
    controls,
    interval_rows,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/current-state/evidence-posend-acq-r1"


def test_authoritative_birth_frame_and_denominator_are_frozen():
    result = build()
    frame = result["birth_frame"]
    assert frame["subject_count"] == 114
    assert len(frame["subject_ids"]) == 114
    assert len(set(frame["subject_ids"])) == 114
    assert hashlib.sha256("\n".join(map(str, sorted(FRAME_IDS))).encode()).hexdigest().upper() == frame["subject_hash"]
    assert frame["tier_distribution"] == {"A": 37, "B": 77}
    assert result["yield"]["candidates_screened"] == 114


def test_exact_day_events_have_distinct_roles_and_event_ids():
    assert len(EVENTS) == 4
    assert len({row["event_id"] for row in EVENTS}) == 4
    assert len({row["role_id"] for row in EVENTS}) == 4
    for row in EVENTS:
        assert row["event_type"] == "POSITION_END"
        assert row["event_subtype"] == "TERM_COMPLETION"
        assert row["event_tier"] == "A"
        assert row["role_start_date"] < row["role_end_date"]


def test_role_intervals_and_controls_are_factual_and_in_bounds():
    intervals = interval_rows()
    assert {row["risk_interval_state"] for row in intervals} == {"RISK_INTERVAL_READY"}
    assert all(row["start_precision"] == row["end_precision"] == "DAY" for row in intervals)
    generated = controls(intervals)
    assert len(generated) == 8
    assert all(row["inside_role_interval"] and not row["post_event"] for row in generated)
    assert len({row["control_id"] for row in generated}) == len(generated)


def test_provenance_blindness_and_governance_boundaries():
    result = build()
    assert result["feature_blind"] is True
    assert result["astrology_blind"] is True
    assert result["feature_governance"]["feature_activation_accessed"] is False
    assert result["feature_governance"]["feature_family_hash"] == FEATURE_FAMILY_HASH
    assert result["feature_governance"]["feature_scoring"] is False
    assert result["feature_governance"]["outcome_association"] is False
    assert result["feature_governance"]["ml"] == "LOCKED"
    assert result["feature_governance"]["pred_m4"] == "UNCHANGED"
    assert result["rag"] == "UNCHANGED"
    assert result["legacy"]["historical_artifacts_modified"] is False


def test_new_split_is_after_freeze_and_holdout_is_locked():
    split = build()["split"]
    assert split["acquisition_frozen_before_split"] is True
    assert split["feature_results_inspected"] is False
    assert split["holdout_protected"] is True
    assert len(split["holdout_subjects"]) == 1
    assert set(split["validation_subjects"]).isdisjoint(split["holdout_subjects"])
    assert split["holdout_event_hash"]


def test_documentary_source_registry_is_official_and_minimal():
    result = build()
    assert result["provenance"]["wikipedia_final_authority"] is False
    assert result["provenance"]["minimal_excerpts_only"] is True
    assert all(
        any(domain in url for domain in ("assemblee-nationale.fr", "ec.europa.eu", "senato.it", "senat.fr", "vlaamsparlement.be"))
        for url in result["provenance"]["source_registry_urls"]
    )


def test_serialized_artifacts_match_current_build():
    result = build()
    manifest = json.loads((OUT / "FINAL_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest == result
    for name, key in {
        "01_BIRTH_FRAME_FREEZE.json": "birth_frame",
        "04_CANDIDATE_REGISTER.json": "candidate_register",
        "05_EVENT_EVIDENCE_REGISTER.json": "events",
        "06_ROLE_INTERVAL_REGISTER.json": "role_intervals",
        "08_ACQUISITION_YIELD.json": "yield",
        "10_NEW_COHORT_FREEZE.json": "new_cohort",
        "11_SPLIT_AND_HOLDOUT.json": "split",
        "13_POWER_READINESS.json": "power",
    }.items():
        assert json.loads((OUT / name).read_text(encoding="utf-8")) == result[key]
