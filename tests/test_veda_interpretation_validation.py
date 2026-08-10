from __future__ import annotations

import json
from pathlib import Path

from engines.ai.knowledge.astrology_interpretation_validation import validate_exported_bundle


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "veda" / "validation" / "interpretations"


def _load_json(name: str):
    with open(DATA_ROOT / name, encoding="utf-8") as handle:
        return json.load(handle)


def test_p005_export_bundle_is_current():
    report = validate_exported_bundle(ROOT)
    assert report["is_valid"] is True
    assert report["missing_files"] == []
    assert report["mismatched_files"] == []


def test_p005_summary_captures_interpretation_baseline():
    payload = _load_json("p005_summary.json")
    summary = payload["summary"]
    samples = payload["runtime_samples"]

    assert summary["phase_id"] == "VEDA-P005"
    assert summary["phase_date"] == "2026-08-10"
    assert summary["surface_count"] == 14
    assert summary["legacy_rule_count"] == 32
    assert summary["source_validated_count"] == 1
    assert summary["high_stakes_count"] == 5
    assert summary["p0_high_stakes_count"] == 3
    assert summary["complete_trace_count"] == 1
    assert summary["incomplete_trace_count"] == 5
    assert summary["production_astrology_behaviour_changed"] == "NO"
    assert summary["production_rules_migrated"] == 0
    assert summary["final_verdict"] == "PASS WITH CONDITIONS"

    assert samples["personal"]["lagna"] == "Libra"
    assert samples["personal"]["mahadasha"] == "Saturn"
    assert samples["personal"]["antardasha"] == "Jupiter"
    assert samples["personal"]["yoga_names"] == ["Sasa Yoga", "Kemadruma Yoga"]
    assert samples["personal"]["dosha_names"] == ["Shani Dosha"]
    assert samples["personal"]["report_sections"]["finance"] is True
    assert samples["personal"]["report_sections"]["marriage"] is True
    assert samples["personal"]["report_sections"]["health"] is True
    assert samples["personal"]["report_sections"]["longevity"] is True
    assert samples["personal"]["report_sections"]["current_period"] is True
    assert samples["personal"]["report_sections"]["remedies"] is True

    assert samples["rest_human"]["interpretation_signal"] == "Cautionary astrology heuristic"
    assert samples["stock"]["interpretation_signal"] == "Strong positive astrology heuristic"
    assert samples["country"]["interpretation_signal"] == "Strong positive astrology heuristic"


def test_p005_surface_inventory_preserves_key_paths_and_statuses():
    rows = {row["surface_id"]: row for row in _load_json("p005_surface_inventory.json")}

    assert rows["VEDA-P005-SURF-0001"]["status"] == "HYBRID"
    assert rows["VEDA-P005-SURF-0003"]["status"] == "RULE_BASED"
    assert rows["VEDA-P005-SURF-0005"]["status"] == "DETERMINISTIC"
    assert rows["VEDA-P005-SURF-0009"]["status"] == "LLM_SYNTHESIZED"
    assert rows["VEDA-P005-SURF-0010"]["status"] == "RULE_BASED"
    assert rows["VEDA-P005-SURF-0007"]["domain"] == "STOCK_KUNDLI_FINANCE"
    assert "kundli_interpretator.py::interpret" in " ".join(rows["VEDA-P005-SURF-0007"]["rule_source"])


def test_p005_high_stakes_register_marks_expected_outputs():
    rows = {row["high_stakes_id"]: row for row in _load_json("p005_high_stakes_register.json")}

    assert set(rows) == {
        "VEDA-P005-HS-0001",
        "VEDA-P005-HS-0002",
        "VEDA-P005-HS-0003",
        "VEDA-P005-HS-0004",
        "VEDA-P005-HS-0005",
    }
    assert rows["VEDA-P005-HS-0001"]["classification"] == "FINANCIAL_LIKE"
    assert rows["VEDA-P005-HS-0001"]["severity"] == "P0"
    assert rows["VEDA-P005-HS-0002"]["domain"] == "FINANCE"
    assert rows["VEDA-P005-HS-0004"]["domain"] == "LONGEVITY"
    assert rows["VEDA-P005-HS-0004"]["severity"] == "P0"
    assert rows["VEDA-P005-HS-0005"]["classification"] == "REMEDIAL"


def test_p005_traceability_cases_capture_single_complete_chain():
    rows = {row["trace_case_id"]: row for row in _load_json("p005_traceability_cases.json")}

    assert rows["VEDA-P005-TRACE-0001"]["status"] == "COMPLETE_CHAIN"
    assert rows["VEDA-P005-TRACE-0001"]["rule_ids"] == [
        "VEDA-RUL-DASHA-000001",
        "VEDA-RUL-DASHA-000002",
    ]
    assert rows["VEDA-P005-TRACE-0001"]["claim_ids"] == [
        "VEDA-CLM-000001",
        "VEDA-CLM-000002",
        "VEDA-CLM-000004",
    ]
    assert rows["VEDA-P005-TRACE-0005"]["status"] == "PARTIAL_CHAIN"
    assert rows["VEDA-P005-TRACE-0006"]["status"] == "INCOMPLETE_CHAIN"
    assert rows["VEDA-P005-TRACE-0006"]["missing_links"] == [
        "P002-registered source",
        "claim",
        "passage",
    ]
