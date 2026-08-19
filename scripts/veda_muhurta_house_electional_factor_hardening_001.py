"""Build the bounded house-electional-factor hardening evidence bundle.

This activity audits reusable calculation paths and source semantics.  It does
not change P032, register a production activity, or create an engine handoff
unless all source and calculation gates are independently satisfied.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


PROGRAMME = "VEDA-MUHURTA-HOUSE-ELECTIONAL-FACTOR-HARDENING-001"
STARTING_COMMIT = "470284ea8b201a9613f114828daa3f8be4ec8170"
SOURCE_STANDARD = "VEDA-KNOWLEDGE-SOURCE-WITNESS-STANDARD-001"
ROOT = Path(__file__).resolve().parents[1]
T2_ROOT = ROOT / "docs/current-state/muhurta-activity-expansion-t2-001"
OUT = ROOT / "docs/current-state/muhurta-house-electional-factor-hardening-001"

T2_CONTRACTS = {
    "HOUSE_CONSTRUCTION_COMMENCEMENT": {
        "contract_file": "06_SELECTED_ACTIVITY_A_RULE_CONTRACT.json",
        "machine_file": "07_SELECTED_ACTIVITY_A_MACHINE_CONTRACT.json",
        "contract_id": "VEDA-MUH-T2-CONTRACT-HOUSE_CONSTRUCTION_COMMENCEMENT-V1",
        "contract_hash": "9939643F8BA87AC13CFD31EA2C4295D0844FE67684E881DB05C1384234C7E12C",
        "machine_hash": "EBAA6885C9761697714A09366848045BF69C6E67D7B1855352D47151CEC01E9F",
    },
    "HOUSE_ENTRY_OR_GRIHA_PRAVESHA": {
        "contract_file": "09_SELECTED_ACTIVITY_B_RULE_CONTRACT.json",
        "machine_file": "10_SELECTED_ACTIVITY_B_MACHINE_CONTRACT.json",
        "contract_id": "VEDA-MUH-T2-CONTRACT-HOUSE_ENTRY_OR_GRIHA_PRAVESHA-V1",
        "contract_hash": "B466C139E179D3ABCB55FD0D9D19F602159755C366E1272CEA8030EACEEB019C",
        "machine_hash": "2AD390E55210E593984BE601EFF928F92B039CD01EF6014A43F516FF570D9A3D",
    },
}

RASHIS = [
    {"id": index, "name": name}
    for index, name in enumerate(
        ("Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya", "Tula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena")
    )
]


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest().upper()


def load_json(name: str) -> Any:
    return json.loads((T2_ROOT / name).read_text(encoding="utf-8"))


def t2_reconciliation() -> dict[str, Any]:
    rows = {}
    for activity, binding in T2_CONTRACTS.items():
        contract = load_json(binding["contract_file"])
        machine = load_json(binding["machine_file"])
        rows[activity] = {
            "contract_id": contract["contract_id"],
            "version": contract["version"],
            "contract_hash": contract["contract_hash"],
            "machine_hash": machine["machine_hash"],
            "expected_contract_hash": binding["contract_hash"],
            "expected_machine_hash": binding["machine_hash"],
            "contract_hash_match": contract["contract_hash"] == binding["contract_hash"],
            "machine_hash_match": machine["machine_hash"] == binding["machine_hash"],
            "machine_state_before": machine["machine_state"],
            "production_activation_before": machine["production_activation"],
            "historical_artifact_mutated": False,
        }
    return {
        "programme": PROGRAMME,
        "predecessor": "VEDA-MUHURTA-ACTIVITY-EXPANSION-T2-001",
        "rows": rows,
        "all_hashes_match": all(row["contract_hash_match"] and row["machine_hash_match"] for row in rows.values()),
        "supersession_created": False,
    }


def lagna_calculation_audit() -> dict[str, Any]:
    return {
        "calculation_location": "engines/intelligence/kundli_engine.py::KundliEngine._ascendant",
        "source_calculation": "Swiss Ephemeris swe.houses(jd, latitude, longitude, b'W') followed by explicit SIDM_LAHIRI ayanamsha subtraction",
        "inputs": ["UTC-derived Julian day", "latitude", "longitude", "numeric timezone offset"],
        "output": "sidereal Ascendant longitude in degrees",
        "downstream_sign_binding": "int(sidereal_ascendant / 30) using the canonical Kundli SIGNS order",
        "downstream_house_binding": "whole-sign house assignment from Lagna sign index",
        "maturity": "COMPLETE_WITH_CONDITION",
        "validation_state": "VALIDATED_WITH_CONDITIONS",
        "evidence": [
            "VEDA-P004 Lagna/Bhava validation",
            "VEDA-CALC-SIDEREAL-ASC-TZ-001 bounded 120-case Ascendant corpus",
        ],
        "conditions": [
            "Runtime W-plus-ayanamsha path is retained; silent migration to houses_ex is prohibited.",
            "A known near-boundary derivation difference can flip the Rashi sign.",
            "Historical/DST/timezone edge cases remain condition-bearing.",
            "This is calculation validation, not electional source validation.",
        ],
        "new_calculation_created": False,
    }


def lagna_factor_contract() -> dict[str, Any]:
    return {
        "factor_id": "MUHURTA_LAGNA_SIGN",
        "contract_version": "1.0.0-diagnostic",
        "production_bound": False,
        "source_calculation": "KUNDLI_SWISSEPH_W_MINUS_LAHIRI_V1",
        "calculation_location": "engines/intelligence/kundli_engine.py::KundliEngine._ascendant",
        "inputs": ["local date/time", "timezone conversion", "latitude", "longitude"],
        "output_type": "CANONICAL_RASHI_ENUM",
        "canonical_enum": RASHIS,
        "uncertainty": "AVAILABLE_WITH_CONDITION",
        "boundary_policy": {
            "classification": "BOUNDARY_POLICY_REQUIRED",
            "hard_rule_policy": "ABSTAIN_IF_GOVERNING_RUNTIME_AND_REFERENCE_SIGN_DIFFER",
            "exact_boundary": "Half-open sign intervals; 360 degrees wraps to zero",
            "false_precision": "Do not infer an electional sign from rounded display degree alone.",
        },
        "validation_state": "INTERNAL_CALCULATION_VALIDATED_WITH_CONDITIONS",
        "source_semantics_state": "SOURCE_PARTIAL",
        "promotion_state": "DIAGNOSTIC_ONLY",
        "new_calculation_created": False,
    }


def lagna_source_semantics() -> dict[str, Any]:
    return {
        "factor_id": "MUHURTA_LAGNA_SIGN",
        "source_assertions": [
            {
                "assertion_id": "VEDA-SWW-ASSERTION-BS-HOUSE-COMMENCEMENT-001",
                "work": "Brihat Samhita",
                "passages": ["Chapter 53, verses 98-112", "Chapter 98, verse 18 witness retained by predecessor"],
                "authority": "CLASSICAL_PRIMARY_SCOPED",
                "supported_scope": "House-ground preparation, construction commencement, foundation and house-entry-related action context; the consulted translation links stable Lagna context with house work.",
                "exact_sign_set": "NOT_VERIFIED",
                "planetary_predicate_set": "NOT_VERIFIED",
                "decision": "SOURCE_PARTIAL",
            },
            {
                "assertion_id": "VEDA-REF-PRACTITIONER-RAMAN-HOUSEBUILDING-001",
                "work": "B. V. Raman, Muhurtha, chapter XII Housebuilding",
                "passages": ["web edition lines 1030-1052", "PDF edition pp. 51-52"],
                "authority": "PRACTITIONER_REFERENCE_ONLY",
                "supported_scope": "Provides explicit fixed-rising-sign and several planet-in-house combinations for house foundation/entry contexts.",
                "exact_sign_set": "PRACTITIONER_STATED_FIXED_SIGNS",
                "planetary_predicate_set": "PRACTITIONER_STATED_COMBINATIONS",
                "decision": "REFERENCE_ONLY_NOT_MACHINE_AUTHORITY",
            },
        ],
        "translation_uncertainty": True,
        "machine_semantics_decision": "SOURCE_PARTIAL",
        "reason": "A reusable Lagna calculation exists, but the selected primary witness does not establish a complete canonical sign predicate and the detailed planetary combinations located are practitioner-level rather than independently verified primary semantics.",
    }


def planetary_dependencies() -> dict[str, Any]:
    practitioner_rules = [
        {"id": "RAMAN-HOUSE-001", "frame": "HOUSE_FROM_ELECTIONAL_LAGNA", "condition": "Moon 10th; Jupiter 4th; Mars and Saturn 11th"},
        {"id": "RAMAN-HOUSE-002", "frame": "HOUSE_FROM_ELECTIONAL_LAGNA", "condition": "Jupiter Lagna; Mercury 7th; Saturn 3rd; Sun 6th; Venus 4th"},
        {"id": "RAMAN-HOUSE-003", "frame": "HOUSE_FROM_ELECTIONAL_LAGNA", "condition": "Venus Lagna; Mercury 10th; Jupiter in a Kendra; Sun 11th"},
        {"id": "RAMAN-HOUSE-004", "frame": "HOUSE_FROM_ELECTIONAL_LAGNA", "condition": "Moon Lagna; Jupiter 7th; Mercury 10th"},
        {"id": "RAMAN-HOUSE-005", "frame": "HOUSE_FROM_ELECTIONAL_LAGNA", "condition": "Venus 10th; Jupiter 7th; Mercury Lagna; fixed Lagna"},
        {"id": "RAMAN-HOUSE-006", "frame": "HOUSE_FROM_ELECTIONAL_LAGNA", "condition": "Jupiter fixed Lagna; Mercury 7th; Moon 10th"},
    ]
    return {
        "source_rule_inventory": practitioner_rules,
        "planets": ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"],
        "reference_frames": ["HOUSE_FROM_ELECTIONAL_LAGNA", "SIGN_FROM_CANONICAL_RASHI"],
        "existing_calculations_reused": {
            "planet_longitudes": "engines/intelligence/kundli_engine.py::_planet_positions; Swiss Ephemeris, sidereal Lahiri, governed MOSEPH flags",
            "rashi": "canonical sign index from sidereal longitude",
            "whole_sign_houses": "existing downstream formula from Lagna sign",
        },
        "dependency_states": {
            "planet_longitude": "AVAILABLE_WITH_CONDITION",
            "rashi": "AVAILABLE_WITH_CONDITION",
            "whole_sign_house_from_lagna": "AVAILABLE_WITH_CONDITION",
            "lordship": "AVAILABLE_BUT_NOT_GOVERNED_FOR_MUHURTA",
            "dignity": "AVAILABLE_BUT_NOT_GOVERNED_FOR_MUHURTA",
            "aspect": "AVAILABLE_BUT_NOT_GOVERNED_FOR_MUHURTA",
            "benefic_malefic_classification": "SOURCE_SEMANTICS_UNRESOLVED",
        },
        "machine_state": "PLANETARY_DEPENDENCY_PARTIAL",
        "blocking_reason": "The detailed planetary combinations are only practitioner-reference evidence; no primary, lineage-complete normalized predicate contract was verified for production Muhurta binding.",
        "unsupported_assumptions_rejected": ["generic planetary strength", "universal benefic/malefic list", "unqualified dignity", "unqualified aspect system", "numeric planetary score"],
    }


def context_schema() -> dict[str, Any]:
    return {
        "activity": "HOUSE_ENTRY_OR_GRIHA_PRAVESHA",
        "source_context": {
            "construction_state": {
                "status": "REQUIRED",
                "type": "ENUM",
                "allowed": ["HALF_BUILT", "WHOLLY_BUILT"],
                "source_basis": "Brihat Samhita Ch53.105 witness describes entry into a half-built or wholly built house.",
            },
            "puja_completed": {
                "status": "REQUIRED",
                "type": "BOOLEAN",
                "source_basis": "Brihat Samhita Ch53.125 places house entry after puja in the consulted translation.",
            },
            "first_occupancy": {
                "status": "SOURCE_VARIANT",
                "type": "BOOLEAN_OR_UNKNOWN",
                "source_basis": "The inspected primary passage does not clearly establish modern first-residence semantics.",
            },
        },
        "practical_context": {
            "habitable": {"status": "OPTIONAL", "type": "BOOLEAN", "effect": "DISCLOSE_ONLY"},
            "legal_possession": {"status": "OPTIONAL", "type": "BOOLEAN", "effect": "PRACTICAL_CAUTION_ONLY"},
        },
        "missing_required_policy": "ABSTAIN",
        "invalid_or_unknown_policy": "FAIL_CLOSED",
        "oversized_questionnaire": False,
        "machine_state": "CONTEXT_DEPENDENCY_PARTIAL",
        "reason": "Construction-stage and post-puja context can be represented declaratively, but first-occupancy semantics are not source-complete and no production request field exists.",
    }


def machine_contract(activity: str) -> dict[str, Any]:
    context_required = activity == "HOUSE_ENTRY_OR_GRIHA_PRAVESHA"
    return {
        "activity_id": activity,
        "contract_id": T2_CONTRACTS[activity]["contract_id"],
        "supersedes": None,
        "candidate_version": None,
        "machine_state": "MACHINE_PARTIAL",
        "production_activation": False,
        "declarative_predicates": [
            {"factor_id": "MUHURTA_LAGNA_SIGN", "operator": "IN", "expected_set": "UNRESOLVED_SOURCE_SIGN_SET", "state": "NOT_BOUND", "missing_value_policy": "ABSTAIN", "effect": "BLOCKING"},
            {"factor_id": "MUHURTA_PLANETARY_ELECTION_CONTEXT", "operator": "ALL_OF", "expected_set": "UNRESOLVED_PRIMARY_SOURCE_PREDICATES", "state": "NOT_BOUND", "missing_value_policy": "ABSTAIN", "effect": "BLOCKING"},
            *([{"factor_id": "GRIHA_PRAVESHA_CONTEXT", "operator": "ALL_OF", "expected_set": ["construction_state", "puja_completed"], "state": "SCHEMA_ONLY", "missing_value_policy": "ABSTAIN", "effect": "BLOCKING"}] if context_required else []),
        ],
        "source_assertion_ids": ["VEDA-SWW-ASSERTION-BS-HOUSE-COMMENCEMENT-001" if activity == "HOUSE_CONSTRUCTION_COMMENCEMENT" else "VEDA-SWW-ASSERTION-BS-HOUSE-ENTRY-001"],
        "no_runtime_registration": True,
        "no_numeric_score": True,
        "blocking_gaps": [
            "SOURCE_PRIMARY_LAGNA_SIGN_PREDICATE_UNRESOLVED",
            "SOURCE_PRIMARY_PLANETARY_CONTEXT_UNRESOLVED",
            *(["EXPLICIT_GRIHA_PRAVESHA_CONTEXT_NOT_IN_PRODUCTION_REQUEST"] if context_required else []),
        ],
        "nonblocking_gaps": ["Activity-specific Tithi/Karana composition remains partial.", "Tradition and translation variants remain disclosed."],
    }


def synthetic_validation() -> dict[str, Any]:
    rows = []
    for activity in T2_CONTRACTS:
        for sign in RASHIS:
            rows.append({"activity": activity, "case": f"lagna_sign_{sign['id']}", "factors": {"MUHURTA_LAGNA_SIGN": sign["id"]}, "expected": "ABSTAIN_SOURCE_SEMANTICS_UNRESOLVED", "production": False})
        for case, factors in (
            ("missing_lagna", {}),
            ("missing_planetary_context", {"MUHURTA_LAGNA_SIGN": 1}),
            ("boundary_ambiguous", {"MUHURTA_LAGNA_SIGN": 1, "LAGNA_BOUNDARY_STATUS": "AMBIGUOUS"}),
            ("scope_mismatch", {"activity_scope": "PROPERTY_PURCHASE_OR_REGISTRATION"}),
            ("missing_entry_context", {"MUHURTA_LAGNA_SIGN": 1, "MUHURTA_PLANETARY_ELECTION_CONTEXT": {}}),
        ):
            rows.append({"activity": activity, "case": case, "factors": factors, "expected": "ABSTAIN", "production": False})
    return {"case_count": len(rows), "lagna_sign_cases_per_activity": 12, "rows": rows, "all_nonproduction": all(row["production"] is False for row in rows)}


def window_readiness() -> dict[str, Any]:
    return {
        "HOUSE_CONSTRUCTION_COMMENCEMENT": {"single_candidate": "NOT_READY", "window_search": "WINDOW_SEARCH_TRANSITION_PARTIAL"},
        "HOUSE_ENTRY_OR_GRIHA_PRAVESHA": {"single_candidate": "NOT_READY", "window_search": "WINDOW_SEARCH_TRANSITION_PARTIAL"},
        "lagna_transition_support": "NOT_AVAILABLE_AS_GOVERNED_TRANSITION_BOUNDARY",
        "planetary_transition_support": "NOT_AVAILABLE_FOR_DECISION_RELEVANT_PREDICATES",
        "existing_p032_transitions": "AVAILABLE_ONLY_FOR_P032_FACT_SEGMENTS",
        "fixed_sampling_introduced": False,
    }


def build_bundle() -> dict[str, Any]:
    reconciliation = t2_reconciliation()
    assert reconciliation["all_hashes_match"]
    return {
        "baseline": {"programme": PROGRAMME, "starting_commit": STARTING_COMMIT, "production_activation": False, "approved_core_before": 17, "approved_core_after": 17},
        "t2_reconciliation": reconciliation,
        "lagna_calculation": lagna_calculation_audit(),
        "lagna_factor": lagna_factor_contract(),
        "lagna_source_semantics": lagna_source_semantics(),
        "planetary_dependencies": planetary_dependencies(),
        "context_schema": context_schema(),
        "machine_contracts": {activity: machine_contract(activity) for activity in T2_CONTRACTS},
        "contract_supersession": {"superseded": False, "new_versions": [], "reason": "No machine-ready immutable V2 is justified while primary source semantics and context scope remain unresolved."},
        "synthetic_validation": synthetic_validation(),
        "window_readiness": window_readiness(),
        "handoff": {"generated": False, "machine_ready_activities": [], "production_activation": False, "reason": "Both activities remain blocked by source semantics; Griha Pravesha also has unresolved modern occupancy scope."},
    }


def write_bundle(bundle: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    files = {
        "01_T2_DEPENDENCY_INVENTORY.json": bundle["t2_reconciliation"],
        "03_LAGNA_FACTOR_CONTRACT.json": bundle["lagna_factor"],
        "04_LAGNA_SOURCE_SEMANTICS.json": bundle["lagna_source_semantics"],
        "05_PLANETARY_ELECTION_DEPENDENCIES.json": bundle["planetary_dependencies"],
        "06_PLANETARY_CALCULATION_READINESS.json": bundle["planetary_dependencies"]["dependency_states"],
        "07_PLANETARY_SOURCE_SEMANTICS.json": bundle["lagna_source_semantics"]["source_assertions"],
        "09_GRIHA_PRAVESHA_CONTEXT_SCHEMA.json": bundle["context_schema"],
        "10_HOUSE_CONSTRUCTION_MACHINE_CONTRACT.json": bundle["machine_contracts"]["HOUSE_CONSTRUCTION_COMMENCEMENT"],
        "11_GRIHA_PRAVESHA_MACHINE_CONTRACT.json": bundle["machine_contracts"]["HOUSE_ENTRY_OR_GRIHA_PRAVESHA"],
        "12_CONTRACT_SUPERSESSION.json": bundle["contract_supersession"],
        "13_SYNTHETIC_VALIDATION.json": bundle["synthetic_validation"],
        "14_WINDOW_TRANSITION_READINESS.json": bundle["window_readiness"],
        "15_ENGINE_HANDOFF_T2_RX.json": bundle["handoff"],
    }
    for name, payload in files.items():
        (OUT / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    bundle = build_bundle()
    write_bundle(bundle)
    print(json.dumps({"programme": PROGRAMME, "decision": "MUHURTA_HOUSE_ELECTIONAL_FACTORS_MACHINE_PARTIAL", "machine_ready": [], "synthetic_cases": bundle["synthetic_validation"]["case_count"]}, sort_keys=True))
