from scripts.veda_emp_event_enrichment import enrich_candidates


def _payload():
    return {
        "feed_id": "VEDA-EMP-OGDB-001",
        "records": [
            {
                "ogid": "verified-subject",
                "subject_label": "Verified Subject",
                "birth_date": "1916-02-12",
                "birth_time": "08:00",
                "birth_time_precision": "MINUTE",
                "birth_place": "San Francisco",
                "timezone_status": "RESOLVED",
                "timezone_offset": "-08:00",
                "identity_status": "VERIFIED",
                "events": [{
                    "event_id": "E-1", "event_class": "DEATH", "event_date_start": "1998-01-29",
                    "date_precision": "EXACT", "verification_status": "VERIFIED_EXACT",
                    "discovery_source": "Wikidata Q1", "verification_source": "Official archive",
                    "source_quality": "MULTI_SOURCE", "public_private_status": "PUBLIC",
                    "claim_id": "Q1$P570-1",
                }],
            },
            {
                "ogid": "unresolved-subject",
                "subject_label": "Unresolved Subject",
                "birth_date": "1900-01-01",
                "birth_time": "12:00",
                "birth_place": "Paris",
                "timezone_status": "UNKNOWN",
                "identity_status": "UNRESOLVED",
                "events": [],
            },
        ],
    }


def test_event_enrichment_accepts_only_governed_case_inputs():
    result = enrich_candidates(_payload(), chart_revision="TEST-REVISION")
    assert result["identity_resolved"] == 1
    assert result["event_enriched_subjects"] == 1
    assert result["empirical_eligible_cases"] == 1
    assert result["astrology_used_for_selection"] is False
    assert result["excluded_subjects"][0]["exclusion_reasons"] == ["IDENTITY_NOT_SUFFICIENTLY_RESOLVED", "TIMEZONE_UNRESOLVED", "NO_VERIFIABLE_EVENTS"]
