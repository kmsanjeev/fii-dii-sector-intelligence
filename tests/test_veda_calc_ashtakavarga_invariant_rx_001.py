import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/veda_calc_ashtakavarga_invariant_rx_001.py"


def load_module():
    spec = importlib.util.spec_from_file_location("veda_calc_ashtakavarga_invariant_rx_001", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_source_matrix_freeze_and_independent_reconstruction_agree():
    module = load_module()
    bundle = module.build()
    freeze = bundle["source_matrix_freeze"]
    reconstruction = bundle["independent_reconstruction"]
    assert freeze["rows"] == 768
    assert freeze["coverage_complete"] is True
    assert freeze["hash_verified"] is True
    assert reconstruction["matches_frozen_matrix"] is True
    assert reconstruction["rows_hash"] == freeze["recorded_rows_hash"]


def test_bphs_totals_are_336_and_385_not_contract_337_and_386():
    module = load_module()
    bundle = module.build()
    totals = bundle["totals"]
    assert totals["independent_totals_agree"] is True
    assert totals["planetary_sav"] == 336
    assert totals["lagna_bav"] == 49
    assert totals["combined_display"] == 385
    assert bundle["decision"] == "ASHTAKAVARGA_CURRENT_CANONICAL_IS_INVALID_HYBRID"


def test_all_56_phaladeepika_pairs_are_audited_without_merging_methods():
    module = load_module()
    bundle = module.build()
    summary = bundle["pair_summary"]
    assert summary["pairs_expected"] == 56
    assert summary["pairs_audited"] == 56
    assert summary["exact_matches"] == 49
    assert summary["count_variants"] == 6
    assert summary["same_count_position_variants"] == 1
    assert summary["phala_total"] == 336


def test_varahamihira_variant_is_preserved_as_a_conflict():
    module = load_module()
    variant = module.build()["varahamihira_delta"]
    assert variant["source_conflict_id"] == "CSR-001"
    assert variant["main_text_positions"] == [1, 2, 4, 7, 8, 10, 11]
    assert variant["varahamihira_alternative_positions"] == [1, 4, 7, 8, 10, 11, 12]


def test_v1_is_not_mutated_and_v2_candidate_is_non_production(tmp_path):
    module = load_module()
    before = json.loads(module.CONTRACT.read_text(encoding="utf-8"))
    module.export(module.build())
    after = json.loads(module.CONTRACT.read_text(encoding="utf-8"))
    candidate = json.loads((module.OUT / "15_CANONICAL_CONTRACT_V2.json").read_text(encoding="utf-8"))
    assert after == before
    assert candidate["status"] == "RESEARCH_CANDIDATE_NOT_PRODUCTION"
    assert candidate["planetary_sav_total"] == 336
    assert candidate["combined_display_total"] == 385
