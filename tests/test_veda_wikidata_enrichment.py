from scripts.veda_wikidata_enrichment import enrich_records


def test_exact_identity_match_preserves_sources_without_creating_case() -> None:
    ogdb = {
        "feed_id": "VEDA-EMP-OGDB-001",
        "records": [{
            "ogid": "one",
            "birth_date": "1924-04-24",
            "birth_place": "Paris",
            "occupation": "cyclist",
            "case_eligibility": "RESEARCH_ONLY_NO_EVENT",
        }],
    }
    candidates = {"one": [{
        "wdid": "Q123",
        "birth_date": "1924-04-24",
        "birth_place": "PARIS",
        "occupation": "cyclist",
        "references": [{"url": "https://www.wikidata.org/wiki/Q123"}],
    }]}

    result = enrich_records(ogdb, candidates)

    assert result["identity_matches"] == 1
    assert result["usable_empirical_cases"] == 0
    assert result["records"][0]["original_ogdb_record"] == ogdb["records"][0]
    assert result["records"][0]["wikidata_identity"]["references"]
    assert result["records"][0]["case_eligibility"] == "RESEARCH_ONLY_NO_EVENT"


def test_name_only_or_partial_match_is_rejected() -> None:
    ogdb = {
        "feed_id": "VEDA-EMP-OGDB-001",
        "records": [{
            "ogid": "one",
            "subject_label": "Pierre Adam",
            "birth_date": "1924-04-24",
            "birth_place": "Paris",
            "occupation": "cyclist",
        }],
    }
    candidates = {"one": [{
        "wdid": "Q123",
        "label": "Pierre Adam",
        "birth_date": "1924-04-24",
        "birth_place": "Lyon",
        "occupation": "cyclist",
    }]}

    result = enrich_records(ogdb, candidates)

    assert result["identity_matches"] == 0
    assert result["records"][0]["identity_status"] == "UNMATCHED_AMBIGUOUS_OR_MISMATCHED"
