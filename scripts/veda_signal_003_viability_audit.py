"""Emit the deterministic, outcome-blind SIGNAL-003 viability decision.

This activity deliberately produces no event signal.  It records the
source-governance gate so a future source expansion cannot silently skip the
required order: source -> implementation -> prevalence -> cases.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


AUDIT = {
    "activity_id": "VEDA-SIGNAL-003",
    "status": "COMPLETED_NO_VIABLE_THIRD_SIGNAL",
    "success_path": "B",
    "signal_found": False,
    "first_empirically_viable_signal": None,
    "negative_evidence": {
        "public_role": "PUBLIC_ROLE_SIGNAL_UNGOVERNABLE",
        "marriage_v1": "REPLICATED_NO_SEPARATION",
        "progeny_v1": "SIGNAL_TOO_SPARSE_TO_TEST",
        "progeny_prevalence_subjects": 999,
        "progeny_subject_activation": 0.064064,
        "progeny_time_weighted_prevalence": 0.000967,
        "progeny_implementation_defect": False,
        "pred_m4": "INSUFFICIENT_SAMPLE / INSUFFICIENT_REPLICATED_DISCRIMINATION",
    },
    "families": [
        {
            "candidate": "EDUCATION",
            "event_types": [
                "EDUCATION_START",
                "HIGHER_EDUCATION_ENTRY",
                "DEGREE_COMPLETION",
                "EDUCATION_COMPLETION",
            ],
            "source_status": "SOURCE_PARTIAL",
            "signal_governable": False,
            "implementation_reachable": "N/A",
            "outcome_blind_prevalence": "NOT_RUN",
            "empirical_viability": "NOT_REACHED",
            "decision": "RETAIN_RESEARCH_CANDIDATE",
            "reason": "Classical material supports educational themes and improvement, but no deterministic, objectively dateable start or completion timing doctrine was established.",
        },
        {
            "candidate": "CAREER_COMMENCEMENT",
            "event_types": ["FIRST_EMPLOYMENT", "PROFESSION_ENTRY", "CAREER_COMMENCEMENT"],
            "source_status": "SOURCE_PARTIAL",
            "signal_governable": False,
            "implementation_reachable": "N/A",
            "outcome_blind_prevalence": "NOT_RUN",
            "empirical_viability": "NOT_REACHED",
            "decision": "RETAIN_RESEARCH_CANDIDATE",
            "reason": "Profession/livelihood significations are not an event-specific first-employment or commencement method; the prior public-role signal remains ungovernable.",
        },
        {
            "candidate": "RELOCATION_FOREIGN_RESIDENCE",
            "event_types": ["CHANGE_OF_RESIDENCE", "FOREIGN_RESIDENCE", "PERMANENT_RELOCATION"],
            "source_status": "SOURCE_PARTIAL",
            "signal_governable": False,
            "implementation_reachable": "N/A",
            "outcome_blind_prevalence": "NOT_RUN",
            "empirical_viability": "NOT_REACHED",
            "decision": "RETAIN_RESEARCH_CANDIDATE",
            "reason": "Travel/residence sources do not establish a validated dated relocation event method; residence, foreign travel and settlement remain distinct.",
        },
        {
            "candidate": "PROPERTY_ACQUISITION",
            "event_types": ["PROPERTY_PURCHASE", "LAND_ACQUISITION", "HOUSE_CONSTRUCTION", "HOME_OWNERSHIP"],
            "source_status": "SOURCE_PARTIAL",
            "signal_governable": False,
            "implementation_reachable": "N/A",
            "outcome_blind_prevalence": "NOT_RUN",
            "empirical_viability": "NOT_REACHED",
            "decision": "RETAIN_RESEARCH_CANDIDATE",
            "reason": "Property event timing and D4 interpretation remain gated; no deterministic source-backed acquisition event method is frozen.",
        },
    ],
    "pipeline": [
        "SOURCE_GOVERNANCE",
        "IMPLEMENTATION_REACHABILITY",
        "OUTCOME_BLIND_PREVALENCE",
        "EMPIRICAL_VIABILITY",
        "CASE_ACQUISITION",
        "PILOT",
        "REPLICATION",
    ],
    "production_changes": "NONE",
    "approved_core": "UNCHANGED",
    "rag": "UNCHANGED",
    "general_emp_050": {"eligible": 25, "target": 50, "holdout": "SEALED"},
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(AUDIT, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": AUDIT["status"], "signal_found": AUDIT["signal_found"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
