"""Validate governed coordinate-resolution records before chart use."""

from __future__ import annotations

from typing import Any


def validate_place_resolution(payload: dict[str, Any]) -> dict[str, Any]:
    errors = []
    accepted = []
    for item in payload.get("records", []):
        required = ("subject_id", "birth_place_raw", "birth_place_normalized", "latitude", "longitude", "coordinate_source", "coordinate_precision", "coordinate_confidence", "historical_place_status", "chart_ready")
        missing = [key for key in required if key not in item and not (key == "coordinate_source" and payload.get("coordinate_source"))]
        if missing or not (-90 <= float(item.get("latitude", 999)) <= 90) or not (-180 <= float(item.get("longitude", 999)) <= 180):
            errors.append({"subject_id": item.get("subject_id"), "reason": "COORDINATE_RECORD_INVALID", "missing": missing})
            continue
        accepted.append(item["subject_id"])
    return {"status": "PASS" if not errors else "FAIL", "records": len(payload.get("records", [])), "chart_ready": len(accepted), "errors": errors, "accepted_subjects": accepted}
