from __future__ import annotations

import json
from pathlib import Path

from scripts.veda_calc_ashtakavarga_decision_001 import (
    OUT,
    canonical_sha,
    compute_bundle,
    load_source_contract,
    reference_bav,
    reference_sav,
)


def test_source_contract_is_complete_and_independent_reference_is_deterministic():
    data, index = load_source_contract()
    assert len(data["rows"]) == 768
    chart = {name: ((offset * 3) % 12) + 1 for offset, name in enumerate(["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Lagna"])}
    assert sum(reference_bav("Sun", chart, index).values()) >= 0
    assert sum(reference_sav(chart, index).values()) >= 0
    first = compute_bundle()
    second = compute_bundle()
    assert canonical_sha(first) == canonical_sha(second)


def test_comparison_exposes_current_contract_gap_without_activation():
    bundle = compute_bundle()
    assert bundle["decisions"]["production_change"] is False
    assert bundle["decisions"]["overall"] == "ASHTAKAVARGA_REMEDIATION_SPEC_READY"
    assert bundle["cell_comparison"]["classification_counts"]["TARGET_NOT_IMPLEMENTED"] == 96
    assert bundle["cell_comparison"]["numeric_or_policy_mismatches"] > 0
    assert bundle["runtime"]["status"] == "IMPLEMENTED_UNVALIDATED"


def test_governance_artifacts_have_expected_status_and_no_raw_data():
    assert OUT.exists()
    acceptance = (OUT / "17_FINAL_ACCEPTANCE.md").read_text(encoding="utf-8")
    assert "PASS_WITH_CONDITION" in acceptance
    assert not list(OUT.glob("*.csv"))
    runtime = json.loads((OUT / "01_RUNTIME_METHOD_FREEZE.json").read_text(encoding="utf-8"))
    assert runtime["self_contributor"] == "excluded by runtime"
    assert runtime["lagna_target"] is False
