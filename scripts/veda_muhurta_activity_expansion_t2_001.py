"""Build the source-governed Muhurta activity-expansion T2 bundle.

This programme creates contracts and diagnostic handoff metadata only.  It does
not register activities with production recommendation or window-search code.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


PROGRAMME = "VEDA-MUHURTA-ACTIVITY-EXPANSION-T2-001"
STARTING_COMMIT = "ac328da39670fa0ef28f564e23ede45adae4971c"
SOURCE_STANDARD = "VEDA-KNOWLEDGE-SOURCE-WITNESS-STANDARD-001"
ROOT = Path(__file__).resolve().parents[1]
T1_ROOT = ROOT / "docs/current-state/muhurta-activity-expansion-t1-001"
OUT = ROOT / "docs/current-state/muhurta-activity-expansion-t2-001"

COMPLETED = {
    "BUSINESS_OPENING_INAUGURATION",
    "EDUCATION_COMMENCEMENT",
    "VEHICLE_CONVEYANCE_COMMENCEMENT",
    "CONSECRATION_INSTALLATION_COMMENCEMENT",
}

SELECTED = ["HOUSE_CONSTRUCTION_COMMENCEMENT", "HOUSE_ENTRY_OR_GRIHA_PRAVESHA"]

ACTIVITIES: dict[str, dict[str, Any]] = {
    "HOUSE_CONSTRUCTION_COMMENCEMENT": {
        "source_activity_class": "BHAVANA_ARAMBHA",
        "normalized_scope": "Commencement of construction and first foundation work on a prepared house site",
        "source_readiness": "SOURCE_CONTRACT_READY_MACHINE_PARTIAL",
        "rule_ids": ["MUH-T2-HOUSE-CONSTRUCTION-001"],
        "assertions": ["VEDA-SWW-ASSERTION-BS-HOUSE-COMMENCEMENT-001"],
        "passages": ["VEDA-SWW-PASSAGE-BRIHAT-SAMHITA-53-98-112-001", "VEDA-SWW-PASSAGE-BRIHAT-SAMHITA-98-18-001"],
        "existing_factors": ["P032-CALC-NAKSHATRA-001", "P032-CALC-TITHI-001", "P032-CALC-KARANA-001"],
        "missing_dependencies": ["VALIDATED_ELECTIONAL_LAGNA_FACTOR", "VALIDATED_PLANETARY_ELECTION_CONTEXT"],
        "machine_state": "MACHINE_PARTIAL",
        "window_state": "TRANSITION_DEPENDENCY_MISSING",
        "variants": ["BRIHAT_SAMHITA_CHAPTER_NUMBERING_VARIANT", "STHIRA_LAGNA_TRANSLATION_SCOPE_UNCERTAINTY"],
        "nonblocking_gaps": ["Activity-specific Tithi/Karana composition is not source-complete.", "Site engineering, permits, title, budget and contractor checks remain external practical requirements."],
        "blocking_gaps": ["The current trusted P032 contract does not expose validated electional Lagna and planetary-context factors."],
        "caution_class": "PROPERTY_CONSTRUCTION_PRACTICAL_AND_LEGAL_CONTEXT",
        "consultation_class": "QUALIFIED_ENGINEERING_LEGAL_AND_TRADITIONAL_CONTEXT_AS_APPLICABLE",
        "hard_exclusions": ["PROPERTY_PURCHASE_OR_REGISTRATION", "LOAN_OR_FINANCING_DECISION", "LEGAL_PERMIT_DECISION"],
        "scope_notes": "Does not cover buying property, title, registration, financing, engineering approval, or guaranteed construction outcome.",
    },
    "HOUSE_ENTRY_OR_GRIHA_PRAVESHA": {
        "source_activity_class": "BHAVANA_PRAVESHA",
        "normalized_scope": "First entry into a completed or substantially completed dwelling after construction",
        "source_readiness": "SOURCE_CONTRACT_READY_MACHINE_PARTIAL",
        "rule_ids": ["MUH-T2-HOUSE-ENTRY-001"],
        "assertions": ["VEDA-SWW-ASSERTION-BS-HOUSE-ENTRY-001"],
        "passages": ["VEDA-SWW-PASSAGE-BRIHAT-SAMHITA-53-105-001", "VEDA-SWW-PASSAGE-BRIHAT-SAMHITA-98-18-001"],
        "existing_factors": ["P032-CALC-NAKSHATRA-001", "P032-CALC-TITHI-001", "P032-CALC-KARANA-001"],
        "missing_dependencies": ["VALIDATED_ELECTIONAL_LAGNA_FACTOR", "VALIDATED_PLANETARY_ELECTION_CONTEXT", "EXPLICIT_COMPLETION_AND_OCCUPANCY_CONTEXT"],
        "machine_state": "MACHINE_PARTIAL",
        "window_state": "TRANSITION_DEPENDENCY_MISSING",
        "variants": ["BRIHAT_SAMHITA_CHAPTER_NUMBERING_VARIANT", "GRIHA_PRAVESHA_TRADITION_AND_TRANSLATION_VARIANT"],
        "nonblocking_gaps": ["Activity-specific Tithi/Karana composition is not source-complete.", "Ritual procedure, lineage and local practice are not universalized."],
        "blocking_gaps": ["The current trusted P032 contract does not expose validated electional Lagna and planetary-context factors.", "The runtime request has no governed completion/occupancy context."],
        "caution_class": "PROPERTY_OCCUPANCY_PRACTICAL_AND_TRADITIONAL_CONTEXT",
        "consultation_class": "QUALIFIED_PROPERTY_AND_TRADITIONAL_CONTEXT_AS_APPLICABLE",
        "hard_exclusions": ["PROPERTY_PURCHASE_OR_REGISTRATION", "LEGAL_OCCUPANCY_DECISION", "STRUCTURAL_SAFETY_DECISION"],
        "scope_notes": "Does not cover property acquisition, title, registration, structural safety, legal occupancy, or a guaranteed household result.",
    },
}


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest().upper()


def contract_payload(activity_id: str) -> dict[str, Any]:
    item = ACTIVITIES[activity_id]
    return {
        "contract_id": f"VEDA-MUH-T2-CONTRACT-{activity_id}-V1",
        "version": "1.0.0",
        "activity_id": activity_id,
        "activity_scope": item["normalized_scope"],
        "source_tradition": ["BRIHAT_SAMHITA_SCOPED_VASTU_AND_NAKSHATRA_ACTIONS", "VEDA_P032_FACT_CONTRACT"],
        "rule_ids": item["rule_ids"],
        "hard_requirements": ["SOURCE_BOUND_ACTIVITY_SCOPE", *item["missing_dependencies"]],
        "hard_exclusions": item["hard_exclusions"],
        "strong_negatives": [],
        "preference_negatives": [],
        "preference_positives": ["SOURCE_BOUND_STHIRA_ACTION_CONTEXT"],
        "strong_positives": [],
        "context_rules": ["NO_UNIVERSAL_AUSPICIOUSNESS", "NO_OUTCOME_GUARANTEE", "NO_CROSS_TRADITION_MERGE"],
        "personal_factors": ["TARA_CHANDRA_DIAGNOSTIC_ONLY"],
        "variants": item["variants"],
        "precedence": ["HARD_EXCLUSION", "HARD_REQUIREMENT", "CONTEXT", "PREFERENCE", "ABSTAIN"],
        "abstention": ["MISSING_ELECTIONAL_FACTORS", "ACTIVITY_SCOPE_MISMATCH", "SOURCE_VARIANT_UNRESOLVED"],
        "caution_class": item["caution_class"],
        "consultation_class": item["consultation_class"],
        "production_bound": False,
        "readiness": item["source_readiness"],
        "source_standard": SOURCE_STANDARD,
    }


def machine_payload(activity_id: str) -> dict[str, Any]:
    item = ACTIVITIES[activity_id]
    return {
        "activity_id": activity_id,
        "contract_id": contract_payload(activity_id)["contract_id"],
        "machine_state": item["machine_state"],
        "production_activation": False,
        "predicates": [
            {"factor_id": "P032-CALC-NAKSHATRA-001", "evaluator_id": "MUH-T2-EVAL-NAKSHATRA-CLASS-001", "operator": "CLASS_CONTEXT_ONLY", "expected_class": "DHRUVA_OR_SOURCE_DEFINED_STHIRA", "missing_value_policy": "ABSTAIN", "recommendation_effect": "PREFERENCE_POSITIVE_ONLY"},
            {"factor_id": "VALIDATED_ELECTIONAL_LAGNA_FACTOR", "evaluator_id": "MUH-T2-EVAL-LAGNA-CONTEXT-001", "operator": "REQUIRED_BUT_UNAVAILABLE", "expected_class": "STHIRA_LAGNA_OR_SOURCE_DEFINED_EQUIVALENT", "missing_value_policy": "ABSTAIN", "recommendation_effect": "BLOCKING_REQUIREMENT"},
            {"factor_id": "VALIDATED_PLANETARY_ELECTION_CONTEXT", "evaluator_id": "MUH-T2-EVAL-GRAHA-CONTEXT-001", "operator": "REQUIRED_BUT_UNAVAILABLE", "expected_class": "SOURCE_DEFINED_PLANETARY_CONTEXT", "missing_value_policy": "ABSTAIN", "recommendation_effect": "BLOCKING_REQUIREMENT"},
        ],
        "source_assertion_ids": item["assertions"],
        "required_existing_p032_factors": item["existing_factors"],
        "blocking_dependencies": item["blocking_gaps"],
        "variant_ids": item["variants"],
        "no_runtime_registration": True,
    }


def build_bundle() -> dict[str, Any]:
    inventory = json.loads((T1_ROOT / "01_ACTIVITY_CANDIDATE_INVENTORY.json").read_text(encoding="utf-8"))
    candidates = inventory["candidates"]
    remaining = [row for row in candidates if row["activity_id"] not in COMPLETED]
    assert len(candidates) == 9
    assert not COMPLETED.intersection({row["activity_id"] for row in remaining})
    assert [row["activity_id"] for row in remaining if row["activity_id"] in SELECTED] == SELECTED

    contracts = {activity_id: {**contract_payload(activity_id), "contract_hash": digest(contract_payload(activity_id))} for activity_id in SELECTED}
    machines = {activity_id: {**machine_payload(activity_id), "machine_hash": digest(machine_payload(activity_id))} for activity_id in SELECTED}
    dry_runs = []
    for activity_id in SELECTED:
        for label, factors in (("supported_context_only", {"nakshatra_class": "DHRUVA"}), ("missing_factors", {}), ("scope_mismatch", {"activity_scope": "PROPERTY_PURCHASE_OR_REGISTRATION"})):
            dry_runs.append({"activity_id": activity_id, "case": label, "factors": factors, "expected": "ABSTAIN_MISSING_ELECTIONAL_FACTORS", "production": False})

    return {
        "baseline": {"programme": PROGRAMME, "starting_commit": STARTING_COMMIT, "production_activation": False, "approved_core_before": 17, "approved_core_after": 17},
        "inventory": {"original_candidates": len(candidates), "completed_excluded": sorted(COMPLETED), "remaining": remaining, "selected": SELECTED, "numeric_readiness_score": False},
        "contracts": contracts,
        "machines": machines,
        "dry_runs": dry_runs,
        "handoff": {"programme": PROGRAMME, "production_activation": False, "machine_ready_activities": [], "reason": "Both selected activities require unavailable validated electional Lagna/planetary context; no production engine handoff is executable."},
    }


def write_bundle(bundle: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for activity_id in SELECTED:
        if activity_id == SELECTED[0]:
            rule_name, machine_name = "06_SELECTED_ACTIVITY_A_RULE_CONTRACT.json", "07_SELECTED_ACTIVITY_A_MACHINE_CONTRACT.json"
        else:
            rule_name, machine_name = "09_SELECTED_ACTIVITY_B_RULE_CONTRACT.json", "10_SELECTED_ACTIVITY_B_MACHINE_CONTRACT.json"
        (OUT / rule_name).write_text(json.dumps(bundle["contracts"][activity_id], ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (OUT / machine_name).write_text(json.dumps(bundle["machines"][activity_id], ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "13_SYNTHETIC_VALIDATION.json").write_text(json.dumps(bundle["dry_runs"], ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "15_ENGINE_HANDOFF_T2.json").write_text(json.dumps(bundle["handoff"], ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    result = build_bundle()
    write_bundle(result)
    print(json.dumps({"programme": PROGRAMME, "selected": SELECTED, "contract_hashes": {key: value["contract_hash"] for key, value in result["contracts"].items()}, "machine_hashes": {key: value["machine_hash"] for key, value in result["machines"].items()}, "machine_ready": result["handoff"]["machine_ready_activities"]}, sort_keys=True))
