import pytest

from scripts.veda_emp_025_method_pilot import build_audit


def _inputs():
    enrichment = {"accepted_cases": [{"case_id": "C1", "subject_id": "s1", "events": [{"event_id": "e1", "event_class": "POSITION_START", "date_precision": "YEAR", "source_quality": "OFFICIAL", "event_date_start": "1950-01-01"}]}, {"case_id": "C2", "subject_id": "s2", "events": [{"event_id": "e2", "event_class": "DEATH", "date_precision": "EXACT", "source_quality": "REFERENCED", "event_date_start": "1951-01-01"}]}]}
    split = {"records": [{"subject_id": "s1", "split": "VALIDATION"}, {"subject_id": "s2", "split": "HOLDOUT"}]}
    manifest = {"corpus_hash": "3b3ac3b7cacfbe9b3d1935fbe0263568db49a37a95ed8e308c355bbb6a61f76f"}
    return enrichment, split, manifest


def test_primary_gate_stops_without_event_signal_governance():
    result = build_audit(*_inputs())
    assert result["primary_sample"]["events"] == 1
    assert result["signal_governance"]["status"] == "FAIL"
    assert result["results"]["method_result_state"] == "INSUFFICIENT_SIGNAL_GOVERNANCE"
    assert result["holdout_audit"]["outcomes_accessed"] is False
    assert result["runs"]["holdout"] == "SEALED_NOT_RUN"


def test_unexpected_corpus_mutation_stops():
    enrichment, split, manifest = _inputs()
    manifest["corpus_hash"] = "unexpected"
    with pytest.raises(ValueError, match="CORPUS_HASH_MISMATCH_STOP"):
        build_audit(enrichment, split, manifest)
