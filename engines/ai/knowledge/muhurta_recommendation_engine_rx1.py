"""Contract-bound general Muhurta recommendation engine (RX1).

This module consumes the frozen RX2 activity contracts and the existing P032
calculation/factor adapter.  It evaluates one supplied candidate only.  It
does not rank windows, score factors, evaluate personal Bala, or make outcome
predictions.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from engines.common.logger import get_logger
from engines.ai.knowledge.muhurta_foundation import compute_panchanga_facts
from scripts.veda_muhurta_predicate_evaluator import (
    PredicateResult,
    SUPPORTED_OPERATORS,
    evaluate_predicate,
    validate_predicate,
)
from scripts.veda_muhurta_rule_evaluator_contract_remediation_001 import adapt_p032_facts


PROGRAMME = "VEDA-MUHURTA-RECOMMENDATION-ENGINE-001-RX1"
ENGINE_ID = "VEDA_MUHURTA_GENERAL_RECOMMENDATION_ENGINE"
ENGINE_VERSION = "1.0.0"
MODE = "GENERAL_MUHURTA"
CONTRACT_ROOT = Path(__file__).resolve().parents[3] / "docs/current-state/muhurta-dedicated-classical-source-rx2-001"

CONTRACTS = {
    "BUSINESS_OPENING_INAUGURATION": {
        "file": "12_BUSINESS_CONTRACT_NEXT.json",
        "contract_id": "VEDA-MUH-CONTRACT-BUSINESS-OPENING-V4",
        "hash": "DBC0DF78DCBDC0DC58842895B68733D0E6DDEFB946550419E88D3B6E2584BE60",
        "caution": "Business opening guidance does not assess commercial viability, financing, tax, legal compliance, or business success.",
        "consultation": "Confirm practical, legal, tax, lease, financing, licensing, and operational requirements independently with qualified professionals.",
    },
    "EDUCATION_COMMENCEMENT": {
        "file": "13_EDUCATION_CONTRACT_NEXT.json",
        "contract_id": "VEDA-MUH-CONTRACT-EDUCATION-COMMENCEMENT-V4",
        "hash": "7A17DB6B6256D9BD1C6F1F6737FACC4A6F2AAF9B8A74C56FD0FA05A3B6805F35",
        "caution": "Education commencement guidance does not guarantee academic outcomes and does not override institutional requirements, deadlines, or mandatory dates.",
        "consultation": "Treat institutional schedules, enrolment rules, attendance requirements, and practical educational obligations as primary.",
    },
}

ALLOWED_SOURCE_LAYERS = {
    "CLASSICAL_PRIMARY",
    "CLASSICAL_PRIMARY_DEDICATED_WITNESS",
    "IMPLEMENTATION",
}
ALLOWED_EXECUTABILITY = {"MACHINE_READY", "SOURCE_PARTIAL", "SOURCE_PARTIAL_NON_BLOCKING"}
NON_BLOCKING_STATES = {"SOURCE_PARTIAL", "SOURCE_PARTIAL_NON_BLOCKING"}
POSITIVE_EFFECTS = {"PREFERENCE_POSITIVE", "STRONG_POSITIVE"}
CONTEXT_EFFECTS = {"CONTEXT_DEPENDENT"}
BLOCKING_REASONS = {
    "INSUFFICIENT_RULE_COVERAGE",
    "SOURCE_CONFLICT_UNRESOLVED",
    "REQUIRED_FACTOR_UNAVAILABLE",
    "PERSONAL_FACTOR_REQUIRED",
    "CALCULATION_DEPENDENCY_UNAVAILABLE",
    "ACTIVITY_SCOPE_MISMATCH",
}

logger = get_logger(__name__)


class MuhurtaEngineError(RuntimeError):
    """Unexpected engine or contract error; never converted to a recommendation."""


class ContractValidationError(MuhurtaEngineError):
    """A frozen contract failed closed validation."""


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _contract_hash(contract: Mapping[str, Any]) -> str:
    value = copy.deepcopy(dict(contract))
    value.pop("contract_hash", None)
    value.pop("contract_hash_full", None)
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest().upper()


def _load_contract(activity_id: str) -> dict[str, Any]:
    binding = CONTRACTS.get(activity_id)
    if binding is None:
        raise ContractValidationError(f"unsupported activity contract: {activity_id}")
    path = CONTRACT_ROOT / binding["file"]
    try:
        contract = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractValidationError(f"contract unavailable: {path.name}") from exc
    if not isinstance(contract, dict):
        raise ContractValidationError("contract root must be an object")
    if contract.get("activity_id") != activity_id or contract.get("contract_id") != binding["contract_id"]:
        raise ContractValidationError("contract identity mismatch")
    if contract.get("contract_hash_full") != binding["hash"] or _contract_hash(contract) != binding["hash"]:
        raise ContractValidationError("contract hash mismatch")
    if contract.get("version") != "4.0.0":
        raise ContractValidationError("unsupported contract version")
    if contract.get("production_bound") is not False or contract.get("arbitrary_numeric_score") is not False:
        raise ContractValidationError("contract activation boundary is invalid")
    rules = contract.get("rules")
    if not isinstance(rules, list) or not rules:
        raise ContractValidationError("contract has no rules")
    declared_ids = set(contract.get("rule_ids", []))
    if declared_ids != {rule.get("rule_id") for rule in rules}:
        raise ContractValidationError("rule id inventory mismatch")
    for rule in rules:
        _validate_rule(rule, activity_id)
    if set(contract.get("machine_rule_ids", [])) - declared_ids:
        raise ContractValidationError("machine rule inventory mismatch")
    return contract


def _validate_rule(rule: Any, activity_id: str) -> None:
    if not isinstance(rule, dict):
        raise ContractValidationError("rule must be an object")
    required = {"rule_id", "activity_scope", "executability_state", "rule_class", "variant_id"}
    missing = sorted(required - set(rule))
    if missing or rule.get("activity_scope") != activity_id:
        raise ContractValidationError(f"invalid rule shape: {rule.get('rule_id')}")
    state = rule.get("executability_state")
    if state not in ALLOWED_EXECUTABILITY:
        raise ContractValidationError(f"unsupported rule state: {rule.get('rule_id')}")
    if state == "MACHINE_READY":
        for field in ("factor_id", "operator", "missing_value_policy", "source_assertions"):
            if field not in rule:
                raise ContractValidationError(f"machine rule missing {field}: {rule.get('rule_id')}")
        if rule["operator"] not in SUPPORTED_OPERATORS or validate_predicate(rule):
            raise ContractValidationError(f"invalid declarative predicate: {rule.get('rule_id')}")
        if not isinstance(rule["source_assertions"], list) or not rule["source_assertions"]:
            raise ContractValidationError(f"machine rule has no source lineage: {rule.get('rule_id')}")
        if rule.get("source_layer") not in ALLOWED_SOURCE_LAYERS:
            raise ContractValidationError(f"unsupported source layer: {rule.get('rule_id')}")
        if not isinstance(rule.get("variant_id"), str) or not rule["variant_id"]:
            raise ContractValidationError(f"machine rule has no variant: {rule.get('rule_id')}")


def load_validated_contract(activity_id: str) -> dict[str, Any]:
    """Public fail-closed contract loader used by tests and the API."""
    return _load_contract(activity_id)


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        result = value
    elif isinstance(value, str):
        try:
            result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise MuhurtaEngineError("candidate_start must be ISO-8601 datetime") from exc
    else:
        raise MuhurtaEngineError("candidate_start must be ISO-8601 datetime")
    if result.tzinfo is None or result.utcoffset() is None:
        raise MuhurtaEngineError("candidate_start must be timezone-aware")
    return result


def _validate_location(location: Any) -> dict[str, Any]:
    if not isinstance(location, Mapping):
        raise MuhurtaEngineError("location is required")
    try:
        latitude = float(location["latitude"])
        longitude = float(location["longitude"])
        timezone_name = str(location["timezone_name"])
    except (KeyError, TypeError, ValueError) as exc:
        raise MuhurtaEngineError("location requires latitude, longitude, timezone_name") from exc
    if not all(math.isfinite(item) for item in (latitude, longitude)):
        raise MuhurtaEngineError("location coordinates must be finite")
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise MuhurtaEngineError("location coordinates are out of range")
    try:
        ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise MuhurtaEngineError("invalid timezone_name") from exc
    return {"latitude": latitude, "longitude": longitude, "timezone_name": timezone_name}


def _normalise_factors(
    *,
    p032_facts: Mapping[str, Any] | None,
    candidate_start: datetime,
    sun_sidereal_longitude: Any,
    moon_sidereal_longitude: Any,
    transition_boundaries: list[Any] | None,
    activity_subscope: str | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    facts = p032_facts
    calculation_metadata: dict[str, Any] = {"source": "CALLER_SUPPLIED_P032_FACTS"}
    if facts is None and sun_sidereal_longitude is not None and moon_sidereal_longitude is not None:
        try:
            facts = compute_panchanga_facts(sun_sidereal_longitude, moon_sidereal_longitude, candidate_start)
        except (TypeError, ValueError, KeyError) as exc:
            raise MuhurtaEngineError(f"P032 calculation failed: {exc}") from exc
        calculation_metadata = {
            "source": "P032_COMPUTE_PANCHANGA_FACTS",
            "method_id": facts.get("calculation_method", {}).get("method_id"),
            "version": facts.get("calculation_method", {}).get("version"),
        }
    if facts is None:
        return {"PANCHANGA_FACTS_AVAILABLE": False}, {"source": "P032_INPUT_MISSING"}
    if not isinstance(facts, Mapping):
        raise MuhurtaEngineError("p032_facts must be an object")
    boundaries = [] if transition_boundaries is None else transition_boundaries
    if not isinstance(boundaries, list):
        raise MuhurtaEngineError("transition_boundaries must be a list")
    factors = adapt_p032_facts(facts, boundaries, activity_subscope=activity_subscope)
    if factors.get("PANCHANGA_FACTS_AVAILABLE") and isinstance(facts.get("karana"), Mapping):
        name = facts["karana"].get("name")
        if name is not None:
            factors["KARANA_NAME"] = str(name).upper()
    return factors, calculation_metadata


def _caution(activity_id: str, activity_binding: Mapping[str, Any]) -> dict[str, str]:
    general = "Muhurta is supplementary traditional guidance based on governed rules; it does not guarantee outcomes, and practical circumstances remain independently important."
    return {
        "general": general,
        "activity": activity_binding["caution"],
        "consultation": activity_binding["consultation"],
    }


def _unsupported_result(activity_id: str, reason: str) -> dict[str, Any]:
    return {
        "activity_id": activity_id,
        "recommendation_state": "ABSTAIN",
        "abstention_reason": reason,
        "mode": MODE,
        "capability_state": "IMPLEMENTED_VALIDATED",
        "access_state": "ENABLED",
        "personal_factors_evaluated": False,
        "source_trace": {"engine_id": ENGINE_ID, "engine_version": ENGINE_VERSION, "rules_evaluated": []},
        "caution": {"general": "This activity is outside the currently activated general Muhurta contract; no recommendation was produced."},
    }


def recommend(request: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate one candidate and return a deterministic, traceable result."""
    if not isinstance(request, Mapping):
        raise MuhurtaEngineError("request must be an object")
    activity_id = request.get("activity_id")
    if not isinstance(activity_id, str):
        raise MuhurtaEngineError("activity_id is required")
    if activity_id not in CONTRACTS:
        return _unsupported_result(activity_id, "NOT_YET_ENGINE_READY")
    contract = _load_contract(activity_id)
    candidate_start = _parse_datetime(request.get("candidate_start"))
    location = _validate_location(request.get("location"))
    explicit_scope = request.get("activity_subscope")
    if explicit_scope is not None and not isinstance(explicit_scope, str):
        raise MuhurtaEngineError("activity_subscope must be a string")
    if activity_id == "BUSINESS_OPENING_INAUGURATION" and explicit_scope in set(contract["activity_scope"]["excluded"]):
        return _result_abstention(contract, location, candidate_start, "ACTIVITY_SCOPE_MISMATCH", "The requested business activity is excluded from this narrow contract.", [], {}, {})
    if activity_id == "EDUCATION_COMMENCEMENT" and explicit_scope is None:
        explicit_scope = "FORMAL_COURSE_COMMENCEMENT"
    factors, calculation_metadata = _normalise_factors(
        p032_facts=request.get("p032_facts"),
        candidate_start=candidate_start,
        sun_sidereal_longitude=request.get("sun_sidereal_longitude"),
        moon_sidereal_longitude=request.get("moon_sidereal_longitude"),
        transition_boundaries=request.get("transition_boundaries"),
        activity_subscope=explicit_scope,
    )
    if not factors.get("PANCHANGA_FACTS_AVAILABLE"):
        return _result_abstention(contract, location, candidate_start, "CALCULATION_DEPENDENCY_UNAVAILABLE", "P032 Panchanga facts and transition boundaries were not available; the candidate was not evaluated.", [], factors, calculation_metadata)

    evaluated: list[dict[str, Any]] = []
    supporting: list[str] = []
    adverse: list[str] = []
    blocking_reason: str | None = None
    hard_exclusion = False
    nonblocking_gaps: list[dict[str, Any]] = []
    for rule in contract["rules"]:
        state = rule["executability_state"]
        if state in NON_BLOCKING_STATES:
            nonblocking_gaps.append({"rule_id": rule["rule_id"], "reason": rule.get("source_partial_reason") or rule.get("non_blocking_reason"), "blocking": False})
            continue
        result = evaluate_predicate(rule, factors)
        result_value = result.value
        evaluated_item = {
            "rule_id": rule["rule_id"],
            "result": result_value,
            "factor_id": rule.get("factor_id"),
            "rule_class": rule.get("rule_class"),
            "variant_id": rule.get("variant_id"),
            "source_assertions": list(rule.get("source_assertions", [])),
        }
        evaluated.append(evaluated_item)
        if result in {PredicateResult.NOT_EVALUABLE, PredicateResult.ERROR}:
            if rule.get("hard_requirement") or rule.get("hard_exclusion"):
                blocking_reason = "REQUIRED_FACTOR_UNAVAILABLE"
            continue
        if result == PredicateResult.TRUE:
            effect = rule.get("recommendation_effect")
            if rule.get("hard_exclusion"):
                hard_exclusion = True
            if effect in POSITIVE_EFFECTS:
                supporting.append(rule["rule_id"])
            elif effect in CONTEXT_EFFECTS:
                supporting.append(rule["rule_id"])
        else:
            if rule.get("hard_requirement"):
                blocking_reason = "ACTIVITY_SCOPE_MISMATCH" if rule["rule_id"].endswith("ROUTINE-SCOPE-001") else "REQUIRED_FACTOR_UNAVAILABLE"
            if rule.get("hard_exclusion"):
                hard_exclusion = False
            if rule.get("recommendation_effect") in POSITIVE_EFFECTS | CONTEXT_EFFECTS:
                adverse.append(rule["rule_id"])
    if blocking_reason:
        return _result_abstention(contract, location, candidate_start, blocking_reason, "A contract-bound required condition was not satisfied.", evaluated, factors, calculation_metadata, supporting, adverse, nonblocking_gaps)
    if hard_exclusion:
        state = "NOT_RECOMMENDED_UNDER_SELECTED_RULESET"
    elif supporting and adverse:
        state = "MIXED_FACTORS"
    elif supporting:
        state = "SUPPORTED_WITH_CAUTION"
    else:
        state = "INSUFFICIENT_RULE_COVERAGE"
    result = _result_base(contract, location, candidate_start, factors, calculation_metadata)
    result.update({
        "recommendation_state": state,
        "rules_applicable": [rule["rule_id"] for rule in contract["rules"]],
        "rules_evaluated": evaluated,
        "supporting_factors": supporting,
        "adverse_factors": adverse,
        "unevaluated_source_gaps": nonblocking_gaps,
        "requirements": [],
        "abstention_reason": None,
        "why_this_candidate": "Source-scoped predicates were evaluated for the supplied candidate; an indicator is not a guarantee of an outcome.",
        "rule_coverage": _coverage(contract, evaluated, nonblocking_gaps),
    })
    return result


def _coverage(contract: Mapping[str, Any], evaluated: list[Mapping[str, Any]], gaps: list[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "applicable_rule_count": len(contract["rules"]),
        "evaluated_rule_count": len(evaluated),
        "satisfied_rule_count": sum(item["result"] == "TRUE" for item in evaluated),
        "unsatisfied_rule_count": sum(item["result"] == "FALSE" for item in evaluated),
        "unevaluated_nonblocking_rule_count": len(gaps),
        "source_gap_rule_ids": [item["rule_id"] for item in gaps],
    }


def _result_base(contract: Mapping[str, Any], location: Mapping[str, Any], candidate_start: datetime, factors: Mapping[str, Any], calculation_metadata: Mapping[str, Any]) -> dict[str, Any]:
    binding = CONTRACTS[contract["activity_id"]]
    return {
        "activity_id": contract["activity_id"],
        "mode": MODE,
        "candidate_start": candidate_start.isoformat(),
        "candidate_end": candidate_start.isoformat(),
        "location": dict(location),
        "personal_factors_evaluated": False,
        "personal_factors": {"tara_bala": "NOT_EVALUATED", "chandra_bala": "NOT_EVALUATED"},
        "contract_metadata": {"contract_id": contract["contract_id"], "contract_hash_full": contract["contract_hash_full"], "version": contract["version"]},
        "engine_metadata": {"programme": PROGRAMME, "engine_id": ENGINE_ID, "engine_version": ENGINE_VERSION, "calculation": dict(calculation_metadata)},
        "source_trace": {"contract_id": contract["contract_id"], "contract_hash_full": contract["contract_hash_full"], "engine_id": ENGINE_ID, "engine_version": ENGINE_VERSION, "rules_evaluated": [], "source_assertion_ids": [], "variant_ids": []},
        "caution": _caution(contract["activity_id"], binding),
        "consultation_guidance": binding["consultation"],
        "capability_state": "IMPLEMENTED_VALIDATED",
        "access_state": "ENABLED",
        "trust_state": "VALIDATED_CONTRACT_BOUND_GENERAL_ONLY",
    }


def _result_abstention(contract: Mapping[str, Any], location: Mapping[str, Any], candidate_start: datetime, reason: str, explanation: str, evaluated: list[Mapping[str, Any]], factors: Mapping[str, Any], calculation_metadata: Mapping[str, Any], supporting: list[str] | None = None, adverse: list[str] | None = None, gaps: list[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    result = _result_base(contract, location, candidate_start, factors, calculation_metadata)
    result.update({
        "recommendation_state": "ABSTAIN",
        "abstention_reason": reason,
        "abstention_explanation": explanation,
        "rules_applicable": [rule["rule_id"] for rule in contract["rules"]],
        "rules_evaluated": list(evaluated),
        "supporting_factors": supporting or [],
        "adverse_factors": adverse or [],
        "unevaluated_source_gaps": list(gaps or []),
        "requirements": [reason],
        "rule_coverage": _coverage(contract, list(evaluated), list(gaps or [])),
    })
    return result


def _refresh_trace(result: dict[str, Any]) -> dict[str, Any]:
    trace = result["source_trace"]
    rules = result.get("rules_evaluated", [])
    trace["rules_evaluated"] = [item["rule_id"] for item in rules]
    trace["source_assertion_ids"] = sorted({assertion for item in rules for assertion in item.get("source_assertions", [])})
    trace["variant_ids"] = sorted({item["variant_id"] for item in rules if item.get("variant_id")})
    return result


_original_recommend = recommend


def recommend(request: Mapping[str, Any]) -> dict[str, Any]:  # noqa: E305
    result = _refresh_trace(_original_recommend(request))
    logger.info(
        "engine_id=%s activity=%s contract_id=%s recommendation_state=%s abstention_reason=%s rule_ids=%s",
        ENGINE_ID,
        result.get("activity_id"),
        result.get("contract_metadata", {}).get("contract_id"),
        result.get("recommendation_state"),
        result.get("abstention_reason"),
        result.get("source_trace", {}).get("rules_evaluated", []),
    )
    return result
