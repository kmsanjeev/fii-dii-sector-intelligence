from __future__ import annotations

import json
from pathlib import Path

from engines.ai.knowledge.astrology_calculation_validation import validate_exported_bundle


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "veda" / "validation" / "calculations"


def _load_json(name: str):
    with open(DATA_ROOT / name, encoding="utf-8") as handle:
        return json.load(handle)


def test_p004_export_bundle_is_current():
    report = validate_exported_bundle(ROOT)
    assert report["is_valid"] is True
    assert report["missing_files"] == []
    assert report["mismatched_files"] == []


def test_p004_summary_captures_foundational_conditions():
    payload = _load_json("p004_summary.json")
    summary = payload["summary"]
    swisseph = payload["meta"]["swisseph"]

    assert summary["reference_fixture_count"] == 25
    assert summary["validation_record_count"] == 650
    assert summary["issue_count"] == 5
    assert summary["lagna_boundary_discrepancy_present"] is True
    assert summary["production_astrology_behaviour_changed"] == "NO"
    assert swisseph["sidereal_mode"] == "SIDM_LAHIRI"
    assert swisseph["node_method"] == "TRUE_NODE"
    assert swisseph["active_ephemeris_mode"] == "MOSEPH"


def test_p004_timezone_validation_preserves_material_dst_findings():
    rows = {row["case_id"]: row for row in _load_json("p004_timezone_validation.json")}

    assert rows["TZ-NYSE-WINTER"]["result"] == "VALIDATED"
    assert rows["TZ-NYSE-SUMMER"]["utc_delta_hours"] == 1.0
    assert rows["TZ-NYSE-SUMMER"]["lagna_longitude_delta_deg"] > 10.0
    assert rows["TZ-LSE-SUMMER"]["utc_delta_hours"] == 1.0
    assert rows["TZ-ASX-SUMMER"]["utc_delta_hours"] == 1.0
    assert rows["TZ-PAK-1947"]["utc_delta_hours"] == 0.0
    assert rows["TZ-PAK-1947"]["result"] == "VALIDATED"


def test_p004_issue_register_contains_expected_issue_ids():
    issues = {row["issue_id"]: row for row in _load_json("p004_issue_register.json")}

    assert set(issues) == {
        "VEDA-CALC-ISSUE-0001",
        "VEDA-CALC-ISSUE-0002",
        "VEDA-CALC-ISSUE-0003",
        "VEDA-CALC-ISSUE-0004",
        "VEDA-CALC-ISSUE-0005",
    }
    assert issues["VEDA-CALC-ISSUE-0001"]["severity"] == "HIGH"
    assert "Moshier fallback" in issues["VEDA-CALC-ISSUE-0001"]["title"]
    assert issues["VEDA-CALC-ISSUE-0002"]["severity"] == "HIGH"
    assert issues["VEDA-CALC-ISSUE-0003"]["severity"] == "MEDIUM"


def test_p004_varga_matrix_matches_active_runtime_surface():
    rows = {row["varga"]: row for row in _load_json("p004_varga_matrix.json")}

    assert rows["D9"]["personal"] == "SURFACED"
    assert rows["D10"]["personal"] == "SURFACED"
    assert rows["D11"]["personal"] == "NOT_SURFACED"
    assert rows["D30"]["rest"] == "SURFACED"
    assert rows["D60"]["status"] == "VALIDATED_WITH_CONDITIONS"
