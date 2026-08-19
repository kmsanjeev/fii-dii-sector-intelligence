"""Small declarative predicate evaluator for Muhurta contract validation only.

This module is intentionally not imported by production recommendation code.
It accepts normalized rule dictionaries, never evaluates Python expressions,
and returns categorical results for deterministic contract dry-runs.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Mapping


class PredicateResult(str, Enum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    NOT_EVALUABLE = "NOT_EVALUABLE"
    ERROR = "ERROR"


SUPPORTED_OPERATORS = {
    "EQ", "NEQ", "IN", "NOT_IN", "LT", "LTE", "GT", "GTE", "BETWEEN",
    "EXISTS", "NOT_EXISTS", "BOOLEAN_TRUE", "BOOLEAN_FALSE",
    "ALL_OF", "ANY_OF", "NOT",
}


def validate_predicate(predicate: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    operator = predicate.get("operator")
    if operator not in SUPPORTED_OPERATORS:
        errors.append("unsupported_operator")
    if "python_expression" in predicate or "expression" in predicate:
        errors.append("arbitrary_expression_forbidden")
    if "code" in predicate or "callable" in predicate:
        errors.append("executable_code_forbidden")
    if operator in {"IN", "NOT_IN"} and not isinstance(predicate.get("expected_set"), list):
        errors.append("expected_set_required")
    if operator == "BETWEEN" and not isinstance(predicate.get("range"), list):
        errors.append("range_required")
    if operator in {"ALL_OF", "ANY_OF"} and not isinstance(predicate.get("children"), list):
        errors.append("children_required")
    if operator == "NOT" and not isinstance(predicate.get("child"), Mapping):
        errors.append("child_required")
    return errors


def _value(factors: Mapping[str, Any], factor_id: str) -> tuple[bool, Any]:
    if factor_id not in factors or factors[factor_id] is None:
        return False, None
    return True, factors[factor_id]


def evaluate_predicate(predicate: Mapping[str, Any], factors: Mapping[str, Any]) -> PredicateResult:
    if validate_predicate(predicate):
        return PredicateResult.ERROR
    operator = predicate["operator"]
    if operator in {"ALL_OF", "ANY_OF", "NOT"}:
        if operator == "NOT":
            child = evaluate_predicate(predicate["child"], factors)
            return {
                PredicateResult.TRUE: PredicateResult.FALSE,
                PredicateResult.FALSE: PredicateResult.TRUE,
            }.get(child, child)
        results = [evaluate_predicate(item, factors) for item in predicate["children"]]
        if any(item == PredicateResult.ERROR for item in results):
            return PredicateResult.ERROR
        if any(item == PredicateResult.NOT_EVALUABLE for item in results):
            return PredicateResult.NOT_EVALUABLE
        if operator == "ALL_OF":
            return PredicateResult.TRUE if all(item == PredicateResult.TRUE for item in results) else PredicateResult.FALSE
        return PredicateResult.TRUE if any(item == PredicateResult.TRUE for item in results) else PredicateResult.FALSE

    factor_id = predicate.get("factor_id")
    if not isinstance(factor_id, str):
        return PredicateResult.ERROR
    present, actual = _value(factors, factor_id)
    if operator == "EXISTS":
        return PredicateResult.TRUE if present else PredicateResult.FALSE
    if operator == "NOT_EXISTS":
        return PredicateResult.TRUE if not present else PredicateResult.FALSE
    if not present:
        return PredicateResult.NOT_EVALUABLE
    try:
        expected = predicate.get("expected_value")
        if operator == "EQ":
            return PredicateResult.TRUE if actual == expected else PredicateResult.FALSE
        if operator == "NEQ":
            return PredicateResult.TRUE if actual != expected else PredicateResult.FALSE
        if operator == "IN":
            return PredicateResult.TRUE if actual in predicate["expected_set"] else PredicateResult.FALSE
        if operator == "NOT_IN":
            return PredicateResult.TRUE if actual not in predicate["expected_set"] else PredicateResult.FALSE
        if operator == "LT":
            return PredicateResult.TRUE if actual < expected else PredicateResult.FALSE
        if operator == "LTE":
            return PredicateResult.TRUE if actual <= expected else PredicateResult.FALSE
        if operator == "GT":
            return PredicateResult.TRUE if actual > expected else PredicateResult.FALSE
        if operator == "GTE":
            return PredicateResult.TRUE if actual >= expected else PredicateResult.FALSE
        if operator == "BETWEEN":
            low, high = predicate["range"]
            return PredicateResult.TRUE if low <= actual <= high else PredicateResult.FALSE
        if operator == "BOOLEAN_TRUE":
            return PredicateResult.TRUE if actual is True else PredicateResult.FALSE
        if operator == "BOOLEAN_FALSE":
            return PredicateResult.TRUE if actual is False else PredicateResult.FALSE
    except (TypeError, ValueError, KeyError):
        return PredicateResult.ERROR
    return PredicateResult.ERROR
