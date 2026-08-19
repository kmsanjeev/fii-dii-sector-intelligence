"""Bounded transition-aware Muhurta window search.

This is orchestration only.  The frozen RX1 single-candidate engine remains
the sole source of rule evaluation, abstention, source gaps and caution.
"""

from __future__ import annotations

import copy
import json
import math
import time
from datetime import datetime, time as datetime_time, timedelta, timezone
from typing import Any, Mapping
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from engines.common.logger import get_logger
from engines.ai.knowledge.muhurta_foundation import build_candidate_windows
from engines.ai.knowledge.muhurta_recommendation_engine_rx1 import (
    CONTRACTS,
    ENGINE_ID,
    ENGINE_VERSION,
    MODE,
    MuhurtaEngineError,
    _load_contract,
    _validate_location,
    recommend,
)
from engines.ai.knowledge.muhurta_transition_source import (
    TRANSITION_CLASSIFICATION,
    TRANSITION_SOURCE_ID,
    TRANSITION_SOURCE_VERSION,
    TransitionSourceError,
    discover_transitions,
    position_facts,
)


PROGRAMME = "VEDA-MUHURTA-WINDOW-SEARCH-001"
SEARCH_ENGINE_ID = "VEDA_MUHURTA_TRANSITION_AWARE_WINDOW_SEARCH"
SEARCH_ENGINE_VERSION = "1.0.0"
DEFAULT_SEARCH_RANGE = timedelta(days=7)
MAX_SEARCH_RANGE = timedelta(days=31)
DEFAULT_MAX_RESULTS = 5
MAX_RESULTS = 20
_REPRESENTATIVE_EPSILON = timedelta(seconds=1)
_RANK = {
    "SUPPORTED_WITH_CAUTION": 3,
    "MIXED_FACTORS": 2,
    "INSUFFICIENT_RULE_COVERAGE": 1,
    "NOT_RECOMMENDED_UNDER_SELECTED_RULESET": 0,
    "ABSTAIN": -1,
}
_RECOMMENDABLE = {"SUPPORTED_WITH_CAUTION", "MIXED_FACTORS"}
logger = get_logger(__name__)


class MuhurtaWindowSearchError(MuhurtaEngineError):
    """Invalid or unavailable bounded window-search input."""


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _parse_datetime(value: Any, field: str) -> datetime:
    if isinstance(value, datetime):
        result = value
    elif isinstance(value, str):
        try:
            result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise MuhurtaWindowSearchError(f"{field} must be ISO-8601 datetime") from exc
    else:
        raise MuhurtaWindowSearchError(f"{field} must be ISO-8601 datetime")
    if result.tzinfo is None or result.utcoffset() is None:
        raise MuhurtaWindowSearchError(f"{field} must be timezone-aware")
    return result


def _parse_daily_time(value: Any, field: str) -> datetime_time | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise MuhurtaWindowSearchError(f"{field} must be HH:MM[:SS]")
    try:
        parsed = datetime_time.fromisoformat(value)
    except ValueError as exc:
        raise MuhurtaWindowSearchError(f"{field} must be HH:MM[:SS]") from exc
    return parsed.replace(tzinfo=None)


def _normalise_request(request: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(request, Mapping):
        raise MuhurtaWindowSearchError("request must be an object")
    activity_id = request.get("activity_id")
    if not isinstance(activity_id, str) or not activity_id:
        raise MuhurtaWindowSearchError("activity_id is required")
    location = _validate_location(request.get("location"))
    start = _parse_datetime(request.get("start_datetime"), "start_datetime")
    end = _parse_datetime(request.get("end_datetime"), "end_datetime")
    zone = ZoneInfo(location["timezone_name"])
    start = start.astimezone(zone)
    end = end.astimezone(zone)
    if end <= start:
        raise MuhurtaWindowSearchError("end_datetime must be after start_datetime")
    if end - start > MAX_SEARCH_RANGE:
        raise MuhurtaWindowSearchError(f"search range cannot exceed {MAX_SEARCH_RANGE.days} days")
    earliest = _parse_daily_time(request.get("daily_earliest_time"), "daily_earliest_time")
    latest = _parse_daily_time(request.get("daily_latest_time"), "daily_latest_time")
    if (earliest is None) != (latest is None):
        raise MuhurtaWindowSearchError("daily_earliest_time and daily_latest_time must be supplied together")
    if earliest is not None and latest is not None and earliest >= latest:
        raise MuhurtaWindowSearchError("daily_earliest_time must be before daily_latest_time")
    max_results = request.get("max_results", DEFAULT_MAX_RESULTS)
    if isinstance(max_results, bool) or not isinstance(max_results, int) or not 1 <= max_results <= MAX_RESULTS:
        raise MuhurtaWindowSearchError(f"max_results must be an integer from 1 to {MAX_RESULTS}")
    scope = request.get("activity_subscope")
    if scope is not None and not isinstance(scope, str):
        raise MuhurtaWindowSearchError("activity_subscope must be a string")
    return {
        "activity_id": activity_id,
        "location": location,
        "start": start,
        "end": end,
        "earliest": earliest,
        "latest": latest,
        "max_results": max_results,
        "activity_subscope": scope,
        "transition_boundaries": request.get("transition_boundaries"),
        "p032_fact_segments": request.get("p032_fact_segments"),
        "p032_facts": request.get("p032_facts"),
    }


def _daily_intervals(start: datetime, end: datetime, earliest: datetime_time | None, latest: datetime_time | None) -> list[tuple[datetime, datetime]]:
    if earliest is None:
        return [(start, end)]
    intervals: list[tuple[datetime, datetime]] = []
    cursor = start.date()
    while cursor <= end.date():
        day_start = datetime.combine(cursor, earliest, tzinfo=start.tzinfo)
        day_end = datetime.combine(cursor, latest, tzinfo=start.tzinfo)
        left, right = max(start, day_start), min(end, day_end)
        if left < right:
            intervals.append((left, right))
        cursor += timedelta(days=1)
    return intervals


def _parse_boundary(item: Any) -> dict[str, Any]:
    if isinstance(item, datetime):
        point = item
        metadata = {"kind": "EXPLICIT_TRANSITION"}
    elif isinstance(item, str):
        point = _parse_datetime(item, "transition boundary")
        metadata = {"kind": "EXPLICIT_TRANSITION"}
    elif isinstance(item, Mapping):
        point = _parse_datetime(item.get("at"), "transition boundary at")
        metadata = dict(item)
    else:
        raise MuhurtaWindowSearchError("transition_boundaries must contain datetimes or objects")
    if point.tzinfo is None:
        raise MuhurtaWindowSearchError("transition boundaries must be timezone-aware")
    metadata["at"] = point
    metadata.setdefault("classification", "EXACT_TRANSITION")
    return metadata


def _group_transitions(items: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for raw in items:
        point = raw["at"]
        key = point.astimezone(timezone.utc).isoformat()
        group = groups.setdefault(key, {
            "at": point,
            "kinds": [],
            "classifications": [],
            "sources": [],
        })
        kind = str(raw.get("kind", "TRANSITION"))
        if kind not in group["kinds"]:
            group["kinds"].append(kind)
        for field, target in (("classification", group["classifications"]), ("source", group["sources"])):
            value = raw.get(field)
            if value is not None and str(value) not in target:
                target.append(str(value))
    result = []
    for group in groups.values():
        group["kinds"].sort()
        group["classifications"].sort()
        group["sources"].sort()
        group["at"] = group["at"].isoformat()
        result.append(group)
    return sorted(result, key=lambda item: datetime.fromisoformat(item["at"]).astimezone(timezone.utc))


def _fact_segment_inputs(value: Any, start: datetime, end: datetime) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list) or not value:
        raise MuhurtaWindowSearchError("p032_fact_segments must be a non-empty list")
    segments = []
    for item in value:
        if not isinstance(item, Mapping):
            raise MuhurtaWindowSearchError("p032_fact_segments entries must be objects")
        left = _parse_datetime(item.get("start"), "p032_fact_segments.start").astimezone(start.tzinfo)
        right = _parse_datetime(item.get("end"), "p032_fact_segments.end").astimezone(start.tzinfo)
        facts = item.get("p032_facts")
        if right <= left or not isinstance(facts, Mapping):
            raise MuhurtaWindowSearchError("each p032 fact segment needs start < end and p032_facts")
        if left < start or right > end:
            raise MuhurtaWindowSearchError("p032 fact segments must stay inside the search range")
        segments.append({"start": left, "end": right, "p032_facts": dict(facts)})
    segments.sort(key=lambda item: item["start"])
    cursor = start
    for segment in segments:
        if segment["start"] != cursor:
            raise MuhurtaWindowSearchError("p032 fact segments must exactly cover the search range")
        cursor = segment["end"]
    if cursor != end:
        raise MuhurtaWindowSearchError("p032 fact segments must exactly cover the search range")
    return segments


def _facts_for(instant: datetime, fact_segments: list[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    for segment in fact_segments:
        if segment["start"] <= instant < segment["end"] or (instant == segment["end"] and instant == fact_segments[-1]["end"]):
            return segment["p032_facts"]
    return None


def _representative(left: datetime, right: datetime) -> datetime:
    if right - left > _REPRESENTATIVE_EPSILON * 2:
        return left + _REPRESENTATIVE_EPSILON
    return left + (right - left) / 2


def _semantic_signature(result: Mapping[str, Any]) -> str:
    value = {
        "recommendation_state": result.get("recommendation_state"),
        "rules_evaluated": result.get("rules_evaluated", []),
        "supporting_factors": result.get("supporting_factors", []),
        "adverse_factors": result.get("adverse_factors", []),
        "requirements": result.get("requirements", []),
        "unevaluated_source_gaps": result.get("unevaluated_source_gaps", []),
        "abstention_reason": result.get("abstention_reason"),
        "contract_metadata": result.get("contract_metadata", {}),
        "caution": result.get("caution", {}),
    }
    return _canonical(value)


def _window_from_result(left: datetime, right: datetime, representative: datetime, result: Mapping[str, Any], transition: Mapping[str, Any] | None) -> dict[str, Any]:
    gaps = list(result.get("unevaluated_source_gaps", []))
    transition_value = dict(transition or {})
    if isinstance(transition_value.get("at"), datetime):
        transition_value["at"] = transition_value["at"].isoformat()
    return {
        "start": left.isoformat(),
        "end": right.isoformat(),
        "representative_instant": representative.isoformat(),
        "recommendation_state": result.get("recommendation_state"),
        "rules_evaluated": copy.deepcopy(result.get("rules_evaluated", [])),
        "supportive_factors": list(result.get("supporting_factors", [])),
        "adverse_factors": list(result.get("adverse_factors", [])),
        "requirements": list(result.get("requirements", [])),
        "unevaluated_factors": gaps,
        "source_gaps": gaps,
        "source_trace": copy.deepcopy(result.get("source_trace", {})),
        "abstention_reason": result.get("abstention_reason"),
        "caution": copy.deepcopy(result.get("caution", {})),
        "consultation_guidance": result.get("consultation_guidance"),
        "contract_metadata": copy.deepcopy(result.get("contract_metadata", {})),
        "transition": copy.deepcopy(transition_value),
        "_semantic_signature": _semantic_signature(result),
    }


def _merge_windows(windows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for window in windows:
        clean = dict(window)
        if merged and merged[-1]["end"] == clean["start"] and merged[-1]["_semantic_signature"] == clean["_semantic_signature"]:
            merged[-1]["end"] = clean["end"]
            merged[-1]["transition"] = {}
        else:
            merged.append(clean)
    for index, window in enumerate(merged, start=1):
        window["window_id"] = f"MUH-SEARCH-WINDOW-{index:03d}"
        window.pop("_semantic_signature", None)
    return merged


def _result_base(req: Mapping[str, Any], *, capability_state: str = "IMPLEMENTED_VALIDATED") -> dict[str, Any]:
    activity = req["activity_id"]
    binding = CONTRACTS.get(activity)
    return {
        "activity_id": activity,
        "mode": MODE,
        "location": dict(req["location"]),
        "search_start": req["start"].isoformat(),
        "search_end": req["end"].isoformat(),
        "search_method": None,
        "transition_types": [],
        "windows_examined": 0,
        "primary_window": None,
        "equivalent_primary_windows": [],
        "alternative_windows": [],
        "abstained_intervals": [],
        "source_gaps": [],
        "contract_id": binding["contract_id"] if binding else None,
        "contract_hash": binding["hash"] if binding else None,
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "search_engine_id": SEARCH_ENGINE_ID,
        "search_engine_version": SEARCH_ENGINE_VERSION,
        "caution": None,
        "consultation_guidance": None,
        "capability_state": capability_state,
        "access_state": "ENABLED",
        "personal_factors_evaluated": False,
        "personal_factors": {"tara_bala": "NOT_EVALUATED", "chandra_bala": "NOT_EVALUATED"},
        "comparison_basis": "CATEGORICAL_STATE_ORDER_V1;NO_NUMERIC_SCORE;SAME_STATE_WINDOWS_REMAIN_EQUIVALENT",
    }


def _not_ready(req: Mapping[str, Any]) -> dict[str, Any]:
    result = _result_base(req, capability_state="NOT_YET_ENGINE_READY")
    result.update({
        "search_method": "NOT_READY_ACTIVITY_GATE",
        "abstention_reason": "NOT_YET_ENGINE_READY",
        "no_result_reason": "The requested activity has no activated general-mode contract.",
    })
    return result


def _transition_inputs(req: Mapping[str, Any], intervals: list[tuple[datetime, datetime]]) -> tuple[list[dict[str, Any]], str, list[dict[str, Any]]]:
    explicit = req.get("transition_boundaries")
    explicit_items = [_parse_boundary(item) for item in explicit] if explicit is not None else []
    fact_segments = _fact_segment_inputs(req.get("p032_fact_segments"), req["start"], req["end"])
    if fact_segments:
        for segment in fact_segments[1:]:
            explicit_items.append({"at": segment["start"], "kind": "EXPLICIT_FACT_SEGMENT_BOUNDARY", "classification": "EXACT_TRANSITION", "source": "CALLER_SUPPLIED_P032_FACT_SEGMENTS"})
    # Caller-supplied exact transitions/fact segments are authoritative for
    # deterministic fixtures and any future validated event provider.  The
    # canonical calculation source is used when no such source is supplied.
    if explicit_items or fact_segments:
        calculated = []
    else:
        calculated = discover_transitions(req["start"], req["end"])
    all_items = explicit_items + [{**item, "at": _parse_datetime(item["at"], "calculated transition") } for item in calculated]
    # Keep only boundaries that can split at least one requested daily interval.
    all_items = [item for item in all_items if any(left < item["at"] < right for left, right in intervals)]
    return all_items, ("EXPLICIT_AND_CALCULATED_TRANSITIONS" if explicit_items else "CALCULATED_TRANSITIONS_EXISTING_KUNDLI_P032"), fact_segments


def search(request: Mapping[str, Any]) -> dict[str, Any]:
    """Search a bounded range and delegate every candidate to RX1."""
    started = time.perf_counter()
    req = _normalise_request(request)
    if req["activity_id"] not in CONTRACTS:
        return _not_ready(req)
    _load_contract(req["activity_id"])  # fail closed before any calculation work
    intervals = _daily_intervals(req["start"], req["end"], req["earliest"], req["latest"])
    if not intervals:
        result = _result_base(req)
        result.update({"search_method": "DAILY_TIME_BOUNDS_EMPTY", "no_result_reason": "No interval remained after the daily time bounds."})
        return result
    try:
        transition_items, method, fact_segments = _transition_inputs(req, intervals)
    except TransitionSourceError as exc:
        result = _result_base(req, capability_state="IMPLEMENTED_VALIDATED_WITH_DEPENDENCY_CONDITION")
        result.update({
            "search_method": "TRANSITION_DEPENDENCY_UNAVAILABLE",
            "result_state": "NO_RESULT",
            "no_result_reason": "CALCULATION_DEPENDENCY_UNAVAILABLE",
            "source_gaps": [{"factor": "PANCHANGA_TRANSITIONS", "reason": str(exc), "blocking": True}],
            "performance": {"wall_ms": round((time.perf_counter() - started) * 1000, 3), "segments_evaluated": 0},
        })
        return result
    transition_groups = _group_transitions(transition_items)
    raw_windows: list[dict[str, Any]] = []
    all_transition_points = [{"at": datetime.fromisoformat(item["at"]), "kind": "+".join(item["kinds"]), "classification": "+".join(item["classifications"]), "source": "+".join(item["sources"])} for item in transition_groups]
    for left, right in intervals:
        points = [item for item in all_transition_points if left < item["at"] < right]
        split = build_candidate_windows(left, right, points)
        for candidate in split:
            window_start = datetime.fromisoformat(candidate["start"])
            window_end = datetime.fromisoformat(candidate["end"])
            representative = _representative(window_start, window_end)
            facts = _facts_for(representative, fact_segments)
            try:
                if facts is None and req.get("p032_facts") is not None:
                    facts = req["p032_facts"]
                if facts is None:
                    facts = position_facts(representative)["p032_facts"]
                rx1_request = {
                    "activity_id": req["activity_id"],
                    "candidate_start": representative,
                    "location": req["location"],
                    "activity_subscope": req["activity_subscope"],
                    "p032_facts": facts,
                    "transition_boundaries": points,
                }
                recommendation = recommend({key: value for key, value in rx1_request.items() if value is not None})
            except (TransitionSourceError, MuhurtaEngineError) as exc:
                recommendation = {
                    "recommendation_state": "ABSTAIN",
                    "abstention_reason": "CALCULATION_DEPENDENCY_UNAVAILABLE",
                    "abstention_explanation": str(exc),
                    "rules_evaluated": [],
                    "supporting_factors": [],
                    "adverse_factors": [],
                    "requirements": ["CALCULATION_DEPENDENCY_UNAVAILABLE"],
                    "unevaluated_source_gaps": [],
                    "source_trace": {"engine_id": ENGINE_ID, "engine_version": ENGINE_VERSION},
                }
            raw_windows.append(_window_from_result(window_start, window_end, representative, recommendation, candidate.get("transition")))
    windows = _merge_windows(raw_windows)
    candidates = [window for window in windows if window["recommendation_state"] in _RECOMMENDABLE]
    result = _result_base(req)
    result.update({
        "search_method": method,
        "transition_types": sorted({kind for item in transition_groups for kind in item["kinds"]}),
        "windows_examined": len(windows),
        "windows_before_merge": len(raw_windows),
        "windows": windows,
        "source_gaps": sorted({json.dumps(gap, sort_keys=True) for window in windows for gap in window.get("source_gaps", [])}),
        "performance": {"wall_ms": round((time.perf_counter() - started) * 1000, 3), "segments_evaluated": len(raw_windows)},
    })
    result["source_gaps"] = [json.loads(item) for item in result["source_gaps"]]
    result["abstained_intervals"] = [window for window in windows if window["recommendation_state"] == "ABSTAIN"]
    if windows:
        first = windows[0]
        result["caution"] = first.get("caution")
        result["consultation_guidance"] = first.get("consultation_guidance")
    if candidates:
        highest = max(_RANK.get(window["recommendation_state"], -1) for window in candidates)
        top = [window for window in candidates if _RANK.get(window["recommendation_state"], -1) == highest]
        result["primary_window"] = top[0]
        result["equivalent_primary_windows"] = top[1:]
        result["alternative_windows"] = [window for window in candidates if window not in top][: req["max_results"]]
        result["result_state"] = "WINDOWS_FOUND" if len(top) == 1 else "EQUIVALENT_TOP_WINDOWS"
    else:
        result["no_result_reason"] = "NO_GOVERNED_RECOMMENDABLE_WINDOW_FOUND"
        result["result_state"] = "NO_RESULT"
    logger.info(
        "engine_id=%s activity=%s range_days=%.3f windows=%s state=%s runtime_ms=%.3f",
        SEARCH_ENGINE_ID,
        req["activity_id"],
        (req["end"] - req["start"]).total_seconds() / 86_400,
        len(windows),
        result.get("result_state"),
        result["performance"]["wall_ms"],
    )
    return result
