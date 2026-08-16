import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_rebaseline_lane_ranking_and_negative_evidence_are_deterministic():
    matrix = json.loads((ROOT / "docs/current-state/timing-rebaseline-001/01_RESEARCH_LANE_MATRIX.json").read_text(encoding="utf-8"))
    totals = [row["total"] for row in matrix["lanes"]]
    assert max(totals) == 34
    assert next(row for row in matrix["lanes"] if row["lane"] == "FEATURE_LEVEL_EMPIRICAL_ANALYSIS")["recommendation"] == "PRIMARY"
    negative = json.loads((ROOT / "docs/current-state/timing-rebaseline-001/02_NEGATIVE_EVIDENCE_REGISTER.json").read_text(encoding="utf-8"))
    assert len(negative["entries"]) >= 8
    assert any(item["hypothesis"] == "PRIM-001/002 interval mechanics" and item["result"] == "100% prevalence" for item in negative["entries"])
    manifest = json.loads((ROOT / "docs/current-state/timing-rebaseline-001/06_AUDIT_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["recommended_next_programme"] == "VEDA-EMP-FEATURE-001"
    assert manifest["useful_timing_primitives"] == 0
    assert manifest["rag_changed"] is False
