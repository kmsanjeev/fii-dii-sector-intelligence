"""Create a deterministic subject-level EMP-025 design/validation/holdout split."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def build_split(subject_ids: list[str]) -> dict[str, Any]:
    ordered = sorted(set(subject_ids), key=lambda value: hashlib.sha256(value.encode("utf-8")).hexdigest())
    total = len(ordered)
    design_n = min(max(1, round(total * 0.4)), max(1, total - 2)) if total else 0
    validation_n = max(1, round(total * 0.3)) if total >= 3 else 0
    if design_n + validation_n >= total and total >= 3:
        validation_n = max(1, total - design_n - 1)
    records = []
    for index, subject_id in enumerate(ordered):
        split = "DESIGN" if index < design_n else "VALIDATION" if index < design_n + validation_n else "HOLDOUT"
        records.append({"subject_id": subject_id, "split": split})
    counts = {split: sum(item["split"] == split for item in records) for split in ("DESIGN", "VALIDATION", "HOLDOUT")}
    return {
        "activity_id": "VEDA-EMP-025-SPLIT-FREEZE",
        "status": "PRE_PILOT_FROZEN",
        "algorithm": "Sort stable subject IDs by SHA256 digest; assign approximately 40% DESIGN, 30% VALIDATION, remainder HOLDOUT with non-empty validation/holdout when n >= 3",
        "subject_level": True,
        "method_tuning_allowed": False,
        "records": records,
        "counts": counts,
    }


def main() -> int:
    parser = __import__("argparse").ArgumentParser()
    parser.add_argument("subjects", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.subjects.read_text(encoding="utf-8"))
    ids = [item["subject_id"] for item in payload.get("records", [])]
    args.output.write_text(json.dumps(build_split(ids), indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
