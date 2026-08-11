from engines.ai.knowledge.yoga_dosha_governance import build_phase_bundle, evaluate_rule, validate_bundle


def test_nested_composite_rule_supports_positive_near_miss_and_modifier():
    positive = evaluate_rule("VEDA-RUL-YOGA-000001", {"relationships": {"jupiter_from_moon": {"house_distance": 3}}})
    strong = evaluate_rule("VEDA-RUL-YOGA-000001", {"relationships": {"jupiter_from_moon": {"house_distance": 0}}})
    near_miss = evaluate_rule("VEDA-RUL-YOGA-000001", {"relationships": {"jupiter_from_moon": {"house_distance": 2}}})
    assert positive["status"] == "FORMED"
    assert strong["status"] == "FORMED_WITH_MODIFICATION"
    assert near_miss["status"] == "NOT_FORMED"
    assert strong["modifier"]["effect"] == "STRONG"


def test_dosha_and_cancellation_are_separate_structural_outputs():
    formed = evaluate_rule("VEDA-RUL-DOSHA-000001", {"planets": {"Mars": {"house": 7}}})
    cancelled = evaluate_rule("VEDA-RUL-DOSHA-000001", {"planets": {"Mars": {"house": 7}}, "cancellations": {"VEDA-RUL-DOSHA-000001": True}})
    assert formed["status"] == "FORMED"
    assert cancelled["status"] == "CANCELLED"
    assert formed["interpretation_status"] == "RESEARCH_REQUIRED"


def test_p017_bundle_preserves_legacy_scope_and_lifecycle_block():
    bundle = build_phase_bundle()
    assert validate_bundle(bundle)["is_valid"] is True
    assert bundle["summary"]["legacy_yogas"] == 13
    assert bundle["summary"]["legacy_doshas"] == 5
    assert bundle["summary"]["production_activation"] == 0
    assert all(row["formation"] == "RESEARCHING" for row in bundle["capability_status"])
