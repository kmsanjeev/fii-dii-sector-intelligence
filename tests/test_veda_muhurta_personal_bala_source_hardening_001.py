"""Independent non-production tests for personal-Bala source hardening."""

from scripts.veda_muhurta_personal_bala_oracle import (
    build_chandra_oracle_matrix,
    build_tara_oracle_matrix,
    compose_personal_factors,
    evaluate_chandra_bala,
    evaluate_tara_bala,
)


def test_tara_exhaustive_matrix_is_deterministic_and_complete():
    first = build_tara_oracle_matrix()
    second = build_tara_oracle_matrix()
    assert len(first) == 729
    assert first == second
    assert {row["category"] for row in first} == {
        "JANMA", "SAMPAT", "VIPAT", "KSHEMA", "PRATYARI",
        "SADHAKA", "NAIDHANA", "MITRA", "PARAMA_MITRA",
    }


def test_tara_identity_and_wrap_boundaries():
    assert evaluate_tara_bala(1, 1)["inclusive_count"] == 1
    assert evaluate_tara_bala(27, 1)["inclusive_count"] == 2
    assert evaluate_tara_bala(1, 27)["inclusive_count"] == 27
    assert evaluate_tara_bala(1, 9)["category"] == "PARAMA_MITRA"
    assert evaluate_tara_bala(1, 7)["hard_exclusion"] is False


def test_chandra_exhaustive_matrix_and_positions():
    matrix = build_chandra_oracle_matrix()
    assert len(matrix) == 144
    assert {row["inclusive_house_count"] for row in matrix} == set(range(1, 13))
    assert evaluate_chandra_bala(1, 1)["effect"] == "SUPPORTIVE"
    assert evaluate_chandra_bala(1, 11)["inclusive_house_count"] == 11
    assert evaluate_chandra_bala(12, 1)["inclusive_house_count"] == 2


def test_chandra_paksha_variant_is_explicit_and_isolated():
    standard = evaluate_chandra_bala(1, 2, paksha="SHUKLA")
    variant = evaluate_chandra_bala(1, 2, paksha="SHUKLA", variant="PAKSHA_CONDITIONAL")
    assert standard["effect"] == "NEUTRAL"
    assert variant["effect"] == "SUPPORTIVE_WITH_VARIANT_CONDITION"
    assert build_chandra_oracle_matrix("STANDARD_1_3_6_7_10_11") == build_chandra_oracle_matrix(
        "STANDARD_1_3_6_7_10_11"
    )


def test_composition_is_qualitative_and_preserves_missing_personal_data():
    assert compose_personal_factors(None, None)["personal_factor_state"] == "PERSONAL_FACTOR_UNAVAILABLE"
    tara = evaluate_tara_bala(1, 2)
    chandra = evaluate_chandra_bala(1, 1)
    result = compose_personal_factors(tara, chandra)
    assert result["personal_factor_state"] == "BOTH_SUPPORTIVE"
    assert result["numeric_score"] is None
    assert result["hidden_weights"] is False
