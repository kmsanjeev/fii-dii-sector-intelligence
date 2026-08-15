import json

from scripts.veda_emp_025_corpus_hash import build_manifest


def test_corpus_manifest_is_deterministic_and_holdout_locked():
    enrichment = {"accepted_cases": [{"case_id": "B", "subject_id": "s", "identity": {"birth_date": "1900-01-01", "birth_time": "12:00", "birth_time_precision": "MINUTE", "birth_place": "X", "timezone_offset": "+00:00"}, "events": [{"event_id": "e", "event_class": "POSITION_START", "event_date_start": "1950-01-01", "date_precision": "YEAR", "verification_status": "VERIFIED_YEAR", "source_quality": "OFFICIAL", "claim_id": "c", "verification_source": "source"}]}]}
    chart = {"charts": [{"case_id": "B", "chart_ready": True}]}
    split = {"status": "PRE_PILOT_FROZEN", "records": [{"subject_id": "s", "split": "HOLDOUT"}], "counts": {"DESIGN": 0, "VALIDATION": 0, "HOLDOUT": 1}, "method_tuning_allowed": False}
    first = build_manifest(enrichment, chart, split, knowledge_cutoff="2026-08-16", engine_revision="rev")
    second = build_manifest(json.loads(json.dumps(enrichment)), chart, split, knowledge_cutoff="2026-08-16", engine_revision="rev")
    assert first["corpus_hash"] == second["corpus_hash"]
    assert first["controls"]["holdout_locked"] is True
    assert first["pilot_scope"]["status"] == "LAUNCHED_HANDOFF"
