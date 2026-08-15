import json
from pathlib import Path

from scripts.veda_place_resolution import validate_place_resolution


def test_governed_place_resolution_has_valid_coordinates():
    payload = json.loads(Path("data/veda/research/empirical/ogdb_place_resolution.json").read_text(encoding="utf-8"))
    result = validate_place_resolution(payload)
    assert result["status"] == "PASS"
    assert result["chart_ready"] == 10
