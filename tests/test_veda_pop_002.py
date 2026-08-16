import json
import subprocess
import sys
from pathlib import Path

from scripts.veda_pop_002 import CONDITIONS, CONDITIONAL_IDS, POPULATION_HASH, audit, read_population


ROOT = Path(__file__).resolve().parents[1]
POPULATION = ROOT / "data/veda/research/populations/veda_pop_ogdb_001.json.gz"
REGISTRY = ROOT / "docs/current-state/know-timing-002/04_timing_primitive_registry.json"


def test_conditional_audit_locks_population_and_source_gates():
    population = read_population(POPULATION)
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    result = audit(population, registry)
    assert population["population_hash"] == POPULATION_HASH
    assert result["conditional_candidates"] == 7
    assert result["audited"] == 0
    assert result["summary"]["empirically_useful_count"] == 0
    assert {row["primitive_id"] for row in result["rows"]} == CONDITIONAL_IDS
    assert all(row["indeterminate_fixture"]["status"] == "REACHABLE" for row in result["rows"])
    assert all(row["positive_fixture"]["status"] == "NOT_EXECUTED_BLOCKED" for row in result["rows"])


def test_prevalence_band_and_script_are_deterministic(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    command = [sys.executable, "scripts/veda_pop_002.py", str(POPULATION), str(REGISTRY), str(first)]
    a = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    command[-1] = str(second)
    b = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    assert first.read_bytes() == second.read_bytes()
    assert json.loads(a.stdout)["audited"] == 0
    assert json.loads(b.stdout)["empirically_useful"] == 0
