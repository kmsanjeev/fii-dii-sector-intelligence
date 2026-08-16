"""Close the final PRIM-011 source-scope audit without changing transit code."""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
from typing import Any

POPULATION_HASH = "10e8debb06afa0280aa1523a7fba0c868788871d4a7736e9358584582b400863"
TRANSIT_ARTIFACT_HASH = "0bd8cb9a4dba25794eeec5724e8ddafc9ad63cd90962be7c0fa70e3a55b66446"


def load_population(path: Path) -> dict[str, Any]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        population = json.load(handle)
    if population.get("population_hash") != POPULATION_HASH:
        raise AssertionError("POP-001 hash lock failed")
    if population.get("outcome_fields_present") is not False or population.get("outcome_joins_performed") is not False:
        raise AssertionError("outcome-free invariant failed")
    return population


def audit(registry: dict[str, Any], population: dict[str, Any]) -> dict[str, Any]:
    row = next(item for item in registry["primitives"] if item["primitive_id"] == "VEDA-TIMING-PRIM-011")
    if row["implementation_status"] != "IMPLEMENTABLE_WITH_CONDITION":
        raise AssertionError("PRIM-011 registry state changed unexpectedly")
    return {
        "programme": "VEDA-PRIM-011-RX",
        "primitive_id": row["primitive_id"],
        "before": "CALCULATION_READY_SOURCE_SCOPE_PENDING",
        "source_resolution": "UNRESOLVED",
        "final_state": "PRIM_011_SOURCE_SCOPE_UNRESOLVED_AFTER_CALCULATION_READY",
        "population_hash": population["population_hash"],
        "transit_artifact_hash": TRANSIT_ARTIFACT_HASH,
        "source_question": "Does a specified transit planet acting on a specified natal target through an explicitly defined relationship produce a specified result within a defined timing domain?",
        "source_records": [
            {
                "source_id": "KT-PHD-001",
                "source": "Phaladeepika",
                "edition": "G.S. Kapoor English translation/commentary PDF",
                "location": "Chapter 16 / transit-related governed record; existing record cites §35",
                "source_class": "PRIMARY_CLASSICAL_TRANSLATION",
                "translation": "Existing governed paraphrase describes a narrow transit conjunction involving Lagna lord and a relevant house lord with a strength qualification.",
                "ambiguity": "The accessible source record does not freeze which event-specific house is relevant, a deterministic strength rule, or timing granularity. The exact passage-level contract remains unverified at the required precision.",
                "result": "SOURCE_SCOPE_UNRESOLVED"
            },
            {
                "source_id": "KT-BPHS-TRANSIT-CATALOGUE",
                "source": "Brihat Parashara Hora Shastra",
                "edition": "Accessible English translation PDF",
                "location": "Transit chapters and Ashtakavarga transit material",
                "source_class": "PRIMARY_CLASSICAL_TRANSLATION",
                "translation": "Transit effects are discussed through specific frameworks and conditions.",
                "ambiguity": "No exact PRIM-011 target/relationship/event contract was established; generic transit doctrine cannot fill the registry placeholders.",
                "result": "SOURCE_SCOPE_UNRESOLVED"
            }
        ],
        "required_elements": {
            "transit_planet": "Jupiter or Saturn available; source does not select one for this generic row",
            "natal_target": "UNRESOLVED",
            "relationship": "UNRESOLVED",
            "event_scope": "UNRESOLVED / OTHER",
            "strength_rule": "UNRESOLVED",
            "timing_domain": "UNRESOLVED"
        },
        "contract_frozen": False,
        "evaluator_created": False,
        "positive_reachable": False,
        "negative_reachable": False,
        "indeterminate_reachable": True,
        "prevalence_entered": False,
        "empirically_useful": False,
        "rebaseline_triggered": True,
        "next_priority": "VEDA-TIMING-RESEARCH-REBASELINE-001",
        "composition_authorized": False,
        "production_changed": False,
        "rag_changed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("population", type=Path)
    parser.add_argument("registry", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = audit(json.loads(args.registry.read_text(encoding="utf-8")), load_population(args.population))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"primitive_id": result["primitive_id"], "state": result["final_state"], "rebaseline": result["rebaseline_triggered"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
