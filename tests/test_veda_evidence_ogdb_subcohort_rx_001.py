import json

from scripts.veda_evidence_ogdb_subcohort_rx_001 import build_audit, canonical_hash, load_pilot


def test_ogdb_subcohort_audit_is_outcome_and_astrology_free(tmp_path):
    pilot = tmp_path / "pilot.json"
    pilot.write_text(json.dumps({
        "feed_id": "VEDA-EMP-OGDB-001",
        "pilot_limit": 2,
        "usable_empirical_cases": 0,
        "records": [
            {"ogid": "one", "birth_time": "00:00", "birth_time_precision": "MINUTE", "timezone_offset": "+01:00"},
            {"ogid": "two", "birth_time": "12:00", "birth_time_precision": "MINUTE", "timezone_offset": None},
        ],
    }), encoding="utf-8")
    audit = build_audit(tmp_path, pilot)
    assert audit["scope"]["astrology"] is False
    assert audit["scope"]["position_end_lookup"] is False
    assert audit["pilot"]["usable_empirical_cases"] == 0
    assert audit["time_provenance"]["round_clock"] == {"00:00": 1, "12:00": 1}
    assert audit["decision"] == "OGDB_SOURCE_DIVERSITY_USEFUL_BUT_SCALE_LIMITED"
    assert canonical_hash(audit) == canonical_hash(audit)


def test_wikidata_correction_does_not_authorize_time_of_birth():
    pilot = load_pilot(__import__("pathlib").Path("data/veda/research/empirical/ogdb_pilot_1000.json"))
    assert pilot["usable_empirical_cases"] == 0
