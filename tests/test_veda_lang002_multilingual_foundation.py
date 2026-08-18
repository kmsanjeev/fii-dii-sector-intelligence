import hashlib
import json
from pathlib import Path

from engines.ai.knowledge.language_foundation import (
    CANONICAL_LOCALE,
    LANGUAGE_TARGET_STATUS,
    available_locales,
    canonicalize_term,
    coverage_report,
    render_interpretation,
    render_message,
    render_source_citation,
    render_structured,
    render_term,
    serialize_unicode,
    validate_epistemic_preservation,
)


def test_lang002_baseline_and_target_selection_are_explicit():
    assert CANONICAL_LOCALE == "en"
    assert LANGUAGE_TARGET_STATUS == "HINDI_LOCALE_REVIEW_CANDIDATE_READY"
    assert available_locales() == ("en", "hi")


def test_canonical_ids_and_aliases_resolve_to_one_identity():
    assert canonicalize_term("JUPITER") == "TERM.PLANET.JUPITER"
    assert canonicalize_term("Guru") == "TERM.PLANET.JUPITER"
    assert canonicalize_term("vimsamsa") == "TERM.VARGA.D20"
    assert canonicalize_term("Navamsa") == "TERM.VARGA.D9"
    assert canonicalize_term("unknown-language-term") is None


def test_term_rendering_preserves_identity_and_english_baseline():
    rendered = render_term("JUPITER", "en")
    assert rendered["canonical_id"] == "TERM.PLANET.JUPITER"
    assert rendered["text"] == "Jupiter"
    assert rendered["fallback_used"] is False
    assert rendered["knowledge_zone"] == "VALIDATED_KNOWLEDGE"


def test_locale_fallback_is_explicit_and_never_empty():
    rendered = render_term("D20", "ta-IN")
    message = render_message("STATUS.NOT_VALIDATED", "ta-IN")
    assert rendered["text"] == "D20 (Vimshamsha)"
    assert rendered["locale_used"] == "en"
    assert rendered["fallback_used"] is True
    assert message["text"] == "Not validated"
    assert message["fallback_used"] is True


def test_unknown_message_and_term_have_explicit_missing_states():
    assert render_term("TERM.NOT_IN_REGISTRY", "en")["status"] == "MISSING_CANONICAL_TERM"
    assert render_message("MESSAGE.NOT_IN_REGISTRY", "en")["status"] == "MISSING_TRANSLATION"


def test_structured_output_keeps_canonical_payload_separate_from_display():
    facts = {
        "planet_id": "JUPITER",
        "house": 10,
        "status": "RESEARCH_ONLY",
        "source_id": "SRC-001",
        "chapter": "1",
        "verse": "2",
        "confidence": "LOW",
        "knowledge_zone": "RESEARCH_CANDIDATE",
    }
    result = render_structured(facts, "en")
    assert result["fact_payload"] == facts
    assert result["display"]["planet_display"] == "Jupiter"
    assert result["display"]["status_display"] == "Research-only"
    assert result["fact_payload"]["status"] == "RESEARCH_ONLY"


def test_source_citation_metadata_survives_localization():
    citation = {"source_id": "BPHS", "chapter": "6", "verse": "17-20", "confidence": "CONDITIONAL", "knowledge_zone": "RESEARCH_CANDIDATE"}
    result = render_source_citation(citation, "hi")
    for key, value in citation.items():
        assert result[key] == value
    assert result["source_label"]["text"] == "स्रोत उद्धरण"


def test_interpretation_text_is_not_machine_translated_without_review():
    source = {"source_id": "SRC-001", "proposition_id": "PROP-001", "status": "RESEARCH_ONLY"}
    result = render_interpretation("This may indicate a study orientation; it is not a deterministic outcome.", "hi", status="RESEARCH_ONLY", source_metadata=source)
    assert result["text"].startswith("This may indicate")
    assert result["locale"] == "en"
    assert result["translation_state"] == "CANONICAL_TEXT_ONLY"
    assert result["source_metadata"] == source
    assert result["translation_note"]["fallback_used"] is False


def test_certainty_and_negation_preservation():
    safe = "This may indicate a theme; it is research-only, not validated, not authorized, and no predictive claim is made."
    assert validate_epistemic_preservation(safe, safe)["passed"] is True
    unsafe = "This will happen and is proven."
    result = validate_epistemic_preservation(safe, unsafe)
    assert result["passed"] is False
    assert "may indicate" in result["missing_phrases"]
    assert "not validated" in result["missing_phrases"]


def test_high_risk_gates_remain_renderable_without_activation():
    assert "not authorized" in render_message("OUTPUT.MUHURTA.RECOMMENDATION_NOT_AUTHORIZED")["text"]
    assert "not validated" in render_message("SAFETY.D20_INTERPRETATION_NOT_VALIDATED")["text"]
    assert "research-only" in render_message("SAFETY.ASHTAKAVARGA_RESEARCH_ONLY")["text"]
    assert "No predictive claim" in render_message("SAFETY.NO_PREDICTIVE_CLAIM")["text"]


def test_unicode_and_json_serialization_are_utf8_safe():
    payload = {"canonical_id": "TERM.PLANET.SUN", "display": "सूर्य — Sūrya", "status": "RESEARCH_ONLY"}
    encoded = serialize_unicode(payload)
    assert "सूर्य" in encoded
    assert "Sūrya" in encoded
    assert json.loads(encoded) == payload


def test_locale_does_not_change_canonical_semantics():
    facts = {"planet_id": "JUPITER", "status": "NOT_VALIDATED", "value": 20.5}
    english = render_structured(facts, "en")
    hindi = render_structured(facts, "hi")
    assert english["fact_payload"] == hindi["fact_payload"] == facts
    assert english["display"]["planet_display"] != hindi["display"]["planet_display"]
    assert english["display"]["status_display"] != hindi["display"]["status_display"]


def test_coverage_report_does_not_claim_unimplemented_locale_complete():
    english = coverage_report("en")
    tamil = coverage_report("ta")
    hindi = coverage_report("hi")
    assert english["coverage"] == 1.0
    assert english["classification"] == "CANONICAL_BASELINE"
    assert english["machine_draft"] == 0
    assert english["missing"] == 0
    assert tamil["status"] == "UNIMPLEMENTED_LOCALE"
    assert tamil["coverage"] == 0.0
    assert tamil["fallback_used"] == tamil["missing"]
    assert hindi["coverage"] == 1.0
    assert hindi["machine_draft"] == 49
    assert hindi["human_reviewed"] == 0


def test_two_runs_are_deterministic():
    first = serialize_unicode({"term": render_term("Vimshottari", "en"), "coverage": coverage_report("en")})
    second = serialize_unicode({"term": render_term("Vimshottari", "en"), "coverage": coverage_report("en")})
    assert hashlib.sha256(first.encode("utf-8")).hexdigest() == hashlib.sha256(second.encode("utf-8")).hexdigest()


def test_compact_language_regression_corpus_covers_required_families():
    cases = json.loads(Path("tests/fixtures/veda_lang002_language_corpus.json").read_text(encoding="utf-8"))
    categories = {case["category"] for case in cases}
    assert {"planet", "sign", "nakshatra", "varga", "dasha", "panchanga", "governance", "citation", "qualified_interpretation", "negation", "muhurta", "ashtakavarga"}.issubset(categories)
