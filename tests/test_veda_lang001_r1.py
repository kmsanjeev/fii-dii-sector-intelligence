import json
from pathlib import Path

from engines.ai.chatbot.language_intelligence import EXPRESSION_REGISTRY, resolve_expressions


def _cases(name):
    return json.loads(Path("tests/fixtures", name).read_text(encoding="utf-8"))


def _matches(case, result):
    target = case["contains"].casefold()
    return [
        item for item in result["resolved"]
        if target in item["record"]["canonical_expression"].casefold()
        or item["record"]["canonical_expression"].casefold() in target
        or any(target == surface.casefold() for surface in item["record"]["surface_forms"])
    ]


def _score(cases):
    known = [case for case in cases if case["resolution"] != "UNKNOWN_EXPRESSION"]
    correct = 0
    fabricated = 0
    for case in cases:
        result = resolve_expressions(case["text"], domain=case.get("domain"))
        matches = _matches(case, result)
        expected = case["resolution"]
        if expected == "UNKNOWN_EXPRESSION":
            fabricated += bool(result["resolved"])
            continue
        correct += bool(
            (expected == "NONE" and not result["resolved"])
            or any(item["resolution"] == expected for item in matches)
        )
    return len(known), correct, fabricated


def test_lang001_r1_original_benchmark_gate_and_unknown_safety():
    known, correct, fabricated = _score(_cases("veda_lang001_benchmark.json"))
    assert (known, correct) == (90, 90)
    assert fabricated == 0


def test_lang001_r1_adversarial_and_holdout_gates():
    assert _score(_cases("veda_lang001_r1_adversarial.json")) == (49, 49, 0)
    assert _score(_cases("veda_lang001_r1_holdout.json")) == (29, 29, 0)


def test_lang001_r1_context_and_surface_regressions():
    assert resolve_expressions("The child broke the ice on the pond.")["resolved"][0]["resolution"] == "LITERAL"
    assert resolve_expressions("She bit the bullet and accepted the role.")["resolved"][0]["resolution"] == "IDIOMATIC"
    assert resolve_expressions("What is meant by 'kick the bucket'?")["resolved"][0]["resolution"] == "METALINGUISTIC_USAGE"
    assert resolve_expressions("मेरा mood off है।")["resolved"]
    assert resolve_expressions("दाँत खट्टे कर दिए।")["resolved"]


def test_lang001_r1_registry_has_no_duplicate_language_canonicals():
    keys = [(record.language, record.canonical_expression) for record in EXPRESSION_REGISTRY]
    assert len(keys) == len(set(keys))
