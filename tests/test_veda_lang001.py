import json
from pathlib import Path

from engines.ai.chatbot.conversation_intelligence import analyze_conversation
from engines.ai.chatbot.language_intelligence import (
    EXPRESSION_REGISTRY,
    EXPRESSION_TYPES,
    corpus_stats,
    resolve_expressions,
)


def _benchmark():
    path = Path("tests/fixtures/veda_lang001_benchmark.json")
    return json.loads(path.read_text(encoding="utf-8"))


def test_lang001_governed_seed_thresholds_and_shared_types():
    stats = corpus_stats()
    assert stats["ENGLISH"] >= 150
    assert stats["HINDI"] >= 150
    assert stats["HINGLISH"] >= 150
    assert stats["TOTAL"] >= 450
    assert len({(record.language, record.canonical_expression) for record in EXPRESSION_REGISTRY}) == len(EXPRESSION_REGISTRY)
    assert {record.expression_type for record in EXPRESSION_REGISTRY}.issubset(set(EXPRESSION_TYPES))


def test_lang001_benchmark_has_one_hundred_cases():
    records = _benchmark()
    assert len(records) >= 100
    assert any(record["resolution"] == "LITERAL" for record in records)
    assert any(record["resolution"] == "METALINGUISTIC_USAGE" for record in records)
    assert any(record["resolution"] == "UNKNOWN_EXPRESSION" for record in records)
    assert any(record["language"] == "HINDI" for record in records)
    assert any(record["language"] == "HINGLISH" for record in records)


def test_lang001_literal_idiomatic_and_metalinguistic_resolution():
    idiom = resolve_expressions("He spilled the beans about the acquisition.")
    assert any(item["resolution"] == "IDIOMATIC" and item["meaning"] == "reveal a secret" for item in idiom["resolved"])
    literal = resolve_expressions("He spilled the beans onto the floor.")
    assert any(item["resolution"] == "LITERAL" for item in literal["resolved"])
    quoted = resolve_expressions("Why do people say 'spill the beans'?")
    assert quoted["metalinguistic_use"] is True
    assert any(item["resolution"] == "METALINGUISTIC_USAGE" for item in quoted["resolved"])


def test_lang001_hindi_roman_hindi_and_hinglish():
    devanagari = resolve_expressions("उसने मेरी नाक कटवा दी।")
    roman = resolve_expressions("Meri band baja di.")
    hinglish = resolve_expressions("Yaar, scene kya hai and mood off hai?")
    assert devanagari["resolved"]
    assert roman["resolved"]
    assert hinglish["resolved"]
    assert any(item["record"]["script"] == "DEVANAGARI" for item in devanagari["resolved"])
    assert any(item["record"]["language"] == "HINDI" for item in roman["resolved"])
    assert any(item["record"]["language"] == "HINGLISH" for item in hinglish["resolved"])


def test_lang001_domain_sensitive_abbreviation():
    jyotisha = resolve_expressions("MD is active in this Dasha analysis.", domain="JYOTISHA")
    business = resolve_expressions("The MD joined the business meeting.", domain="BUSINESS")
    health = resolve_expressions("The patient has an MD appointment.", domain="HEALTH")
    assert any(item["meaning"] == "Mahadasha" for item in jyotisha["resolved"])
    assert any(item["meaning"] == "Managing Director" for item in business["resolved"])
    assert any(item["meaning"] == "Doctor of Medicine" for item in health["resolved"])


def test_lang001_unknown_does_not_fabricate_definition():
    result = resolve_expressions("What does 'glorp baz' mean?")
    assert result["resolved"] == []
    assert result["unknown_expressions"]
    assert result["unknown_expressions"][0]["candidate_meaning"] == "UNKNOWN_EXPRESSION"


def test_lang001_understanding_is_separate_from_active_usage():
    result = resolve_expressions("Bakwaas mat bolo.")
    assert result["resolved"]
    item = next(item for item in result["resolved"] if item["record"]["canonical_expression"] == "bakwaas")
    assert item["can_understand"] is True
    assert item["appropriate_to_use"] is False
    assert item["record"]["offensiveness_level"] == "MILD"


def test_lang001_comm001_and_chat_context_receive_expression_evidence():
    context = analyze_conversation("Yaar, scene kya hai? This is a piece of cake.")
    expressions = {item["record"]["canonical_expression"] for item in context.expression_evidence}
    assert "scene kya hai" in expressions
    assert "piece of cake" in expressions
    assert context.understood_not_mirrored is True
