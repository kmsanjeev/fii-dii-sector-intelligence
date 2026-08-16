import json
from pathlib import Path

from scripts.veda_prim_011_rx import POPULATION_HASH, audit, load_population

ROOT = Path(__file__).resolve().parents[1]


def test_prim_011_source_scope_closes_without_prevalence_or_rule_creation():
    result = audit(
        json.loads((ROOT / "docs/current-state/know-timing-002/04_timing_primitive_registry.json").read_text(encoding="utf-8")),
        load_population(ROOT / "data/veda/research/populations/veda_pop_ogdb_001.json.gz"),
    )
    assert result["population_hash"] == POPULATION_HASH
    assert result["source_resolution"] == "UNRESOLVED"
    assert result["contract_frozen"] is False
    assert result["evaluator_created"] is False
    assert result["prevalence_entered"] is False
    assert result["rebaseline_triggered"] is True
    assert result["composition_authorized"] is False
