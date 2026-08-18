"""Governed stop-condition tests for Ashtakavarga remediation."""

from scripts.veda_calc_ashtakavarga_remediation_001 import audit


def test_frozen_contract_and_source_matrix_are_complete_and_hash_stable():
    result = audit()
    assert result["contract"]["hash_verified"] is True
    assert result["source_matrix"]["hash_verified"] is True
    assert result["source_matrix"]["coverage_complete"] is True
    assert result["source_matrix"]["rows"] == 768


def test_remediation_stops_on_contract_total_inconsistency():
    result = audit()
    assert result["decision"] == "CANONICAL_CONTRACT_INCONSISTENT"
    assert result["computed_invariants"]["planetary_sav_total"] == 336
    assert result["computed_invariants"]["lagna_bav_total"] == 49
    assert result["computed_invariants"]["combined_total"] == 385
    assert result["computed_invariants"]["invariant_failures"] == [
        {"invariant": "ordinary_planetary_sav", "expected": 337, "actual": 336},
        {"invariant": "lagna_combined_display", "expected": 386, "actual": 385},
    ]
    assert result["production_change"] is False
