"""Focused production conformance tests for Ashtakavarga V2 remediation."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import jsonschema

from engines.ai.knowledge.ashtakavarga_contract_v2 import (
    CONTRACT_HASH,
    CONTRACT_ID,
    SOURCE_MATRIX_HASH,
    normalized_cells,
)
from engines.ai.knowledge.shadbala_engine import (
    ASHTAKAVARGA_RUNTIME_VALIDATED,
    calculate_bav,
    calculate_bav_legacy,
    calculate_lagna_bav,
    calculate_sav,
    calculate_sav_legacy,
)

ROOT = Path(__file__).parents[1]


def _harness():
    path = ROOT / "scripts/veda_calc_ashtakavarga_remediation_rx2_001.py"
    spec = importlib.util.spec_from_file_location("ashtakavarga_remediation_rx2", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _chart() -> dict[str, int]:
    return {name: ((index * 3 + 2) % 12) + 1 for index, name in enumerate(("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Lagna"))}


def test_contract_binding_and_source_matrix_are_immutable():
    contract = json.loads((ROOT / "docs/current-state/calc-ashtakavarga-contract-rx2-001/03_V2_CANONICAL_CONTRACT.json").read_text(encoding="utf-8"))
    assert contract["CONTRACT_ID"] == CONTRACT_ID
    assert contract["CONTRACT_HASH"] == CONTRACT_HASH
    assert contract["SOURCE_MATRIX_HASH"] == SOURCE_MATRIX_HASH
    assert len(normalized_cells()) == 768


def test_production_table_matches_independent_source_matrix():
    result = _harness().build()
    assert result["table_conformance"]["exact_matches"] is True
    assert result["table_conformance"]["mismatch_count"] == 0
    assert result["table_conformance"]["target_totals"] == {
        "Sun": 49,
        "Moon": 49,
        "Mars": 39,
        "Mercury": 54,
        "Jupiter": 54,
        "Venus": 52,
        "Saturn": 39,
        "Lagna": 49,
    }


def test_99_synthetic_charts_match_bav_sav_lagna_and_combined_oracle():
    result = _harness().build()["runtime_comparison"]
    assert result["charts"] == 99
    assert result["planetary_bav_exact"] == 99
    assert result["planetary_sav_exact"] == 99
    assert result["lagna_bav_exact"] == 99
    assert result["combined_exact"] == 99
    assert result["all_exact"] is True


def test_runtime_metadata_and_semantics_are_bound():
    result = calculate_sav(_chart(), include_lagna=True)
    assert result["status"] == ASHTAKAVARGA_RUNTIME_VALIDATED
    assert result["contract_id"] == CONTRACT_ID
    assert result["contract_hash"] == CONTRACT_HASH
    assert result["source_matrix_hash"] == SOURCE_MATRIX_HASH
    assert result["ordinary_sav_excludes_lagna"] is True
    assert result["lagna_bav"]["total_bindus"] == sum(item["bindus"] for item in result["lagna_bav"]["rashis"])
    assert result["combined_total_bindus"] == result["total_bindus"] + result["lagna_bav"]["total_bindus"]
    assert result["combined_label"] == "RAW_SAV_WITH_LAGNA_COMBINED"


def test_lagna_and_node_policies_are_explicit():
    chart = _chart()
    lagna = calculate_lagna_bav(chart)
    assert lagna["status"] == ASHTAKAVARGA_RUNTIME_VALIDATED
    assert calculate_bav("Rahu", chart)["status"] == "UNSUPPORTED_TARGET"
    assert calculate_bav("Ketu", chart)["status"] == "UNSUPPORTED_TARGET"
    partial = calculate_bav("Sun", {key: value for key, value in chart.items() if key != "Lagna"})
    assert partial["status"] == "INSUFFICIENT_DATA"
    assert "Lagna" in partial["missing_inputs"]


def test_legacy_route_remains_replayable_and_is_not_default():
    chart = _chart()
    assert calculate_bav_legacy("Sun", chart)["calculation_version"] == "P018-R2-BAV-001"
    assert calculate_sav_legacy(chart)["calculation_version"] == "P018-R2-SAV-001"
    assert calculate_sav(chart)["calculation_version"] == "P018-SAV-BPHS-V2"


def test_result_schema_accepts_bound_metadata():
    result = calculate_bav("Sun", _chart())
    schema = json.loads((ROOT / "schemas/astrology/ashtakavarga_result.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(result, schema)
