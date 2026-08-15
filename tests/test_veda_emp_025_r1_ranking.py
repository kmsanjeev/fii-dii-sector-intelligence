import json
from pathlib import Path

from scripts.veda_emp_025_r1_ranking import build_ranking


def test_ranking_excludes_astrology_and_preserves_lane_fields():
    payload = json.loads(Path("data/veda/research/empirical/ogdb_pilot_1000.json").read_text(encoding="utf-8"))
    result = build_ranking(payload, limit=10)
    assert result["screened"] == 1000
    assert "LEADERSHIP" in result["lanes"]
    assert all(item["astrology_used_for_selection"] is False for item in result["records"])
