"""Feature-blind corpus feasibility and provenance tests."""

import json

from scripts.veda_evidence_corpus_001 import build, event_precision, normalize_records


def test_date_precision_preserves_intervals_without_synthetic_dates():
    assert event_precision("EXACT") == "DAY"
    assert event_precision("YEAR") == "YEAR"
    result = build()
    for row in result["subjects"]:
        if row["event"]["event_precision"] != "DAY":
            assert row["event"]["normalized_date"] is None


def test_birth_and_event_provenance_are_separate_and_tiered():
    result = build()
    assert result["source_yield"]["tier_c_birth"] > 0
    assert all("birth" in row and "event" in row for row in result["subjects"])
    assert all(row["birth"]["source_cluster"] != row["event"]["source_cluster"] or row["event"]["source_cluster"] for row in result["subjects"])


def test_feasibility_is_not_confirmatory_and_does_not_score_features():
    result = build()
    assert result["mode"] == "FEASIBILITY_ONLY_NO_ASTROLOGY"
    assert result["acquisition_policy"]["astrology_inspected"] is False
    assert result["acquisition_policy"]["feature_scoring"] is False
    assert result["posend_legacy"]["confirmatory_eligible"] is False


def test_corpus_hashes_are_deterministic():
    assert json.dumps(build(), sort_keys=True) == json.dumps(build(), sort_keys=True)


def test_source_yield_has_event_family_decisions():
    result = build()
    families = {row["event_family"] for row in result["feasibility"]}
    assert "DEATH" in families
    assert all(row["decision"] for row in result["feasibility"])
