"""Run the bounded source-resolution fallback for one conditional primitive at a time."""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
from typing import Any

POPULATION_ID = "VEDA-POP-OGDB-001"
POPULATION_HASH = "10e8debb06afa0280aa1523a7fba0c868788871d4a7736e9358584582b400863"
SOURCE_BLOCKED_IDS = [
    "VEDA-TIMING-PRIM-003",
    "VEDA-TIMING-PRIM-004",
    "VEDA-TIMING-PRIM-006",
    "VEDA-TIMING-PRIM-012",
    "VEDA-TIMING-PRIM-014",
    "VEDA-TIMING-PRIM-015",
]

ATTEMPTS = {
    "VEDA-TIMING-PRIM-003": {
        "selection_rank": 1,
        "selection_reason": "Highest existing Dasha/event-family relevance and existing house-lord facts.",
        "source": "BPHS Ch. 48 pp. 89-90; Phaladeepika Ch. 20 pp. 181-182",
        "passage": "House-lord Dasha results are conditional on placement and relationships; the inspected material does not fix one event-scoped family predicate.",
        "resolution": "UNRESOLVED",
        "blocker": "The source leaves result family and exact house-lord relationship scope conditional; encoding one would add discretionary interpretation.",
    },
    "VEDA-TIMING-PRIM-004": {
        "selection_rank": 2,
        "selection_reason": "Existing D1 planet-in-house and Vimshottari facts are available.",
        "source": "BPHS Ch. 47 pp. 88-89; Phaladeepika Ch. 20 pp. 181-182",
        "passage": "Named planet Dasha results are qualified by placement, strength and relationships; no universal planet-in-house event predicate is established.",
        "resolution": "UNRESOLVED",
        "blocker": "The source does not identify a single retained result scope that can be evaluated without broadening a named result into a universal rule.",
    },
    "VEDA-TIMING-PRIM-006": {
        "selection_rank": 3,
        "selection_reason": "Existing compact Antardasha intervals make calculation readiness high.",
        "source": "BPHS Ch. 51 pp. 95-96 and Ch. 53 pp. 97-98",
        "passage": "Antardasha assessment and selected named results are conditional; the exact house-lord family condition remains unspecified.",
        "resolution": "UNRESOLVED",
        "blocker": "The source supports Antardasha mechanics, not a deterministic event-family house-lord predicate for this registry row.",
    },
    "VEDA-TIMING-PRIM-012": {
        "selection_rank": 4,
        "selection_reason": "D1 house-lord relationships are calculation-ready and could be useful if one relationship type were source-fixed.",
        "source": "BPHS Ch. 48 pp. 89-90; Phaladeepika Ch. 20 pp. 181-182",
        "passage": "Placement and relationships are used contextually in results; the inspected sources do not make placement, conjunction, aspect and exchange interchangeable.",
        "resolution": "UNRESOLVED",
        "blocker": "The registry intentionally leaves relationship type unresolved; selecting one would be a new method rather than source resolution.",
    },
    "VEDA-TIMING-PRIM-014": {
        "selection_rank": 5,
        "selection_reason": "Dignity is present in D1 facts, but source precision is lower than the preceding candidates.",
        "source": "BPHS Ch. 48 pp. 89-90; Phaladeepika Ch. 20 pp. 181-182",
        "passage": "Strength and dignity qualify results in context; no single dignity threshold and Dasha result scope is fixed for this modifier.",
        "resolution": "UNRESOLVED",
        "blocker": "A dignity modifier cannot be converted into a prevalence primitive without an explicit source method and threshold.",
    },
    "VEDA-TIMING-PRIM-015": {
        "selection_rank": 6,
        "selection_reason": "Aspect facts are available only through method-specific chart logic and are the least source-ready candidate.",
        "source": "BPHS Ch. 48 pp. 89-90; Phaladeepika Ch. 20 pp. 181-182",
        "passage": "Relationships are mentioned contextually; the inspected passages do not fix the aspect school, target and orb for this modifier.",
        "resolution": "UNRESOLVED",
        "blocker": "No exact aspect contract can be encoded without choosing an unresolved school, target or orb.",
    },
}


def load_population(path: Path) -> dict[str, Any]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        population = json.load(handle)
    if population.get("population_id") != POPULATION_ID or population.get("population_hash") != POPULATION_HASH:
        raise AssertionError("POP-001 population hash lock failed")
    if population.get("outcome_fields_present") is not False or population.get("outcome_joins_performed") is not False:
        raise AssertionError("outcome-free invariant failed")
    return population


def run(population: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    load_population_from_value(population)
    rows_by_id = {row["primitive_id"]: row for row in registry["primitives"]}
    if any(rows_by_id[primitive_id]["implementation_status"] != "IMPLEMENTABLE_WITH_CONDITION" for primitive_id in SOURCE_BLOCKED_IDS):
        raise AssertionError("source-blocked candidate set changed")
    attempts = []
    for primitive_id in SOURCE_BLOCKED_IDS:
        item = ATTEMPTS[primitive_id].copy()
        item.update({
            "primitive_id": primitive_id,
            "source_status_before": rows_by_id[primitive_id]["source_status"],
            "source_status_after": "BLOCKED_BY_SOURCE",
            "contract": "NOT_CREATED",
            "positive_fixture": "NOT_REACHABLE_WITHOUT_INVENTED_METHOD",
            "negative_fixture": "NOT_REACHABLE_WITHOUT_INVENTED_METHOD",
            "indeterminate_fixture": "REACHABLE_MISSING_SOURCE_CONDITION",
            "prevalence": "NOT_ENTERED",
        })
        attempts.append(item)
    return {
        "programme": "VEDA-PRIM-RX-001",
        "population_id": POPULATION_ID,
        "population_hash": POPULATION_HASH,
        "population_hash_verified": True,
        "selected_primitive_id": SOURCE_BLOCKED_IDS[0],
        "selection_rationale": ATTEMPTS[SOURCE_BLOCKED_IDS[0]]["selection_reason"],
        "alternatives_considered": SOURCE_BLOCKED_IDS[1:],
        "attempts": attempts,
        "resolved": False,
        "prevalence_entered": False,
        "empirically_useful": False,
        "composition_authorized": False,
        "next_recommendation": "TARGETED_SOURCE_CLARIFICATION_OR_HISTORICAL_TRANSIT_FOUNDATION",
    }


def load_population_from_value(population: dict[str, Any]) -> None:
    if population.get("population_id") != POPULATION_ID or population.get("population_hash") != POPULATION_HASH:
        raise AssertionError("POP-001 population hash lock failed")
    if population.get("outcome_fields_present") is not False or population.get("outcome_joins_performed") is not False:
        raise AssertionError("outcome-free invariant failed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("population", type=Path)
    parser.add_argument("registry", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    population = load_population(args.population)
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    result = run(population, registry)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"selected": result["selected_primitive_id"], "attempts": len(result["attempts"]), "resolved": result["resolved"], "prevalence_entered": result["prevalence_entered"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
