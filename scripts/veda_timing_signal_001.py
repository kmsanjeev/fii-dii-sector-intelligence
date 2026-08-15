"""Govern the EMP-025 public-role signal without fitting it to the corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

CORPUS_HASH = "3b3ac3b7cacfbe9b3d1935fbe0263568db49a37a95ed8e308c355bbb6a61f76f"
METHOD_ID = "VEDA-DASHA-VIMSHOTTARI"
METHOD_VERSION = "P016_CANONICAL_TIMING"
EVENT_CLASSES = ["POSITION_START", "POSITION_END", "PUBLIC_APPOINTMENT", "ELECTION_WIN"]


def _hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def source_candidates() -> list[dict[str, Any]]:
    return [
        {
            "rule_id": "TS-001",
            "source": "Brihat Parashara Hora Shastra, translated PDF edition",
            "passage_reference": "PDF pp. 106-107; Antardasha results in Dasha of Mars",
            "source_class": "CLASSICAL_PRIMARY_TRANSLATION",
            "translation_status": "TRANSLATION_REVIEW_REQUIRED",
            "rule_statement": "Specific conditional Antardasha passages describe conferment of authority by government/king under named planetary and positional conditions.",
            "event_relevance": ["POSITION_START", "PUBLIC_APPOINTMENT"],
            "method_relevance": "Dasha/Antardasha results, but not a general public-role event label.",
            "contradictions": ["historical king/government language is not identical to modern appointment or election labels"],
            "authority_status": "SOURCE_PARTIAL",
            "implementation_status": "NOT_IMPLEMENTED",
        },
        {
            "rule_id": "TS-002",
            "source": "Brihat Parashara Hora Shastra, translated PDF edition",
            "passage_reference": "PDF p. 106; Saturn Antardasha results from the Dasha lord",
            "source_class": "CLASSICAL_PRIMARY_TRANSLATION",
            "translation_status": "TRANSLATION_REVIEW_REQUIRED",
            "rule_statement": "A conditional passage includes loss of reputation and loss of position among adverse results.",
            "event_relevance": ["POSITION_END"],
            "method_relevance": "Potentially relevant to a loss-of-position theme, not a validated termination-event detector.",
            "contradictions": ["the passage is conditional and does not define event dates, modern employment, or a reverse of appointment"],
            "authority_status": "SOURCE_PARTIAL",
            "implementation_status": "NOT_IMPLEMENTED",
        },
        {
            "rule_id": "TS-003",
            "source": "Phaladeepika, Chapter 5, Profession and Livelihood",
            "passage_reference": "Chapter 5, verses 1-8; Wisdomlib translation page",
            "source_class": "CLASSICAL_PRIMARY_TRANSLATION",
            "translation_status": "TRANSLATION_REVIEW_REQUIRED",
            "rule_statement": "Profession/livelihood is related to the tenth lord and its navamsha context, with occupational examples.",
            "event_relevance": ["POSITION_START", "PUBLIC_APPOINTMENT"],
            "method_relevance": "Structural profession context; no Vimshottari event-timing contract.",
            "contradictions": ["occupation is not equivalent to appointment, election victory, or a dated transition"],
            "authority_status": "SOURCE_PARTIAL",
            "implementation_status": "NOT_IMPLEMENTED",
        },
        {
            "rule_id": "TS-004",
            "source": "VEDA P016 canonical timing governance",
            "passage_reference": "docs/current-state/p016 and dasha_governance.py",
            "source_class": "VEDA_GOVERNED_FOUNDATION",
            "translation_status": "NOT_APPLICABLE",
            "rule_statement": "Vimshottari sequence, Moon Janma Nakshatra remainder, Mahadasha and Antardasha facts are deterministic calculation foundations.",
            "event_relevance": [],
            "method_relevance": "Calculation-safe timing facts only; event interpretation remains research-required.",
            "contradictions": [],
            "authority_status": "SOURCE_VALIDATED",
            "implementation_status": "IMPLEMENTED_CALCULATION_ONLY",
        },
        {
            "rule_id": "TS-005",
            "source": "Modern generic career heuristics and unsourced legacy interpretations",
            "passage_reference": "REFERENCE_NOT_VERIFIED",
            "source_class": "MODERN_UNSOURCED",
            "translation_status": "NOT_VERIFIED",
            "rule_statement": "Generic 10th-lord, Sun, Saturn, Jupiter or 'career Dasha' combinations predict a public-role transition.",
            "event_relevance": EVENT_CLASSES,
            "method_relevance": "Not admissible without explicit source and method provenance.",
            "contradictions": ["existing P020/P005 governance labels career interpretation as shadow/research-only"],
            "authority_status": "REJECTED",
            "implementation_status": "PROHIBITED",
        },
    ]


def build_audit(primary_events: list[dict[str, Any]], *, corpus_hash: str = CORPUS_HASH) -> dict[str, Any]:
    if corpus_hash != CORPUS_HASH:
        raise ValueError("CORPUS_HASH_MISMATCH_STOP")
    if any(item.get("event_class") not in EVENT_CLASSES for item in primary_events):
        raise ValueError("PRIMARY_EVENT_CLASS_OUTSIDE_FROZEN_CONTRACT")
    candidates = source_candidates()
    contract_basis = {
        "method_id": METHOD_ID,
        "method_version": METHOD_VERSION,
        "event_classes": EVENT_CLASSES,
        "candidate_rule_ids": [item["rule_id"] for item in candidates],
        "signal_governance": "NO_SOURCE_GOVERNABLE_PUBLIC_ROLE_SIGNAL",
        "corpus_hash": corpus_hash,
    }
    return {
        "activity_id": "VEDA-TIMING-SIGNAL-001",
        "status": "COMPLETED_WITH_NO_GOVERNABLE_SIGNAL",
        "research_question": "What source-backed Jyotisha conditions can define a Vimshottari public-role activation signal?",
        "corpus_hash": corpus_hash,
        "holdout_accessed": False,
        "sources_reviewed": [item["source"] for item in candidates],
        "rules": candidates,
        "event_support": {event_class: "NOT_GOVERNABLE" for event_class in EVENT_CLASSES},
        "signal_id": None,
        "signal_version": None,
        "signal_hash": _hash(contract_basis),
        "signal_governance": "FAIL",
        "decision": "NO_SOURCE_GOVERNABLE_PUBLIC_ROLE_SIGNAL",
        "primary_pilot_rerun": "NOT_READY",
        "inputs": ["D1 chart", "Mahadasha lord", "Antardasha lord", "governed house/lord facts only if later sourced"],
        "outputs": ["SIGNAL_PRESENT", "SIGNAL_ABSENT", "SIGNAL_INDETERMINATE"],
        "indeterminate_state": "DEFINED_FOR_FUTURE_CONTRACT_ONLY",
        "date_precision": {"EXACT": 2, "MONTH": 0, "YEAR": 13},
        "next_activity": "CHOOSE_NEXT_SOURCE_GOVERNABLE_EVENT_METHOD_PAIR",
        "emp_050": "CONTINUE_IN_PARALLEL",
        "prospective_candidates": 0,
        "rag_changed": False,
        "approved_core_changes": 0,
        "predictive_validation_changed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("primary_events", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    events = json.loads(args.primary_events.read_text(encoding="utf-8"))
    result = build_audit(events)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "decision": result["decision"], "signal_hash": result["signal_hash"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
