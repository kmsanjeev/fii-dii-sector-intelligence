"""Deterministic source-governance audit for the EMP-050 second-signal search."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


AUDIT = {
    "activity_id": "VEDA-EMP-050-REPLICATION-SIGNAL-002",
    "second_signal_found": False,
    "decision": "NO_SECOND_SOURCE_GOVERNABLE_SIGNAL",
    "candidates": [
        {
            "domain": "PROGENY",
            "status": "SOURCE_PARTIAL",
            "blockers": ["D7 interpretation and dated event timing are not validated", "historical and gendered rules require contextual governance"],
        },
        {
            "domain": "EDUCATION",
            "status": "SOURCE_PARTIAL",
            "blockers": ["start/completion/higher-study event taxonomy is not source-governed", "D24 is cross-domain context, not a frozen event signal"],
        },
        {
            "domain": "CAREER_COMMENCEMENT",
            "status": "SOURCE_PARTIAL",
            "blockers": ["no deterministic event-specific commencement signal is frozen", "the prior public-role signal audit did not establish a source-governable signal"],
        },
        {
            "domain": "RELOCATION",
            "status": "SOURCE_PARTIAL",
            "blockers": ["travel/residence sources do not provide a validated dated relocation event method"],
        },
        {
            "domain": "PROPERTY_ACQUISITION",
            "status": "SOURCE_PARTIAL",
            "blockers": ["D4 interpretation remains gated", "property event timing is not frozen as a deterministic source-backed signal"],
        },
    ],
    "production_changes": "NONE",
    "approved_core": "UNCHANGED",
    "rag": "UNCHANGED",
    "pred_m4": "INSUFFICIENT_SAMPLE",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(AUDIT, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decision": AUDIT["decision"], "candidates": AUDIT["candidates"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
