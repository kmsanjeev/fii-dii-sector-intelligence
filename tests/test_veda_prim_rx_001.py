import json
import subprocess
import sys
from pathlib import Path

from scripts.veda_prim_rx_001 import POPULATION_HASH, SOURCE_BLOCKED_IDS, load_population, run

ROOT = Path(__file__).resolve().parents[1]
POPULATION = ROOT / "data/veda/research/populations/veda_pop_ogdb_001.json.gz"
REGISTRY = ROOT / "docs/current-state/know-timing-002/04_timing_primitive_registry.json"


def test_all_source_blocked_candidates_receive_precise_bounded_attempts():
    result = run(load_population(POPULATION), json.loads(REGISTRY.read_text(encoding="utf-8")))
    assert result["population_hash_verified"] is True
    assert result["selected_primitive_id"] == "VEDA-TIMING-PRIM-003"
    assert [row["primitive_id"] for row in result["attempts"]] == SOURCE_BLOCKED_IDS
    assert all(row["resolution"] == "UNRESOLVED" for row in result["attempts"])
    assert all(row["contract"] == "NOT_CREATED" for row in result["attempts"])
    assert result["prevalence_entered"] is False
    assert result["composition_authorized"] is False


def test_script_is_deterministic_and_hash_locked(tmp_path):
    first, second = tmp_path / "a.json", tmp_path / "b.json"
    command = [sys.executable, "scripts/veda_prim_rx_001.py", str(POPULATION), str(REGISTRY), str(first)]
    a = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    command[-1] = str(second)
    b = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    assert first.read_bytes() == second.read_bytes()
    assert json.loads(a.stdout)["resolved"] is False
    assert json.loads(b.stdout)["prevalence_entered"] is False
    assert POPULATION_HASH in first.read_text(encoding="utf-8")
