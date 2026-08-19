"""Deterministic state gates for the calculation-lane rebaseline."""

import hashlib

from scripts.veda_calculation_lane_rebaseline_001 import OUT, build, emit


def test_rebaseline_inventory_and_rx2_state_are_current():
    bundle = build()
    assert bundle["starting_commit"] == "f22a6998c200ee15da6dc951c40efbd1a38df1ea"
    assert bundle["production_code_changed"] is False
    assert bundle["ashtakavarga"]["decision"] == "ASHTAKAVARGA_V2_RAW_RUNTIME_REMEDIATED_WITH_LEGACY_COMPATIBILITY"
    assert bundle["ashtakavarga"]["source_cells"] == 768
    assert bundle["ashtakavarga"]["source_exact"] is True
    assert bundle["ashtakavarga"]["synthetic"]["all_exact"] is True
    assert any(row["family"] == "D20_vimshamsha" and row["capability_class"] == "PARTIALLY_VALIDATED" for row in bundle["inventory"])
    assert any(row["family"] == "ashtakavarga_raw_bav_sav" and row["capability_class"] == "COMPLETE_WITH_CONDITION" for row in bundle["inventory"])
    assert bundle["primary_decision"]["programme_id"] == "VEDA-KNOWLEDGE-SOURCE-WITNESS-STANDARD-001"
    assert bundle["primary_decision"]["automatically_started"] is False


def test_rebaseline_preserves_governance_boundaries():
    bundle = build()
    assert bundle["governance"] == {
        "approved_core_before": 17,
        "approved_core_after": 17,
        "rag_changed": False,
        "rag_rebuild": False,
        "prediction_changed": False,
        "pred_m4": "UNCHANGED",
        "ml": "LOCKED",
        "external_evidence_changed": False,
        "human_validation": "COMM-002/GROUP-001 PENDING",
        "emp_001": "ACTIVE LONGITUDINAL",
    }
    assert not any(item["selected"] and item["autonomous"] == "NO" for item in bundle["candidates"])
    assert not any(item["selected"] and item["id"] in {"VEDA-CALC-D20-SOURCE-RECONCILIATION-001", "VEDA-KNOW-MUHURTA-BALA-001"} for item in bundle["candidates"])


def test_rebaseline_artifacts_are_deterministic(tmp_path):
    first = build()
    emit(first)
    names = sorted(path.name for path in OUT.iterdir() if path.is_file())
    before = {name: hashlib.sha256((OUT / name).read_bytes()).hexdigest() for name in names}
    emit(build())
    after = {name: hashlib.sha256((OUT / name).read_bytes()).hexdigest() for name in names}
    assert before == after
    assert names == [
        "00_BASELINE.md", "01_CALCULATION_INVENTORY.json", "02_CALCULATION_MATURITY_MATRIX.json",
        "03_SOURCE_READINESS_MATRIX.json", "04_CONSUMER_MAP.json", "05_STOP_DEFER_FREEZE_REGISTER.json",
        "06_HIGH_VALUE_GAPS.md", "07_NEXT_PROGRAMME_CANDIDATES.json", "08_PRIMARY_NEXT_DECISION.md",
        "09_SOURCE_WITNESS_STANDARD_ASSESSMENT.md", "10_PARALLEL_LANE_STATE.md", "11_ROADMAP_SYNCHRONIZATION.md",
        "12_FINAL_ACCEPTANCE.md",
    ]
