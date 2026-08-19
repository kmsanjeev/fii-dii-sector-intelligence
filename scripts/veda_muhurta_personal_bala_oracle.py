"""Independent, non-production Tara/Chandra Bala diagnostic evaluators.

This module is deliberately outside the Muhurta runtime.  It records the
widely repeated calculation candidates so they can be tested independently
while the source-witness and advisory semantics remain source-limited.
"""

from __future__ import annotations

from typing import Any, Mapping


TARA_CATEGORIES = {
    1: "JANMA",
    2: "SAMPAT",
    3: "VIPAT",
    4: "KSHEMA",
    5: "PRATYARI",
    6: "SADHAKA",
    7: "NAIDHANA",
    8: "MITRA",
    0: "PARAMA_MITRA",
}

TARA_EFFECTS = {
    "JANMA": "CAUTION",
    "SAMPAT": "SUPPORTIVE",
    "VIPAT": "CAUTION",
    "KSHEMA": "SUPPORTIVE",
    "PRATYARI": "CAUTION",
    "SADHAKA": "SUPPORTIVE",
    "NAIDHANA": "CAUTION",
    "MITRA": "SUPPORTIVE",
    "PARAMA_MITRA": "SUPPORTIVE",
}

CHANDRA_POSITIONS = {
    1: "SUPPORTIVE",
    2: "NEUTRAL",
    3: "SUPPORTIVE",
    4: "CAUTION",
    5: "NEUTRAL",
    6: "SUPPORTIVE",
    7: "SUPPORTIVE",
    8: "CAUTION",
    9: "NEUTRAL",
    10: "SUPPORTIVE",
    11: "SUPPORTIVE",
    12: "CAUTION",
}


def _bounded_int(value: Any, lower: int, upper: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not lower <= value <= upper:
        raise ValueError(f"{name} must be an integer in {lower}..{upper}")
    return value


def evaluate_tara_bala(janma_nakshatra: int, event_nakshatra: int) -> dict[str, Any]:
    """Evaluate the diagnostic 27-star inclusive-count Navatara candidate."""
    janma = _bounded_int(janma_nakshatra, 1, 27, "janma_nakshatra")
    event = _bounded_int(event_nakshatra, 1, 27, "event_nakshatra")
    count = ((event - janma) % 27) + 1
    remainder = count % 9
    category = TARA_CATEGORIES[remainder]
    return {
        "factor": "TARA_BALA",
        "contract_id": "VEDA-MUH-TARA-DIAGNOSTIC-V1",
        "production_activation": "DISABLED",
        "janma_nakshatra": janma,
        "event_nakshatra": event,
        "inclusive_count": count,
        "remainder_mod_9": remainder,
        "category": category,
        "effect": TARA_EFFECTS[category],
        "hard_exclusion": False,
        "source_state": "SOURCE_SEMANTICS_PARTIAL",
    }


def evaluate_chandra_bala(
    janma_moon_sign: int,
    event_moon_sign: int,
    *,
    paksha: str | None = None,
    variant: str = "STANDARD_1_3_6_7_10_11",
) -> dict[str, Any]:
    """Evaluate the diagnostic 12-sign inclusive-count Chandra candidate."""
    natal = _bounded_int(janma_moon_sign, 1, 12, "janma_moon_sign")
    event = _bounded_int(event_moon_sign, 1, 12, "event_moon_sign")
    if paksha is not None and paksha not in {"SHUKLA", "KRISHNA"}:
        raise ValueError("paksha must be SHUKLA, KRISHNA, or omitted")
    if variant not in {"STANDARD_1_3_6_7_10_11", "PAKSHA_CONDITIONAL"}:
        raise ValueError("unsupported Chandra Bala diagnostic variant")

    relation = ((event - natal) % 12) + 1
    effect = CHANDRA_POSITIONS[relation]
    if variant == "PAKSHA_CONDITIONAL" and paksha:
        if paksha == "SHUKLA" and relation in {2, 5, 9}:
            effect = "SUPPORTIVE_WITH_VARIANT_CONDITION"
        elif paksha == "KRISHNA" and relation in {4, 8, 12}:
            effect = "SUPPORTIVE_WITH_VARIANT_CONDITION"
    return {
        "factor": "CHANDRA_BALA",
        "contract_id": "VEDA-MUH-CHANDRA-DIAGNOSTIC-V1",
        "production_activation": "DISABLED",
        "janma_moon_sign": natal,
        "event_moon_sign": event,
        "inclusive_house_count": relation,
        "paksha": paksha,
        "variant": variant,
        "effect": effect,
        "hard_exclusion": False,
        "source_state": "SOURCE_SEMANTICS_PARTIAL",
    }


def compose_personal_factors(
    tara: Mapping[str, Any] | None,
    chandra: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Return a qualitative overlay state; never produces a score or ranking."""
    if tara is None and chandra is None:
        state = "PERSONAL_FACTOR_UNAVAILABLE"
    else:
        effects = {item.get("effect") for item in (tara, chandra) if item}
        supportive = {"SUPPORTIVE", "SUPPORTIVE_WITH_VARIANT_CONDITION"}
        if effects and effects.issubset(supportive):
            state = "BOTH_SUPPORTIVE" if tara and chandra else "ONE_FACTOR_SUPPORTIVE"
        elif "CAUTION" in effects and effects.intersection(supportive):
            state = "MIXED_PERSONAL_FACTORS"
        elif "CAUTION" in effects:
            state = "PERSONAL_CAUTION"
        else:
            state = "PERSONAL_FACTOR_UNCERTAIN"
    return {
        "personal_factor_state": state,
        "tara_evaluated": tara is not None,
        "chandra_evaluated": chandra is not None,
        "numeric_score": None,
        "hidden_weights": False,
        "production_activation": "DISABLED",
    }


def build_tara_oracle_matrix() -> list[dict[str, Any]]:
    return [
        evaluate_tara_bala(janma, event)
        for janma in range(1, 28)
        for event in range(1, 28)
    ]


def build_chandra_oracle_matrix(variant: str = "STANDARD_1_3_6_7_10_11") -> list[dict[str, Any]]:
    return [
        evaluate_chandra_bala(natal, event, variant=variant)
        for natal in range(1, 13)
        for event in range(1, 13)
    ]


__all__ = [
    "CHANDRA_POSITIONS",
    "TARA_CATEGORIES",
    "TARA_EFFECTS",
    "build_chandra_oracle_matrix",
    "build_tara_oracle_matrix",
    "compose_personal_factors",
    "evaluate_chandra_bala",
    "evaluate_tara_bala",
]
