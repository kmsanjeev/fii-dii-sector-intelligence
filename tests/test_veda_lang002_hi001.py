import json

from engines.ai.knowledge.language_foundation import (
    coverage_report,
    canonicalize_term,
    load_locale,
    render_interpretation,
    render_message,
    render_source_citation,
    render_structured,
    render_term,
    serialize_unicode,
)


def test_hindi_pack_is_complete_source_reviewed_and_not_production_authorized():
    pack = load_locale("hi")
    report = coverage_report("hi")
    assert pack["status"] == "REVIEW_CANDIDATE"
    assert pack["review_state"] == "SOURCE_REVIEWED"
    assert pack["human_reviewed"] is False
    assert pack["production_authorized"] is False
    assert report["total_keys"] == 49
    assert report["translated"] == 49
    assert report["missing"] == 0
    assert report["fallback_used"] == 0
    assert pack["entry_metadata_defaults"]["translation_state"] == "SOURCE_REVIEWED"
    assert "canonical_term_registry.json" in pack["entry_metadata_defaults"]["terminology_reference"]


def test_hindi_planet_terms_and_localized_aliases_keep_canonical_identity():
    assert render_term("JUPITER", "hi")["text"] == "गुरु"
    assert render_term("गुरु", "hi")["canonical_id"] == "TERM.PLANET.JUPITER"
    assert canonicalize_term("बृहस्पति", "hi") == "TERM.PLANET.JUPITER"
    assert render_term("सूर्य", "hi")["canonical_id"] == "TERM.PLANET.SUN"
    assert canonicalize_term("गुरु", "en") is None


def test_hindi_rashi_nakshatra_varga_dasha_and_panchanga_terms_are_bounded():
    expected = {
        "ARIES": "मेष",
        "PISCES": "मीन",
        "ASHWINI": "अश्विनी",
        "D9": "D9 (नवांश)",
        "D20": "D20 (विंशांश)",
        "MAHADASHA": "महादशा",
        "TITHI": "तिथि",
        "KARANA": "करण",
    }
    values = {
        "ARIES": render_term("TERM.SIGN.ARIES", "hi")["text"],
        "PISCES": render_term("TERM.SIGN.PISCES", "hi")["text"],
        "ASHWINI": render_term("TERM.NAKSHATRA.ASHWINI", "hi")["text"],
        "D9": render_term("TERM.VARGA.D9", "hi")["text"],
        "D20": render_term("TERM.VARGA.D20", "hi")["text"],
        "MAHADASHA": render_term("TERM.DASHA.MAHADASHA", "hi")["text"],
        "TITHI": render_term("TERM.PANCHANGA.TITHI", "hi")["text"],
        "KARANA": render_term("TERM.PANCHANGA.KARANA", "hi")["text"],
    }
    assert values == expected


def test_critical_hindi_messages_preserve_state_and_negation():
    assert "नहीं" in render_message("STATUS.NOT_VALIDATED", "hi")["text"]
    assert "अधिकृत नहीं" in render_message("STATUS.NOT_AUTHORIZED", "hi")["text"]
    assert "नहीं" in render_message("SAFETY.NO_PREDICTIVE_CLAIM", "hi")["text"]
    assert "नहीं" in render_message("SAFETY.D20_INTERPRETATION_NOT_VALIDATED", "hi")["text"]
    assert "शोध हेतु" in render_message("SAFETY.ASHTAKAVARGA_RESEARCH_ONLY", "hi")["text"]
    assert "अधिकृत नहीं" in render_message("OUTPUT.MUHURTA.RECOMMENDATION_NOT_AUTHORIZED", "hi")["text"]
    assert "निश्चित परिणाम नहीं" in render_message("SAFETY.QUALIFIED_INDICATION", "hi", variables={"topic": "अध्ययन"})["text"]


def test_explicit_safety_fixtures_cover_unrepresented_negations():
    fixtures = load_locale("hi")["safety_fixtures"]
    assert len(fixtures) == 7
    assert all(item["translation_state"] == "SOURCE_REVIEWED" for item in fixtures)
    assert all("नहीं" in item["hindi"] for item in fixtures)
    assert {item["criticality"] for item in fixtures} == {"CRITICAL"}


def test_structured_facts_and_numbers_are_identical_between_locales():
    facts = {
        "planet_id": "JUPITER",
        "house": 10,
        "value": 20.5,
        "status": "RESEARCH_ONLY",
        "source_id": "SRC-001",
        "confidence": "LOW",
    }
    english = render_structured(facts, "en")
    hindi = render_structured(facts, "hi")
    assert english["fact_payload"] == hindi["fact_payload"] == facts
    assert hindi["display"]["planet_display"] == "गुरु"
    assert hindi["display"]["status_display"] == "केवल शोध हेतु"


def test_source_citation_and_trust_metadata_are_unchanged():
    citation = {"source_id": "BPHS", "chapter": "89", "verse": "2", "confidence": "CONDITIONAL", "knowledge_zone": "RESEARCH_CANDIDATE"}
    result = render_source_citation(citation, "hi")
    assert {key: result[key] for key in citation} == citation
    assert result["source_label"]["text"] == "स्रोत उद्धरण"


def test_free_text_interpretation_remains_canonical_until_human_review():
    result = render_interpretation("This may indicate a study orientation; it is not a deterministic outcome.", "hi", status="RESEARCH_ONLY")
    assert result["locale"] == "en"
    assert result["translation_state"] == "CANONICAL_TEXT_ONLY"
    assert result["translation_note"]["locale_used"] == "hi"


def test_hindi_unicode_normalization_and_json_are_stable():
    payload = {"display": "गुरु — विंशांश", "status": "NOT_VALIDATED", "number": 20.5}
    encoded = serialize_unicode(payload)
    assert "गुरु" in encoded and "विंशांश" in encoded
    assert json.loads(encoded) == payload
    assert serialize_unicode(payload) == serialize_unicode(json.loads(encoded))


def test_hindi_parent_fallback_is_explicit_and_nonempty():
    result = render_message("STATUS.NOT_VALIDATED", "hi-IN")
    assert result["text"] == "सत्यापित नहीं"
    assert result["locale_used"] == "hi"
    assert result["fallback_used"] is True
    missing = render_message("MESSAGE.NOT_IN_REGISTRY", "hi")
    assert missing["status"] == "MISSING_TRANSLATION"
    assert missing["text"] is None


def test_hindi_source_review_and_production_gates_are_not_promoted():
    pack = load_locale("hi")
    counts = pack["review_counts"]
    assert counts["MACHINE_DRAFT"] == 0
    assert counts["SOURCE_REVIEWED"] == 49
    assert counts["REVIEW_PENDING"] == 0
    assert counts["HUMAN_REVIEWED"] == 0
    assert counts["APPROVED_PRESENTATION"] == 0
    assert pack["production_authorized"] is False
