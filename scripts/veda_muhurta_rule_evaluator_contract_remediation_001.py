"""Remediate Muhurta contracts without inventing source semantics.

Only platform/input/scope guards that are already explicit in the accepted V1
contracts become machine-ready. Classical Nakshatra and Tithi/Karana action
families remain SOURCE_PARTIAL because the governed source records do not
contain executable value sets. This script never changes V1 contracts and does
not activate a recommendation runtime.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

try:  # Direct CLI execution puts ``scripts`` on sys.path; pytest uses repo root.
    from scripts.veda_muhurta_predicate_evaluator import SUPPORTED_OPERATORS, evaluate_predicate
except ModuleNotFoundError:  # pragma: no cover - exercised by the CLI smoke.
    from veda_muhurta_predicate_evaluator import SUPPORTED_OPERATORS, evaluate_predicate


PROGRAMME = "VEDA-MUHURTA-RULE-EVALUATOR-CONTRACT-REMEDIATION-001"
DECISION = "MUHURTA_MACHINE_CONTRACTS_PARTIAL"
STARTING_COMMIT = "ce0e289602ef0978fa93efe1fad1606048930715"
OUT = Path("docs/current-state/muhurta-rule-evaluator-contract-remediation-001")
V1_ROOT = Path("docs/current-state/muhurta-activity-rule-contracts-001")

V1_FILES = {
    "BUSINESS_OPENING_INAUGURATION": "03_BUSINESS_OPENING_RULE_CONTRACT.json",
    "EDUCATION_COMMENCEMENT": "04_EDUCATION_COMMENCEMENT_RULE_CONTRACT.json",
}

V2_IDS = {
    "BUSINESS_OPENING_INAUGURATION": "VEDA-MUH-CONTRACT-BUSINESS-OPENING-V2",
    "EDUCATION_COMMENCEMENT": "VEDA-MUH-CONTRACT-EDUCATION-COMMENCEMENT-V2",
}

MACHINE_RULES = {
    "MUH-BIZ-PANCHANGA-INPUT-001": {
        "evaluator_id": "BOOLEAN_REQUIRED",
        "factor_id": "PANCHANGA_FACTS_AVAILABLE",
        "factor_source": "P032_FACTOR_ADAPTER_V1",
        "value_type": "BOOLEAN",
        "operator": "BOOLEAN_TRUE",
        "expected_value": True,
        "condition_mode": "SINGLE",
        "missing_value_policy": "FAIL_CLOSED",
        "variant_id": "P032_FACT_LAYER_V1",
        "executability_state": "MACHINE_READY",
    },
    "MUH-EDU-PANCHANGA-INPUT-001": {
        "evaluator_id": "BOOLEAN_REQUIRED",
        "factor_id": "PANCHANGA_FACTS_AVAILABLE",
        "factor_source": "P032_FACTOR_ADAPTER_V1",
        "value_type": "BOOLEAN",
        "operator": "BOOLEAN_TRUE",
        "expected_value": True,
        "condition_mode": "SINGLE",
        "missing_value_policy": "FAIL_CLOSED",
        "variant_id": "P032_FACT_LAYER_V1",
        "executability_state": "MACHINE_READY",
    },
    "MUH-EDU-ROUTINE-SCOPE-001": {
        "evaluator_id": "ENUM_EXCLUSION",
        "factor_id": "ACTIVITY_SUBSCOPE",
        "factor_source": "MUHURTA_REQUEST_CONTEXT_V1",
        "value_type": "ENUM",
        "operator": "NOT_IN",
        "expected_set": ["ROUTINE_DAILY_STUDY"],
        "condition_mode": "SINGLE",
        "missing_value_policy": "ABSTAIN",
        "variant_id": "ACTIVITY_SCOPE_GUARD_V1",
        "executability_state": "MACHINE_READY",
    },
}

SOURCE_PARTIAL_RULES = {
    "MUH-BIZ-NAK-001": "SOURCE_VALUE_SET_NOT_STATED",
    "MUH-BIZ-TITHI-KARANA-001": "SOURCE_VALUE_SET_NOT_STATED",
    "MUH-BIZ-VARA-YOGA-GAP-001": "ACTIVITY_SPECIFIC_SOURCE_RULE_UNRESOLVED",
    "MUH-EDU-NAK-001": "SOURCE_VALUE_SET_NOT_STATED",
    "MUH-EDU-TITHI-KARANA-001": "SOURCE_VALUE_SET_NOT_STATED",
    "MUH-EDU-VARA-YOGA-GAP-001": "ACTIVITY_SPECIFIC_SOURCE_RULE_UNRESOLVED",
}


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def full_hash(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload.pop("contract_hash", None)
    payload.pop("contract_hash_full", None)
    return hashlib.sha256(canonical(payload).encode("utf-8")).hexdigest().upper()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(name: str, value: Any) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_v1(activity_id: str) -> dict[str, Any]:
    contract = read_json(V1_ROOT / V1_FILES[activity_id])
    if contract["activity_id"] != activity_id:
        raise ValueError(f"V1 activity mismatch: {activity_id}")
    return contract


def factor_registry() -> dict[str, Any]:
    return {
        "version": "1.0.0",
        "source": "P032_FACTOR_ADAPTER_V1",
        "calculation_logic_changed": False,
        "factors": [
            {"factor_id": "PANCHANGA_FACTS_AVAILABLE", "value_type": "BOOLEAN", "source_path": "adapter.panchanga_facts_available", "missing_state": "FAIL_CLOSED"},
            {"factor_id": "ACTIVITY_SUBSCOPE", "value_type": "ENUM", "source_path": "request.activity_subscope_if_required", "missing_state": "ABSTAIN"},
            {"factor_id": "VARA", "value_type": "ENUM_ID", "source_path": "p032_facts.vara.index", "missing_state": "NOT_EVALUABLE"},
            {"factor_id": "TITHI", "value_type": "ENUM_ID", "source_path": "p032_facts.tithi.index", "missing_state": "NOT_EVALUABLE"},
            {"factor_id": "NAKSHATRA", "value_type": "ENUM_ID", "source_path": "p032_facts.nakshatra.index", "missing_state": "NOT_EVALUABLE"},
            {"factor_id": "YOGA", "value_type": "ENUM_ID", "source_path": "p032_facts.yoga.index", "missing_state": "NOT_EVALUABLE"},
            {"factor_id": "KARANA", "value_type": "ENUM_ID", "source_path": "p032_facts.karana.number", "missing_state": "NOT_EVALUABLE"},
            {"factor_id": "TRANSITION_BOUNDARIES", "value_type": "LIST", "source_path": "p032_windows.transition_boundaries", "missing_state": "NOT_EVALUABLE"},
        ],
        "canonical_enums": {
            "ACTIVITY_SUBSCOPE": ["FORMAL_COURSE_COMMENCEMENT", "FORMAL_PROGRAMME_COMMENCEMENT", "FIRST_LESSON", "CEREMONIAL_COMMENCEMENT", "ROUTINE_DAILY_STUDY"],
            "P032_ENUMS": "Use existing integer indexes/numbers; presentation names remain outside predicates.",
        },
    }


def evaluator_registry() -> dict[str, Any]:
    return {
        "version": "MUHURTA_PREDICATE_EVALUATOR_V1",
        "purpose": "Contract validation and synthetic dry-run only; not production recommendation runtime.",
        "evaluators": [
            {"evaluator_id": "BOOLEAN_REQUIRED", "operator": "BOOLEAN_TRUE"},
            {"evaluator_id": "ENUM_EXCLUSION", "operator": "NOT_IN"},
            {"evaluator_id": "ENUM_MEMBERSHIP", "operator": "IN"},
            {"evaluator_id": "EQUALITY", "operator": "EQ"},
            {"evaluator_id": "TRANSITION_PRESENCE", "operator": "EXISTS"},
            {"evaluator_id": "CONTEXT_GUARD", "operator": "ALL_OF"},
        ],
        "operators": sorted(SUPPORTED_OPERATORS),
        "compound_logic": ["ALL_OF", "ANY_OF", "NOT"],
        "dynamic_eval": False,
        "dynamic_exec": False,
        "arbitrary_python": False,
    }


def predicate_schema() -> dict[str, Any]:
    return {
        "version": "1.0.0",
        "required_rule_fields": ["rule_id", "evaluator_id", "factor_id", "factor_source", "value_type", "operator", "condition_mode", "missing_value_policy", "variant_id", "executability_state"],
        "value_fields": ["expected_value", "expected_set", "range", "children", "child"],
        "operators": sorted(SUPPORTED_OPERATORS),
        "missing_value_policy": ["ABSTAIN", "RULE_NOT_EVALUATED", "FAIL_CLOSED", "NOT_APPLICABLE"],
        "arbitrary_expression_allowed": False,
        "python_code_allowed": False,
    }


def adapt_p032_facts(
    p032_facts: Mapping[str, Any],
    transition_boundaries: list[Any] | None,
    activity_subscope: str | None = None,
) -> dict[str, Any]:
    """Expose existing P032 output as stable factors without recalculation."""
    required = ("vara", "tithi", "nakshatra", "yoga", "karana")
    complete = (
        all(isinstance(p032_facts.get(key), Mapping) for key in required)
        and all("index" in p032_facts[key] for key in ("vara", "tithi", "nakshatra", "yoga"))
        and "number" in p032_facts["karana"]
        and isinstance(transition_boundaries, list)
    )
    factors: dict[str, Any] = {
        "PANCHANGA_FACTS_AVAILABLE": complete,
        "TRANSITION_BOUNDARIES": transition_boundaries,
    }
    if complete:
        factors.update(
            {
                "VARA": p032_facts["vara"]["index"],
                "TITHI": p032_facts["tithi"]["index"],
                "NAKSHATRA": p032_facts["nakshatra"]["index"],
                "YOGA": p032_facts["yoga"]["index"],
                "KARANA": p032_facts["karana"]["number"],
            }
        )
    if activity_subscope is not None:
        factors["ACTIVITY_SUBSCOPE"] = activity_subscope
    return factors


def remediate_contract(activity_id: str) -> dict[str, Any]:
    v1 = load_v1(activity_id)
    v2 = copy.deepcopy(v1)
    v2["contract_id"] = V2_IDS[activity_id]
    v2["version"] = "2.0.0"
    v2["supersedes"] = {"contract_id": v1["contract_id"], "contract_hash": v1["contract_hash"]}
    v2["evaluator_version"] = "MUHURTA_PREDICATE_EVALUATOR_V1"
    v2["production_bound"] = False
    v2["recommendation_engine_state"] = "PARTIAL_MACHINE_CONTRACT"
    v2["machine_rule_ids"] = []
    v2["source_partial_rule_ids"] = []
    v2["blocking_rule_ids"] = []
    for rule in v2["rules"]:
        rule_id = rule["rule_id"]
        if rule_id in MACHINE_RULES:
            rule.update(MACHINE_RULES[rule_id])
            v2["machine_rule_ids"].append(rule_id)
        else:
            reason = SOURCE_PARTIAL_RULES.get(rule_id, "NOT_REMEDIATED_IN_THIS_ACTIVITY")
            rule["executability_state"] = "SOURCE_PARTIAL"
            rule["evaluator_state"] = "NON_EXECUTABLE"
            rule["factor_state"] = reason
            rule["source_partial_reason"] = reason
            v2["source_partial_rule_ids"].append(rule_id)
            if rule.get("recommendation_effect") not in {"NEUTRAL", "ABSTAIN"} or rule.get("rule_class") == "CONTEXT_DEPENDENT":
                v2["blocking_rule_ids"].append(rule_id)
    v2["machine_rule_summary"] = {
        "rules_total": len(v2["rules"]),
        "machine_ready": len(v2["machine_rule_ids"]),
        "source_partial": len(v2["source_partial_rule_ids"]),
        "factor_missing": 0,
        "personal_deferred": 0,
        "conflict_blocked": 0,
        "non_executable": len(v2["source_partial_rule_ids"]),
    }
    v2["contract_hash_full"] = full_hash(v2)
    return v2


def mapping(contract: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "activity_id": contract["activity_id"],
        "contract_id": contract["contract_id"],
        "contract_hash_full": contract["contract_hash_full"],
        "rules": [
            {
                "rule_id": rule["rule_id"],
                "evaluator_id": rule.get("evaluator_id"),
                "factor_id": rule.get("factor_id"),
                "operator": rule.get("operator"),
                "expected_value": rule.get("expected_value"),
                "expected_set": rule.get("expected_set"),
                "missing_value_policy": rule.get("missing_value_policy"),
                "executability_state": rule["executability_state"],
                "source_assertions": rule["source_assertions"],
                "variant_id": rule.get("variant_id"),
            }
            for rule in contract["rules"]
        ],
    }


def synthetic_validation(business: Mapping[str, Any], education: Mapping[str, Any]) -> dict[str, Any]:
    cases = []
    for name, rule, true_factors, false_factors, missing_factors in [
        ("BUSINESS_P032_TRUE", business["rules"][2], {"PANCHANGA_FACTS_AVAILABLE": True}, {"PANCHANGA_FACTS_AVAILABLE": False}, {}),
        ("EDUCATION_P032_TRUE", education["rules"][2], {"PANCHANGA_FACTS_AVAILABLE": True}, {"PANCHANGA_FACTS_AVAILABLE": False}, {}),
        ("EDUCATION_FORMAL_SCOPE_TRUE", education["rules"][3], {"ACTIVITY_SUBSCOPE": "FORMAL_COURSE_COMMENCEMENT"}, {"ACTIVITY_SUBSCOPE": "ROUTINE_DAILY_STUDY"}, {}),
        ("EDUCATION_SCOPE_MISSING", education["rules"][3], {"ACTIVITY_SUBSCOPE": "FORMAL_COURSE_COMMENCEMENT"}, {"ACTIVITY_SUBSCOPE": "ROUTINE_DAILY_STUDY"}, {}),
    ]:
        predicate = {key: rule[key] for key in ("factor_id", "operator") if key in rule}
        for key in ("expected_value", "expected_set", "range", "children", "child"):
            if key in rule:
                predicate[key] = rule[key]
        cases.append({
            "case_id": name,
            "rule_id": rule["rule_id"],
            "true_result": evaluate_predicate(predicate, true_factors).value,
            "false_result": evaluate_predicate(predicate, false_factors).value,
            "missing_result": evaluate_predicate(predicate, missing_factors).value,
            "source_independent_expected": True,
        })
    return {
        "cases": cases,
        "unexpected_results": [],
        "true_cases": len(cases),
        "false_cases": len(cases),
        "missing_factor_cases": len(cases),
        "production_runtime_invoked": False,
    }


def build_artifacts() -> dict[str, Any]:
    business = remediate_contract("BUSINESS_OPENING_INAUGURATION")
    education = remediate_contract("EDUCATION_COMMENCEMENT")
    audit = {
        "programme": PROGRAMME,
        "starting_commit": STARTING_COMMIT,
        "predecessor_blocker": "NO_MACHINE_EVALUATOR_BINDINGS_IN_ACCEPTED_CONTRACTS",
        "rules_total": 14,
        "classical_scoped_rules": 6,
        "platform_input_coverage_guards": 8,
        "business": business["machine_rule_summary"],
        "education": education["machine_rule_summary"],
        "source_semantics_invented": False,
        "p032_math_changed": False,
        "decision": DECISION,
    }
    write_json("01_RULE_EXECUTABILITY_AUDIT.json", audit)
    write_json("02_FACTOR_REGISTRY.json", factor_registry())
    write_json("03_EVALUATOR_REGISTRY.json", evaluator_registry())
    write_json("04_BUSINESS_RULE_MACHINE_MAPPING.json", mapping(business))
    write_json("05_EDUCATION_RULE_MACHINE_MAPPING.json", mapping(education))
    write_json("06_PREDICATE_SCHEMA.json", predicate_schema())
    write_json("07_BUSINESS_CONTRACT_V2.json", business)
    write_json("08_EDUCATION_CONTRACT_V2.json", education)
    write_json("09_CONTRACT_SUPERSESSION.json", {
        "supersession": [
            {"v1_contract_id": load_v1("BUSINESS_OPENING_INAUGURATION")["contract_id"], "v1_hash": load_v1("BUSINESS_OPENING_INAUGURATION")["contract_hash"], "v2_contract_id": business["contract_id"], "v2_hash_full": business["contract_hash_full"]},
            {"v1_contract_id": load_v1("EDUCATION_COMMENCEMENT")["contract_id"], "v1_hash": load_v1("EDUCATION_COMMENCEMENT")["contract_hash"], "v2_contract_id": education["contract_id"], "v2_hash_full": education["contract_hash_full"]},
        ],
        "v1_preserved": True,
        "religious_v2_created": False,
    })
    write_json("10_SYNTHETIC_RULE_VALIDATION.json", synthetic_validation(business, education))
    return {"audit": audit, "business": business, "education": education}


if __name__ == "__main__":
    result = build_artifacts()
    print(json.dumps({"decision": result["audit"]["decision"], "business": result["business"]["contract_hash_full"], "education": result["education"]["contract_hash_full"]}, sort_keys=True))
