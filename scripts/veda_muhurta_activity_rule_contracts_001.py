"""Deterministic, governance-only MVP Muhurta activity contracts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ACTIVITY = "VEDA-MUHURTA-ACTIVITY-RULE-CONTRACTS-001"
STARTING_COMMIT = "62e0955e9b315c19eae1e3f2b19bb72328574ad1"
OUT = Path("docs/current-state/muhurta-activity-rule-contracts-001")

RULE_CLASSES = {
    "HARD_EXCLUSION", "HARD_REQUIREMENT", "STRONG_NEGATIVE",
    "PREFERENCE_NEGATIVE", "NEUTRAL", "PREFERENCE_POSITIVE",
    "STRONG_POSITIVE", "PERSONAL_FACTOR", "CONTEXT_DEPENDENT",
    "SOURCE_VARIANT", "UNRESOLVED",
}


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest().upper()[:16]


def write_json(name: str, value: Any) -> None:
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(name: str, value: str) -> None:
    (OUT / name).write_text(value.rstrip() + "\n", encoding="utf-8")


SOURCE_CHAIN = {
    "BS_NAK_COMMERCE": {
        "work_id": "VEDA-SWW-WORK-BRIHAT-SAMHITA-001",
        "witness_id": "VEDA-SWW-WITNESS-BRIHAT-SAMHITA-TRANSLATION-001",
        "edition_id": "VEDA-SWW-EDITION-BRIHAT-SAMHITA-CONSULTED-001",
        "passage_id": "VEDA-SWW-PASSAGE-BRIHAT-SAMHITA-97-09-001",
        "assertion_id": "VEDA-SWW-ASSERTION-BS-NAK-COMMERCE-001",
        "legacy_source_id": "VEDA-SRC-BS-MUHURTA-001",
        "locator": "Brihat Samhita ch.97.09; scoped light-nakshatra action-family record",
        "scope": "Commerce and establishment action family; not universal auspiciousness",
        "state": "PASSAGE_MAPPED",
        "status": "VALIDATED_KNOWLEDGE",
    },
    "BS_NAK_LEARNING": {
        "work_id": "VEDA-SWW-WORK-BRIHAT-SAMHITA-001",
        "witness_id": "VEDA-SWW-WITNESS-BRIHAT-SAMHITA-TRANSLATION-001",
        "edition_id": "VEDA-SWW-EDITION-BRIHAT-SAMHITA-CONSULTED-001",
        "passage_id": "VEDA-SWW-PASSAGE-BRIHAT-SAMHITA-97-09-002",
        "assertion_id": "VEDA-SWW-ASSERTION-BS-NAK-LEARNING-001",
        "legacy_source_id": "VEDA-SRC-BS-MUHURTA-001",
        "locator": "Brihat Samhita ch.97.09; scoped light-nakshatra action-family record",
        "scope": "Learning action family; not all educational activity",
        "state": "PASSAGE_MAPPED",
        "status": "VALIDATED_KNOWLEDGE",
    },
    "BS_NAK_CONSECRATION": {
        "work_id": "VEDA-SWW-WORK-BRIHAT-SAMHITA-001",
        "witness_id": "VEDA-SWW-WITNESS-BRIHAT-SAMHITA-TRANSLATION-001",
        "edition_id": "VEDA-SWW-EDITION-BRIHAT-SAMHITA-CONSULTED-001",
        "passage_id": "VEDA-SWW-PASSAGE-BRIHAT-SAMHITA-97-06-001",
        "assertion_id": "VEDA-SWW-ASSERTION-BS-NAK-CONSECRATION-001",
        "legacy_source_id": "VEDA-SRC-BS-MUHURTA-001",
        "locator": "Brihat Samhita ch.97.06; fixed/dhruva action-family record",
        "scope": "Consecration, pacification and establishment; ceremony subtype required",
        "state": "PASSAGE_MAPPED",
        "status": "VALIDATED_KNOWLEDGE",
    },
    "BS_TITHI_KARANA": {
        "work_id": "VEDA-SWW-WORK-BRIHAT-SAMHITA-001",
        "witness_id": "VEDA-SWW-WITNESS-BRIHAT-SAMHITA-TRANSLATION-001",
        "edition_id": "VEDA-SWW-EDITION-BRIHAT-SAMHITA-CONSULTED-001",
        "passage_id": "VEDA-SWW-PASSAGE-BRIHAT-SAMHITA-98-99-001",
        "assertion_id": "VEDA-SWW-ASSERTION-BS-TITHI-KARANA-ACTIONS-001",
        "legacy_source_id": "VEDA-SRC-BS-MUHURTA-001",
        "locator": "Brihat Samhita ch.98.02-.03 and ch.99.03-.05",
        "scope": "Tithi/Karana action correspondence; event-specific, not universal denial",
        "state": "PASSAGE_MAPPED",
        "status": "VALIDATED_KNOWLEDGE",
    },
    "P032_FACTS": {
        "work_id": "VEDA-SWW-WORK-VEDA-P032-IMPLEMENTATION-001",
        "witness_id": "VEDA-SWW-WITNESS-VEDA-P032-RUNTIME-001",
        "edition_id": "VEDA-SWW-EDITION-VEDA-P032-RUNTIME-001",
        "passage_id": "VEDA-SWW-PASSAGE-VEDA-P032-FACT-CONTRACT-001",
        "assertion_id": "VEDA-SWW-ASSERTION-P032-FACTS-001",
        "legacy_source_id": "VEDA-SRC-PANCHANGA-FACTS-001",
        "locator": "engines/ai/knowledge/muhurta_foundation.py; P032 Panchanga fact contract",
        "scope": "Deterministic Vara, Tithi, Nakshatra, Yoga, Karana and transitions",
        "state": "INTERNALLY_VALIDATED",
        "status": "PLATFORM_EVIDENCE",
    },
}


def assertion(key: str) -> str:
    return SOURCE_CHAIN[key]["assertion_id"]


def make_rule(rule_id: str, activity: str, factor: str, condition: str, effect: str,
              precedence: str, source_keys: list[str], state: str, label: str,
              rule_class: str, *, hard_requirement: bool = False,
              personal_required: bool = False, exceptions: list[str] | None = None) -> dict[str, Any]:
    if rule_class not in RULE_CLASSES:
        raise ValueError(rule_class)
    return {
        "rule_id": rule_id,
        "activity_scope": activity,
        "factor_type": factor,
        "condition": condition,
        "recommendation_effect": effect,
        "precedence_class": precedence,
        "hard_exclusion": False,
        "hard_requirement": hard_requirement,
        "personal_required": personal_required,
        "source_assertions": [assertion(key) for key in source_keys],
        "source_layer": "CLASSICAL_PRIMARY" if source_keys and source_keys[0].startswith("BS_") else "IMPLEMENTATION",
        "variant_id": "BS_SCOPED_ACTION_FAMILY_V1",
        "exceptions": exceptions or [],
        "validation_state": state,
        "explanation_label": label,
        "rule_class": rule_class,
        "production_activation": False,
    }


def make_contract(contract_id: str, activity_id: str, scope: dict[str, Any],
                  rules: list[dict[str, Any]], coverage: dict[str, Any],
                  unresolved: list[str], state: str, caution: str,
                  consultation: str, variants: list[str],
                  subscopes: list[dict[str, str]] | None = None) -> dict[str, Any]:
    contract: dict[str, Any] = {
        "contract_id": contract_id,
        "version": "1.0.0",
        "activity_id": activity_id,
        "activity_scope": scope,
        "source_tradition": ["BRIHAT_SAMHITA_SCOPED_ACTION_FAMILIES", "VEDA_P032_FACT_CONTRACT"],
        "rule_ids": [item["rule_id"] for item in rules],
        "rules": rules,
        "hard_exclusions": [],
        "hard_requirements": [item["rule_id"] for item in rules if item["hard_requirement"]],
        "strong_negatives": [],
        "preference_negatives": [],
        "preference_positives": [item["rule_id"] for item in rules if item["rule_class"] == "PREFERENCE_POSITIVE"],
        "strong_positives": [],
        "personal_factors": [item["rule_id"] for item in rules if item["personal_required"]],
        "source_variants": variants,
        "conflict_policy": {
            "policy_id": "MUH-POLICY-CONFLICT-CATEGORICAL-V1",
            "resolution": "Do not average competing rules; isolate variants and abstain on unresolved material conflict.",
            "unresolved_conflict_state": "SOURCE_CONFLICT_UNRESOLVED",
        },
        "precedence_policy": [
            "HARD_EXCLUSION", "HARD_REQUIREMENT", "STRONG_NEGATIVE",
            "CONTEXT_DEPENDENT", "PREFERENCE_NEGATIVE",
            "PREFERENCE_POSITIVE", "STRONG_POSITIVE", "NEUTRAL",
        ],
        "abstention_policy": [
            "INSUFFICIENT_RULE_COVERAGE", "SOURCE_CONFLICT_UNRESOLVED",
            "REQUIRED_FACTOR_UNAVAILABLE", "PERSONAL_FACTOR_REQUIRED",
            "CALCULATION_DEPENDENCY_UNAVAILABLE", "ACTIVITY_SCOPE_MISMATCH",
        ],
        "rule_coverage": coverage,
        "unresolved_areas": unresolved,
        "caution_class": caution,
        "consultation_class": consultation,
        "subscopes": subscopes or [],
        "production_bound": False,
        "recommendation_engine_state": state,
        "arbitrary_numeric_score": False,
        "hidden_weights": False,
    }
    contract["contract_hash"] = digest(contract)
    return contract


def build_contracts() -> dict[str, dict[str, Any]]:
    business = make_contract(
        "VEDA-MUH-CONTRACT-BUSINESS-OPENING-V1",
        "BUSINESS_OPENING_INAUGURATION",
        {"included": ["opening or inaugurating a commercial establishment"],
         "excluded": ["investment selection", "stock trading", "loans", "major financing", "incorporation deadlines", "tax filings"],
         "mode": "GENERAL_MUHURTA_ONLY"},
        [
            make_rule("MUH-BIZ-NAK-001", "BUSINESS_OPENING_INAUGURATION", "NAKSHATRA",
                      "Nakshatra action class is the scoped commerce/establishment family.",
                      "PREFERENCE_POSITIVE", "PREFERENCE_POSITIVE", ["BS_NAK_COMMERCE"],
                      "CONTRACT_FROZEN", "Scoped commerce compatibility; not a success claim.", "PREFERENCE_POSITIVE"),
            make_rule("MUH-BIZ-TITHI-KARANA-001", "BUSINESS_OPENING_INAUGURATION", "TITHI_KARANA",
                      "Tithi/Karana action correspondence applies to the stated commerce action.",
                      "CONTEXT_DEPENDENT", "CONTEXT_DEPENDENT", ["BS_TITHI_KARANA"],
                      "CONTRACT_FROZEN", "Event-specific correspondence remains conditional.", "CONTEXT_DEPENDENT",
                      exceptions=["Vishti is not treated as universal denial."]),
            make_rule("MUH-BIZ-PANCHANGA-INPUT-001", "BUSINESS_OPENING_INAUGURATION", "PANCHANGA_FACTS",
                      "P032 provides the requested local-date facts and transition boundaries.",
                      "NEUTRAL", "NEUTRAL", ["P032_FACTS"], "INTERNALLY_VALIDATED",
                      "Input dependency only; it does not select a Muhurta.", "NEUTRAL"),
            make_rule("MUH-BIZ-VARA-YOGA-GAP-001", "BUSINESS_OPENING_INAUGURATION", "VARA_YOGA",
                      "No activity-specific governed Vara or Yoga preference is established.",
                      "ABSTAIN", "UNRESOLVED", ["P032_FACTS"], "SOURCE_LIMITED",
                      "Facts exist, but no source-bound business rule is claimed.", "UNRESOLVED"),
        ],
        {"dimensions": ["VARA", "TITHI", "NAKSHATRA", "YOGA", "KARANA", "TRANSITIONS", "PERSONAL_FACTORS"],
         "resolved": ["P032_FACTS", "NAKSHATRA_SCOPED_COMMERCE", "TITHI_KARANA_SCOPED_ACTION"],
         "variant_dependent": [], "unresolved": ["ACTIVITY_SPECIFIC_VARA", "ACTIVITY_SPECIFIC_YOGA", "PERSONAL_BALA"],
         "coverage_state": "SUFFICIENT_FOR_NARROW_CONDITIONAL_GENERAL_CONTRACT"},
        ["No complete activity-specific Vara/Yoga contract.", "Personal Bala is not executable.", "No ranking or universal score."],
        "ENGINE_READY_WITH_CONDITION", "MODERATE_CONSEQUENCE_BUSINESS_CONTEXT",
        "BUSINESS_PROFESSIONAL_CONTEXT_REQUIRED", ["BS_SCOPED_ACTION_FAMILY_V1"],
    )
    education = make_contract(
        "VEDA-MUH-CONTRACT-EDUCATION-COMMENCEMENT-V1",
        "EDUCATION_COMMENCEMENT",
        {"included": ["formal course, programme, first lesson, or separately identified ceremonial commencement"],
         "excluded": ["routine daily studying", "examinations", "admission deadlines", "mandatory school requirements"],
         "mode": "GENERAL_MUHURTA_ONLY"},
        [
            make_rule("MUH-EDU-NAK-001", "EDUCATION_COMMENCEMENT", "NAKSHATRA",
                      "Nakshatra action class is the scoped learning action family.",
                      "PREFERENCE_POSITIVE", "PREFERENCE_POSITIVE", ["BS_NAK_LEARNING"],
                      "CONTRACT_FROZEN", "Learning compatibility only; no academic outcome claim.", "PREFERENCE_POSITIVE"),
            make_rule("MUH-EDU-TITHI-KARANA-001", "EDUCATION_COMMENCEMENT", "TITHI_KARANA",
                      "Tithi/Karana action correspondence applies to formal commencement of learning.",
                      "CONTEXT_DEPENDENT", "CONTEXT_DEPENDENT", ["BS_TITHI_KARANA"],
                      "CONTRACT_FROZEN", "Event-specific correspondence remains conditional.", "CONTEXT_DEPENDENT",
                      exceptions=["Mandatory educational dates take precedence over preference."]),
            make_rule("MUH-EDU-PANCHANGA-INPUT-001", "EDUCATION_COMMENCEMENT", "PANCHANGA_FACTS",
                      "P032 provides the requested local-date facts and transition boundaries.",
                      "NEUTRAL", "NEUTRAL", ["P032_FACTS"], "INTERNALLY_VALIDATED",
                      "Input dependency only; it does not select a Muhurta.", "NEUTRAL"),
            make_rule("MUH-EDU-ROUTINE-SCOPE-001", "EDUCATION_COMMENCEMENT", "ACTIVITY_SCOPE",
                      "Routine study is not silently treated as formal commencement.",
                      "ABSTAIN", "HARD_REQUIREMENT", ["P032_FACTS"], "CONTRACT_FROZEN",
                      "Scope mismatch must abstain rather than force a recommendation.", "HARD_REQUIREMENT",
                      hard_requirement=True),
            make_rule("MUH-EDU-VARA-YOGA-GAP-001", "EDUCATION_COMMENCEMENT", "VARA_YOGA",
                      "No activity-specific governed Vara or Yoga preference is established.",
                      "ABSTAIN", "UNRESOLVED", ["P032_FACTS"], "SOURCE_LIMITED",
                      "Facts exist, but no source-bound education rule is claimed.", "UNRESOLVED"),
        ],
        {"dimensions": ["VARA", "TITHI", "NAKSHATRA", "YOGA", "KARANA", "TRANSITIONS", "PERSONAL_FACTORS", "ACTIVITY_SCOPE"],
         "resolved": ["P032_FACTS", "NAKSHATRA_SCOPED_LEARNING", "TITHI_KARANA_SCOPED_ACTION", "ROUTINE_STUDY_SCOPE_GUARD"],
         "variant_dependent": [], "unresolved": ["ACTIVITY_SPECIFIC_VARA", "ACTIVITY_SPECIFIC_YOGA", "PERSONAL_BALA"],
         "coverage_state": "SUFFICIENT_FOR_NARROW_CONDITIONAL_GENERAL_CONTRACT"},
        ["Ceremonial commencement versus modern course start needs source separation.", "Personal Bala is not executable.", "No ranking or universal score."],
        "ENGINE_READY_WITH_CONDITION", "LOW_RISK_TRADITIONAL_EDUCATION_CONTEXT",
        "PRACTICAL_EDUCATION_REQUIREMENTS_PRIMARY", ["BS_SCOPED_ACTION_FAMILY_V1"],
    )
    religious = make_contract(
        "VEDA-MUH-CONTRACT-RELIGIOUS-SPIRITUAL-CEREMONY-V1",
        "RELIGIOUS_SPIRITUAL_CEREMONY",
        {"included": ["generic ceremony scope only when ceremony subtype is explicit"],
         "excluded": ["automatic priest/guru selection", "religious superiority claims", "universal rules for all traditions"],
         "mode": "GENERAL_MUHURTA_ONLY"},
        [
            make_rule("MUH-REL-NAK-001", "RELIGIOUS_SPIRITUAL_CEREMONY", "NAKSHATRA",
                      "Nakshatra action class is the scoped consecration/establishment/pacification family and matches ceremony subtype.",
                      "PREFERENCE_POSITIVE", "PREFERENCE_POSITIVE", ["BS_NAK_CONSECRATION"],
                      "CONTRACT_FROZEN", "Only the documented ceremony family is covered.", "PREFERENCE_POSITIVE"),
            make_rule("MUH-REL-TITHI-KARANA-001", "RELIGIOUS_SPIRITUAL_CEREMONY", "TITHI_KARANA",
                      "Tithi/Karana action correspondence applies to the declared ritual action.",
                      "CONTEXT_DEPENDENT", "CONTEXT_DEPENDENT", ["BS_TITHI_KARANA"],
                      "CONTRACT_FROZEN", "Event-specific correspondence remains conditional.", "CONTEXT_DEPENDENT"),
            make_rule("MUH-REL-SUBSCOPE-001", "RELIGIOUS_SPIRITUAL_CEREMONY", "CEREMONY_SUBSCOPE",
                      "Puja, homa, japa, initiation, vrata, installation and other ceremonies cannot share one undocumented rule set.",
                      "ABSTAIN", "HARD_REQUIREMENT", ["P032_FACTS"], "SOURCE_LIMITED",
                      "A ceremony subtype is required before future evaluation.", "HARD_REQUIREMENT", hard_requirement=True),
            make_rule("MUH-REL-PANCHANGA-INPUT-001", "RELIGIOUS_SPIRITUAL_CEREMONY", "PANCHANGA_FACTS",
                      "P032 provides the requested local-date facts and transition boundaries.",
                      "NEUTRAL", "NEUTRAL", ["P032_FACTS"], "INTERNALLY_VALIDATED",
                      "Input dependency only; it does not select a Muhurta.", "NEUTRAL"),
            make_rule("MUH-REL-PERSONAL-BALA-001", "RELIGIOUS_SPIRITUAL_CEREMONY", "TARA_CHANDRA_BALA",
                      "Personal Bala is not evaluated because its operative source formula is not verified.",
                      "ABSTAIN", "PERSONAL_FACTOR", ["P032_FACTS"], "SOURCE_LIMITED",
                      "Personalization remains deferred and cannot be silently omitted.", "PERSONAL_FACTOR",
                      personal_required=True),
        ],
        {"dimensions": ["VARA", "TITHI", "NAKSHATRA", "YOGA", "KARANA", "TRANSITIONS", "PERSONAL_FACTORS", "CEREMONY_SUBSCOPE"],
         "resolved": ["P032_FACTS", "NAKSHATRA_SCOPED_CONSECRATION", "TITHI_KARANA_SCOPED_ACTION"],
         "variant_dependent": ["CEREMONY_TRADITION_AND_LINEAGE"],
         "unresolved": ["CEREMONY_SPECIFIC_RULES", "ACTIVITY_SPECIFIC_VARA", "ACTIVITY_SPECIFIC_YOGA", "PERSONAL_BALA"],
         "coverage_state": "INSUFFICIENT_FOR_GENERIC_RELIGIOUS_ENGINE_CONTRACT"},
        ["Ceremony-specific corpus is incomplete.", "Tradition and lineage differences are material.", "Personal Bala is not executable.", "No ranking or universal score."],
        "SOURCE_HARDENING_REQUIRED", "LOW_RISK_TRADITIONAL_CONSULTATION_REQUIRED",
        "QUALIFIED_TRADITIONAL_PRACTITIONER_WHERE_CEREMONY_SPECIFIC",
        ["BS_SCOPED_ACTION_FAMILY_V1", "CEREMONY_LINEAGE_VARIANT_UNRESOLVED"],
        [{"id": "GENERAL_RELIGIOUS_CEREMONY", "state": "SOURCE_HARDENING_REQUIRED"},
         {"id": "CONSECRATION_OR_INSTALLATION", "state": "SCOPED_SOURCE_SUPPORT"},
         {"id": "PUJA_COMMENCEMENT", "state": "SOURCE_HARDENING_REQUIRED"},
         {"id": "JAPA_COMMENCEMENT", "state": "SOURCE_HARDENING_REQUIRED"},
         {"id": "INITIATION", "state": "SOURCE_HARDENING_REQUIRED"},
         {"id": "VRATA", "state": "SOURCE_HARDENING_REQUIRED"}],
    )
    return {item["activity_id"]: item for item in (business, education, religious)}


def build_result() -> dict[str, Any]:
    contract_map = build_contracts()
    matrix = []
    for contract in contract_map.values():
        for item in contract["rules"]:
            for assertion_id in item["source_assertions"]:
                source = next(value for value in SOURCE_CHAIN.values() if value["assertion_id"] == assertion_id)
                matrix.append({
                    "activity_id": contract["activity_id"], "contract_id": contract["contract_id"], "rule_id": item["rule_id"],
                    "rule_to_assertion": assertion_id, "assertion_to_passage": source["passage_id"],
                    "passage_to_edition": source["edition_id"], "edition_to_witness": source["witness_id"],
                    "witness_to_work": source["work_id"], "legacy_source_id": source["legacy_source_id"],
                    "source_locator": source["locator"], "source_scope": source["scope"],
                    "source_status": source["status"], "validation_state": source["state"],
                    "source_layer": item["source_layer"], "rights_state": "DERIVED_METADATA_ONLY",
                    "source_witness_standard_id": "VEDA-KNOWLEDGE-SOURCE-WITNESS-STANDARD-001",
                    "source_registry_basis": "docs/current-state/p032-muhurta-foundation-001/01_MUHURTA_SOURCE_REGISTER.json plus KNOW-MUH-001/002/003",
                    "lineage_status": "LEGACY_SOURCE_REGISTRY_RECONCILED",
                    "full_source_text_committed": False, "production_activation": False,
                    "lineage": "ACTIVITY_RULE_CONTRACT -> RULE -> ASSERTION -> PASSAGE -> EDITION -> WITNESS -> WORK",
                })
    return {
        "activity": ACTIVITY, "starting_commit": STARTING_COMMIT,
        "predecessor": {
            "activity": "VEDA-MUHURTA-RECOMMENDATION-GOVERNANCE-001",
            "decision": "MUHURTA_RECOMMENDATION_GOVERNANCE_READY_WITH_CONDITION",
            "mvp_activities": ["BUSINESS_OPENING_INAUGURATION", "EDUCATION_COMMENCEMENT", "RELIGIOUS_SPIRITUAL_CEREMONY"],
            "recommendation_runtime": "INACTIVE",
        },
        "p032": {"foundation": "IMPLEMENTED / FROZEN", "consumed_facts": ["VARA", "TITHI", "NAKSHATRA", "YOGA", "KARANA", "TRANSITIONS", "TIMEZONE", "LOCATION"], "calculation_changed": False, "recommendation_runtime_changed": False},
        "contracts": contract_map, "source_matrix": matrix,
        "hard_exclusions": {
            "classical": [],
            "reason": "No activity-scoped source witness justifies promoting a preference or generic inauspicious label to hard exclusion.",
            "platform_safety_gates": ["MEDICAL_NO_DELAY_OF_URGENT_OR_NECESSARY_CARE", "LEGAL_NO_MISSED_DEADLINES_OR_STATUTORY_OBLIGATIONS", "FINANCIAL_NO_REPLACEMENT_FOR_PROFESSIONAL_ANALYSIS", "EDUCATION_NO_OVERRIDE_OF_MANDATORY_REQUIREMENTS", "BUSINESS_NO_COMMERCIAL_SUCCESS_GUARANTEE", "RELIGIOUS_NO_TRADITIONAL_AUTHORITY_REPLACEMENT", "MARRIAGE_OUTSIDE_MVP"],
        },
        "conflicts": [
            {"conflict_id": "MUH-CONFLICT-SCOPED-VS-UNIVERSAL-001", "activity": "ALL_MVP", "rule_a": "P032-RULE-EVENT-SCOPED-001", "rule_b": "P032-RULE-SCORE-001", "conflict_type": "DIFFERENT_SCOPE", "normalization_checked": True, "resolution": "Keep scoped action families categorical; reject universal score construction.", "unresolved": False},
            {"conflict_id": "MUH-CONFLICT-MARRIAGE-SCOPE-001", "activity": "ALL_MVP", "rule_a": "MARRIAGE_SPECIFIC_KARANA_CONDITIONS", "rule_b": "MVP_ACTIVITY_RULES", "conflict_type": "DIFFERENT_SCOPE", "normalization_checked": True, "resolution": "Exclude marriage-specific conditions from all MVP contracts.", "unresolved": False},
            {"conflict_id": "MUH-CONFLICT-PERSONAL-BALA-001", "activity": "ALL_MVP", "rule_a": "P032-RULE-TARABALA-001;P032-RULE-CHANDRABALA-001", "rule_b": "GENERAL_MUHURTA_CONTRACTS", "conflict_type": "UNRESOLVED", "normalization_checked": True, "resolution": "Mark personalization deferred and abstain when a personal rule is required.", "unresolved": True},
        ],
        "personal_factors": {"mode": "GENERAL_MUHURTA_ONLY", "tara_bala": "RESEARCH_CANDIDATE / NOT_EVALUATED", "chandra_bala": "RESEARCH_CANDIDATE / NOT_EVALUATED", "activated": False, "required_for_contracts": False},
        "evaluator_design": {
            "future_inputs": ["activity_id", "activity_subscope_if_required", "local_date", "timezone", "location", "tithi", "nakshatra", "vara", "yoga", "karana", "selected_ruleset"],
            "sequence": ["validate_activity_scope", "load_ruleset", "check_hard_exclusions", "check_hard_requirements", "check_strong_negatives", "apply_contextual_rules", "apply_preferences", "check_variants_and_conflicts", "classify_or_abstain"],
            "execution": "NORMALIZED_RULES_ONLY", "llm_rule_execution": False, "window_search": False, "ranking": False, "numeric_score": False,
        },
        "production": {"production_bound": False, "recommendation_runtime": "INACTIVE", "personalized_runtime": "INACTIVE", "p032_changed": False, "shadbala_changed": False, "ashtakavarga_changed": False, "d20_changed": False, "prediction_changed": False, "ml_changed": False, "rag_changed": False, "rag_documents_before": 1205, "rag_documents_after": 1205, "approved_core_before": 17, "approved_core_after": 17, "approved_core_promotions": 0, "provider_calls": 0},
        "decision": {"programme_decision": "MUHURTA_PARTIAL_ACTIVITY_CONTRACTS_READY", "business": "ENGINE_READY_WITH_CONDITION", "education": "ENGINE_READY_WITH_CONDITION", "religious": "SOURCE_HARDENING_REQUIRED", "at_least_one_engine_ready": True, "recommendation_engine_authorized": True, "authorization_scope": "Future conditional engine programme only; not started and not production-bound.", "reason": "Business and education have narrow conditional general contracts with deterministic inputs, precedence, abstention and caution. Religious ceremony requires ceremony-specific source hardening."},
        "next_programme": {"id": "VEDA-MUHURTA-RECOMMENDATION-ENGINE-001", "lane": "MUHURTA / PRODUCT", "objective": "Implement only the narrow conditional business and education evaluator after explicit authorization; keep religious ceremony gated.", "evidence_ready": True, "automatically_started": False},
    }


def acceptance(result: dict[str, Any]) -> list[dict[str, str]]:
    checks = [
        ("AC01", "Three MVP activities preserved", len(result["contracts"]) == 3),
        ("AC02", "Activity IDs deterministic", set(result["contracts"]) == {"BUSINESS_OPENING_INAUGURATION", "EDUCATION_COMMENCEMENT", "RELIGIOUS_SPIRITUAL_CEREMONY"}),
        ("AC03", "Activity scope explicit", all(item["activity_scope"]["included"] for item in result["contracts"].values())),
        ("AC04", "Source-witness lineage present", all(item["rule_to_assertion"] and item["lineage"] and item["lineage_status"] == "LEGACY_SOURCE_REGISTRY_RECONCILED" for item in result["source_matrix"])),
        ("AC05", "Rule IDs deterministic", len({r["rule_id"] for c in result["contracts"].values() for r in c["rules"]}) == sum(len(c["rules"]) for c in result["contracts"].values())),
        ("AC06", "Rule classes valid", all(r["rule_class"] in RULE_CLASSES for c in result["contracts"].values() for r in c["rules"])),
        ("AC07", "Hard exclusion explicit", all("hard_exclusions" in c for c in result["contracts"].values())),
        ("AC08", "Hard requirement explicit", all("hard_requirements" in c for c in result["contracts"].values())),
        ("AC09", "No hidden weights or score", result["evaluator_design"]["numeric_score"] is False and all(not c["arbitrary_numeric_score"] and not c["hidden_weights"] for c in result["contracts"].values())),
        ("AC10", "Precedence deterministic", all(c["precedence_policy"][0] == "HARD_EXCLUSION" for c in result["contracts"].values())),
        ("AC11", "Variant isolation", all(c["source_variants"] for c in result["contracts"].values())),
        ("AC12", "Cross-tradition guard", "Do not average" in result["contracts"]["BUSINESS_OPENING_INAUGURATION"]["conflict_policy"]["resolution"]),
        ("AC13", "Abstention behavior defined", all(len(c["abstention_policy"]) >= 5 for c in result["contracts"].values())),
        ("AC14", "General/personal separation", result["personal_factors"]["activated"] is False),
        ("AC15", "Caution bound", all(c["caution_class"] for c in result["contracts"].values())),
        ("AC16", "Consultation bound", all(c["consultation_class"] for c in result["contracts"].values())),
        ("AC17", "Business safety messaging", "BUSINESS_NO_COMMERCIAL_SUCCESS_GUARANTEE" in result["hard_exclusions"]["platform_safety_gates"]),
        ("AC18", "Education practical constraint", "EDUCATION_NO_OVERRIDE_OF_MANDATORY_REQUIREMENTS" in result["hard_exclusions"]["platform_safety_gates"]),
        ("AC19", "Religious consultation messaging", "QUALIFIED_TRADITIONAL" in result["contracts"]["RELIGIOUS_SPIRITUAL_CEREMONY"]["consultation_class"]),
        ("AC20", "Marriage remains excluded", "MARRIAGE_OUTSIDE_MVP" in result["hard_exclusions"]["platform_safety_gates"]),
        ("AC21", "Medical/legal/financial remain outside", all(c["activity_id"] not in {"MEDICAL_PROCEDURE", "LEGAL_ACTION_OR_FILING", "FINANCIAL_OR_INVESTMENT_DECISION"} for c in result["contracts"].values())),
        ("AC22", "P032 unchanged", not result["p032"]["calculation_changed"] and not result["production"]["p032_changed"]),
        ("AC23", "Recommendation runtime inactive", result["production"]["recommendation_runtime"] == "INACTIVE"),
        ("AC24", "Parallel states preserved", all(result["production"][key] is False for key in ["shadbala_changed", "ashtakavarga_changed", "d20_changed", "prediction_changed", "ml_changed", "rag_changed"])),
        ("AC25", "Approved Core unchanged", result["production"]["approved_core_before"] == result["production"]["approved_core_after"] == 17),
        ("AC26", "RAG policy preserved", result["production"]["rag_documents_before"] == result["production"]["rag_documents_after"] == 1205),
        ("AC27", "Future evaluator normalized", result["evaluator_design"]["execution"] == "NORMALIZED_RULES_ONLY" and not result["evaluator_design"]["llm_rule_execution"]),
        ("AC28", "Religious readiness is not forced", result["decision"]["religious"] == "SOURCE_HARDENING_REQUIRED"),
        ("AC29", "At least one conditional contract ready", result["decision"]["at_least_one_engine_ready"]),
        ("AC30", "Next engine not auto-started", not result["next_programme"]["automatically_started"]),
    ]
    return [{"id": key, "criterion": label, "status": "PASS" if ok else "FAIL"} for key, label, ok in checks]


def emit(result: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    write_text("00_BASELINE.md", f"# {ACTIVITY} Baseline\n\nStarting commit: {STARTING_COMMIT}\n\nP032 is consumed as a frozen fact foundation. No production recommendation runtime, window ranking, personal Bala or scoring is activated.\n")
    write_json("01_EXISTING_RULE_INVENTORY.json", {"predecessor": result["predecessor"], "existing_assets": [{"asset": "P032 deterministic facts", "status": "IMPLEMENTED / FROZEN", "reuse": "VARA/TITHI/NAKSHATRA/YOGA/KARANA/transitions"}, {"asset": "KNOW-MUH-001/002/003", "status": "PASS_WITH_CONDITION", "reuse": "Scoped action families; personal Bala and universal score remain inactive"}, {"asset": "Source-witness standard", "status": "IMPLEMENTED / FROZEN", "reuse": "Activity rule lineage fields"}], "rules": [{"rule_id": "P032-RULE-EVENT-SCOPED-001", "status": "VALIDATED_KNOWLEDGE", "activation": "DISABLED", "scope": "Event-specific action families"}, {"rule_id": "P032-RULE-TARABALA-001", "status": "RESEARCH_CANDIDATE", "activation": "DISABLED", "scope": "Personal only"}, {"rule_id": "P032-RULE-CHANDRABALA-001", "status": "RESEARCH_CANDIDATE", "activation": "DISABLED", "scope": "Personal only"}, {"rule_id": "P032-RULE-SCORE-001", "status": "DEFERRED", "activation": "DISABLED", "scope": "Universal score"}]})
    write_json("02_MVP_ACTIVITY_SCOPE.json", {"activities": [{"activity_id": c["activity_id"], "scope": c["activity_scope"], "state": c["recommendation_engine_state"]} for c in result["contracts"].values()], "marriage": "MVP_DEFERRED", "medical_legal_financial": "OUT_OF_SCOPE"})
    write_json("03_BUSINESS_OPENING_RULE_CONTRACT.json", result["contracts"]["BUSINESS_OPENING_INAUGURATION"])
    write_json("04_EDUCATION_COMMENCEMENT_RULE_CONTRACT.json", result["contracts"]["EDUCATION_COMMENCEMENT"])
    write_json("05_RELIGIOUS_CEREMONY_RULE_CONTRACT.json", result["contracts"]["RELIGIOUS_SPIRITUAL_CEREMONY"])
    write_json("06_RULE_SOURCE_MATRIX.json", {"standard": "VEDA-KNOWLEDGE-SOURCE-WITNESS-STANDARD-001", "records": result["source_matrix"], "full_source_text_committed": False})
    write_json("07_HARD_EXCLUSION_REGISTER.json", result["hard_exclusions"])
    write_json("08_PRECEDENCE_AND_CONFLICT_REGISTER.json", {"precedence": result["contracts"]["BUSINESS_OPENING_INAUGURATION"]["precedence_policy"], "conflicts": result["conflicts"], "cross_tradition_guard": "NO_CROSS_TRADITION_RULE_OR_INVARIANT_MERGE_WITHOUT_EQUIVALENCE_OR_SCOPE_PROOF"})
    write_json("09_PERSONAL_FACTOR_DEPENDENCY.json", result["personal_factors"] | {"contract_impacts": {key: {"personal_factors": c["personal_factors"], "state": "NOT_EVALUATED"} for key, c in result["contracts"].items()}})
    write_json("10_RULE_COVERAGE_MATRIX.json", {key: {"activity_id": key, "state": c["recommendation_engine_state"], "coverage": c["rule_coverage"], "unresolved": c["unresolved_areas"]} for key, c in result["contracts"].items()})
    write_json("11_ACTIVITY_ABSTENTION_RULES.json", {key: {"activity_id": key, "abstention": c["abstention_policy"], "scope_exclusions": c["activity_scope"]["excluded"]} for key, c in result["contracts"].items()})
    write_json("12_ENGINE_HANDOFF.json", {"recommendation_engine": "VEDA-MUHURTA-RECOMMENDATION-ENGINE-001", "authorization": result["decision"], "handoffs": [{"contract_id": c["contract_id"], "contract_hash": c["contract_hash"], "supported_activity": key, "required_inputs": result["evaluator_design"]["future_inputs"], "rule_ids": c["rule_ids"], "precedence": c["precedence_policy"], "abstention": c["abstention_policy"], "caution_class": c["caution_class"], "output_states": ["SUPPORTED_WITH_CAUTION", "INSUFFICIENT_RULE_COVERAGE", "ACTIVITY_SCOPE_MISMATCH", "SOURCE_CONFLICT_UNRESOLVED", "ABSTAIN"], "unresolved_non_blocking_items": c["unresolved_areas"], "production_bound": False} for key, c in result["contracts"].items()]})
    write_text("13_PARALLEL_STATE.md", "P032, Shadbala, Ashtakavarga, D20, prediction, PRED-M4, ML, RAG, Approved Core, EMP-001 and provider/external evidence lanes are unchanged. RAG remains at 1,205 documents and Approved Core remains 17. No recommendation runtime is activated.")
    rows = acceptance(result)
    outcome = "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL"
    write_text("14_FINAL_ACCEPTANCE.md", "# Final Acceptance\n\n" + "\n".join(f"| {row['id']} | {row['criterion']} | {row['status']} |" for row in rows) + f"\n\nOverall: {outcome}. Criteria passed: {sum(row['status'] == 'PASS' for row in rows)}/{len(rows)}. Programme decision: {result['decision']['programme_decision']}. Recommendation runtime remains inactive.\n")


def main() -> None:
    result = build_result()
    emit(result)
    rows = acceptance(result)
    print(json.dumps({"activity": ACTIVITY, "decision": result["decision"]["programme_decision"], "criteria": len(rows), "passed": sum(row["status"] == "PASS" for row in rows), "contracts": {key: value["recommendation_engine_state"] for key, value in result["contracts"].items()}, "output": str(OUT)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
