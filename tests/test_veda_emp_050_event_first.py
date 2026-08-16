import pytest

from scripts.veda_emp_050_event_first import build_event_first_candidate


def test_event_first_candidate_preserves_event_provenance_without_chart_selection():
    result = build_event_first_candidate(event_id="e1", event_class="MARRIAGE", event_date="2020-05-01", date_precision="EXACT", event_sources=["official-record"], subject_id="s1")
    assert result["acquisition_lane"] == "EVENT_FIRST"
    assert result["chart_fit_used_for_selection"] is False
    assert result["eligibility_state"] == "EVENT_EVIDENCE_CAPTURED_BIRTH_VALIDATION_PENDING"


def test_event_first_rejects_missing_or_unsupported_provenance():
    with pytest.raises(ValueError, match="EVENT_FIRST_EVENT_SOURCE_REQUIRED"):
        build_event_first_candidate(event_id="e1", event_class="MARRIAGE", event_date="2020-05-01", date_precision="EXACT", event_sources=[])
    with pytest.raises(ValueError, match="EVENT_FIRST_DATE_PRECISION_INVALID"):
        build_event_first_candidate(event_id="e1", event_class="MARRIAGE", event_date="2020-05-01", date_precision="DAY_UNKNOWN", event_sources=["source"])
