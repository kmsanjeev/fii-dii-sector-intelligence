"""Focused acceptance tests for VEDA-CALC-JYOTISHA-CORE-001."""

from pathlib import Path

from scripts.veda_calc_jyotisha_core_001 import (
    OUT,
    build_bundle,
    independent_varga,
    source_matrix,
)


def test_d1_and_varga_reference_harness_is_complete_and_deterministic():
    first = build_bundle()
    second = build_bundle()
    assert first["hash"] == second["hash"]
    assert first["d1"]["failed"] == 0
    assert first["vargas"]["all_pass"] is True
    assert first["vargas"]["summary"]["D9"] == {"cases": 108, "passed": 108, "failed": 0}
    assert first["vargas"]["summary"]["D10"] == {"cases": 120, "passed": 120, "failed": 0}
    assert independent_varga(0.0, 20, "d20_vimshamsha_bphs_category_start_v1") == "Aries"


def test_dasha_and_antardasha_contract_is_internally_validated():
    result = build_bundle()["dasha"]
    assert result["standard"]["sequence"] == ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
    assert result["standard"]["total_years"] == 120.0
    assert result["standard"]["period_day_policy"] == "365.25"
    assert result["passed"] == result["cases"] == 32
    assert result["failed"] == 0


def test_ashtakavarga_is_invariant_only_and_not_method_validated():
    result = build_bundle()["ashtakavarga"]
    assert result["passed"] == 1
    assert result["method_status"] == "UNVALIDATED"
    assert result["interpretation_status"] == "NOT_AUTHORIZED"
    row = result["rows"][0]
    assert row["external_numerical_witness"] is False
    assert row["bav_total"] == 6
    assert row["sav_total"] == 38


def test_rule_engine_is_structural_trace_only():
    result = build_bundle()["rules"]
    assert result["passed"] == result["cases"] == 10
    assert result["failed"] == 0
    assert result["production_activation"] == "NOT_EXECUTED"
    assert all(row["interpretation_status"] == "RESEARCH_REQUIRED" for row in result["rows"])


def test_source_matrix_has_primary_locators_and_explicit_limits():
    rows = source_matrix()
    assert any(row["source_id"] == "SRC-BPHS-PDF-CH6-7" and "Ch.6.12-21" in row["locator"] for row in rows)
    assert any(row["source_id"] == "SRC-BPHS-PDF-CH46" and "Ch.46.12-16" in row["locator"] for row in rows)
    assert any("contributor table" in " ".join(row["limitations"]) for row in rows)


def test_generated_governance_artifacts_are_present_and_safe():
    required = {
        "00_BASELINE.md",
        "01_SOURCE_AND_VARIANT_MATRIX.md",
        "02_VARGA_INVENTORY.md",
        "03_VARGA_REFERENCE_REGISTRY.json",
        "04_VARGA_RESULTS.json",
        "05_DASHA_STANDARD.md",
        "06_DASHA_REFERENCE_REGISTRY.json",
        "07_DASHA_RESULTS.json",
        "08_ASHTAKAVARGA_SOURCE_CONTRACT.md",
        "09_ASHTAKAVARGA_RULE_MATRIX.json",
        "10_ASHTAKAVARGA_RESULTS.json",
        "11_RULE_ENGINE_SOURCE_TRACEABILITY.json",
        "12_RULE_ENGINE_RESULTS.json",
        "13_COMPONENT_GOLD_REGISTRY.json",
        "14_EXPECTED_CHANGE_REGISTER.json",
        "15_COMPONENT_MATURITY_SCORECARD.md",
        "16_SILVER_STRESS_RESULTS.json",
        "17_LIMITATIONS.md",
        "18_FINAL_ACCEPTANCE.md",
    }
    assert required <= {path.name for path in OUT.iterdir()}
    content = "\n".join(path.read_text(encoding="utf-8") for path in OUT.rglob("*") if path.is_file())
    assert "PRED-M4" in content
    assert "raw ADB" in content or "raw_adb" in content
    assert "prediction" in content.lower()
    assert "data/research/adb-sample-001" not in content
