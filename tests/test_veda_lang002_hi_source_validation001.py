import json
import subprocess
from pathlib import Path

from engines.ai.knowledge.language_foundation import (
    coverage_report,
    load_locale,
    load_term_registry,
    render_message,
    render_structured,
    render_term,
)


ROOT = Path(__file__).resolve().parents[1]
LOCALE_PATH = ROOT / "data/veda/localization/locales/hi.json"
DECISIONS_PATH = ROOT / "docs/current-state/lang-002-hi-source-validation-001/02_FINAL_REVIEW_DECISIONS.json"


def _baseline_locale():
    raw = subprocess.check_output(["git", "show", "b603fde41441c8a93b25e7fa4688f838ffe6ce8e:data/veda/localization/locales/hi.json"])
    return json.loads(raw)


def test_exactly_two_authorized_strings_changed_and_47_remain_identical():
    before = _baseline_locale()
    after = json.loads(LOCALE_PATH.read_text(encoding="utf-8"))
    changes = []
    for section in ("terms", "messages"):
        for canonical_id, value in before[section].items():
            if after[section][canonical_id] != value:
                changes.append(canonical_id)
    assert changes == [
        "SAFETY.MISSING_TRANSLATION",
        "OUTPUT.MUHURTA.RECOMMENDATION_NOT_AUTHORIZED",
    ]
    assert len(changes) == 2
    assert after["messages"]["GOVERNANCE.SOURCE_CITATION"] == "स्रोत उद्धरण"


def test_external_review_state_is_nonhuman_and_artifact_is_deterministic():
    pack = load_locale("hi")
    report = coverage_report("hi")
    decisions = json.loads(DECISIONS_PATH.read_text(encoding="utf-8"))
    assert report["total_keys"] == 49
    assert report["source_reviewed"] == 49
    assert report["review_pending"] == 0
    assert pack["review_state"] == "SOURCE_REVIEWED"
    assert pack["human_reviewed"] is False
    assert pack["production_authorized"] is False
    assert pack["review_metadata"]["validation_result"] == "47_ACCEPT_2_CHANGE_0_UNSURE"
    assert decisions["counts"] == {"ACCEPT": 47, "CHANGE": 2, "UNSURE": 0}
    assert decisions["human_reviewed"] is False
    assert decisions["approved_presentation"] is False
    assert decisions["review_hash"] == pack["review_metadata"]["review_hash"]


def test_legacy_aliases_and_iast_metadata_are_distinct():
    registry = load_term_registry()
    planets = {item["canonical_id"]: item for item in registry["terms"] if item["term_class"] == "JYOTISHA_TECHNICAL" and "iast" in item}
    assert len(planets) == 9
    assert planets["TERM.PLANET.SUN"]["iast"] == "Sūrya"
    assert planets["TERM.PLANET.SUN"]["transliteration"] == "Surya"
    assert planets["TERM.PLANET.SUN"]["metadata_roles"]["transliteration"] == "LEGACY_ROMAN_ALIAS"
    assert planets["TERM.PLANET.SUN"]["metadata_roles"]["iast"] == "IAST"
    assert "surya" in planets["TERM.PLANET.SUN"]["aliases"]
    assert render_term("TERM.PLANET.SUN", "hi")["text"] == "सूर्य"


def test_semantic_payload_and_frozen_boundaries_remain_unchanged():
    assert "अधिकृत नहीं" in render_message("OUTPUT.MUHURTA.RECOMMENDATION_NOT_AUTHORIZED", "hi")["text"]
    assert "मानक अंग्रेज़ी पाठ" in render_message("SAFETY.MISSING_TRANSLATION", "hi")["text"]
    facts = {"planet_id": "JUPITER", "status": "RESEARCH_ONLY", "source_id": "SRC-001", "value": 20.5}
    rendered = render_structured(facts, "hi")
    assert rendered["fact_payload"] == facts
    assert rendered["display"]["source_id"] == "SRC-001"
    assert rendered["display"]["status_display"] == "केवल शोध हेतु"
