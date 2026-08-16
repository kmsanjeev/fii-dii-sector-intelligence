"""Frozen, research-only progeny occurrence signal contract.

This is deliberately narrower than the existing P025 progeny synthesis.  It
uses only a D1 structural gate and one explicitly documented Vimshottari
timing lane.  It does not use D7, medical facts, weights, or empirical fitting.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


CONTRACT: dict[str, Any] = {
    "signal_id": "VEDA-SIGNAL-PROGENY-OCCURRENCE-001",
    "version": "1.0.0",
    "event_family": "CHILD_BIRTH",
    "eligible_events": ["objectively dated live birth of a child"],
    "inputs": [
        "D1 fifth-lord house and dignity facts",
        "D1 Jupiter conjunction/aspect to the fifth lord",
        "Vimshottari Mahadasha and Antardasha interval",
        "D1 Sun house, sign dignity and strength facts",
    ],
    "timing_method": "VIMSHOTTARI_JUPITER_MAHADASHA_SUN_ANTARDASHA",
    "positive_conditions": {
        "structural_gate": [
            "fifth lord exalted",
            "fifth lord in house 2, 5 or 9",
            "fifth lord conjunct Jupiter",
            "fifth lord aspected by Jupiter",
        ],
        "timing_gate": [
            "Mahadasha lord is Jupiter",
            "Antardasha lord is Sun",
            "Sun is exalted, in own sign, in house 2, 3, 5, 9 or 11, and marked strong",
        ],
    },
    "negative_conditions": [
        "Sun is in house 6, 8 or 12 from Lagna",
        "Sun is in house 6, 8 or 12 from the Mahadasha lord",
    ],
    "indeterminate_conditions": [
        "missing D1 fifth-lord/Jupiter facts",
        "missing Vimshottari interval facts",
        "missing Sun dignity/strength facts",
        "birth event is not objectively dated",
        "D7 interpretation is requested",
    ],
    "precision_rules": {
        "event": ["EXACT_DAY", "MONTH", "YEAR"],
        "timing": "Dasha interval only; no exact birth day is inferred",
        "fallback": "INDETERMINATE",
    },
    "source_lineage": [
        {
            "source": "Brihat Parashara Hora Shastra",
            "edition": "Rishi Parashara translation PDF, pp. 18-19",
            "passage": "Chapter 16, verses 1-3 and 16",
            "claim": "D1 fifth-house/lord conditions are associated with obtaining children.",
            "authority": "PRIMARY_CLASSICAL",
            "url": "https://vedic-astro.s3.amazonaws.com/books/bhrihat_parasara_hora_shastra.pdf",
        },
        {
            "source": "Brihat Parashara Hora Shastra",
            "edition": "Rishi Parashara translation PDF, pp. 109-110",
            "passage": "Chapter 56, verses 51-60",
            "claim": "Birth/increase of children is described in Jupiter Mahadasha Antardasha lanes with specified planetary conditions; this contract selects the explicit Sun Antardasha birth-of-children lane.",
            "authority": "PRIMARY_CLASSICAL",
            "url": "https://vedic-astro.s3.amazonaws.com/books/bhrihat_parasara_hora_shastra.pdf",
        },
    ],
    "method_limits": [
        "research-only; not production activated",
        "D1-first; D7 calculation/interpretation is not consumed",
        "not a fertility, infertility, conception, miscarriage, number, sex, or medical diagnosis signal",
        "historical source language is retained without modern gender generalization",
        "no empirical weights or thresholds",
    ],
}


def signal_hash() -> str:
    payload = json.dumps(CONTRACT, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def evaluate(facts: dict[str, Any]) -> dict[str, Any]:
    required = ("fifth_lord_house", "fifth_lord_exalted", "fifth_lord_conjunct_jupiter", "fifth_lord_aspected_by_jupiter", "mahadasha", "antardasha", "sun_house", "sun_strong")
    if any(key not in facts or facts[key] is None for key in required):
        return {"state": "INDETERMINATE", "reason": "MISSING_REQUIRED_INPUT", "signal_id": CONTRACT["signal_id"], "version": CONTRACT["version"]}
    structure = bool(facts["fifth_lord_exalted"] or facts["fifth_lord_house"] in {2, 5, 9} or facts["fifth_lord_conjunct_jupiter"] or facts["fifth_lord_aspected_by_jupiter"])
    sun_positive = bool(facts["sun_strong"] and (facts.get("sun_exalted") or facts.get("sun_own_sign") or facts["sun_house"] in {2, 3, 5, 9, 11}))
    timing = facts["mahadasha"] == "Jupiter" and facts["antardasha"] == "Sun" and sun_positive
    negative = facts["sun_house"] in {6, 8, 12} or facts.get("sun_house_from_mahadasha_lord") in {6, 8, 12}
    if negative:
        return {"state": "CONDITIONAL_BLOCKED", "reason": "SOURCE_NEGATIVE_CONDITION", "signal_id": CONTRACT["signal_id"], "version": CONTRACT["version"]}
    return {"state": "SIGNAL_PRESENT" if structure and timing else "SIGNAL_ABSENT", "structural_gate": structure, "timing_gate": timing, "signal_id": CONTRACT["signal_id"], "version": CONTRACT["version"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = {"contract": CONTRACT, "hash": signal_hash(), "status": "FROZEN_RESEARCH_ONLY", "d7_used": False, "production_activation": "NONE", "empirical_outcomes_inspected_before_freeze": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"signal_id": CONTRACT["signal_id"], "version": CONTRACT["version"], "hash": result["hash"], "status": result["status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
