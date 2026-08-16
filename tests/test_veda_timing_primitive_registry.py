import json
import subprocess
import sys
from pathlib import Path


def test_timing_primitive_registry_is_deterministic_and_non_composite(tmp_path: Path) -> None:
    output = tmp_path / "registry.json"
    command = [sys.executable, "scripts/veda_timing_primitive_registry.py", str(output)]
    first = subprocess.run(command, check=True, capture_output=True, text=True)
    first_bytes = output.read_bytes()
    second = subprocess.run(command, check=True, capture_output=True, text=True)
    assert first_bytes == output.read_bytes()
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["registry_id"] == "VEDA_TIMING_PRIMITIVE_REGISTRY"
    assert payload["primitive_count"] >= 10
    assert payload["status"] == "RESEARCH_ONLY_NO_COMPOSITE_SIGNAL"
    assert payload["prevalence_audited"] == ["VEDA-TIMING-PRIM-001", "VEDA-TIMING-PRIM-002"]
    assert payload["production_changes"] == "NONE"
    assert json.loads(first.stdout)["primitive_count"] == json.loads(second.stdout)["primitive_count"]
    assert all(item["primitive_id"] for item in payload["primitives"])
