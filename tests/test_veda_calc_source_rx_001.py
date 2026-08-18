"""Focused deterministic tests for VEDA-CALC-SOURCE-RX-001."""

from scripts.veda_calc_source_rx_001 import build_bundle, source_positions


def test_source_ashtakavarga_matrix_is_complete_and_unique():
    result = build_bundle()
    assert result["source"]["target_count"] == 8
    assert result["source"]["reference_point_count"] == 8
    assert len(result["source"]["rows"]) == 8 * 12 * 8
    keys = {(row["target"], row["contributor"], row["relative_position"]) for row in result["source"]["rows"]}
    assert len(keys) == len(result["source"]["rows"])
    assert set(source_positions()) == {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Lagna"}


def test_current_ashtakavarga_remains_unvalidated_and_structurally_distinct():
    result = build_bundle()
    current = result["current_ashtakavarga"]
    assert current["runtime_status"] == "IMPLEMENTED_UNVALIDATED"
    assert current["lagna_target"] is False
    assert current["reductions"] == {"trikona_shodhana": False, "ekadhipatya_shodhana": False, "pinda_shodhana": False}
    assert result["ashtakavarga_diff"]["current_has_no_source_exact_match"] is True


def test_d20_source_resolution_is_gated_and_diagnostic_only():
    result = build_bundle()
    d20 = result["d20_current"]
    assert d20["division"] == 20
    assert d20["division_size_degrees"] == "1.5"
    assert d20["starting_signs"] == {"dual": "Leo", "fixed": "Sagittarius", "movable": "Aries"}
    assert d20["interpretation_status"] == "NOT_VALIDATED"
    assert result["source_decisions"]["d20"] == "D20_SOURCE_UNRESOLVED"
    assert result["d20_impact"]["cases"] == 240


def test_audit_is_deterministic_and_has_no_predictive_activation():
    first = build_bundle()
    second = build_bundle()
    assert first["bundle_hash"] == second["bundle_hash"]
    content = str(first).lower()
    assert "outcomes" in content
    assert "pred-m4" not in content
    assert "production_runtime_change': 'none" in content
