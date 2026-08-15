"""Rank empirical acquisition candidates without chart-derived features."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

TARGET_OCCUPATIONS = {
    "politician": "LEADERSHIP",
    "scientist": "SCIENCE_AWARDS",
    "mathematician": "SCIENCE_AWARDS",
    "social-scientist": "SCIENCE_AWARDS",
    "athletics-competitor": "LEADERSHIP",
    "cyclist": "LEADERSHIP",
}


def rank_record(record: dict[str, Any]) -> dict[str, Any]:
    occupation = (record.get("occupation") or "").split("+")[0].strip().lower()
    reasons = []
    score = 0
    lane = TARGET_OCCUPATIONS.get(occupation, "OTHER")
    if lane != "OTHER":
        score += 3
        reasons.append("target_lane_occupation")
    if record.get("birth_time"):
        score += 2
        reasons.append("timed_birth_record")
    if record.get("birth_place"):
        score += 2
        reasons.append("birth_place_present")
    if record.get("timezone_offset"):
        score += 2
        reasons.append("timezone_present")
    if record.get("wdid"):
        score += 1
        reasons.append("existing_wikidata_link")
    priority = "HIGH" if score >= 8 else "MEDIUM" if score >= 5 else "LOW"
    return {"subject_id": record.get("ogid"), "subject_label": record.get("subject_label"), "occupation": record.get("occupation"), "lane": lane, "score": score, "priority": priority, "reasons": reasons, "astrology_used_for_selection": False}


def build_ranking(payload: dict[str, Any], *, limit: int = 100) -> dict[str, Any]:
    ranked = sorted((rank_record(record) for record in payload.get("records", [])), key=lambda item: (-item["score"], item["subject_id"] or ""))
    lanes = {}
    for item in ranked:
        lane = lanes.setdefault(item["lane"], {"screened": 0, "high_priority": 0})
        lane["screened"] += 1
        lane["high_priority"] += item["priority"] == "HIGH"
    return {"activity_id": "VEDA-EMP-025-R1-ACQUISITION-RANKING", "source_feed": payload.get("feed_id"), "screened": len(ranked), "ranking_policy": "identity, event-richness proxy, source-likelihood proxy, birth completeness, timezone and coordinate solvability; no chart features", "lanes": lanes, "records": ranked[:limit]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    result = build_ranking(json.loads(args.input.read_text(encoding="utf-8")), limit=args.limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"screened": result["screened"], "returned": len(result["records"]), "lanes": result["lanes"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
