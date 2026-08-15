"""Generate reproducible chart snapshots for the governed EMP-025 corpus."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

from engines.common import config as cfg
from engines.intelligence.kundli_engine import KundliEngine


def _offset(value: str | None) -> float:
    text = str(value or "").strip()
    sign = -1 if text.startswith("-") else 1
    parts = text.lstrip("+-").split(":")
    hours = int(parts[0] or 0)
    minutes = int(parts[1] or 0) if len(parts) > 1 else 0
    seconds = int(parts[2] or 0) if len(parts) > 2 else 0
    return sign * (hours + minutes / 60 + seconds / 3600)


def _engine_time(value: str) -> str:
    """Normalize corpus minute precision to the existing engine's HH:MM:SS contract."""
    text = str(value or "").strip()
    return text if text.count(":") == 2 else f"{text}:00"


def generate_snapshot(place_payload: dict[str, Any], *, db_path: str | Path | None = None, engine_revision: str) -> dict[str, Any]:
    places = {item["subject_id"]: item for item in place_payload.get("records", [])}
    db = Path(db_path or cfg.VEDA_RESEARCH_PLATFORM_DB)
    engine = KundliEngine()
    charts = []
    with sqlite3.connect(str(db)) as con:
        rows = con.execute("SELECT case_id, payload FROM pred_cases WHERE case_class='HISTORICAL_VERIFIED' AND leakage_status='VALID' ORDER BY case_id").fetchall()
        for case_id, raw in rows:
            payload = json.loads(raw)
            subject_id = payload.get("subject_id")
            place = places.get(subject_id)
            chart_input = payload.get("chart_input") or {}
            if not place or not place.get("chart_ready"):
                continue
            chart = engine.compute_human(
                payload.get("subject_label") or subject_id,
                chart_input["birth_date"],
                _engine_time(chart_input["birth_time"]),
                float(place["latitude"]),
                float(place["longitude"]),
                _offset(chart_input.get("timezone")),
            )
            if not chart:
                continue
            chart_input.update({
                "birth_place_raw": place["birth_place_raw"],
                "birth_place_normalized": place["birth_place_normalized"],
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "coordinate_source": place.get("coordinate_source", place_payload.get("coordinate_source", "UNSPECIFIED")),
                "coordinate_precision": place["coordinate_precision"],
                "coordinate_confidence": place["coordinate_confidence"],
                "historical_place_status": place["historical_place_status"],
            })
            chart_input["chart_ready"] = True
            chart_input["chart_engine_revision"] = engine_revision
            chart_input["engine_time_normalization"] = "MINUTE_TO_SECOND_ZERO_FILL"
            payload["chart_input"] = chart_input
            payload["chart_engine_version"] = engine_revision
            payload["chart_facts"] = chart
            payload["feature_governance"] = {"validated_features": "D1 calculation facts only", "conditional_features": "historical timezone/coordinate caveat", "research_features": ["BAV", "SAV"], "disabled_features": ["BAV", "SAV"]}
            payload["notes"] = str(payload.get("notes") or "") + " Chart snapshot generated without BAV/SAV activation."
            con.execute("UPDATE pred_cases SET payload=? WHERE case_id=?", (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")), case_id))
            charts.append({"case_id": case_id, "subject_id": subject_id, "chart_engine_revision": engine_revision, "chart_ready": True, "feature_governance": payload["feature_governance"], "chart_facts": chart})
        con.commit()
    return {"activity_id": "VEDA-EMP-025-CHART-SNAPSHOT", "cases_considered": len(rows), "chart_ready_cases": len(charts), "bav_sav_activated": False, "charts": charts}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("place_resolution", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--engine-revision", required=True)
    args = parser.parse_args()
    result = generate_snapshot(json.loads(args.place_resolution.read_text(encoding="utf-8")), engine_revision=args.engine_revision)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("cases_considered", "chart_ready_cases", "bav_sav_activated")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
