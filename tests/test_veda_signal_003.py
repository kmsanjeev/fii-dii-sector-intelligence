import json
import subprocess
import sys
from pathlib import Path


def test_signal_003_is_a_deterministic_no_signal_gate(tmp_path: Path) -> None:
    output = tmp_path / "signal_003.json"
    command = [sys.executable, "scripts/veda_signal_003_viability_audit.py", str(output)]
    first = subprocess.run(command, check=True, capture_output=True, text=True)
    first_bytes = output.read_bytes()
    second = subprocess.run(command, check=True, capture_output=True, text=True)
    assert first_bytes == output.read_bytes()
    assert json.loads(first.stdout)["signal_found"] is False
    assert json.loads(second.stdout)["status"] == "COMPLETED_NO_VIABLE_THIRD_SIGNAL"
    audit = json.loads(output.read_text(encoding="utf-8"))
    assert audit["success_path"] == "B"
    assert len(audit["families"]) == 4
    assert all(item["source_status"] == "SOURCE_PARTIAL" for item in audit["families"])
    assert audit["production_changes"] == "NONE"
    assert audit["approved_core"] == "UNCHANGED"
