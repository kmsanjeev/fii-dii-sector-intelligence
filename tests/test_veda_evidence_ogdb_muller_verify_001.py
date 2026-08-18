import json
from pathlib import Path

import pytest

from scripts.veda_evidence_ogdb_muller_verify_001 import (
    build_audit,
    immutable_sample_check,
    parse_french,
    parse_german,
)


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/veda/research/muller_verify_001_raw"


def test_official_muller_source_counts_and_fields():
    german = parse_german(RAW / "german.zip")
    french = parse_french(RAW / "french.zip")
    assert len(german) == 1145
    assert len(french) == 1083
    assert all(row["muid"].startswith("M4-") for row in german)
    # The official AFD5 export contains three inherited M2 identifiers among
    # the otherwise M5-prefixed Müller records; preserve source lineage.
    assert all(row["muid"].startswith(("M5-", "M2-")) for row in french)
    assert sum(bool(row.get("tob")) for row in french) == 1083


def test_sample_is_deterministic_and_frozen():
    audit = build_audit(ROOT, RAW / "german.zip", RAW / "french.zip")
    assert audit["sample_policy"]["sampled_total"] == 50
    immutable_sample_check(audit["sample_policy"], audit["sample_policy"])
    changed = dict(audit["sample_policy"], sample_hash="changed")
    with pytest.raises(ValueError):
        immutable_sample_check(audit["sample_policy"], changed)


def test_scope_is_feature_blind_and_no_frame_is_created():
    audit = build_audit(ROOT, RAW / "german.zip", RAW / "french.zip")
    assert audit["scope"] == {"position_end_lookup": False, "astrology": False, "feature_scoring": False, "ml": False, "prediction": False}
    assert audit["next_frame"]["automatically_started"] is False
    assert audit["overall_decision"] == "MULLER_MANUAL_VERIFICATION_REQUIRED_FOR_SCALE"


def test_french_source_independence_is_mixed():
    audit = build_audit(ROOT, RAW / "german.zip", RAW / "french.zip")
    assert audit["adb_overlap"]["source_independence"]["french"] == "MIXED_224_WITHOUT_GQID_AND_859_GQ_LINKED"
    assert audit["provenance"]["document_to_muller_to_ogdb_complete"] == 0


def test_documentary_layers_time_audit_and_parallel_lanes_are_explicit():
    audit = build_audit(ROOT, RAW / "german.zip", RAW / "french.zip")
    rows = audit["documentary_verification"]
    assert len(rows) == 50
    assert all(row["muller_source_match"] == "MULLER_SOURCE_MATCH" for row in rows)
    assert all(row["civil_document_match"] == "MANUAL_ARCHIVE_ACCESS_REQUIRED" for row in rows)
    assert audit["time_audit"]["local_time_records_in_sample"] == 50
    assert audit["time_audit"]["utc_conversion_check"] == "NOT_PERFORMED_RECORD_LEVEL_DOCUMENT_ACCESS_REQUIRED"
    assert audit["time_audit"]["calendar_mismatch_check"] == "NOT_ASSESSED"
    assert audit["parallel_lanes"]["position_end"] == "WAIT_EXTERNAL_ACCESS"
    assert audit["parallel_lanes"]["ashtakavarga_started"] is False
    assert audit["governance"]["rag_changed"] is False
    assert audit["governance"]["ml_locked"] is True
