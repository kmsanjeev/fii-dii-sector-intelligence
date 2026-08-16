"""Audit conditional timing primitives without weakening their source gates."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

POPULATION_ID = "VEDA-POP-OGDB-001"
POPULATION_HASH = "10e8debb06afa0280aa1523a7fba0c868788871d4a7736e9358584582b400863"
CONDITIONAL_IDS = {
    "VEDA-TIMING-PRIM-003",
    "VEDA-TIMING-PRIM-004",
    "VEDA-TIMING-PRIM-006",
    "VEDA-TIMING-PRIM-011",
    "VEDA-TIMING-PRIM-012",
    "VEDA-TIMING-PRIM-014",
    "VEDA-TIMING-PRIM-015",
}

CONDITIONS = {
    "VEDA-TIMING-PRIM-003": ("SOURCE_PRECISION_REQUIRED", "source-scoped house-lord result family is not resolved", "BLOCKED_BY_SOURCE"),
    "VEDA-TIMING-PRIM-004": ("SOURCE_PRECISION_REQUIRED", "source-scoped planet-in-house result is not resolved", "BLOCKED_BY_SOURCE"),
    "VEDA-TIMING-PRIM-006": ("SOURCE_PRECISION_REQUIRED", "source-scoped Antardasha house-lord result is not resolved", "BLOCKED_BY_SOURCE"),
    "VEDA-TIMING-PRIM-011": ("DATA_INPUT_REQUIRED", "historical transit positions are absent from the population", "NOT_RUN_INPUT_GAP"),
    "VEDA-TIMING-PRIM-012": ("METHOD_VALIDATION_REQUIRED", "relationship type is not fixed between placement, aspect, exchange and conjunction", "BLOCKED_BY_SOURCE"),
    "VEDA-TIMING-PRIM-014": ("METHOD_VALIDATION_REQUIRED", "source-specific dignity method and thresholds are unresolved", "BLOCKED_BY_SOURCE"),
    "VEDA-TIMING-PRIM-015": ("METHOD_VALIDATION_REQUIRED", "aspect school, target and orb are unresolved", "BLOCKED_BY_SOURCE"),
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_population(path: Path) -> dict[str, Any]:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            return json.load(handle)
    return read_json(path)


def verify_population(population: dict[str, Any]) -> None:
    if population.get("population_id") != POPULATION_ID:
        raise AssertionError("unexpected population id")
    if population.get("population_hash") != POPULATION_HASH:
        raise AssertionError("POP-001 population hash changed")
    if population.get("outcome_fields_present") is not False:
        raise AssertionError("outcome field invariant violated")
    if population.get("outcome_joins_performed") is not False:
        raise AssertionError("outcome join invariant violated")


def prevalence_band(value: float | None) -> str:
    if value is None:
        return "NOT_TESTED"
    if value >= 0.8:
        return "TOO_COMMON"
    if value >= 0.5:
        return "HIGH_PREVALENCE"
    if value >= 0.1:
        return "EMPIRICALLY_USEFUL_RANGE"
    if value >= 0.03:
        return "LOW_PREVALENCE"
    if value >= 0.01:
        return "VERY_LOW_PREVALENCE"
    if value > 0:
        return "NEAR_ZERO"
    return "ZERO"


def audit(population: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    verify_population(population)
    candidates = [row for row in registry["primitives"] if row["primitive_id"] in CONDITIONAL_IDS]
    if {row["primitive_id"] for row in candidates} != CONDITIONAL_IDS:
        raise AssertionError("conditional registry set changed")
    rows = []
    for row in candidates:
        blocker, resolution, status = CONDITIONS[row["primitive_id"]]
        rows.append({
            "primitive_id": row["primitive_id"],
            "name": row["name"],
            "source_status": row["source_status"],
            "implementation_status": row["implementation_status"],
            "condition_class": blocker,
            "condition": row["indeterminate_condition"],
            "resolution_required": resolution,
            "resolution_status": status,
            "observation_domain": "NOT_ENTERED_BLOCKED_BEFORE_POPULATION_EXECUTION",
            "subjects_analyzed": 0,
            "subjects_with_any_activation": 0,
            "subject_activation_rate": None,
            "total_observation_time": None,
            "active_time": None,
            "time_weighted_prevalence": None,
            "mean_subject_prevalence": None,
            "median_subject_prevalence": None,
            "zero_activation_rate": None,
            "indeterminate_rate": 1.0,
            "activation_interval_count": 0,
            "median_interval_duration": None,
            "classification": status if status != "NOT_RUN_INPUT_GAP" else "CALCULATION_BLOCKED",
            "empirically_useful_for_study_design": False,
            "positive_fixture": {"status": "NOT_EXECUTED_BLOCKED", "condition": row["positive_condition"]},
            "negative_fixture": {"status": "NOT_EXECUTED_BLOCKED", "condition": row["negative_condition"]},
            "indeterminate_fixture": {"status": "REACHABLE", "condition": row["indeterminate_condition"]},
            "component_decomposition": {"source_condition": "BLOCKED", "calculation": "NOT_ENTERED", "population": "NOT_ENTERED"},
        })
    return {
        "programme": "VEDA-POP-002",
        "population_id": POPULATION_ID,
        "population_hash_verified": True,
        "conditional_candidates": len(rows),
        "audited": 0,
        "rows": rows,
        "summary": {
            "TOO_COMMON": 0,
            "HIGH_PREVALENCE": 0,
            "EMPIRICALLY_USEFUL_RANGE": 0,
            "LOW_PREVALENCE": 0,
            "VERY_LOW_PREVALENCE": 0,
            "NEAR_ZERO": 0,
            "ZERO": 0,
            "STRUCTURALLY_UNIVERSAL": 0,
            "BLOCKED_BY_SOURCE": sum(row["classification"] == "BLOCKED_BY_SOURCE" for row in rows),
            "NOT_DETERMINISTIC": 0,
            "CALCULATION_BLOCKED": sum(row["classification"] == "CALCULATION_BLOCKED" for row in rows),
            "empirically_useful_count": 0,
        },
        "composition_authorized": False,
        "composition_reason": "No conditional primitive reached prevalence testing; no composition is authorized.",
        "outcome_free": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("population", type=Path)
    parser.add_argument("registry", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = audit(read_population(args.population), read_json(args.registry))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"programme": result["programme"], "conditional_candidates": result["conditional_candidates"], "audited": result["audited"], "empirically_useful": result["summary"]["empirically_useful_count"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
