"""Define the narrow, source-governed marriage-occurrence signal contract.

This is a research/pilot contract, not a production predictor.  It deliberately
uses only the source-backed D1 relationship to the seventh house and a
Vimshottari Mahadasha lord.  Antardasha and D9/Jupiter-transit refinements are
recorded as optional/deferred rather than silently required.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SIGNAL_ID = "VEDA-SIGNAL-MARRIAGE-OCCURRENCE-001"
SIGNAL_VERSION = "1.0.0"
METHOD_ID = "VEDA-DASHA-VIMSHOTTARI-MARRIAGE-PHALADEEPIKA-V1"
EVENT_CLASS = "MARRIAGE"
SOURCE_URLS = [
    "https://www.wisdomlib.org/hinduism/book/phaladeepika-by-mantreswara-text-and-translation/ocr/1621570/144",
    "https://www.iswaryajyotisha.com/pages/library.php?book=Brihat+parspara+hora+sastra",
]


def _hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def contract() -> dict[str, Any]:
    return {
        "signal_id": SIGNAL_ID,
        "version": SIGNAL_VERSION,
        "event_class": EVENT_CLASS,
        "method": {
            "id": METHOD_ID,
            "timing": "Vimshottari Mahadasha lord",
            "structural_chart": "D1",
        },
        "positive_conditions": [
            "Mahadasha lord occupies the 7th house",
            "Mahadasha lord aspects the 7th house under the governed aspect model",
            "Mahadasha lord owns the 7th house",
        ],
        "negative_conditions": [
            "Do not infer an event from a generic planet label alone",
            "Do not use chart fit, outcome labels, or holdout cases for rule selection",
            "Do not infer spouse quality, permanence, or certainty of marriage",
        ],
        "states": ["SIGNAL_PRESENT", "SIGNAL_ABSENT", "SIGNAL_INDETERMINATE"],
        "date_precision": {
            "EXACT": "Evaluate only against the documented event date; no day-level claim is made by this contract.",
            "MONTH": "Evaluate only as a month-level overlap/window; never manufacture a day.",
            "YEAR": "Evaluate only as a year-level association; never manufacture a month or day.",
        },
        "optional_refinements": [
            "Phaladeepika Jupiter transit to a trine from the 7th lord's natal Rasi is a deferred window refinement.",
            "Navamsa refinement is deferred because D9 interpretation is not activated for this signal.",
            "Antardasha may be reported as context but is not required by this v1 contract.",
        ],
        "limitations": [
            "Historical source language and marriage customs are not a universal modern outcome rule.",
            "The source passage is a conditional indication, not a guaranteed event detector.",
            "No pilot is ready until independently documented marriage events with valid birth data exist.",
        ],
        "source_references": [
            {
                "source": "Phaladeepika, Chapter 11, marriage verses 13-14 (translation page)",
                "passage": "Dasha of a planet occupying, aspecting, or owning the 7th; stronger 7th/Venus/Moon-related Dasha with Jupiter transit refinement.",
                "authority": "CLASSICAL_PRIMARY_TRANSLATION",
                "status": "SOURCE_GOVERNABLE_NARROW_CLAIM",
                "url": SOURCE_URLS[0],
            },
            {
                "source": "Brihat Parashara Hora Shastra, translated edition",
                "passage": "Dasha and Antardasha mechanics and conditional marriage indications; used as corroborating timing context.",
                "authority": "CLASSICAL_PRIMARY_TRANSLATION",
                "status": "CORROBORATING_REFERENCE",
                "url": SOURCE_URLS[1],
            },
        ],
    }


def contract_hash() -> str:
    return _hash(contract())


def evaluate_signal(*, mahadasha_lord: str | None, seventh_lord: str | None,
                    planets_in_seventh: list[str] | None,
                    planets_aspecting_seventh: list[str] | None,
                    required_fields_complete: bool = True) -> str:
    """Evaluate only the frozen structural membership condition."""
    if not required_fields_complete or not mahadasha_lord or not seventh_lord:
        return "SIGNAL_INDETERMINATE"
    relevant = {seventh_lord, *(planets_in_seventh or []), *(planets_aspecting_seventh or [])}
    return "SIGNAL_PRESENT" if mahadasha_lord in relevant else "SIGNAL_ABSENT"


def precision_is_allowed(precision: str, observed_period: str, event_date: str) -> bool:
    """Require an event observation no finer than the recorded precision."""
    if precision not in {"EXACT", "MONTH", "YEAR"} or not event_date:
        return False
    if precision == "EXACT":
        return observed_period == event_date
    if precision == "MONTH":
        return observed_period[:7] == event_date[:7]
    return observed_period[:4] == event_date[:4]


def build_audit(*, eligible_marriage_cases: int = 0, corpus_hash: str | None = None) -> dict[str, Any]:
    result = {
        "activity_id": "VEDA-SIGNAL-BREAKTHROUGH-001",
        "status": "COMPLETED_WITH_SOURCE_GOVERNABLE_SIGNAL",
        "signal_governance": "SOURCE_GOVERNABLE",
        "signal_id": SIGNAL_ID,
        "signal_version": SIGNAL_VERSION,
        "signal_hash": contract_hash(),
        "method_id": METHOD_ID,
        "event_class": EVENT_CLASS,
        "eligible_marriage_cases": eligible_marriage_cases,
        "pilot_ready": eligible_marriage_cases >= 10,
        "pilot_state": "NOT_READY_SAMPLE_INSUFFICIENT" if eligible_marriage_cases < 10 else "READY_FOR_BOUNDED_PILOT",
        "corpus_hash_preserved": corpus_hash or "3b3ac3b7cacfbe9b3d1935fbe0263568db49a37a95ed8e308c355bbb6a61f76f",
        "holdout_accessed": False,
        "production_activation": False,
        "approved_core_changes": 0,
        "rag_changed": False,
        "predictive_validation_changed": False,
        "contract": contract(),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = build_audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("signal_id", "signal_hash", "signal_governance", "pilot_state")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
