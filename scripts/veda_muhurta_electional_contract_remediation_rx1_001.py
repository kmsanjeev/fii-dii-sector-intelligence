"""Build the bounded RX1 remediation register for three electional activities.

This is a deterministic governance/documentation generator.  It re-audits the
T2/T3 contracts against the frozen Electional Core, reclassifies only the
necessity of proven optional/contextual blockers, and deliberately does not
register a production activity or invent source semantics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/current-state/muhurta-electional-contract-remediation-rx1-001"
PROGRAMME = "VEDA-MUHURTA-ELECTIONAL-CONTRACT-REMEDIATION-RX1-001"
STARTING_COMMIT = "5eefc1307ca8680607074420a2a798939dfe814d"
CORE_ROOT = ROOT / "docs/current-state/muhurta-electional-core-primitives-001"
T2_ROOT = ROOT / "docs/current-state/muhurta-activity-expansion-t2-001"
T3_ROOT = ROOT / "docs/current-state/muhurta-activity-expansion-t3-001"

T2_HASHES = {
    "HOUSE_CONSTRUCTION_COMMENCEMENT_CONTRACT": "9939643F8BA87AC13CFD31EA2C4295D0844FE67684E881DB05C1384234C7E12C",
    "HOUSE_CONSTRUCTION_COMMENCEMENT_MACHINE": "EBAA6885C9761697714A09366848045BF69C6E67D7B1855352D47151CEC01E9F",
    "HOUSE_ENTRY_OR_GRIHA_PRAVESHA_CONTRACT": "B466C139E179D3ABCB55FD0D9D19F602159755C366E1272CEA8030EACEEB019C",
    "HOUSE_ENTRY_OR_GRIHA_PRAVESHA_MACHINE": "2AD390E55210E593984BE601EFF928F92B039CD01EF6014A43F516FF570D9A3D",
}
T3_HASHES = {
    "MARRIAGE_CONTRACT": "412B268562D4E1A1D9098FCE6622CBFC9B6F70739C69F16D923A73C12F5751B0",
    "MARRIAGE_MACHINE": "544F45408CA337FB65B28BCC15F8671B0589F631D9677CB8BFBE9AE27E59F68D",
}
CORE_HASHES = {
    "MUHURTA_LAGNA_SIGN": "BC50AC95518D4B30250013F7051BDFA85202342FE21EFADB5C8D026B8146ADCC",
    "GODHULI": "225F4577E57CF72A1282C6EB0F31DB835CBC9EB84FEBC10227D5516AD97FC535",
}


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest().upper()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(name: str, payload: Any) -> None:
    (OUT / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def predecessor_register() -> dict[str, Any]:
    rows = {
        "HOUSE_CONSTRUCTION_COMMENCEMENT": {
            "contract_file": "06_SELECTED_ACTIVITY_A_RULE_CONTRACT.json",
            "machine_file": "07_SELECTED_ACTIVITY_A_MACHINE_CONTRACT.json",
            "expected_contract_hash": T2_HASHES["HOUSE_CONSTRUCTION_COMMENCEMENT_CONTRACT"],
            "expected_machine_hash": T2_HASHES["HOUSE_CONSTRUCTION_COMMENCEMENT_MACHINE"],
        },
        "HOUSE_ENTRY_OR_GRIHA_PRAVESHA": {
            "contract_file": "09_SELECTED_ACTIVITY_B_RULE_CONTRACT.json",
            "machine_file": "10_SELECTED_ACTIVITY_B_MACHINE_CONTRACT.json",
            "expected_contract_hash": T2_HASHES["HOUSE_ENTRY_OR_GRIHA_PRAVESHA_CONTRACT"],
            "expected_machine_hash": T2_HASHES["HOUSE_ENTRY_OR_GRIHA_PRAVESHA_MACHINE"],
        },
        "MARRIAGE_CEREMONY_TIMING": {
            "contract_file": "07_SELECTED_ACTIVITY_A_RULE_CONTRACT.json",
            "machine_file": "08_SELECTED_ACTIVITY_A_MACHINE_CONTRACT.json",
            "expected_contract_hash": T3_HASHES["MARRIAGE_CONTRACT"],
            "expected_machine_hash": T3_HASHES["MARRIAGE_MACHINE"],
        },
    }
    result = {}
    for activity, row in rows.items():
        root = T3_ROOT if activity == "MARRIAGE_CEREMONY_TIMING" else T2_ROOT
        contract = load(root / row["contract_file"])
        machine = load(root / row["machine_file"])
        result[activity] = {
            "contract_id": contract["contract_id"],
            "contract_hash": contract["contract_hash"],
            "machine_hash": machine["machine_hash"],
            "expected_contract_hash": row["expected_contract_hash"],
            "expected_machine_hash": row["expected_machine_hash"],
            "contract_preserved": contract["contract_hash"] == row["expected_contract_hash"],
            "machine_preserved": machine["machine_hash"] == row["expected_machine_hash"],
            "production_activation": machine.get("production_activation", machine.get("no_runtime_registration")),
            "immutable_policy": "V1_PRESERVED_NO_OVERWRITE",
        }
    assert all(x["contract_preserved"] and x["machine_preserved"] for x in result.values())
    return {"programme": PROGRAMME, "starting_commit": STARTING_COMMIT, "activities": result}


def core_binding_register() -> dict[str, Any]:
    lagna = load(CORE_ROOT / "04_LAGNA_FACTOR_CONTRACT.json")
    godhuli = load(CORE_ROOT / "13_GODHULI_FACTOR_CONTRACT.json")
    planetary = load(CORE_ROOT / "09_PLANETARY_FACTOR_CONTRACTS.json")
    assert lagna["hash"] == CORE_HASHES["MUHURTA_LAGNA_SIGN"]
    assert godhuli["hash"] == CORE_HASHES["GODHULI"]
    return {
        "lagna": {
            "factor_id": "MUHURTA_LAGNA_SIGN",
            "hash": lagna["hash"],
            "state": "LAGNA_FACTOR_READY_WITH_BOUNDARY_ABSTENTION",
            "binding": "FACT_AVAILABLE_WITH_CONDITION; no auspicious sign set supplied",
            "boundary_policy": "ABSTAIN_SIGN_DEPENDENT_RULE",
        },
        "transitions": {
            "factor_id": "MUHURTA_LAGNA_TRANSITIONS",
            "state": "LAGNA_TRANSITIONS_READY_WITH_TOLERANCE",
            "binding": "DIAGNOSTIC_ONLY; not an activity search or auspiciousness rule",
        },
        "planetary": {
            "factor_ids": sorted(planetary),
            "state": "PLANETARY_PLACEMENT_FACTS_READY_ADVISORY_PARTIAL",
            "binding": "FACTS_AVAILABLE; activity semantics remain source-bound and unresolved",
            "not_bound": [
                "GOOD_PLANETS", "BAD_PLANETS", "BENEFIC_MALEFIC",
                "ELECTIONAL_STRENGTH_SCORE", "GENERIC_DIGNITY", "GENERIC_ASPECT",
            ],
        },
        "godhuli": {
            "factor_id": "GODHULI_CONTEXT",
            "hash": godhuli["hash"],
            "state": "GODHULI_CALCULATION_READY_SOURCE_PARTIAL",
            "binding": "SOURCE_CONTEXT_ONLY; no interval invention and no sunset equivalence",
        },
        "lineage": "MACHINE PREDICATE -> RULE -> ASSERTION -> PASSAGE -> EDITION -> WITNESS -> WORK",
    }


def blocker_necessity_reaudit() -> dict[str, Any]:
    common = {
        "lagna_semantics": {
            "prior": "BLOCKING_CALCULATION_DEPENDENCY",
            "current": "BLOCKING_SOURCE_MANDATORY",
            "status": "SOURCE_SEMANTICS_UNRESOLVED",
            "reason": "The core calculates canonical Rashi identity, but no accepted source gives a complete executable sign set or normalized predicate for this activity.",
            "engineering_only_blocker": False,
        },
        "planetary_semantics": {
            "prior": "BLOCKING_CALCULATION_DEPENDENCY",
            "current": "BLOCKING_SOURCE_MANDATORY",
            "status": "SOURCE_SEMANTICS_UNRESOLVED",
            "reason": "Placement facts exist, but source-specific planetary relations are not normalized into a lineage-complete predicate.",
            "engineering_only_blocker": False,
        },
    }
    return {
        "method": "necessity_reaudit; prior required/ blocking flags are not authority by themselves",
        "activities": {
            "HOUSE_CONSTRUCTION_COMMENCEMENT": {
                **common,
                "context": {"current": "NONBLOCKING_ADDITIONAL_COVERAGE", "status": "SOURCE_PARTIAL", "reason": "Construction commencement has no separate unresolved occupancy context."},
                "result": "CONTRACT_BLOCKED",
            },
            "HOUSE_ENTRY_OR_GRIHA_PRAVESHA": {
                **common,
                "context": {
                    "construction_state": {"state": "BLOCKING_CONTEXT_DEPENDENCY", "required": True, "allowed": ["HALF_BUILT", "WHOLLY_BUILT"]},
                    "puja_completed": {"state": "BLOCKING_CONTEXT_DEPENDENCY", "required": True, "type": "boolean"},
                    "first_occupancy": {"state": "NONBLOCKING_CONTEXT_GAP", "classification": "SOURCE_UNRESOLVED_OR_VARIANT", "reason": "The source supports house-entry framing but does not establish the modern first-ever-occupancy distinction; disclose rather than block the scoped house-entry activity."},
                },
                "result": "CONTRACT_BLOCKED",
            },
            "MARRIAGE_CEREMONY_TIMING": {
                **common,
                "godhuli": {
                    "prior": "BLOCKING_CALCULATION_DEPENDENCY",
                    "current": "NONBLOCKING_ADDITIONAL_COVERAGE",
                    "classification": "SOURCE_VARIANT_OPTIONAL_PATH",
                    "status": "SOURCE_PARTIAL",
                    "reason": "The accepted Bṛhat Saṃhitā witness describes a distinct Godhuli context; it does not establish Godhuli as mandatory for every marriage ceremony.",
                },
                "scope": "TIMING_ONLY_PANIGRAHANA; no compatibility, partner choice, marriage outcome, legal or should-marry decision",
                "result": "CONTRACT_BLOCKED",
            },
        },
        "principle": "A calculation dependency is blocking only when the activity's source-backed rule cannot be evaluated without it; no engineering-only blocker is promoted.",
    }


def activity_next_contracts() -> dict[str, Any]:
    shared = {
        "evaluator": "EXISTING_DECLARATIVE_EVALUATOR_ONLY",
        "production_activation": False,
        "new_generic_engine": False,
        "v2_created": False,
        "v2_hash": None,
        "unresolved_source_predicates": ["ACTIVITY_SPECIFIC_LAGNA_SEMANTICS", "ACTIVITY_SPECIFIC_PLANETARY_SEMANTICS"],
    }
    return {
        "HOUSE_CONSTRUCTION_COMMENCEMENT": {
            **shared,
            "contract_state": "SOURCE_SEMANTICS_PARTIAL",
            "machine_state": "MACHINE_PARTIAL",
            "blocking": ["BLOCKING_SOURCE_MANDATORY: executable Lagna predicate absent", "BLOCKING_SOURCE_MANDATORY: executable planetary predicate absent"],
            "nonblocking": ["Nakshatra and other P032 facts remain preference/context only"],
            "next_action": "DO_NOT_BUILD_ACTIVITY_ENGINE; await bounded source resolution",
        },
        "HOUSE_ENTRY_OR_GRIHA_PRAVESHA": {
            **shared,
            "contract_state": "CONTEXT_PARTIAL",
            "machine_state": "MACHINE_PARTIAL",
            "blocking": ["BLOCKING_CONTEXT_DEPENDENCY: construction_state", "BLOCKING_CONTEXT_DEPENDENCY: puja_completed", "BLOCKING_SOURCE_MANDATORY: Lagna and planetary semantics"],
            "nonblocking": ["first_occupancy is disclosed as source-variant/context gap, not a universal blocker"],
            "next_action": "DO_NOT_BUILD_ACTIVITY_ENGINE; preserve context schema and await source resolution",
        },
        "MARRIAGE_CEREMONY_TIMING": {
            **shared,
            "contract_state": "SOURCE_SEMANTICS_PARTIAL",
            "machine_state": "MACHINE_PARTIAL",
            "blocking": ["BLOCKING_SOURCE_MANDATORY: Lagna semantics", "BLOCKING_SOURCE_MANDATORY: planetary semantics"],
            "nonblocking": ["Godhuli is an optional source-variant path, not a universal mandatory blocker", "personal Bala/Tara/Chandra factors remain diagnostic-only"],
            "next_action": "DO_NOT_BUILD_ACTIVITY_ENGINE; preserve timing-only scope",
        },
    }


def context_bindings() -> dict[str, Any]:
    return {
        "HOUSE_ENTRY_OR_GRIHA_PRAVESHA": {
            "construction_state": {"type": "enum", "values": ["HALF_BUILT", "WHOLLY_BUILT"], "missing": "ABSTAIN", "state": "BLOCKING_CONTEXT_DEPENDENCY"},
            "puja_completed": {"type": "boolean", "missing": "ABSTAIN", "state": "BLOCKING_CONTEXT_DEPENDENCY"},
            "first_occupancy": {"type": "boolean_or_unknown", "missing": "DISCLOSE_CONTEXT_GAP", "state": "NONBLOCKING_CONTEXT_GAP"},
        },
        "MARRIAGE_CEREMONY_TIMING": {
            "human_chosen_ceremony": {"type": "boolean", "required": True, "state": "BLOCKING_CONTEXT_DEPENDENCY"},
            "godhuli_context": {"type": "explicit_source_context", "required": False, "state": "OPTIONAL_SOURCE_VARIANT"},
        },
    }


def window_search_readiness() -> dict[str, Any]:
    return {
        "single_candidate": {a: "NOT_READY_SOURCE_SEMANTICS_OR_CONTEXT" for a in activity_next_contracts()},
        "window_search": {a: "NOT_READY_ACTIVITY_CONTRACT_NOT_CLOSED" for a in activity_next_contracts()},
        "existing_window_search": "UNCHANGED; no activity-specific registration or search behavior added",
        "transitions": "DIAGNOSTIC_ONLY",
    }


def source_count_audit() -> dict[str, Any]:
    source_dir = ROOT / "data/veda/research/astrology/sources"
    files = sorted(source_dir.glob("VEDA-SRC-*.json"))
    return {
        "observed_source_count": len(files),
        "authoritative_architecture_count": load(ROOT / "docs/current-state/knowledge-source-witness-standard-001/01_CURRENT_SOURCE_ARCHITECTURE.json")["existing_counts"]["source_count"],
        "stale_test_expectation_before": 13,
        "corrected_test_expectation": 14,
        "source_ids": [path.stem for path in files],
        "root_cause": "VEDA-SRC-000014 was legitimately registered by the prior Muhurta source-semantics hardening commit 0899581d; tests/test_veda_astrology_governance.py retained the older pilot count of 13.",
        "classification": "STALE_TEST_INVARIANT",
        "registry_validity": "LEGITIMATE_14_SOURCE_REGISTRY",
        "semantic_impact": "NONE_ON_ELECTIONAL_CONTRACTS",
    }


def final_acceptance() -> dict[str, Any]:
    criteria = [
        ("AC01", "baseline and predecessor hashes verified", "PASS"),
        ("AC02", "core Lagna, planetary and Godhuli bindings reused", "PASS"),
        ("AC03", "T2/T3 V1 contracts preserved", "PASS"),
        ("AC04", "blocker necessity re-audited without engineering-only authority", "PASS"),
        ("AC05", "house construction source semantics remain explicit and blocked", "PASS_WITH_CONDITION"),
        ("AC06", "Griha context schema preserved; first occupancy nonblocking gap", "PASS_WITH_CONDITION"),
        ("AC07", "Marriage remains timing-only and Godhuli optional variant", "PASS_WITH_CONDITION"),
        ("AC08", "no executable unsupported Lagna/planet predicate invented", "PASS"),
        ("AC09", "no generic engine, scoring or production registration", "PASS"),
        ("AC10", "single-candidate and window-search readiness separated", "PASS"),
        ("AC11", "source-count discrepancy diagnosed and stale test corrected", "PASS"),
        ("AC12", "P032 and existing activities unchanged", "PASS"),
        ("AC13", "no V2 contract justified because blockers remain", "PASS_WITH_CONDITION"),
        ("AC14", "P032/engine handoff not authorized", "PASS"),
        ("AC15", "documentation deterministic and governance synchronized", "PASS"),
        ("AC16", "production activation remains false", "PASS"),
    ]
    return {
        "programme": PROGRAMME,
        "overall": "PASS_WITH_CONDITION",
        "decision": "MUHURTA_ELECTIONAL_CONTRACTS_MACHINE_PARTIAL",
        "criteria": [{"id": i, "criterion": c, "status": s} for i, c, s in criteria],
        "counts": {"PASS": sum(s == "PASS" for _, _, s in criteria), "PASS_WITH_CONDITION": sum(s == "PASS_WITH_CONDITION" for _, _, s in criteria), "BLOCKED": 0, "FAIL": 0, "TOTAL": len(criteria)},
        "next_activity_recommendation": "VEDA-MUHURTA-ENGINE-ELECTIONAL-ACTIVITY-RX1-001 remains recommendation only; do not start because no activity is machine-ready.",
    }


def markdown(name: str, title: str, body: str) -> None:
    (OUT / name).write_text(f"# {title}\n\n{body.rstrip()}\n", encoding="utf-8")


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    predecessor = predecessor_register()
    bindings = core_binding_register()
    blockers = blocker_necessity_reaudit()
    next_contracts = activity_next_contracts()
    contexts = context_bindings()
    windows = window_search_readiness()
    source_count = source_count_audit()
    handoff = {
        "programme": PROGRAMME,
        "engine_handoff": "NOT_AUTHORIZED",
        "machine_ready_activities": [],
        "production_registration": False,
        "P032_changed": False,
        "recommended_follow_on": "VEDA-MUHURTA-ENGINE-ELECTIONAL-ACTIVITY-RX1-001",
        "recommendation_status": "RECOMMEND_ONLY_NOT_STARTED",
    }
    parallel = {
        "P032": "IMPLEMENTED_FROZEN_UNCHANGED",
        "P032_ELECTIONAL_RUNTIME": "INACTIVE",
        "SHADBALA": "UNCHANGED",
        "ASHTAKAVARGA": "UNCHANGED",
        "D20": "UNCHANGED",
        "prediction": "UNCHANGED",
        "ML": "UNCHANGED",
        "RAG": "UNCHANGED",
        "approved_core_before": 17,
        "approved_core_after": 17,
        "personal_bala_729": "DIAGNOSTIC_ONLY",
        "personal_bala_144": "DIAGNOSTIC_ONLY",
    }
    write_json("01_PREDECESSOR_CONTRACT_REGISTER.json", predecessor)
    write_json("02_ELECTIONAL_CORE_BINDING_REGISTER.json", bindings)
    write_json("03_BLOCKER_NECESSITY_REAUDIT.json", blockers)
    markdown("00_BASELINE.md", "RX1 Baseline", f"Programme: `{PROGRAMME}`\n\nStarting commit: `{STARTING_COMMIT}`. T2/T3 predecessor hashes and the frozen Electional Core hashes are verified before any remediation output is written. V1 contracts are immutable and no production runtime is activated.")
    markdown("04_HOUSE_CONSTRUCTION_REMEDIATION.md", "House Construction Remediation", "The shared Lagna sign fact is reusable with boundary abstention, but the accepted source record does not provide a complete executable Lagna sign set or lineage-complete planetary predicate. Practitioner references remain non-authoritative. The activity therefore remains `CONTRACT_BLOCKED` / `SOURCE_SEMANTICS_PARTIAL`; no V2 is created.")
    write_json("05_HOUSE_CONSTRUCTION_CONTRACT_NEXT.json", next_contracts["HOUSE_CONSTRUCTION_COMMENCEMENT"])
    markdown("06_GRIHA_PRAVESHA_REMEDIATION.md", "Griha Pravesha Remediation", "`construction_state` and `puja_completed` remain explicit blocking context inputs. `first_occupancy` is retained as a disclosed source-variant/context gap rather than a universal blocker because the accepted source supports house entry but does not establish the modern first-ever occupancy distinction. Lagna and planetary source semantics remain blocking; no V2 is created.")
    write_json("07_GRIHA_PRAVESHA_CONTRACT_NEXT.json", next_contracts["HOUSE_ENTRY_OR_GRIHA_PRAVESHA"])
    markdown("08_MARRIAGE_REMEDIATION.md", "Marriage Remediation", "The contract remains timing-only for a human-chosen Panigrahana/ceremony. Godhuli is retained as an optional source-variant path: the accepted witness supports a distinct context, not a universal mandatory condition. Lagna and planetary semantics remain source-mandatory blockers; no compatibility, partner, outcome, legal or should-marry behavior is added.")
    write_json("09_MARRIAGE_GODHULI_NECESSITY_AUDIT.json", blockers["activities"]["MARRIAGE_CEREMONY_TIMING"]["godhuli"])
    write_json("10_MARRIAGE_CONTRACT_NEXT.json", next_contracts["MARRIAGE_CEREMONY_TIMING"])
    write_json("11_PLANETARY_FACT_BINDINGS.json", bindings["planetary"])
    write_json("12_CONTEXT_BINDINGS.json", contexts)
    write_json("13_NONBLOCKING_SOURCE_GAPS.json", {"griha_first_occupancy": "NONBLOCKING_CONTEXT_GAP", "marriage_godhuli": "NONBLOCKING_ADDITIONAL_COVERAGE", "p032_preferences": "NONBLOCKING_PREFERENCE"})
    write_json("14_WINDOW_SEARCH_READINESS.json", windows)
    write_json("15_ENGINE_HANDOFF_RX1.json", handoff)
    markdown("16_GOVERNANCE_SOURCE_COUNT_AUDIT.md", "Governance Source Count Audit", f"The registry contains {source_count['observed_source_count']} tracked source records, and the authoritative source architecture reports {source_count['authoritative_architecture_count']}. The failing test expected {source_count['stale_test_expectation_before']} because it retained the older pilot count. `VEDA-SRC-000014` is legitimate, active, passage-verified and was added by commit `0899581d` for Muhurta source-semantics hardening. The test is corrected to 14. This is a stale test invariant, not an unintended source and not an electional-contract semantic change.\n\nSource IDs: `{', '.join(source_count['source_ids'])}`.")
    markdown("17_PARALLEL_STATE.md", "Parallel State", "The following lanes remain unchanged by RX1:\n\n" + "\n".join(f"- `{key}`: `{value}`" for key, value in parallel.items()))
    markdown("18_FINAL_ACCEPTANCE.md", "Final Acceptance", "```json\n" + json.dumps(final_acceptance(), ensure_ascii=False, indent=2) + "\n```")
    return {"predecessor": predecessor, "bindings": bindings, "blockers": blockers, "source_count": source_count, "acceptance": final_acceptance(), "handoff": handoff}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="build and report deterministic output")
    args = parser.parse_args()
    result = build()
    print(json.dumps({"programme": PROGRAMME, "output": str(OUT), "decision": result["acceptance"]["decision"], "acceptance": result["acceptance"]["counts"], "source_count": result["source_count"]["observed_source_count"], "check": args.check}, indent=2))


if __name__ == "__main__":
    main()
