"""Build the governed Muhurta Activity Expansion T3 bundle.

T3 is a source-governance and machine-contract activity only.  It recovers the
authoritative T1/T2 inventory, freezes the two house-lane contracts, selects
one evidence-rich remaining activity, and records a diagnostic machine
mapping.  It deliberately does not register a production activity, change
P032, or authorize the engine expansion automatically.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


PROGRAMME = "VEDA-MUHURTA-ACTIVITY-EXPANSION-T3-001"
STARTING_COMMIT = "2bfe37d0154cd4857f79d629087c090b523370fb"
SOURCE_STANDARD = "VEDA-KNOWLEDGE-SOURCE-WITNESS-STANDARD-001"
ROOT = Path(__file__).resolve().parents[1]
T1_ROOT = ROOT / "docs/current-state/muhurta-activity-expansion-t1-001"
T2_ROOT = ROOT / "docs/current-state/muhurta-activity-expansion-t2-001"
HOUSE_ROOT = ROOT / "docs/current-state/muhurta-house-electional-factor-hardening-001"
OUT = ROOT / "docs/current-state/muhurta-activity-expansion-t3-001"

COMPLETED = {
    "BUSINESS_OPENING_INAUGURATION",
    "EDUCATION_COMMENCEMENT",
    "VEHICLE_CONVEYANCE_COMMENCEMENT",
    "CONSECRATION_INSTALLATION_COMMENCEMENT",
}
HOUSE_ACTIVITIES = {"HOUSE_CONSTRUCTION_COMMENCEMENT", "HOUSE_ENTRY_OR_GRIHA_PRAVESHA"}
SELECTED = ["MARRIAGE_CEREMONY_TIMING"]

HOUSE_EXPECTED = {
    "HOUSE_CONSTRUCTION_COMMENCEMENT": {
        "contract_id": "VEDA-MUH-T2-CONTRACT-HOUSE_CONSTRUCTION_COMMENCEMENT-V1",
        "contract_hash": "9939643F8BA87AC13CFD31EA2C4295D0844FE67684E881DB05C1384234C7E12C",
        "machine_hash": "EBAA6885C9761697714A09366848045BF69C6E67D7B1855352D47151CEC01E9F",
    },
    "HOUSE_ENTRY_OR_GRIHA_PRAVESHA": {
        "contract_id": "VEDA-MUH-T2-CONTRACT-HOUSE_ENTRY_OR_GRIHA_PRAVESHA-V1",
        "contract_hash": "B466C139E179D3ABCB55FD0D9D19F602159755C366E1272CEA8030EACEEB019C",
        "machine_hash": "2AD390E55210E593984BE601EFF928F92B039CD01EF6014A43F516FF570D9A3D",
    },
}

MARRIAGE = {
    "source_activity_class": "PANIGRAHANA",
    "normalized_scope": "Timing of a human-chosen marriage ceremony or panigrahana event",
    "source_readiness": "SOURCE_STRONG_MACHINE_PARTIAL",
    "machine_feasibility": "PARTIAL_LAGNA_PLANETARY_AND_CONTEXT_DEPENDENCY",
    "rule_ids": [
        "MUH-T3-MARRIAGE-SCOPE-001",
        "MUH-T3-MARRIAGE-GODHULI-001",
        "MUH-T3-MARRIAGE-LAGNA-001",
        "MUH-T3-MARRIAGE-GRAHA-001",
    ],
    "assertions": [
        "VEDA-SWW-ASSERTION-BS-MARRIAGE-GODHULI-001",
        "VEDA-SWW-ASSERTION-MC-MARRIAGE-BALA-LAGNA-001",
    ],
    "passages": [
        "VEDA-SWW-PASSAGE-BRIHAT-SAMHITA-103-13-001",
        "VEDA-SWW-PASSAGE-MUHURTACINTAMANI-6-P249-001",
        "VEDA-SWW-PASSAGE-MUHURTACINTAMANI-6-76-001",
    ],
    "works": [
        "VEDA-SWW-WORK-BRIHAT-SAMHITA-001",
        "VEDA-SWW-WORK-MUHURTACINTAMANI-001",
    ],
    "existing_factors": [
        "P032-CALC-NAKSHATRA-001",
        "P032-CALC-TITHI-001",
        "P032-CALC-KARANA-001",
        "P032-CALC-VARA-001",
        "P032-CALC-YOGA-001",
    ],
    "missing_dependencies": [
        "VALIDATED_ELECTIONAL_LAGNA_FACTOR",
        "VALIDATED_ELECTIONAL_PLANETARY_CONTEXT",
        "GODHULI_SUNSET_CONTEXT_FACTOR",
    ],
    "personal_dependencies": [
        "TARA_CHANDRA_DIAGNOSTIC_ONLY",
        "BRIDE_GROOM_PERSONAL_FACTORS_SOURCE_PARTIAL",
    ],
    "variants": [
        "GODHULI_OVERRIDE_SCOPE_VARIANT",
        "MARRIAGE_LAGNA_AND_PLANETARY_PRIORITY_VARIANT",
        "HISTORICAL_GENDERED_OUTCOME_LANGUAGE_LIMITATION",
    ],
    "nonblocking_gaps": [
        "No complete VEDA activity-specific Tithi/Karana/Vara/Yoga value contract was established.",
        "Local ritual, family and lineage practice is not universalized.",
        "The source outcome language is historical and is not used as a modern outcome claim.",
    ],
    "blocking_gaps": [
        "Validated electional Lagna and planetary predicates are not exposed by the trusted P032 contract.",
        "The source-specific Godhuli/sunset context is not a governed P032 factor.",
        "A high-consequence marriage activity requires explicit human-choice and practical-context boundaries.",
    ],
    "hard_exclusions": [
        "PARTNER_SELECTION_OR_COMPATIBILITY",
        "SHOULD_MARRY_OR_SHOULD_NOT_MARRY_DECISION",
        "MARRIAGE_OUTCOME_OR_DURATION_GUARANTEE",
        "LEGAL_REGISTRATION_OR_DEADLINE_DECISION",
    ],
    "caution_class": "HIGH_CONSEQUENCE_HUMAN_DECISION",
    "consultation_class": "QUALIFIED_TRADITIONAL_AND_PRACTICAL_CONTEXT_AS_APPLICABLE",
}


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest().upper()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def t2_preservation() -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for activity_id, expected in HOUSE_EXPECTED.items():
        contract_file = "06_SELECTED_ACTIVITY_A_RULE_CONTRACT.json" if activity_id == "HOUSE_CONSTRUCTION_COMMENCEMENT" else "09_SELECTED_ACTIVITY_B_RULE_CONTRACT.json"
        machine_file = "07_SELECTED_ACTIVITY_A_MACHINE_CONTRACT.json" if activity_id == "HOUSE_CONSTRUCTION_COMMENCEMENT" else "10_SELECTED_ACTIVITY_B_MACHINE_CONTRACT.json"
        contract = load_json(T2_ROOT / contract_file)
        machine = load_json(T2_ROOT / machine_file)
        rows[activity_id] = {
            "contract_id": contract["contract_id"],
            "contract_hash": contract["contract_hash"],
            "machine_hash": machine["machine_hash"],
            "expected_contract_hash": expected["contract_hash"],
            "expected_machine_hash": expected["machine_hash"],
            "contract_hash_match": contract["contract_hash"] == expected["contract_hash"],
            "machine_hash_match": machine["machine_hash"] == expected["machine_hash"],
            "machine_state": machine["machine_state"],
            "production_activation": machine["production_activation"],
            "frozen": True,
            "reopen_trigger": "REOPEN_ON_NEW_ELECTIONAL_SOURCE_EVIDENCE",
        }
    assert all(row["contract_hash_match"] and row["machine_hash_match"] for row in rows.values())
    return rows


def inventory() -> dict[str, Any]:
    t1 = load_json(T1_ROOT / "01_ACTIVITY_CANDIDATE_INVENTORY.json")["candidates"]
    t2 = load_json(T2_ROOT / "02_REMAINING_ACTIVITY_READINESS.json")["remaining"]
    by_id = {row["activity_id"]: dict(row) for row in t1}
    for row in t2:
        by_id.setdefault(row["activity_id"], {}).update(row)
    by_id["MARRIAGE_CEREMONY_TIMING"].update(MARRIAGE)
    remaining = [by_id[key] for key in sorted(by_id) if key not in COMPLETED]
    assert len(remaining) == 7
    assert not set(COMPLETED).intersection({row["activity_id"] for row in remaining})
    return {
        "original_candidate_count": len(t1),
        "completed_excluded": sorted(COMPLETED),
        "house_frozen_excluded": sorted(HOUSE_ACTIVITIES),
        "remaining": remaining,
        "selected": SELECTED,
        "candidate_ids_unique": len({row["activity_id"] for row in remaining}) == len(remaining),
        "numeric_readiness_score": False,
    }


def source_register() -> dict[str, Any]:
    return {
        "programme": PROGRAMME,
        "research_mode": "existing_witness_first_with_one_bounded_marriage_gap_check",
        "queries": [
            "Brihat Samhita chapter 103 marriage vivaha patala Godhuli Lagna",
            "Muhurtacintamani marriage prakarana bride groom Bala Lagna page 249",
            "Muhurtacintamani chapter 6 verse 76 marriage Lagna Navamsha",
        ],
        "accepted_witnesses": [
            {
                "work_id": "VEDA-SWW-WORK-BRIHAT-SAMHITA-001",
                "edition_id": "VEDA-SWW-EDITION-BRIHAT-SAMHITA-TRANSLATION-IYER-1884-001",
                "witness_id": "VEDA-SWW-WITNESS-BRIHAT-SAMHITA-WISDOMLIB-001",
                "passage_id": "VEDA-SWW-PASSAGE-BRIHAT-SAMHITA-103-13-001",
                "locator": "English translation chapter 103, verse 13; Sanskrit link exposed on witness page",
                "url": "https://www.wisdomlib.org/hinduism/book/brihat-samhita/d/doc229367.html",
                "role": "secondary translation witness for the bounded Godhuli exception",
                "claim": "The marriage chapter describes a distinct Godhuli context and says the ordinary Nakshatra/Tithi/Yoga/Karana/Lagna considerations need not be applied in that context.",
                "authority": "CLASSICAL_TEXT_SECONDARY_TRANSLATION",
                "rights": "DERIVED_METADATA_ONLY",
            },
            {
                "work_id": "VEDA-SWW-WORK-MUHURTACINTAMANI-001",
                "edition_id": "VEDA-SWW-EDITION-MUHURTACINTAMANI-NARAYANRAM-ACHARYA-1945-001",
                "witness_id": "VEDA-SWW-WITNESS-MUHURTACINTAMANI-JAINQUANTUM-001",
                "passage_id": "VEDA-SWW-PASSAGE-MUHURTACINTAMANI-6-P249-001",
                "locator": "Marriage Prakarana 6, scanned edition page 249 / printed page 233",
                "url": "https://jainqq.org/explore/002342/249",
                "role": "digitized Sanskrit/Hindi edition witness",
                "claim": "The marriage section discusses Guru/Sun/Moon strength and the need to examine the marriage Lagna; the source is historical and not generalized into modern outcome claims.",
                "authority": "TRADITIONAL_WORK_DIGITIZED_EDITION",
                "rights": "DERIVED_METADATA_ONLY; no scan committed",
            },
            {
                "work_id": "VEDA-SWW-WORK-MUHURTACINTAMANI-001",
                "edition_id": "VEDA-SWW-EDITION-MUHURTACINTAMANI-MANUSCRIPT-TRADITION-001",
                "witness_id": "VEDA-SWW-WITNESS-MUHURTACINTAMANI-VEDICPUPIL-001",
                "passage_id": "VEDA-SWW-PASSAGE-MUHURTACINTAMANI-6-76-001",
                "locator": "Chapter 6, verse 76, online Sanskrit/Hindi witness",
                "url": "https://vedicpupil.in/library/muhurta-chintamani-book-by-narayana/chapter-ch06/76",
                "role": "secondary manuscript-tradition comparison",
                "claim": "A marriage-time Lagna/Navamsha relationship is described as a condition for favorable result within the source's own historical marriage framework.",
                "authority": "TRADITIONAL_COMMENTARIAL_REFERENCE",
                "rights": "DERIVED_METADATA_ONLY",
            },
        ],
        "downgraded_or_rejected": [
            {"claim": "Generic online marriage-nakshatra tables", "reason": "No passage-level lineage or method scope."},
            {"claim": "Modern marriage success/compatibility guarantees", "reason": "Outside timing-only scope and unsupported outcome certainty."},
            {"claim": "Historical gendered outcome statements as universal rules", "reason": "Context and translation limitations; not machine-promoted."},
            {"claim": "OCR or search snippets without image/page verification", "reason": "Discovery only under the source-witness standard."},
        ],
        "ocr_used": False,
        "translation_uncertainty": [
            "Godhuli is a contextual traditional term and is not treated as a generic sunset-time calculator.",
            "Edition/page numbering and translated outcome language are not silently normalized into modern claims.",
        ],
        "lineage": "MACHINE PREDICATE -> RULE -> ASSERTION -> PASSAGE -> EDITION -> WITNESS -> WORK",
    }


def rule_contract() -> dict[str, Any]:
    return {
        "contract_id": "VEDA-MUH-T3-CONTRACT-MARRIAGE-CEREMONY-TIMING-V1",
        "version": "1.0.0",
        "activity_id": "MARRIAGE_CEREMONY_TIMING",
        "activity_scope": MARRIAGE["normalized_scope"],
        "source_tradition": ["BRIHAT_SAMHITA_VIVAHAPATALA", "MUHURTACINTAMANI_VIVAHA_PRAKARANA"],
        "rule_ids": MARRIAGE["rule_ids"],
        "hard_requirements": ["HUMAN_CHOSEN_MARRIAGE_CEREMONY_SCOPE", *MARRIAGE["missing_dependencies"]],
        "hard_exclusions": MARRIAGE["hard_exclusions"],
        "strong_negatives": [],
        "preference_negatives": [],
        "preference_positives": ["SOURCE_BOUND_GODHULI_CONTEXT_WHEN_EXPLICIT"],
        "strong_positives": [],
        "context_rules": [
            "TIMING_ONLY",
            "NO_PARTNER_MATCHING",
            "NO_SHOULD_MARRY_DECISION",
            "NO_OUTCOME_GUARANTEE",
            "NO_CROSS_TRADITION_MERGE",
            "HUMAN_PRACTICAL_AND_LEGAL_CONTEXT_REMAINS_PRIMARY",
        ],
        "personal_factors": MARRIAGE["personal_dependencies"],
        "variants": MARRIAGE["variants"],
        "precedence": ["HARD_EXCLUSION", "HARD_REQUIREMENT", "EXPLICIT_CONTEXT_OVERRIDE", "CONTEXT", "PREFERENCE", "ABSTAIN"],
        "abstention": ["MISSING_ELECTIONAL_FACTORS", "MISSING_GODHULI_CONTEXT", "ACTIVITY_SCOPE_MISMATCH", "PERSONAL_FACTOR_REQUIRED_BUT_UNAVAILABLE", "SOURCE_VARIANT_UNRESOLVED"],
        "caution_class": MARRIAGE["caution_class"],
        "consultation_class": MARRIAGE["consultation_class"],
        "production_bound": False,
        "readiness": "SOURCE_CONTRACT_READY_MACHINE_PARTIAL",
        "source_standard": SOURCE_STANDARD,
    }


def machine_contract(contract: dict[str, Any]) -> dict[str, Any]:
    predicates = [
        {"factor_id": "P032-CALC-NAKSHATRA-001", "evaluator_id": "MUH-T3-EVAL-MARRIAGE-NAKSHATRA-001", "operator": "OPTIONAL_CONTEXT_ONLY", "expected_class": "SOURCE_DEFINED_MARRIAGE_CLASS", "missing_value_policy": "ABSTAIN_PREFERENCE_ONLY", "recommendation_effect": "NONBLOCKING_PREFERENCE", "source_assertion_ids": ["VEDA-SWW-ASSERTION-MC-MARRIAGE-BALA-LAGNA-001"]},
        {"factor_id": "P032-CALC-TITHI-001", "evaluator_id": "MUH-T3-EVAL-MARRIAGE-TITHI-001", "operator": "OPTIONAL_CONTEXT_ONLY", "expected_class": "SOURCE_DEFINED_MARRIAGE_TITHI", "missing_value_policy": "ABSTAIN_PREFERENCE_ONLY", "recommendation_effect": "NONBLOCKING_PREFERENCE", "source_assertion_ids": []},
        {"factor_id": "P032-CALC-KARANA-001", "evaluator_id": "MUH-T3-EVAL-MARRIAGE-KARANA-001", "operator": "OPTIONAL_CONTEXT_ONLY", "expected_class": "SOURCE_DEFINED_MARRIAGE_KARANA", "missing_value_policy": "ABSTAIN_PREFERENCE_ONLY", "recommendation_effect": "NONBLOCKING_PREFERENCE", "source_assertion_ids": []},
        {"factor_id": "GODHULI_SUNSET_CONTEXT_FACTOR", "evaluator_id": "MUH-T3-EVAL-GODHULI-CONTEXT-001", "operator": "BOOLEAN_TRUE", "expected_value": True, "missing_value_policy": "ABSTAIN", "recommendation_effect": "EXPLICIT_CONTEXT_OVERRIDE_ONLY", "source_assertion_ids": ["VEDA-SWW-ASSERTION-BS-MARRIAGE-GODHULI-001"]},
        {"factor_id": "VALIDATED_ELECTIONAL_LAGNA_FACTOR", "evaluator_id": "MUH-T3-EVAL-MARRIAGE-LAGNA-001", "operator": "REQUIRED_BUT_UNAVAILABLE", "expected_class": "SOURCE_DEFINED_MARRIAGE_LAGNA", "missing_value_policy": "ABSTAIN", "recommendation_effect": "BLOCKING_REQUIREMENT", "source_assertion_ids": ["VEDA-SWW-ASSERTION-MC-MARRIAGE-BALA-LAGNA-001"]},
        {"factor_id": "VALIDATED_ELECTIONAL_PLANETARY_CONTEXT", "evaluator_id": "MUH-T3-EVAL-MARRIAGE-GRAHA-001", "operator": "REQUIRED_BUT_UNAVAILABLE", "expected_class": "SOURCE_DEFINED_MARRIAGE_PLANETARY_CONTEXT", "missing_value_policy": "ABSTAIN", "recommendation_effect": "BLOCKING_REQUIREMENT", "source_assertion_ids": ["VEDA-SWW-ASSERTION-BS-MARRIAGE-GODHULI-001", "VEDA-SWW-ASSERTION-MC-MARRIAGE-BALA-LAGNA-001"]},
    ]
    payload = {
        "activity_id": contract["activity_id"],
        "contract_id": contract["contract_id"],
        "machine_state": "SOURCE_CONTRACT_READY_MACHINE_PARTIAL",
        "production_activation": False,
        "predicates": predicates,
        "source_assertion_ids": MARRIAGE["assertions"],
        "blocking_dependencies": MARRIAGE["blocking_gaps"],
        "nonblocking_gaps": MARRIAGE["nonblocking_gaps"],
        "variant_ids": MARRIAGE["variants"],
        "no_runtime_registration": True,
        "no_numeric_score": True,
    }
    payload["machine_hash"] = digest(payload)
    return payload


def dry_runs() -> list[dict[str, Any]]:
    cases = [
        ("supporting_godhuli_context", {"activity_scope": "MARRIAGE_CEREMONY_TIMING", "godhuli_context": True, "validated_lagna": None, "validated_planetary_context": None}, "ABSTAIN_BLOCKING_ELECTIONAL_DEPENDENCY"),
        ("nonmatching_context", {"activity_scope": "MARRIAGE_CEREMONY_TIMING", "godhuli_context": False, "validated_lagna": None, "validated_planetary_context": None}, "ABSTAIN_BLOCKING_ELECTIONAL_DEPENDENCY"),
        ("missing_factor", {"activity_scope": "MARRIAGE_CEREMONY_TIMING"}, "ABSTAIN_MISSING_ELECTIONAL_FACTORS"),
        ("scope_mismatch", {"activity_scope": "PARTNER_COMPATIBILITY"}, "ABSTAIN_ACTIVITY_SCOPE_MISMATCH"),
        ("required_context_missing", {"activity_scope": "MARRIAGE_CEREMONY_TIMING", "godhuli_context": None}, "ABSTAIN_MISSING_GODHULI_OR_LAGNA_CONTEXT"),
        ("variant_isolation", {"activity_scope": "MARRIAGE_CEREMONY_TIMING", "tradition_variant": "LOCAL_LINEAGE_UNSPECIFIED"}, "ABSTAIN_SOURCE_VARIANT_UNRESOLVED"),
        ("source_trace", {"activity_scope": "MARRIAGE_CEREMONY_TIMING", "trace_requested": True}, "TRACE_REQUIRED_WITH_NO_RECOMMENDATION"),
    ]
    return [{"activity_id": "MARRIAGE_CEREMONY_TIMING", "case": name, "factors": factors, "expected": expected, "production": False} for name, factors, expected in cases]


def build_bundle() -> dict[str, Any]:
    contract = rule_contract()
    machine = machine_contract(contract)
    contract["contract_hash"] = digest(contract)
    inv = inventory()
    preservation = t2_preservation()
    handoff = {
        "programme": PROGRAMME,
        "production_activation": False,
        "machine_ready_activities": [],
        "selected_activity_ids": SELECTED,
        "reason": "Marriage has a source contract and diagnostic predicate mapping, but validated electional Lagna/planetary context and a governed Godhuli factor are unavailable; no executable production handoff is generated.",
        "activities": [{
            "activity_id": "MARRIAGE_CEREMONY_TIMING",
            "contract_id": contract["contract_id"],
            "contract_hash": contract["contract_hash"],
            "machine_hash": machine["machine_hash"],
            "source_activity_class": MARRIAGE["source_activity_class"],
            "required_factors": ["VALIDATED_ELECTIONAL_LAGNA_FACTOR", "VALIDATED_ELECTIONAL_PLANETARY_CONTEXT"],
            "optional_factors": MARRIAGE["existing_factors"],
            "required_context": ["HUMAN_CHOSEN_MARRIAGE_CEREMONY_SCOPE", "GODHULI_SUNSET_CONTEXT_FACTOR"],
            "rule_ids": MARRIAGE["rule_ids"],
            "machine_predicates": machine["predicates"],
            "nonblocking_gaps": MARRIAGE["nonblocking_gaps"],
            "blocking_gaps": MARRIAGE["blocking_gaps"],
            "precedence": contract["precedence"],
            "abstention": contract["abstention"],
            "caution": contract["caution_class"],
            "consultation": contract["consultation_class"],
            "source_trace": {"assertions": MARRIAGE["assertions"], "passages": MARRIAGE["passages"], "works": MARRIAGE["works"], "standard": SOURCE_STANDARD},
            "single_candidate_readiness": "NOT_READY",
            "window_search_readiness": "WINDOW_SEARCH_NOT_READY",
        }],
    }
    return {
        "baseline": {"programme": PROGRAMME, "starting_commit": STARTING_COMMIT, "production_activation": False, "approved_core_before": 17, "approved_core_after": 17, "rag_changed": False, "provider_calls": 0},
        "inventory": inv,
        "house_lane_freeze": preservation,
        "source_research": source_register(),
        "selected": {"activity": MARRIAGE, "rule_contract": contract, "machine_contract": machine},
        "dry_runs": dry_runs(),
        "window_dependency": {"activity_id": "MARRIAGE_CEREMONY_TIMING", "rule_factor_transition_map": [{"rule_id": rule_id, "factor_id": factor, "transition_source": "NOT_AVAILABLE_OR_NOT_VALIDATED"} for rule_id, factor in [("MUH-T3-MARRIAGE-GODHULI-001", "GODHULI_SUNSET_CONTEXT_FACTOR"), ("MUH-T3-MARRIAGE-LAGNA-001", "VALIDATED_ELECTIONAL_LAGNA_FACTOR"), ("MUH-T3-MARRIAGE-GRAHA-001", "VALIDATED_ELECTIONAL_PLANETARY_CONTEXT")]], "single_candidate": "NOT_READY", "window_search": "WINDOW_SEARCH_NOT_READY"},
        "handoff": handoff,
        "capability_register": {
            "capability_access_separated": True,
            "permanent_topic_restrictions": False,
            "activities": [
                {"activity_id": "BUSINESS_OPENING_INAUGURATION", "capability_state": "IMPLEMENTED_VALIDATED", "access_state": "ENABLED", "runtime_state": "OPERATIONAL_WITH_CONDITIONS"},
                {"activity_id": "EDUCATION_COMMENCEMENT", "capability_state": "IMPLEMENTED_VALIDATED", "access_state": "ENABLED", "runtime_state": "OPERATIONAL_WITH_CONDITIONS"},
                {"activity_id": "VEHICLE_CONVEYANCE_COMMENCEMENT", "capability_state": "IMPLEMENTED_VALIDATED", "access_state": "ENABLED", "runtime_state": "OPERATIONAL_WITH_CONDITIONS"},
                {"activity_id": "CONSECRATION_INSTALLATION_COMMENCEMENT", "capability_state": "IMPLEMENTED_VALIDATED", "access_state": "ENABLED", "runtime_state": "OPERATIONAL_WITH_CONDITIONS"},
                {"activity_id": "HOUSE_CONSTRUCTION_COMMENCEMENT", "capability_state": "MACHINE_PARTIAL", "access_state": "INACTIVE_UNTIL_IMPLEMENTED_VALIDATED", "runtime_state": "INACTIVE", "reopen": "REOPEN_ON_NEW_ELECTIONAL_SOURCE_EVIDENCE"},
                {"activity_id": "HOUSE_ENTRY_OR_GRIHA_PRAVESHA", "capability_state": "MACHINE_PARTIAL", "access_state": "INACTIVE_UNTIL_IMPLEMENTED_VALIDATED", "runtime_state": "INACTIVE", "reopen": "REOPEN_ON_NEW_ELECTIONAL_SOURCE_EVIDENCE"},
                {"activity_id": "MARRIAGE_CEREMONY_TIMING", "capability_state": "SOURCE_CONTRACT_READY_MACHINE_PARTIAL", "access_state": "INACTIVE_UNTIL_IMPLEMENTED_VALIDATED", "runtime_state": "INACTIVE", "window_search_state": "WINDOW_SEARCH_NOT_READY", "personalization_state": "DIAGNOSTIC_ONLY"},
                {"activity_id": "TRAVEL_JOURNEY_COMMENCEMENT", "capability_state": "SOURCE_HARDENING_REQUIRED", "access_state": "INACTIVE", "runtime_state": "INACTIVE"},
                {"activity_id": "PUJA_JAPA_VRATA_COMMENCEMENT", "capability_state": "SOURCE_HARDENING_REQUIRED", "access_state": "INACTIVE", "runtime_state": "INACTIVE"},
                {"activity_id": "PROPERTY_PURCHASE_OR_REGISTRATION", "capability_state": "SOURCE_HARDENING_REQUIRED", "access_state": "INACTIVE", "runtime_state": "INACTIVE"},
                {"activity_id": "MEDICAL_PROCEDURE", "capability_state": "SOURCE_HARDENING_REQUIRED", "access_state": "INACTIVE", "runtime_state": "INACTIVE"},
                {"activity_id": "PERSONAL_TARA_CHANDRA_BALA", "capability_state": "DIAGNOSTIC_OPERATIONAL", "access_state": "DISABLED_FOR_PRODUCTION", "runtime_state": "INACTIVE"},
            ],
        },
        "parallel_state": {"p032": "UNCHANGED", "shadbala": "UNCHANGED", "ashtakavarga": "UNCHANGED", "d20": "UNCHANGED", "rag": "UNCHANGED", "approved_core": "17_TO_17", "prediction": "UNCHANGED", "pred_m4": "INSUFFICIENT_SAMPLE", "ml": "LOCKED", "emp_001": "ACTIVE_LONGITUDINAL"},
    }


def write_bundle(bundle: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    files = {
        "01_ACTIVITY_INVENTORY_RECONCILIATION.json": {"programme": PROGRAMME, "inventory": bundle["inventory"], "completed_activities": sorted(COMPLETED), "house_activities_frozen": sorted(HOUSE_ACTIVITIES)},
        "03_REMAINING_ACTIVITY_READINESS.json": {"remaining": bundle["inventory"]["remaining"], "selected": SELECTED, "readiness_policy": "qualitative_only_no_numeric_score"},
        "05_SOURCE_RESEARCH_REGISTER.json": bundle["source_research"],
        "07_SELECTED_ACTIVITY_A_RULE_CONTRACT.json": bundle["selected"]["rule_contract"],
        "08_SELECTED_ACTIVITY_A_MACHINE_CONTRACT.json": bundle["selected"]["machine_contract"],
        "12_VARIANT_REGISTER.json": {"activity_id": "MARRIAGE_CEREMONY_TIMING", "variants": MARRIAGE["variants"], "cross_source_composition": "NOT_PERMITTED", "resolution": "retain separately; no union or averaging"},
        "13_CAUTION_CONSULTATION_MATRIX.json": {"activity_id": "MARRIAGE_CEREMONY_TIMING", "caution": MARRIAGE["caution_class"], "consultation": MARRIAGE["consultation_class"], "hard_exclusions": MARRIAGE["hard_exclusions"]},
        "14_SYNTHETIC_VALIDATION.json": bundle["dry_runs"],
        "15_WINDOW_DEPENDENCY_AUDIT.json": bundle["window_dependency"],
        "16_ENGINE_HANDOFF_T3.json": bundle["handoff"],
        "17_CAPABILITY_REGISTER.json": bundle["capability_register"],
        "18_PARALLEL_STATE.json": bundle["parallel_state"],
    }
    for name, value in files.items():
        (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    bundle = build_bundle()
    write_bundle(bundle)
    print(json.dumps({"programme": PROGRAMME, "selected": SELECTED, "contract_hash": bundle["selected"]["rule_contract"]["contract_hash"], "machine_hash": bundle["selected"]["machine_contract"]["machine_hash"], "machine_ready": bundle["handoff"]["machine_ready_activities"]}, sort_keys=True))


if __name__ == "__main__":
    main()
